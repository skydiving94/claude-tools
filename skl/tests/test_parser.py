import unittest

from helpers import SKL_PATH, FIXTURES, SklCase, load_skl

skl = load_skl()
NOTES = (FIXTURES / "notes" / "SKILL.md").read_text()
MEAL = (FIXTURES / "meal" / "SKILL.md").read_text()


def names(flags):
    return [f["names"][0] for f in flags]


class ParserTests(SklCase):
    def test_extract_block(self):
        block = skl.extract_block(NOTES)
        self.assertTrue(block.startswith("/notes <action> [<target>] [options]"))
        self.assertIn("list:  --format <short|long>", block)
        self.assertNotIn("```", block)
        self.assertNotIn("Not part of the interface", block)

    def test_extract_block_variants(self):
        self.assertIsNone(skl.extract_block("# Title\nno interface here\n"))
        self.assertIsNone(skl.extract_block("## Command interface\ntext only\n## Next\n```\nx\n```\n"))
        crlf = NOTES.replace("\n", "\r\n")
        self.assertEqual(skl.extract_block(crlf), skl.extract_block(NOTES))
        info = NOTES.replace("```\n/notes", "```text\n/notes")
        self.assertEqual(skl.extract_block(info), skl.extract_block(NOTES))

    def test_frontmatter_name(self):
        self.assertEqual(skl.frontmatter_name(NOTES), "notes")
        self.assertEqual(skl.frontmatter_name('---\nname: "a-b"\n---\n'), "a-b")
        self.assertIsNone(skl.frontmatter_name("no frontmatter"))

    def test_actions(self):
        iface = skl.parse_interface(skl.extract_block(NOTES))
        self.assertEqual(iface["usage_line"], "/notes <action> [<target>] [options]")
        self.assertEqual(list(iface["actions"]), ["add", "show", "list"])
        self.assertEqual(iface["actions"]["add"], {"targets": [{"name": "title", "required": True}], "description": "Create a note"})
        self.assertEqual(iface["actions"]["show"]["targets"], [{"name": "title", "required": False}])
        self.assertEqual(iface["actions"]["list"], {"targets": [], "description": "List notes"})

    def test_unparseable(self):
        self.assertIsNone(skl.parse_interface("just some words\nno actions\n"))

    def test_notes_groups(self):
        iface = skl.parse_interface(skl.extract_block(NOTES))
        g = iface["groups"]
        self.assertEqual(g[0]["label"], "Global")
        self.assertIsNone(g[0]["actions"])
        self.assertEqual(g[0]["flags"], [
            {"names": ["--commit"], "takes_value": False, "choices": []},
            {"names": ["--help", "-h"], "takes_value": False, "choices": []}])
        self.assertEqual(names(skl.flags_for(iface, "add")), ["--commit", "--help", "--tag", "--no-index"])
        self.assertEqual(names(skl.flags_for(iface, "show")), ["--commit", "--help"])
        fmt = [f for f in skl.flags_for(iface, "list") if f["names"][0] == "--format"][0]
        self.assertEqual(fmt, {"names": ["--format"], "takes_value": True, "choices": ["short", "long"]})

    def test_meal_groups(self):
        iface = skl.parse_interface(skl.extract_block(MEAL))
        self.assertEqual(list(iface["actions"]), ["add", "update", "duplicate", "remove", "list"])
        self.assertEqual(iface["actions"]["duplicate"]["description"], "Copy with customizations (--as required)")
        self.assertEqual(names(skl.flags_for(iface, "add")),
            ["--commit", "--help", "--sizes", "--parent", "--nutrition", "--no-cost", "--no-sauce-tray", "--no-freezing", "--lang"])
        self.assertEqual(names(skl.flags_for(iface, "duplicate"))[-3:], ["--as", "--swap", "--note"])
        self.assertEqual(names(skl.flags_for(iface, "remove")), ["--commit", "--help", "--cascade"])
        self.assertEqual(names(skl.flags_for(iface, "list")), ["--commit", "--help", "--parent", "--lang", "--search", "--flat"])
        by = {f["names"][0]: f for f in skl.flags_for(iface, "duplicate")}
        self.assertTrue(by["--swap"]["takes_value"])
        self.assertEqual(by["--swap"]["choices"], [])
        self.assertEqual(by["--nutrition"]["choices"], ["label", "none"])
        self.assertEqual(by["--lang"]["choices"], ["en", "zh"])
        self.assertFalse(by["--no-cost"]["takes_value"])
        self.assertIn("--cascade", skl.all_flag_names(iface))
        self.assertIn("-h", skl.all_flag_names(iface))


if __name__ == "__main__":
    unittest.main()
