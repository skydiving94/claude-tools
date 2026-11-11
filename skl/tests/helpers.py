import importlib.machinery
import importlib.util
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

SKL_PATH = pathlib.Path(__file__).resolve().parent.parent / "skl"
FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"

_cached = None


def load_skl():
    global _cached
    if _cached is None:
        loader = importlib.machinery.SourceFileLoader("skl", str(SKL_PATH))
        spec = importlib.util.spec_from_loader("skl", loader)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        _cached = module
    return _cached


class SklCase(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="skl-test-"))
        self.addCleanup(shutil.rmtree, str(self.tmp), True)
        for d in ("home", "data", "bin", "work"):
            (self.tmp / d).mkdir()
        self.env = {
            "HOME": str(self.tmp / "home"),
            "XDG_DATA_HOME": str(self.tmp / "data"),
            "PATH": "%s:/usr/bin:/bin" % (self.tmp / "bin"),
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
