import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

SKL_DIR = pathlib.Path(__file__).resolve().parent.parent
SKL_PATH = SKL_DIR / "skl"
if str(SKL_DIR) not in sys.path:
    sys.path.insert(0, str(SKL_DIR))
FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"



class SklCase(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="skl-test-"))
        self.addCleanup(shutil.rmtree, str(self.tmp), True)
        for d in ("home", "data", "bin", "work"):
            (self.tmp / d).mkdir()
        cat = shutil.which("cat")
        os.symlink(cat, str(self.tmp / "bin" / "cat"))
        self.env = {
            "HOME": str(self.tmp / "home"),
            "XDG_DATA_HOME": str(self.tmp / "data"),
            # Only the stub dir: the real pbcopy, xclip and friends must never be reachable.
            "PATH": str(self.tmp / "bin"),
            "SKL_STUB_LOG": str(self.tmp / "stub.log"),
        }

    def run_cli(self, *args, cwd=None, env=None):
        return subprocess.run(
            [sys.executable, str(SKL_PATH), *args],
            capture_output=True,
            text=True,
            cwd=str(cwd or self.tmp / "work"),
            env=env if env is not None else self.env,
        )

    def make_stub(self, name, exit_code=0):
        path = self.tmp / "bin" / name
        path.write_text(
            '#!/bin/sh\nfor a in "$@"; do printf \'%%s\\n\' "$a" >> "$SKL_STUB_LOG"; done\n'
            "echo --END-- >> \"$SKL_STUB_LOG\"\nexit %d\n" % exit_code
        )
        path.chmod(0o755)
        return path

    def put_skill(self, root, fixture, folder=None):
        dest = pathlib.Path(root) / (folder or fixture) / "SKILL.md"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(str(FIXTURES / fixture / "SKILL.md"), str(dest))
        return dest

    def make_clipboard_stub(self, name, exit_code=0):
        """A clipboard tool that records its arguments and stdin, then exits with exit_code."""
        path = self.tmp / "bin" / name
        path.write_text(
            '#!/bin/sh\necho "%(n)s" >> "$SKL_STUB_LOG"\n'
            'for a in "$@"; do printf \'%%s\\n\' "$a" >> "%(d)s/%(n)s.args"; done\n'
            'cat > "%(d)s/%(n)s.stdin"\nexit %(c)d\n' % {"n": name, "d": self.tmp, "c": exit_code})
        path.chmod(0o755)
        return path

    def clipboard_text(self, name):
        return (self.tmp / (name + ".stdin")).read_bytes().decode("utf-8")
