import io
import os
import subprocess
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock

from helpers import SklCase
from sklcli.cli import main
from sklcli.runmode.command import build_command, quote_arg
from sklcli.runmode.modes import RunMode, split_mode


class RunTests(SklCase):
    def setUp(self):
        super().setUp()
        self.put_skill(self.tmp / "work" / ".claude" / "skills", "notes")
        r = self.run_cli("sync")
        self.assertEqual(r.returncode, 0, r.stderr)

    def log(self):
        p = Path(self.env["SKL_STUB_LOG"])
        return p.read_text().splitlines() if p.exists() else []

    def test_quote_and_build(self):
        self.assertEqual(quote_arg("farro=rice"), "farro=rice")
        self.assertEqual(quote_arg("My note"), '"My note"')
        self.assertEqual(quote_arg('say "hi" \\ $x'), '"say \\"hi\\" \\\\ $x"')
        self.assertEqual(quote_arg(""), '""')
        self.assertEqual(build_command("notes", ["add", "My note", "--tag", "a b"]),
                         '/notes add "My note" --tag "a b"')

    def test_run_mode(self):
        self.make_stub("claude")
        r = self.run_cli("notes", "add", "My $HOME note", "--commit", "--run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.log(), ['/notes add "My $HOME note" --commit', "--END--"])

    def test_tricky_args_intact(self):
        self.make_stub("claude")
        r = self.run_cli("notes", "add", 'say "hi" $x', "--tag=a b", "--tag", "-dash", "--run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.log(),
                         ['/notes add "say \\"hi\\" $x" "--tag=a b" --tag -dash', "--END--"])

    def test_print_mode_and_exit_code(self):
        self.make_stub("claude", exit_code=3)
        r = self.run_cli("run", "notes", "list", "--print")
        self.assertEqual(r.returncode, 3)
        self.assertEqual(self.log(), ["-p", "/notes list", "--END--"])

    def test_app_mode(self):
        self.make_stub("xdg-open")
        self.make_stub("open")
        r = self.run_cli("notes", "add", "My note", "--app")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(self.log()[0], "https://claude.ai/new?q=%2Fnotes%20add%20%22My%20note%22")
        self.assertIn("opening https://claude.ai/new?q=", r.stderr)

    def test_app_mode_without_opener_prints_url(self):
        r = self.run_cli("notes", "list", "--app")
        self.assertEqual(r.stdout.strip(), "https://claude.ai/new?q=%2Fnotes%20list")

    def test_help_and_validation_do_not_call_claude(self):
        self.make_stub("claude")
        r = self.run_cli("notes", "add", "--help")
        self.assertEqual(r.returncode, 0)
        self.assertTrue(r.stdout.startswith("/notes <action>"))
        r = self.run_cli("notes", "list", "--nope", "--run")
        self.assertEqual(r.returncode, 2)
        self.assertEqual(r.stderr.splitlines(),
                         ["error: unknown flag '--nope'", "usage: /notes <action> [<target>] [options]"])
        self.assertFalse(Path(self.env["SKL_STUB_LOG"]).exists())

    def test_missing_claude(self):
        for flag in ("--run", "--print"):
            r = self.run_cli("notes", "list", flag)
            self.assertEqual(r.returncode, 127, flag)
            self.assertIn("claude CLI not found", r.stderr)

    def test_copy_does_not_need_claude(self):
        r = self.run_cli("notes", "list")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("claude CLI not found", r.stderr)

    def test_unknown_skill(self):
        r = self.run_cli("nots", "list")
        self.assertEqual(r.returncode, 2)
        self.assertIn("error: unknown skill 'nots'", r.stderr)
        self.assertIn("did you mean: notes", r.stderr)
        self.assertNotIn("Traceback", r.stderr)

    def test_split_mode_clash(self):
        e = {"interface": {"usage_line": "", "actions": {}, "groups": [{"label": "Global", "actions": None,
             "flags": [{"names": ["--print", "--copy"], "takes_value": False, "choices": []}]}]}}
        self.assertEqual(split_mode(e, ["go", "--print"]), (RunMode.COPY, ["go", "--print"]))
        self.assertEqual(split_mode(e, ["go", "--skl-print"]), (RunMode.PRINT, ["go"]))
        self.assertEqual(split_mode(e, ["go", "--copy"]), (RunMode.COPY, ["go", "--copy"]))
        self.assertEqual(split_mode(e, ["go", "--skl-copy"]), (RunMode.COPY, ["go"]))
        self.assertEqual(split_mode(e, ["go", "--run"]), (RunMode.RUN, ["go"]))

    def test_doctor(self):
        r = self.run_cli("doctor")
        self.assertEqual(r.returncode, 1)
        self.assertIn("claude: not found", r.stdout)
        self.assertIn("clipboard: none (--copy prints the command instead)", r.stdout)
        self.make_stub("claude")
        self.make_clipboard_stub("wl-copy")
        r = self.run_cli("doctor")
        self.assertEqual(r.returncode, 0)
        self.assertIn("sign-in: ok", r.stdout)
        self.assertIn("clipboard: wl-copy\n", r.stdout)
        self.assertIn("skills: 1 indexed (0 pass-through)", r.stdout)

    def run_main(self, argv):
        self.make_stub("claude")
        with mock.patch.dict(os.environ, self.env), mock.patch("os.execvp") as ex:
            code = main(argv)
        return code, ex

    def test_run_and_print_exec_claude(self):
        code, ex = self.run_main(["notes", "add", "My note", "--run"])
        ex.assert_called_once_with("claude", ["claude", '/notes add "My note"'])
        code, ex = self.run_main(["notes", "list", "--print"])
        ex.assert_called_once_with("claude", ["claude", "-p", "/notes list"])

    def test_copy_mode_never_execs_claude(self):
        with redirect_stderr(io.StringIO()), mock.patch("sys.stdout", io.StringIO()):
            code, ex = self.run_main(["notes", "add", "My note"])
        self.assertEqual(code, 0)
        ex.assert_not_called()

    def test_exec_failure_reports_error(self):
        self.make_stub("claude")
        err = io.StringIO()
        with mock.patch.dict(os.environ, self.env), \
                mock.patch("os.execvp", side_effect=OSError(13, "Permission denied")), \
                redirect_stderr(err):
            code = main(["notes", "list", "--run"])
        self.assertEqual(code, 1)
        self.assertEqual(err.getvalue(), "error: Permission denied\n")

    def test_doctor_closes_stdin_for_claude(self):
        self.make_stub("claude")
        real = subprocess.run
        calls = []

        def spy(*a, **kw):
            calls.append(kw)
            return real(*a, **kw)

        with mock.patch.dict(os.environ, self.env), \
                mock.patch("subprocess.run", side_effect=spy), \
                mock.patch("sys.stdout", io.StringIO()):
            main(["doctor"])
        self.assertEqual(len(calls), 2)
        for kw in calls:
            self.assertIs(kw.get("stdin"), subprocess.DEVNULL)

    def test_unknown_skill_with_empty_index_hints_sync(self):
        r = self.run_cli("remove", "notes")
        self.assertEqual(r.returncode, 0, r.stderr)
        r = self.run_cli("notes", "list")
        self.assertEqual(r.returncode, 2)
        self.assertEqual(r.stderr.splitlines(), ["error: unknown skill 'notes'",
                                                 "run 'skl sync' to index your skills"])

    def test_ctrl_c_returns_130_without_traceback(self):
        err = io.StringIO()
        with mock.patch.dict(os.environ, self.env), \
                mock.patch("sklcli.store.index.load_index", side_effect=KeyboardInterrupt), \
                redirect_stderr(err):
            code = main(["list"])
        self.assertEqual(code, 130)
        self.assertNotIn("Traceback", err.getvalue())


if __name__ == "__main__":
    unittest.main()
