# Tutorial verification and completion

Recorded November 8, 2026.

## Completion boundary

The Local AI Agent with Tool Calling and Memory tutorial baseline and selected
extensions are complete. Optional application and research extensions remain
future work. Completion does not mean production readiness or comprehensive
model-quality validation.

The source baseline for the recorded Windows checks is commit `df76246`.
The closeout adds documentation and reproducible offline tests, removes an unused
constant, and normalizes one argument's indentation without changing behavior.

## Evidence inventory

| Check | Result | Evidence and boundary |
| --- | --- | --- |
| Local inference and word count | Passed | Windows CLI: Llama selected word_count and answered 3; before final routing revision |
| Conversation recall without tools | Passed | Windows CLI: recalled copper-91 without tool calls |
| Character count | Passed | Windows CLI: character_count returned 9 for copper-91 |
| Explicit note save/read | Passed | Windows CLI: routing_check_01 round trip returned exact saved text |
| SQLite persistence | Passed | Windows CLI: saved demo_project_name recalled after restarting the process |
| Fact retrieval after middleware | Passed | Windows CLI: Recall fact prefix selected recall_fact |
| Four execution-guard scenarios | Passed | Windows Python script: direct middleware invocation with a fake handler |
| Fresh installation | Passed | Windows, Python 3.14.4: GitHub clone, new venv, pinned install, pip check, compile, import and build |
| Offline routing and storage suite | Passed | Linux, Python 3.12.14: eight test methods with pinned requirements |
| Note discovery | Passed offline | Missing notes directory and sorted saved-note names; no new model-driven Windows listing run claimed |
| Fresh-environment inference | Not tested | Fresh-install script constructs the agent without calling Ollama |
| Systematic model comparison | Deferred | FunctionGemma failure and Llama success are individual observations |

Windows checks were executed by the project owner and supplied as terminal
transcripts. Closeout offline checks were executed separately against the
repository source. No personal note files or fact databases are committed.

## Reproduce the offline checks

After following the README installation steps, run from the repository root:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The eight methods cover:

1. Supported and unsupported routing patterns (12 subcases).
2. Execution guard behavior (four subcases).
3. Note discovery when the notes directory does not exist.
4. Sorted discovery of saved notes, excluding unrelated files.
5. Exact note save/read round trip.
6. Duplicate saves preserving the original note.
7. Invalid note names being rejected before storage creation.
8. Fact save, normalized-key lookup, and update.

The suite imports the real agent module and invokes its tools or middleware
directly. Storage paths are patched to temporary locations. The guard uses a
fake handler, so permitted execution does not perform a real write. No Ollama
inference or model download is required. Agent tool selection, model-generated
arguments, and final-answer quality are outside this suite's scope.

Expected summary:

```text
Ran 8 tests
OK
```

## Reproduce the fresh Windows installation check

In a new directory, clone the repository and follow the README's venv and
dependency steps. Then run:

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m py_compile .\agent.py
.\.venv\Scripts\python.exe -c "import agent; agent.build_agent(); print('PASS: import and build')"
```

The recorded run installed successfully, reported `No broken requirements
found.`, compiled, and printed the import/build success message. It reused the
machine's Python installation and package cache. It was not a clean-machine,
cross-platform, or fresh-Ollama verification.

## Extension audit

| Direction | Implementation or disposition |
| --- | --- |
| Add tools | Six additions beyond time and word count: characters, save/read/list notes, remember/recall facts |
| Read and list files | Restricted to the application's saved notes; arbitrary filesystem browsing is not included |
| Improve prompts and descriptions | Implemented; prompt-only prevention of unsolicited saves proved insufficient |
| Long-term memory | Explicit tool-mediated SQLite facts, with recall across restarts |
| Model experiments | Llama is the working default; FunctionGemma repeated calls even after refresh; root cause unresolved |
| Tool access controls | Deterministic request patterns filter tools and check execution |
| Automated evaluation | Reserved for the separate evaluation tutorial |

## Deferred work

- Wider phrasing support and multi-turn clarification routing.
- LLM-judge evaluation, repeated runs, and systematic model comparisons.
- Stronger argument checks and clearer final responses after tool results.
- CLI timeout/error handling, persistent conversation threads, and multiple users.
- General file access, document retrieval, UI, and deployment.

The routing rules authorize a tool category for the current request. They do
not prove that every generated argument matches the user's intended name or
content. FunctionGemma troubleshooting is documented as an unresolved observation,
not a defect attributed to a particular component.

Source: [Darsh Shah's freeCodeCamp tutorial](https://www.freecodecamp.org/news/how-to-build-your-own-local-ai-agent-with-tool-calling-and-memory/).
