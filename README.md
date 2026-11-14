# 🤖 Local AI Agent with Tool Calling and Memory

![Project overview and reading map](assets/readme-overview.svg)

**🟦 Learn AI · 🟩 Portfolio evidence · 🟪 PhD research · 🟠 Planned work**

<a id="explore-the-project"></a>

## 🧭 Explore the project

[🧩 Architecture](#architecture) · [🚀 Setup](#windows-powershell-setup) · [🧪 Results & verification](#tutorial-completion-and-reproducible-checks) · [🗂️ Evidence & guides](#verified-manual-demonstrations) · [🎨 Visual standard](VISUAL_STYLE.md)

🎨 [Shared architecture colors and diagram conventions](VISUAL_STYLE.md)

> **📚 Tutorial foundation:** This learning project is based on [Darsh Shah's freeCodeCamp tutorial](https://www.freecodecamp.org/news/how-to-build-your-own-local-ai-agent-with-tool-calling-and-memory/). See [Tutorial Acknowledgment and Attribution](#tutorial-acknowledgment-and-attribution) for the original source and the repository's extensions.


![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-Local%20Inference-222222)
![Llama](https://img.shields.io/badge/Llama-3.2%203B-7C3AED)
![SQLite](https://img.shields.io/badge/SQLite-Durable%20Memory-003B57?logo=sqlite&logoColor=white)

A Python command-line assistant using local Ollama inference, eight tools,
conversation history, text-file notes, and SQLite fact memory.

Middleware selects available tools for each user turn and checks tool access
before execution. Ordinary conversation starts with no tools available.

Built from Darsh Shah's freeCodeCamp tutorial and extended with note storage,
note discovery, character counting, durable facts, and tool-access middleware.

| 🟦 Learn AI | 🟩 Explore the implementation | 🟪 Inspect the evidence |
| --- | --- | --- |
| Tool calling | Eight Python tools | Tool-call and tool-result traces |
| Conversation memory | LangGraph InMemorySaver | Recall within a session |
| Persistent memory | Text files and SQLite | Saved information across restarts |
| Tool access | Selection and execution middleware | Request-specific tool availability |

## 🟦 Base tutorial

The working tutorial builds a local LangChain and Ollama agent with time and word-count tools and conversation history within a thread. The article discusses long-term memory as a next step. [Darsh Shah’s freeCodeCamp tutorial: How to Build Your Own Local AI Agent with Tool Calling and Memory](https://www.freecodecamp.org/news/how-to-build-your-own-local-ai-agent-with-tool-calling-and-memory/)

## 🧩 Extensions added in Project 2

| Extension | What this project added |
| --- | --- |
| **Additional tools** | Added character counting and text-file note saving, reading, and discovery. |
| **Durable fact memory** | Implemented explicit SQLite fact storage and recall across process restarts. |
| **Tool access and diagnostics** | Added per-turn tool selection and execution checks, model configuration, and tool-result logging. |
| **Verification** | Recorded Windows demonstrations and added offline checks for routing, access control, and storage. |

See [verified demonstrations](#verified-manual-demonstrations) and [reproducible checks](#tutorial-completion-and-reproducible-checks).

<a id="architecture"></a>

## 🧩 Architecture

```mermaid
flowchart TD
    U["User request"] --> R["Request-pattern rules"]
    R --> A["LangChain agent + local Llama"]
    S["Session history"] <--> A
    A --> G["Tool execution check"]
    G --> C["Time and counting"]
    G --> N["Note tools"]
    G --> F["Fact tools"]
    N <--> D["Local text files"]
    F <--> Q["SQLite database"]
    A --> O["Final answer"]

    %% Shared architecture palette: see VISUAL_STYLE.md
    classDef default fill:#F8FAFC,stroke:#475569,color:#0F172A,stroke-width:2px;
    classDef process fill:#DBEAFE,stroke:#2563EB,color:#172554,stroke-width:2px;
    classDef model fill:#EDE9FE,stroke:#7C3AED,color:#3B0764,stroke-width:2px;
    classDef store fill:#CCFBF1,stroke:#0F766E,color:#134E4A,stroke-width:2px;
    classDef decision fill:#FEF3C7,stroke:#B45309,color:#78350F,stroke-width:2px;
    classDef human fill:#FFEDD5,stroke:#C2410C,color:#7C2D12,stroke-width:2px;
    classDef output fill:#DCFCE7,stroke:#15803D,color:#14532D,stroke-width:2px;
    classDef failure fill:#FEE2E2,stroke:#B91C1C,color:#7F1D1D,stroke-width:2px;
    class U,R,G,C,N,F process;
    class A model;
    class S,D,Q store;
    class O output;
```

<a id="features"></a>

## ✨ Features

| Capability | Implementation |
| --- | --- |
| Default local model | llama3.2:3b through ChatOllama |
| Model override | CHAT_MODEL environment variable |
| Local date and time | current_time |
| Whitespace-separated word count | word_count |
| Character count | character_count using Python len() |
| Save, read, and discover notes | save_note, read_note, list_notes |
| Conversation history | InMemorySaver, keyed by thread ID |
| Persistent facts | remember_fact and recall_fact |
| Tool access | select_turn_tools and enforce_turn_tools |
| CLI visibility | Tool calls, tool results, and final answers |

<a id="windows-powershell-setup"></a>

## 🚀 Windows PowerShell setup

Install Python 3.14, Git, and Ollama, then run:

```powershell
git clone https://github.com/anne500/local-ai-agent-tool-memory.git
Set-Location local-ai-agent-tool-memory

ollama pull llama3.2:3b
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

$env:CHAT_MODEL = "llama3.2:3b"
.\.venv\Scripts\python.exe .\agent.py
```

Ensure Ollama is running before launching the agent.
Type `exit` to end a session.

The verified development environment used Windows, Python 3.14.4,
and Ollama 0.40.5. `requirements.txt` records installed package versions.
A fresh GitHub checkout and virtual environment on the development Windows
machine passed dependency installation, `pip check`, compilation, and agent
construction. This check did not exercise inference or a new Ollama installation.

<a id="supported-requests"></a>

## 💬 Supported requests

Routing uses explicit prefixes and regular expressions. It does not provide
general natural-language intent recognition.

| Operation | Example request |
| --- | --- |
| Word count | How many words are in "build release integration"? |
| Character count | How many characters are in "copper-91"? |
| Local time | What time is it? |
| Local date | What is today's date? |
| Save note | Save a note: name release_plan, text Run the CI smoke test. |
| Read note | Read note: release_plan |
| Discover notes | List saved notes |
| Save fact | Remember this fact: my demo project name is Local Agent Memory Lab. |
| Retrieve fact | Recall fact: my demo project name. |

Memory prefixes are case-insensitive. Counting and time requests must match
the patterns in `allowed_tools_for_turn()`.

For an ambiguous text-length question, the prompt instructs the assistant to
ask whether the user means words or characters. After clarification, use a
complete supported request, such as `How many characters are in "Cedar CI!"?`.
A reply such as `Characters, please.` does not enable a tool by itself.

<a id="verified-manual-demonstrations"></a>

## 🧪 Verified manual demonstrations

<a id="conversation-history-without-tools"></a>

### 💬 Conversation history without tools

```text
You: My practice release label is copper-91.
Answer: You're using a practice release label for your project.
        What would you like to do with that label?

You: What practice release label did I just give you?
Answer: You mentioned that your practice release label is copper-91.
```

Neither turn produced a tool call.

<a id="character-counting"></a>

### 🔢 Character counting

```text
You: How many characters are in "copper-91"?
[tool call] character_count({'text': 'copper-91'})
[tool result] 9

Answer: There are 9 characters in the text "copper-91".
```

Word counting also returned 3 for `build release integration` in an
earlier Llama agent run, before the final routing revision.

<a id="explicit-note-saving-and-retrieval"></a>

### 💾 Explicit note saving and retrieval

```text
You: Save a note: name routing_check_01, text Tool access is controlled by middleware.
[tool call] save_note({'name': 'routing_check_01', 'text': 'Tool access is controlled by middleware.'})
[tool result] Saved note 'routing_check_01'.

You: Read note: routing_check_01
[tool call] read_note({'name': 'routing_check_01'})
[tool result] Tool access is controlled by middleware.
```

The operations succeeded. The model's final responses did not clearly
confirm the save or attribute the retrieved text to the note file.

<a id="facts-across-process-restarts"></a>

### 💾 Facts across process restarts

The agent saved `Local Agent Memory Lab` under `demo_project_name`.
After exiting and restarting, `recall_fact` retrieved that value.

Following the middleware introduction, this request also retrieved it:

```text
You: Recall fact: my demo project name.
[tool call] recall_fact({'key': 'demo_project_name'})
[tool result] Local Agent Memory Lab
```

<a id="tutorial-completion-and-reproducible-checks"></a>

## 🧪 Tutorial completion and reproducible checks

The tutorial baseline and selected extensions are complete. This checkpoint
includes eight tools, session history, persistent notes and facts, model
configuration, tool-result logging, and explicit per-turn tool access.

Four execution-guard scenarios passed in the Windows development environment:
ordinary statements cannot save notes, explicit saves reach a fake handler,
previous-turn permission expires, and fact retrieval cannot enable fact writes.
These checks use a fake handler and do not invoke a model or write personal data.

The repository now preserves these checks alongside routing and temporary-storage
tests, including note discovery, duplicate-save protection, invalid names, and
fact updates. Run them from the repository root after installing dependencies:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Eight automated test methods passed during closeout on Linux with Python 3.12.14
and the pinned requirements. Storage tests use temporary directories and databases.
This is additional offline coverage, not a substitute for the Windows manual
agent demonstrations or a model-quality benchmark.

See [verification details](docs/verification.md) for evidence boundaries,
reproduction instructions, extension coverage, and deferred work.

The next evaluation tutorial is a separate learning milestone. No evaluation
harness or LLM-judge results are included in this completion claim.

<a id="memory-and-storage"></a>

## 💾 Memory and storage

| Storage | Lifetime | Behavior |
| --- | --- | --- |
| Conversation history | Current Python process | One CLI thread; lost on exit |
| notes/note-NAME.txt | Across restarts | Explicit note saves; existing notes are not overwritten |
| facts.sqlite3 | Across restarts | Facts saved by key; an existing key is updated |

Note names accept 1 to 40 ASCII letters, digits, hyphens, or underscores.
Filenames are normalized to lowercase.

Fact keys are stripped and lowercased. Retrieval uses exact keys.
The prompt specifies `demo_project_name` for the demo project name.

The virtual environment, Python cache, notes, SQLite database files, and
agent backup are excluded by `.gitignore`.

<a id="model-troubleshooting-evidence"></a>

## 🔬 Model troubleshooting evidence

| Model | Observed behavior |
| --- | --- |
| functiongemma:270m | Repeated word_count calls and reached the generation limit |
| llama3.2:3b | One correctly formed word_count call and normal termination |

FunctionGemma's repetition persisted after refreshing the official model.
It also occurred with an explicitly formatted raw prompt and in a request
using `num_gpu: 0`. CPU placement was not independently confirmed.

The root cause remains unresolved. These observations do not establish a
general model ranking or isolate a specific Ollama defect.

Llama is the working default. Other installed models have not been
systematically evaluated against the final middleware implementation.

<a id="scope-and-limitations"></a>

## ⚠️ Scope and limitations

- Evidence combines manual agent checks and offline automated checks, not a benchmark.
- Narrow request patterns restrict supported phrasing and combined requests.
- Middleware controls tool availability; model-selected arguments can still be wrong.
- Guard checks exercise middleware directly; they do not simulate every full-agent failure path.
- Final responses can be vague or misinterpret tool results.
- Character counting measures Unicode code points, not visual grapheme clusters.
- The CLI uses one conversation thread and shared local storage.
- The CLI does not yet handle invocation failures or recursion-limit errors gracefully.
- Public multi-user hosting, authentication, and broader model evaluation are future work.

<a id="tutorial-and-attribution"></a>

<a id="tutorial-acknowledgment-and-attribution"></a>

## 📚 Tutorial Acknowledgment and Attribution

We acknowledge **Darsh Shah** as the author of the foundational tutorial published by **freeCodeCamp**:

**[How to Build Your Own Local AI Agent with Tool Calling and Memory](https://www.freecodecamp.org/news/how-to-build-your-own-local-ai-agent-with-tool-calling-and-memory/)**  
Published: July 7, 2026.

| Credit and provenance | Description |
| --- | --- |
| 👨‍🏫 Original author | Darsh Shah |
| 📚 Publisher | freeCodeCamp |
| 🧱 Tutorial foundation | A local tool-calling agent with time and word-count tools and conversational memory. |
| 🛠️ Repository adaptations and extensions | Character counting, note storage and discovery, SQLite fact memory, model configuration, per-turn tool-access middleware, logging, and verification. |

The tutorial is credited for the original learning foundation. Repository-specific adaptations, experiments, verification records, and research connections are documented separately in the project documentation.


Starting point: Darsh Shah's freeCodeCamp tutorial,
[How to Build Your Own Local AI Agent with Tool Calling and Memory](https://www.freecodecamp.org/news/how-to-build-your-own-local-ai-agent-with-tool-calling-and-memory/).

The tutorial baseline introduced time and word-count tools with session memory.
This project adds character counting, note storage and discovery, SQLite facts,
model selection through an environment variable, tool-result logging, and
request-specific tool access.

