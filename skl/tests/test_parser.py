import unittest

from helpers import SKL_PATH, FIXTURES, SklCase, load_skl

skl = load_skl()
NOTES = (FIXTURES / "notes" / "SKILL.md").read_text()


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
        self.assertEqual(iface["groups"], [])

    def test_unparseable(self):
        self.assertIsNone(skl.parse_interface("just some words\nno actions\n"))


if __name__ == "__main__":
    unittest.main()
