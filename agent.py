from datetime import datetime

from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents.middleware import wrap_model_call, wrap_tool_call
from langchain_core.messages import HumanMessage, ToolMessage

import re
from pathlib import Path
import sqlite3

import os

CHAT_MODEL = os.environ.get("CHAT_MODEL", "llama3.2:3b")

SYSTEM_PROMPT = (
    "You are a helpful local assistant. "
    "Distinguish conversation history from explicitly saved information. "
    "When the user states information without asking you to save it, "
    "briefly acknowledge it and do not call a storage tool. "
    "When asked what the user just said or mentioned earlier in this "
    "conversation, answer from conversation history without using tools. "

    "Use current_time for requests about the current local date or time. "
    "Use word_count for word counts and character_count for character counts. "
    "Character counts include spaces and punctuation. "
    "If a text-length request does not specify words or characters, "
    "ask which unit the user means before calling a counting tool. "

    "Use save_note only when the user explicitly asks to save a note. "
    "Note names must contain 1 to 40 letters, digits, hyphens, or underscores. "
    "Use read_note only when the user asks to retrieve a saved note. "
    "Use list_notes when the user asks which saved notes are available "
    "or cannot remember a saved note name. "

    "Use remember_fact only when the user explicitly asks you to remember "
    "or persist a fact. "
    "Use recall_fact when the user asks for an explicitly saved fact. "
    "For the user's demo project name, always use demo_project_name "
    "as the key for both saving and recalling. "

    "If a tool returns an error, accurately describe that error. "
    "Do not claim that saving or retrieval succeeded when it failed. "
    "If no tool is needed, answer directly. "

    "Saved-memory operations require these explicit request prefixes: "
    "'Save a note:', 'Read note:', 'List saved notes', "
    "'Remember this fact:', or 'Recall fact:'. "
    "For other wording that requests persistent storage or retrieval, "
    "explain the required prefix without claiming the operation succeeded. "
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

@tool
def list_notes() -> str:
    """List saved note names when the user wants to discover available notes."""
    try:
        if not NOTES_DIR.exists():
            return "No saved notes are available."

        names = sorted(
            path.stem.removeprefix("note-")
            for path in NOTES_DIR.glob("note-*.txt")
            if path.is_file()
        )
    except OSError:
        return "Could not list the local notes."

    return "\n".join(names) if names else "No saved notes are available."


TOOLS = [
    current_time,
    word_count,
    character_count,
    save_note,
    read_note,
    list_notes,
    remember_fact,
    recall_fact,
]

# Deliberately narrow request syntax for this demo.
MEMORY_REQUESTS = {
    "save a note:": "save_note",
    "read note:": "read_note",
    "list saved notes": "list_notes",
    "remember this fact:": "remember_fact",
    "recall fact:": "recall_fact",
}


def allowed_tools_for_turn(state):
    latest_text = ""
    for message in reversed(state["messages"]):
        if isinstance(message, HumanMessage):
            if isinstance(message.content, str):
                latest_text = message.content.strip().casefold()
            break

    # Ordinary conversation starts with no tools available.
    allowed = set()

    if re.match(
        r"^(?:how many words\b|count (?:the )?words\b|word count\b)",
        latest_text,
    ):
        allowed.add("word_count")

    if re.match(
        r"^(?:how many characters\b|count (?:the )?characters\b|"
        r"character count\b)",
        latest_text,
    ):
        allowed.add("character_count")

    if re.match(
        r"^(?:what(?:'s| is) (?:the )?(?:current |local )?"
        r"(?:time|date)\b|what time is it\b|"
        r"what(?:'s| is) today's date\b)",
        latest_text,
    ):
        allowed.add("current_time")

    for prefix, tool_name in MEMORY_REQUESTS.items():
        if prefix == "list saved notes":
            matches = latest_text.rstrip(".?!") == prefix
        else:
            matches = latest_text.startswith(prefix)

        if matches:
            allowed.add(tool_name)
            break

    return allowed

@wrap_model_call
def select_turn_tools(request, handler):
    allowed = allowed_tools_for_turn(request.state)
    selected = [item for item in TOOLS if item.name in allowed]
    return handler(request.override(tools=selected))


@wrap_tool_call
def enforce_turn_tools(request, handler):
    call = request.tool_call
    if call["name"] not in allowed_tools_for_turn(request.state):
        return ToolMessage(
            content=(
                "Blocked: this tool is not enabled for the current request. "
                "Use conversation history to answer when appropriate. "
                "No tool action was performed."
            ),
            tool_call_id=call["id"],
            name=call["name"],
        )
    return handler(request)
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
        middleware=[select_turn_tools, enforce_turn_tools],
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

        # Print tool calls and their actual results.
        for msg in new_messages:
            tool_calls = getattr(msg, "tool_calls", None)
            if tool_calls:
                for call in tool_calls:
                    print(f"[tool call] {call['name']}({call['args']})")

            if getattr(msg, "type", None) == "tool":
                print(f"[tool result] {msg.content}")

        print(f"\nAnswer: {result['messages'][-1].content}\n")

        # Update the count for the next turn.
        prev_message_count = len(result["messages"])

if __name__ == "__main__":
    main()
