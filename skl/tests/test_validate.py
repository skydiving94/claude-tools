import unittest

from helpers import FIXTURES, SklCase
from sklcli.errors import UsageError
from sklcli.models import Source
from sklcli.parsing.validate import validate
from sklcli.store.entries import make_entry

N = make_entry(FIXTURES / "notes" / "SKILL.md", Source.IMPORT)
M = make_entry(FIXTURES / "meal" / "SKILL.md", Source.IMPORT)


class ValidateTests(SklCase):
    def ok(self, entry, *a):
        validate(entry, list(a))

    def bad(self, entry, msg, *a):
        with self.assertRaises(UsageError) as c:
            validate(entry, list(a))
        self.assertEqual(str(c.exception), msg)
        self.assertEqual(c.exception.usage_line, entry["interface"]["usage_line"])

    def test_valid(self):
        self.ok(N, "add", "My note", "--tag", "x", "--no-index", "--commit")
        self.ok(N, "add", "t", "--tag=x")
        self.ok(N, "add", "t", "--tag", "-starts-with-dash")
        self.ok(N, "show")
        self.ok(N, "show", "t")
        self.ok(N, "list", "--format", "long")
        self.ok(M, "update", "ossobuco", "--swap", "farro=rice")
        self.ok(M, "remove", "x", "--cascade", "--commit")

    def test_errors(self):
        self.bad(N, "missing action")
        self.bad(N, "missing action", "--commit")
        self.bad(N, "unknown action 'ad'", "ad", "t")
        self.bad(N, "missing title for 'add'", "add")
        self.bad(N, "missing title for 'add'", "add", "--commit")
        self.bad(N, "second action 'list'", "add", "t", "list")
        self.bad(N, "unexpected argument 'extra'", "list", "extra")
        self.bad(N, "unknown flag '--nope'", "list", "--nope")
        self.bad(N, "flag '--tag' is not valid for 'list'", "list", "--tag", "x")
        self.bad(N, "flag '--tag' needs a value", "add", "t", "--tag")
        self.bad(N, "flag '--tag' needs a value", "add", "t", "--tag", "--commit")
        self.bad(N, "flag '--format' needs a value", "list", "--format", "--help")
        self.bad(N, "invalid value 'bogus' for '--format' (choose short, long)", "list", "--format", "bogus")
        self.bad(N, "invalid value 'bogus' for '--format' (choose short, long)", "list", "--format=bogus")
        self.bad(N, "invalid value '' for '--format' (choose short, long)", "list", "--format=")
        self.bad(N, "flag '--commit' takes no value", "add", "t", "--commit=yes")
        self.bad(M, "flag '--cascade' is not valid for 'update'", "update", "x", "--cascade")

    def test_dash_values_and_positionals(self):
        self.ok(N, "add", "-")
        self.ok(N, "add", "-5")
        self.ok(N, "add", "-5.5", "--tag", "-5")
        self.ok(N, "add", "t", "--tag=--weird=x")
        self.ok(N, "add", "t", "--tag=")
        self.bad(N, "unknown flag '--nope'", "add", "t", "--nope=1")
        self.bad(N, "unknown flag '--tag2'", "add", "t", "--tag2=x")
        self.bad(N, "flag '--tag' is not valid for 'list'", "list", "--tag=x")
        self.bad(N, "unknown flag '-z'", "list", "-z")
        self.bad(N, "unexpected argument 'a'", "add", "t", "a")

    def test_passthrough_skips(self):
        validate({"name": "odd", "interface": None}, ["anything", "--goes"])


if __name__ == "__main__":
    unittest.main()
