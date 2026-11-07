from datetime import datetime

from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import InMemorySaver

import re
from pathlib import Path
import sqlite3

CHAT_MODEL = "qwen3.5:4b"   # Ollama chat model. Must support tool calling.

SYSTEM_PROMPT = (
    "You are a helpful local assistant. "
    "Use current_time for requests about the current local date or time. "
    "Use word_count for word counts and character_count for character counts. "
    "Character counts include spaces and punctuation. "
    "If the user asks for the length of text without specifying a unit, "
    "ask whether they mean words or characters before calling a counting tool. "
    "Use save_note only when the user explicitly asks to save a note. "
    "Use read_note when the user asks to retrieve a saved note by name. "
    "If the question doesn't need a tool, answer directly. "
    "If a tool returns an error, explain it plainly."
    "Use remember_fact only when the user explicitly asks you to remember a fact. "
    "Use recall_fact to look up previously saved facts when the user asks about them. "
    "Use the same key for saving and recalling. For the user's demo project name, "
    "always use the key demo_project_name. "
)

# ----- Tools -----
@tool
def current_time() -> str:
    """Return the current local date and time.
    Use this when the user asks what time or date it is.
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@tool
def word_count(text: str) -> int:
    """Count whitespace-separated words in text. Use for word-count requests."""
    return len(text.split())

@tool
def character_count(text: str) -> int:
    """Count characters in text, including spaces and punctuation."""
    return len(text)


NOTES_DIR = Path(__file__).resolve().parent / "notes"


def note_path(name: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,40}", name):
        raise ValueError("Use 1 to 40 letters, digits, hyphens, or underscores.")
    return NOTES_DIR / f"note-{name.lower()}.txt"


@tool
def save_note(name: str, text: str) -> str:
    """Save a new local note when the user explicitly asks to save one."""
    try:
        path = note_path(name)
        NOTES_DIR.mkdir(exist_ok=True)
        with path.open("x", encoding="utf-8") as note:
            note.write(text)
    except FileExistsError:
        return f"A note named {name!r} already exists."
    except (ValueError, OSError) as error:
        return f"Could not save the note: {error}"
    return f"Saved note {name!r}."


@tool
def read_note(name: str) -> str:
    """Read a previously saved local note by name."""
    try:
        return note_path(name).read_text(encoding="utf-8")
    except FileNotFoundError:
        return f"No saved note named {name!r} was found."
    except (ValueError, OSError) as error:
        return f"Could not read the note: {error}"

FACTS_DB = Path(__file__).resolve().parent / "facts.sqlite3"


@tool
def remember_fact(key: str, value: str) -> str:
    """Save or update a fact the user explicitly asks you to remember."""
    key = key.strip().lower()
    value = value.strip()
    if not key or not value:
        return "A fact needs both a key and a value."

    try:
        with sqlite3.connect(FACTS_DB, autocommit=False) as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS facts "
                "(key TEXT PRIMARY KEY, value TEXT NOT NULL)"
            )
            db.execute(
                "INSERT INTO facts (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )
    except sqlite3.Error:
        return "Could not save the fact to the local database."
    finally:
        if "db" in locals():
            db.close()

    return f"Remembered {key!r}."


@tool
def recall_fact(key: str) -> str:
    """Look up a saved fact by key, such as demo_project_name."""
    key = key.strip().lower()
    if not FACTS_DB.exists():
        return f"No saved fact found for {key!r}."

    try:
        with sqlite3.connect(FACTS_DB) as db:
            row = db.execute(
                "SELECT value FROM facts WHERE key = ?", (key,)
            ).fetchone()
    except sqlite3.Error:
        return "Could not read the local facts database."
    finally:
        if "db" in locals():
            db.close()

    return row[0] if row else f"No saved fact found for {key!r}."

#TOOLS = [current_time, word_count, character_count, save_note, read_note]
TOOLS = [
    current_time,
    word_count,
    character_count,
    save_note,
    read_note,
    remember_fact,
    recall_fact,
]
# ----- Agent -----

def build_agent():
    model = ChatOllama(model=CHAT_MODEL, temperature=0)

    # InMemorySaver keeps conversation history in memory, keyed by thread ID.
    # When the process exits, the history is gone because of short-term memory.
    checkpointer = InMemorySaver()

    return create_agent(
        model=model,
        tools=TOOLS,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )


def main():
    agent = build_agent()

    # The thread ID tells the checkpointer which conversation to load and save.
    config = {"configurable": {"thread_id": "thread"}}

    print("Ready! Ask the agent something. It remembers the conversation.\n")

    # Track how many messages existed before this turn, so we can slice out
    # only the new ones (tool calls + final answer) from the returned state.
    prev_message_count = 0

    while True:
        question = input("You: ").strip()
        if not question or question.lower() == "exit":
            break

        result = agent.invoke(
            {"messages": [{"role": "user", "content": question}]},
            config=config,
        )

        # Only look at messages added during this turn, not the full history.
        new_messages = result["messages"][prev_message_count:]

        # Print any tool calls made in this turn.
        for msg in new_messages:
            tool_calls = getattr(msg, "tool_calls", None)
            if tool_calls:
                for call in tool_calls:
                    print(f"[tool call] {call['name']}({call['args']})")

        print(f"\nAnswer: {result['messages'][-1].content}\n")

        # Update the count for the next turn.
        prev_message_count = len(result["messages"])

if __name__ == "__main__":
    main()