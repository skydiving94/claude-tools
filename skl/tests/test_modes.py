import unittest
from pathlib import Path

from helpers import SklCase
from sklcli.errors import UsageError
from sklcli.runmode.modes import DEFAULT_MODE, RunMode, match_mode_flag, mode_flag_for, split_mode

PLAIN = {"interface": None}


def skill_with(*names):
    flags = [{"names": [n], "takes_value": False, "choices": []} for n in names]
    return {"interface": {"usage_line": "", "actions": {},
                          "groups": [{"label": "Global", "actions": None, "flags": flags}]}}


class ModeTests(SklCase):
    def test_default_is_copy(self):
        self.assertIs(DEFAULT_MODE, RunMode.COPY)
        self.assertEqual(split_mode(PLAIN, ["list"]), (RunMode.COPY, ["list"]))

    def test_each_flag_selects_its_mode(self):
        for mode in RunMode:
            self.assertEqual(split_mode(PLAIN, ["list", mode.flag]), (mode, ["list"]))
            self.assertEqual(split_mode(PLAIN, [mode.flag, "list"]), (mode, ["list"]))
            self.assertEqual(split_mode(PLAIN, ["list", mode.skl_flag]), (mode, ["list"]))

    def test_flag_names(self):
        self.assertEqual([m.flag for m in RunMode], ["--copy", "--run", "--print", "--app"])
        self.assertEqual(RunMode.RUN.skl_flag, "--skl-run")

    def test_more_than_one_mode_is_an_error(self):
        message = "choose only one of --copy, --run, --print, --app"
        for args in (["--copy", "--run"], ["--print", "--app"], ["--run", "--skl-print"],
                     ["--copy", "--copy"], ["--run", "--skl-run"], ["--app", "--app"]):
            with self.assertRaises(UsageError) as c:
                split_mode(PLAIN, ["x"] + args)
            self.assertEqual(str(c.exception), message, args)

    def test_skill_flags_win_for_every_mode_name(self):
        for mode in RunMode:
            skill = skill_with(mode.flag)
            self.assertEqual(split_mode(skill, ["go", mode.flag]), (RunMode.COPY, ["go", mode.flag]))
            self.assertEqual(split_mode(skill, ["go", mode.skl_flag]), (mode, ["go"]))
            self.assertEqual(mode_flag_for(mode, {mode.flag}), mode.skl_flag)
            self.assertEqual(mode_flag_for(mode, set()), mode.flag)

    def test_skl_prefix_is_accepted_without_a_clash(self):
        self.assertEqual(split_mode(PLAIN, ["--skl-run"]), (RunMode.RUN, []))

    def test_clash_on_one_mode_leaves_the_others(self):
        skill = skill_with("--run")
        self.assertEqual(split_mode(skill, ["go", "--run", "--copy"]), (RunMode.COPY, ["go", "--run"]))
        self.assertEqual(split_mode(skill, ["go", "--run", "--print"]), (RunMode.PRINT, ["go", "--run"]))

    def test_match_mode_flag(self):
        self.assertIsNone(match_mode_flag("--tag", set()))
        self.assertIsNone(match_mode_flag("--copy", {"--copy"}))
        self.assertIs(match_mode_flag("--skl-copy", {"--copy"}), RunMode.COPY)


class SkillFlagClashCliTests(SklCase):
    """A skill that defines --run and --copy keeps them; skl's modes become --skl-run and --skl-copy."""

    def setUp(self):
        super().setUp()
        self.put_skill(self.tmp / "work" / ".claude" / "skills", "clash")
        self.assertEqual(self.run_cli("sync").returncode, 0)
        self.make_stub("claude")
        self.make_clipboard_stub("pbcopy")

    def log(self):
        p = Path(self.env["SKL_STUB_LOG"])
        return p.read_text().splitlines() if p.exists() else []

    def test_plain_flags_go_to_the_skill_in_copy_mode(self):
        r = self.run_cli("clash", "go", "--run", "--copy")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.clipboard_text("pbcopy"), "/clash go \\\n--run \\\n--copy")
        self.assertNotIn("claude", self.log())

    def test_skl_prefixed_flags_select_the_modes(self):
        r = self.run_cli("clash", "go", "--run", "--skl-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.log(), ["/clash go --run", "--END--"])
        r = self.run_cli("clash", "go", "--skl-copy")
        self.assertEqual(self.clipboard_text("pbcopy"), "/clash go")

    def test_two_skl_modes_still_conflict(self):
        r = self.run_cli("clash", "go", "--skl-run", "--skl-copy")
        self.assertEqual(r.returncode, 2)
        self.assertIn("choose only one of", r.stderr)

    def test_completion_offers_the_prefixed_names(self):
        out = self.run_cli("__complete", "--", "clash", "go", "--").stdout.split()
        self.assertEqual(out, ["--run", "--copy", "--help", "--skl-copy", "--skl-run", "--print", "--app"])


if __name__ == "__main__":
    unittest.main()
