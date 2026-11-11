import pathlib
import re

from helpers import SklCase, load_skl

skl = load_skl()


class HelpTests(SklCase):
    def sync_notes(self):
        self.put_skill(self.tmp / "home" / ".claude" / "skills", "notes")
        r = self.run_cli("sync")
        self.assertEqual(r.returncode, 0, r.stderr)

    # version
    def test_version(self):
        for flag in ("--version", "-V"):
            r = self.run_cli(flag)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertRegex(r.stdout, r"^skl \d+\.\d+\.\d+\n$")
            self.assertEqual(r.stdout, "skl " + skl.__version__ + "\n")
            self.assertEqual(r.stderr, "")

    def test_version_only_when_sole_argument(self):
        self.sync_notes()
        r = self.run_cli("notes", "list", "--version")
        self.assertEqual(r.returncode, 2)
        self.assertIn("unknown flag '--version'", r.stderr)

    # top-level help
    def test_top_level_help_identical(self):
        outs = []
        for args in (("--help",), ("-h",), ("help",), ()):
            r = self.run_cli(*args)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(r.stderr, "")
            outs.append(r.stdout)
        self.assertEqual(len(set(outs)), 1)
        self.assertTrue(outs[0].startswith("skl 0.1.0 - "))
        self.assertEqual(outs[0].splitlines()[0],
                         "skl %s - run command-style Claude skills from your shell" % skl.__version__)

    def test_help_lists_every_builtin(self):
        out = self.run_cli("--help").stdout
        for name in skl._BUILTINS:
            self.assertRegex(out, r"(?m)^  %s\b" % re.escape(name))
        self.assertEqual([c[0] for c in skl._COMMANDS_HELP], list(skl._BUILTINS))
        self.assertIn("  help [<command>]        Show this help, or help for one command\n", out)
        self.assertIn("  show <skill> [--parsed] Print a skill's usage block\n", out)

    def test_help_sections(self):
        out = self.run_cli("--help").stdout
        for part in ("Usage:\n  skl <command> [args]\n  skl <skill> <action> [<target>] [options] [--print | --app]\n",
                     "Run options:\n  --print      Run non-interactively",
                     "  --version    Show the version\n",
                     "Environment:\n  SKL_SKILL_PATH   Extra skill folders",
                     "Indexed skills:\n"):
            self.assertIn(part, out)

    def test_help_indexed_skills(self):
        self.sync_notes()
        out = self.run_cli("--help").stdout
        self.assertRegex(out, r"(?m)^  notes +add, show, list$")

    def test_help_empty_index(self):
        out = self.run_cli("--help").stdout
        self.assertIn("none indexed, run 'skl sync'", out)

    def test_help_corrupt_index(self):
        self.sync_notes()
        (pathlib.Path(self.env["XDG_DATA_HOME"]) / "skl" / "index.json").write_text("{broken")
        r = self.run_cli("--help")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stderr, "")
        self.assertTrue(r.stdout.startswith("skl 0.1.0 - "))
        self.assertIn("none indexed, run 'skl sync'", r.stdout)

    # per-command help
    def test_each_builtin_help(self):
        for name, usage, _s, _d in skl._COMMANDS_HELP:
            for args in ((name, "--help"), (name, "-h"), ("help", name)):
                r = self.run_cli(*args)
                self.assertEqual(r.returncode, 0, (args, r.stderr))
                self.assertEqual(r.stderr, "")
                self.assertTrue(r.stdout.startswith("usage: skl %s\n\n" % usage), (args, r.stdout))
                self.assertGreater(len(r.stdout.splitlines()), 2)

    def test_show_and_run_extras(self):
        self.assertIn("--parsed", self.run_cli("show", "--help").stdout.split("\n\n", 1)[1])
        out = self.run_cli("run", "--help").stdout
        self.assertIn("--print", out)
        self.assertIn("--app", out)

    def test_sync_help_no_error(self):
        r = self.run_cli("sync", "--help")
        self.assertEqual(r.returncode, 0)
        self.assertTrue(r.stdout.startswith("usage: skl sync"))

    def test_show_skill_help_is_command_help(self):
        self.sync_notes()
        r = self.run_cli("show", "notes", "--help")
        self.assertEqual(r.returncode, 0)
        self.assertTrue(r.stdout.startswith("usage: skl show <skill> [--parsed]\n"))

    def test_run_skill_help_is_skill_usage(self):
        self.sync_notes()
        expect = self.run_cli("show", "notes").stdout
        r = self.run_cli("run", "notes", "list", "--help")
        self.assertEqual((r.returncode, r.stdout), (0, expect))
        r = self.run_cli("notes", "--help")
        self.assertEqual((r.returncode, r.stdout), (0, expect))

    def test_run_alone_help(self):
        r = self.run_cli("run", "-h")
        self.assertTrue(r.stdout.startswith("usage: skl run <skill> [args]\n"))

    def test_help_unknown_command(self):
        r = self.run_cli("help", "nosuch")
        self.assertEqual(r.returncode, 2)
        self.assertEqual(r.stdout, "")
        self.assertEqual(r.stderr, "error: unknown command 'nosuch'\nrun 'skl help' to see the commands\n")
