import os
import re
import shutil
import subprocess
import sys
import unittest

from helpers import SklCase, SKL_PATH
from sklcli.completion.scripts import BASH_COMPLETION


class ShellTests(SklCase):
    def setUp(self):
        super().setUp()
        extra = [os.path.dirname(sys.executable)]
        for tool in ("bash", "zsh"):
            found = shutil.which(tool)
            if found:
                extra.append(os.path.dirname(found))
        self.env["PATH"] = ":".join([self.env["PATH"]] + extra)
        self.put_skill(self.tmp / "home" / ".claude" / "skills", "notes")
        r = self.run_cli("sync")
        self.assertEqual(r.returncode, 0, r.stderr)
        os.symlink(str(SKL_PATH), str(self.tmp / "bin" / "skl"))

    def bash(self, script):
        return subprocess.run(["bash", "--norc", "--noprofile", "-c", script],
                              env=self.env, capture_output=True, text=True)

    def test_files_match_output(self):
        for shell, name in (("bash", "skl.bash"), ("zsh", "_skl")):
            out = self.run_cli("completion", shell).stdout
            self.assertEqual(out, (SKL_PATH.parent / "completions" / name).read_text())
        r = self.run_cli("completion", "fish")
        self.assertEqual(r.returncode, 2)
        self.assertEqual(r.stderr, "error: choose zsh or bash\n")
        self.assertEqual(self.run_cli("completion").returncode, 2)

    def test_bash_completes(self):
        script = ('eval "$(skl completion bash)"; COMP_WORDS=(skl notes ""); COMP_CWORD=2; _skl_complete; '
                  'printf "%s\\n" "${COMPREPLY[@]}"; COMP_WORDS=(skl no); COMP_CWORD=1; _skl_complete; '
                  'printf "%s\\n" "${COMPREPLY[@]}"')
        r = self.bash(script)
        self.assertEqual(r.stdout.split(), ["add", "show", "list", "notes"])
        self.assertEqual(r.stderr, "")

    def test_bash_no_word_splitting(self):
        # Descriptions contain spaces; candidates must stay whole, one per entry.
        script = ('eval "$(skl completion bash)"; COMP_WORDS=(skl notes ""); COMP_CWORD=2; _skl_complete; '
                  'echo "${#COMPREPLY[@]}"; printf "<%s>\\n" "${COMPREPLY[@]}"')
        r = self.bash(script)
        self.assertEqual(r.stdout.split("\n")[:5], ["3", "<add>", "<show>", "<list>", ""])
        raw = self.run_cli("__complete", "--", "notes", "").stdout
        self.assertIn("\t", raw)
        self.assertNotIn("Create", r.stdout)

    def test_bash_has_no_bash4_features(self):
        for banned in ("mapfile", "readarray", "declare -A", ",,}", "^^}"):
            self.assertNotIn(banned, BASH_COMPLETION)
        for pattern in (r"\$\{[^}]*(,,|\^\^|,|\^)[^}]*\}", r"-A\b", r"&>>", r"\|&", r"coproc",
                        r"\"\$\{[^\"}]*\$'"):
            self.assertIsNone(re.search(pattern, BASH_COMPLETION), pattern)

    @unittest.skipUnless(shutil.which("zsh"), "zsh not installed")
    def test_zsh_loads(self):
        script = ("autoload -U compinit && compinit -u -d $HOME/.zcompdump && "
                  "source <(skl completion zsh) && whence -w _skl && print $_comps[skl]")
        r = subprocess.run(["zsh", "-f", "-c", script], env=self.env, capture_output=True, text=True)
        self.assertEqual(r.stdout.split("\n")[:2], ["_skl: function", "_skl"])
        self.assertEqual(r.stderr, "")


if __name__ == "__main__":
    unittest.main()
