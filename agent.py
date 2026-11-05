from datetime import datetime

from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import InMemorySaver

import re
from pathlib import Path

CHAT_MODEL = "qwen3.5:4b"   # Ollama chat model. Must support tool calling.

SYSTEM_PROMPT = (
    "You are a helpful assistant with access to tools for getting the current time and counting words in text. "
    "Use tools when the user's request needs one. "
    "If the question doesn't need a tool, answer directly. "
    "If a tool returns an error, explain the error plainly."
    "You can get the local time, count words, and save or read local notes. "
    "Save notes only when explicitly requested and retrieve saved notes by name. "
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
    """Count the number of words in a piece of text.
    Use this when the user asks how long a piece of writing is,
    or asks you to count the words in something they've shared.
    Returns the word count as an integer.
    """
    return len(text.split())


#TOOLS = [current_time, word_count]
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


TOOLS = [current_time, word_count, save_note, read_note]

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