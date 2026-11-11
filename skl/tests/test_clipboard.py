import unittest
from unittest import mock

from helpers import SklCase
from sklcli.runmode import clipboard
from sklcli.runmode.command import command_lines, join_lines

EXPECTED = '/notes add \\\n"My note" \\\n--tag x \\\n--commit'


class CopyModeTests(SklCase):
    def setUp(self):
        super().setUp()
        self.put_skill(self.tmp / "work" / ".claude" / "skills", "notes")
        self.assertEqual(self.run_cli("sync").returncode, 0)
        self.make_stub("claude")

    def copy(self, *extra):
        return self.run_cli("notes", "add", "My note", "--tag", "x", "--commit", *extra)

    def calls(self):
        return [l for l in self.env_log() if l != "--END--"]

    def env_log(self):
        from pathlib import Path
        p = Path(self.env["SKL_STUB_LOG"])
        return p.read_text().splitlines() if p.exists() else []

    def test_default_copies_exact_text(self):
        self.make_clipboard_stub("pbcopy")
        r = self.copy()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.clipboard_text("pbcopy"), EXPECTED)
        self.assertEqual(r.stdout, "")
        self.assertEqual(r.stderr, 'copied to clipboard (pbcopy): /notes add "My note" --tag x --commit\n')
        self.assertNotIn("claude", self.calls())

    def test_explicit_copy_is_the_default(self):
        self.make_clipboard_stub("pbcopy")
        self.assertEqual(self.copy("--copy").returncode, 0)
        self.assertEqual(self.clipboard_text("pbcopy"), EXPECTED)

    def test_no_trailing_newline(self):
        self.make_clipboard_stub("pbcopy")
        self.run_cli("notes", "list")
        self.assertEqual(self.clipboard_text("pbcopy"), "/notes list")

    def test_order_is_pbcopy_wl_copy_xclip_xsel(self):
        for name in ("xsel", "xclip", "wl-copy", "pbcopy"):
            self.make_clipboard_stub(name)
        self.copy()
        self.assertEqual(self.calls(), ["pbcopy"])
        (self.tmp / "bin" / "pbcopy").unlink()
        self.copy()
        self.assertEqual(self.calls(), ["pbcopy", "wl-copy"])

    def test_tool_arguments(self):
        self.make_clipboard_stub("xclip")
        self.copy()
        self.assertEqual((self.tmp / "xclip.args").read_text().split(), ["-selection", "clipboard"])
        (self.tmp / "bin" / "xclip").unlink()
        self.make_clipboard_stub("xsel")
        self.copy()
        self.assertEqual((self.tmp / "xsel.args").read_text().split(), ["--clipboard", "--input"])

    def test_failing_tool_falls_through_to_the_next(self):
        self.make_clipboard_stub("pbcopy", exit_code=1)
        self.make_clipboard_stub("wl-copy")
        r = self.copy()
        self.assertEqual(r.returncode, 0)
        self.assertEqual(self.calls(), ["pbcopy", "wl-copy"])
        self.assertEqual(self.clipboard_text("wl-copy"), EXPECTED)
        self.assertTrue(r.stderr.startswith("copied to clipboard (wl-copy):"))

    def test_all_tools_failing_prints_the_command(self):
        self.make_clipboard_stub("pbcopy", exit_code=1)
        r = self.copy()
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, EXPECTED + "\n")
        self.assertEqual(r.stderr, "clipboard tool failed, printing the command instead\n")

    def test_no_tool_prints_the_command(self):
        r = self.copy()
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, EXPECTED + "\n")
        self.assertEqual(r.stderr, "no clipboard tool found, printing the command instead\n")
        self.assertEqual(self.calls(), [])

    def test_metacharacters_arrive_literally(self):
        self.make_clipboard_stub("pbcopy")
        r = self.run_cli("notes", "add", "$(touch pwned) `x` ; & |")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.clipboard_text("pbcopy"), '/notes add \\\n"$(touch pwned) `x` ; & |"')
        self.assertFalse((self.tmp / "work" / "pwned").exists())

    def test_invalid_input_copies_nothing(self):
        self.make_clipboard_stub("pbcopy")
        r = self.run_cli("notes", "list", "--nope")
        self.assertEqual(r.returncode, 2)
        self.assertFalse((self.tmp / "pbcopy.stdin").exists())


class ClipboardUnitTests(SklCase):
    def test_runs_without_a_shell_and_sends_plain_bytes(self):
        done = mock.Mock(returncode=0)
        with mock.patch("shutil.which", side_effect=lambda n: "/bin/" + n if n == "xclip" else None), \
                mock.patch("subprocess.run", return_value=done) as run:
            self.assertEqual(clipboard.copy_text("héllo $x"), "xclip")
        argv = run.call_args[0][0]
        self.assertEqual(argv, ["/bin/xclip", "-selection", "clipboard"])
        kw = run.call_args[1]
        self.assertEqual(kw["input"], "héllo $x".encode("utf-8"))
        self.assertFalse(kw.get("shell", False))
        self.assertIs(kw["stdout"], __import__("subprocess").DEVNULL)

    def test_timeout_counts_as_failure(self):
        import subprocess
        with mock.patch("shutil.which", side_effect=lambda n: "/bin/" + n if n in ("pbcopy", "xsel") else None), \
                mock.patch("subprocess.run", side_effect=[subprocess.TimeoutExpired("pbcopy", 5),
                                                          mock.Mock(returncode=0)]):
            self.assertEqual(clipboard.copy_text("x"), "xsel")

    def test_none_when_nothing_installed(self):
        with mock.patch("shutil.which", return_value=None):
            self.assertIsNone(clipboard.copy_text("x"))
            self.assertIsNone(clipboard.first_tool_name())


class CommandLinesTests(SklCase):
    def test_flags_keep_their_values_on_one_line(self):
        lines = command_lines("notes", ["add", "My note", "--tag", "x", "--commit"], {"--tag"})
        self.assertEqual(lines, ["/notes add", '"My note"', "--tag x", "--commit"])
        self.assertEqual(join_lines(lines), EXPECTED)

    def test_boolean_flag_before_a_target_does_not_take_it(self):
        lines = command_lines("notes", ["add", "--commit", "My note"], {"--tag"})
        self.assertEqual(lines, ["/notes add", "--commit", '"My note"'])

    def test_equals_form_and_dash_values(self):
        lines = command_lines("notes", ["add", "t", "--tag=a b", "--tag", "-dash"], {"--tag"})
        self.assertEqual(lines, ["/notes add", "t", '"--tag=a b"', "--tag -dash"])

    def test_pass_through_pairs_a_flag_with_a_following_word(self):
        lines = command_lines("odd", ["go", "--x", "val", "--y", "--z"], None)
        self.assertEqual(lines, ["/odd go", "--x val", "--y", "--z"])

    def test_action_only_is_one_line_with_no_backslash(self):
        self.assertEqual(join_lines(command_lines("notes", ["list"], set())), "/notes list")
        self.assertEqual(join_lines(command_lines("notes", [], None)), "/notes")


if __name__ == "__main__":
    unittest.main()
