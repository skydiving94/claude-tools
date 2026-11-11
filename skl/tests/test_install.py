import os
import subprocess
import sys
from pathlib import Path

from helpers import SKL_PATH, SklCase


class InstallTest(SklCase):
    def test_install(self):
        dest = Path(self.tmp) / "dest"
        tools_env = {**self.env, "PATH": "/usr/bin:/bin", "SKL_BIN_DIR": str(dest)}
        r = subprocess.run(["/bin/sh", str(SKL_PATH.parent / "install.sh")], env=tools_env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(os.access(dest / "skl", os.X_OK))
        self.assertIn("source <(skl completion zsh)", r.stdout)
        self.assertIn('Add to ~/.bashrc:  eval "$(skl completion bash)"', r.stdout)
        self.assertNotIn("source <(skl completion bash)", r.stdout)
        self.assertIn("is not on your PATH", r.stdout)
        r = subprocess.run([sys.executable, str(dest / "skl"), "list"], env=self.env, capture_output=True, text=True)
        self.assertIn("no skills indexed", r.stdout)
        with open(str(dest / "skl"), "rb") as f:
            self.assertEqual(f.readline(), b"#!/usr/bin/env python3\n")
        r = subprocess.run([sys.executable, str(dest / "skl"), "nosuch", "x"], env=self.env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.assertIn("error: unknown skill", r.stderr)
        self.assertFalse(list(dest.glob("*.tmp")))

    def test_missing_python(self):
        dest = Path(self.tmp) / "dest2"
        env = {**self.env, "SKL_BIN_DIR": str(dest), "PATH": str(self.tmp / "bin")}
        r = subprocess.run(["/bin/sh", str(SKL_PATH.parent / "install.sh")], env=env, capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("error: python3 not found", r.stderr)
