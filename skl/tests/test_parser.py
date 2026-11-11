import unittest

from helpers import FIXTURES, SklCase
from sklcli.parsing.interface import all_flag_names, flags_for, parse_interface
from sklcli.parsing.skillmd import extract_block, frontmatter_name
NOTES = (FIXTURES / "notes" / "SKILL.md").read_text()
MEAL = (FIXTURES / "meal" / "SKILL.md").read_text()


def names(flags):
    return [f["names"][0] for f in flags]


class ParserTests(SklCase):
    def test_extract_block(self):
        block = extract_block(NOTES)
        self.assertTrue(block.startswith("/notes <action> [<target>] [options]"))
        self.assertIn("list:  --format <short|long>", block)
        self.assertNotIn("```", block)
        self.assertNotIn("Not part of the interface", block)

    def test_extract_block_variants(self):
        self.assertIsNone(extract_block("# Title\nno interface here\n"))
        self.assertIsNone(extract_block("## Command interface\ntext only\n## Next\n```\nx\n```\n"))
        crlf = NOTES.replace("\n", "\r\n")
        self.assertEqual(extract_block(crlf), extract_block(NOTES))
        info = NOTES.replace("```\n/notes", "```text\n/notes")
        self.assertEqual(extract_block(info), extract_block(NOTES))

    def test_frontmatter_name(self):
        self.assertEqual(frontmatter_name(NOTES), "notes")
        self.assertEqual(frontmatter_name('---\nname: "a-b"\n---\n'), "a-b")
        self.assertIsNone(frontmatter_name("no frontmatter"))

    def test_actions(self):
        iface = parse_interface(extract_block(NOTES))
        self.assertEqual(iface["usage_line"], "/notes <action> [<target>] [options]")
        self.assertEqual(list(iface["actions"]), ["add", "show", "list"])
        self.assertEqual(iface["actions"]["add"], {"targets": [{"name": "title", "required": True}], "description": "Create a note"})
        self.assertEqual(iface["actions"]["show"]["targets"], [{"name": "title", "required": False}])
        self.assertEqual(iface["actions"]["list"], {"targets": [], "description": "List notes"})

    def test_unparseable(self):
        self.assertIsNone(parse_interface("just some words\nno actions\n"))

    def test_notes_groups(self):
        iface = parse_interface(extract_block(NOTES))
        g = iface["groups"]
        self.assertEqual(g[0]["label"], "Global")
        self.assertIsNone(g[0]["actions"])
        self.assertEqual(g[0]["flags"], [
            {"names": ["--commit"], "takes_value": False, "choices": []},
            {"names": ["--help", "-h"], "takes_value": False, "choices": []}])
        self.assertEqual(names(flags_for(iface, "add")), ["--commit", "--help", "--tag", "--no-index"])
        self.assertEqual(names(flags_for(iface, "show")), ["--commit", "--help"])
        fmt = [f for f in flags_for(iface, "list") if f["names"][0] == "--format"][0]
        self.assertEqual(fmt, {"names": ["--format"], "takes_value": True, "choices": ["short", "long"]})

    def test_meal_groups(self):
        iface = parse_interface(extract_block(MEAL))
        self.assertEqual(list(iface["actions"]), ["add", "update", "duplicate", "remove", "list"])
        self.assertEqual(iface["actions"]["duplicate"]["description"], "Copy with customizations (--as required)")
        self.assertEqual(names(flags_for(iface, "add")),
            ["--commit", "--help", "--sizes", "--parent", "--nutrition", "--no-cost", "--no-sauce-tray", "--no-freezing", "--lang"])
        self.assertEqual(names(flags_for(iface, "duplicate"))[-3:], ["--as", "--swap", "--note"])
        self.assertEqual(names(flags_for(iface, "remove")), ["--commit", "--help", "--cascade"])
        self.assertEqual(names(flags_for(iface, "list")), ["--commit", "--help", "--parent", "--lang", "--search", "--flat"])
        by = {f["names"][0]: f for f in flags_for(iface, "duplicate")}
        self.assertTrue(by["--swap"]["takes_value"])
        self.assertEqual(by["--swap"]["choices"], [])
        self.assertEqual(by["--nutrition"]["choices"], ["label", "none"])
        self.assertEqual(by["--lang"]["choices"], ["en", "zh"])
        self.assertFalse(by["--no-cost"]["takes_value"])
        self.assertIn("--cascade", all_flag_names(iface))
        self.assertIn("-h", all_flag_names(iface))


if __name__ == "__main__":
    unittest.main()
