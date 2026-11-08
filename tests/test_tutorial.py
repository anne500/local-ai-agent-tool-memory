"""Offline tutorial checks. Run: python -m unittest discover -s tests -v."""

import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from langchain_core.messages import HumanMessage, ToolMessage
import agent


class RoutingAndGuardTests(unittest.TestCase):
    def test_supported_routes(self):
        cases = [
            ('How many words are in "build release integration"?', {"word_count"}),
            ('How many characters are in "copper-91"?', {"character_count"}),
            ("What time is it?", {"current_time"}),
            ("What is today's date?", {"current_time"}),
            ("Save a note: name test, text example.", {"save_note"}),
            ("Read note: test", {"read_note"}),
            ("List saved notes", {"list_notes"}),
            ("Remember this fact: my demo project name is Test.", {"remember_fact"}),
            ("Recall fact: my demo project name.", {"recall_fact"}),
            ("My practice release label is copper-91.", set()),
            ("What practice release label did I just give you?", set()),
            ("Characters, please.", set()),
        ]
        for text, expected in cases:
            with self.subTest(text=text):
                state = {"messages": [HumanMessage(content=text)]}
                self.assertEqual(agent.allowed_tools_for_turn(state), expected)

    def test_execution_guard(self):
        cases = [
            ("ordinary statement blocks saving", ["My label is test-92."], "save_note", False),
            ("explicit save permits saving", ["Save a note: name test, text example."], "save_note", True),
            ("previous permission expires", ["Save a note: name test, text example.", "What label did I mention?"], "save_note", False),
            ("fact retrieval cannot write", ["Recall fact: my demo project name."], "remember_fact", False),
        ]
        for label, turns, tool_name, should_execute in cases:
            with self.subTest(case=label):
                executions = []

                def fake_handler(request):
                    executions.append(request.tool_call["name"])
                    return ToolMessage(content="FAKE_HANDLER_EXECUTED", tool_call_id="guard-test")

                request = SimpleNamespace(
                    state={"messages": [HumanMessage(content=text) for text in turns]},
                    tool_call={"name": tool_name, "args": {}, "id": "guard-test", "type": "tool_call"},
                )
                result = agent.enforce_turn_tools.wrap_tool_call(request, fake_handler)
                self.assertEqual(len(executions), int(should_execute))
                if not should_execute:
                    self.assertTrue(result.content.startswith("Blocked:"))


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.notes = root / "notes"
        notes_patch = patch.object(agent, "NOTES_DIR", self.notes)
        facts_patch = patch.object(agent, "FACTS_DB", root / "facts.sqlite3")
        notes_patch.start()
        facts_patch.start()
        self.addCleanup(notes_patch.stop)
        self.addCleanup(facts_patch.stop)

    def test_empty_note_discovery(self):
        self.assertEqual(agent.list_notes.invoke({}), "No saved notes are available.")

    def test_note_discovery_lists_sorted_saved_names(self):
        for name in ["zebra", "Routing_Check_01"]:
            agent.save_note.invoke({"name": name, "text": "test content"})
        (self.notes / "unrelated.txt").write_text("ignore", encoding="utf-8")
        self.assertEqual(agent.list_notes.invoke({}), "routing_check_01\nzebra")

    def test_note_round_trip(self):
        text = "Tool access is controlled by middleware."
        result = agent.save_note.invoke({"name": "routing_check_01", "text": text})
        self.assertEqual(result, "Saved note 'routing_check_01'.")
        self.assertEqual(agent.read_note.invoke({"name": "routing_check_01"}), text)

    def test_duplicate_note_does_not_overwrite(self):
        agent.save_note.invoke({"name": "example", "text": "original"})
        result = agent.save_note.invoke({"name": "example", "text": "replacement"})
        self.assertIn("already exists", result)
        self.assertEqual(agent.read_note.invoke({"name": "example"}), "original")

    def test_invalid_note_name_does_not_create_storage(self):
        result = agent.save_note.invoke({"name": "invalid name", "text": "example"})
        self.assertTrue(result.startswith("Could not save the note:"))
        self.assertFalse(self.notes.exists())

    def test_fact_save_recall_and_update(self):
        agent.remember_fact.invoke({"key": " Demo_Project_Name ", "value": "First"})
        self.assertEqual(agent.recall_fact.invoke({"key": "demo_project_name"}), "First")
        agent.remember_fact.invoke({"key": "demo_project_name", "value": "Second"})
        self.assertEqual(agent.recall_fact.invoke({"key": "demo_project_name"}), "Second")


if __name__ == "__main__":
    unittest.main()
