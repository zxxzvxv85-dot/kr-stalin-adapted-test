"""Check generator safety and dependency drift using isolated temporary files only."""

from contextlib import redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory, gettempdir
import unittest
from unittest.mock import patch

from generation_io import encoded, process_outputs
from kr_generation_baseline import inputs, verify


TOOLS = Path(__file__).resolve().parent


class GenerationIOTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory(prefix="kr-generation-io-test-")
        self.scratch = Path(self.temp.name).resolve()
        # TemporaryDirectory cleanup stays inside the known OS temporary directory.
        assert self.scratch.parent == Path(gettempdir()).resolve()
        self.addCleanup(self.temp.cleanup)
        self.source = self.scratch / "source"
        self.source.mkdir()

    def process(self, outputs, destination=None, write=False):
        with redirect_stdout(io.StringIO()):
            return process_outputs(outputs, destination or self.source, write=write)

    def cli(self, arguments, body="return {'events/generated.txt': 'event = { value = 1 }\\n'}"):
        script = (
            "import sys\nfrom pathlib import Path\n"
            f"sys.path.insert(0, {str(TOOLS)!r})\n"
            "from generation_io import cli\n"
            "counter = 0\n"
            "def render():\n"
            + "\n".join("    " + line for line in body.splitlines()) + "\n"
            + f"cli(render, root=Path({str(self.source)!r}))\n"
        )
        return subprocess.run([sys.executable, "-B", "-c", script, *arguments], capture_output=True, text=True)

    def test_read_only_default_and_explicit_stage(self):
        result = self.cli([])
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(list(self.source.iterdir()), [])
        stage = self.scratch / "stage"
        result = self.cli(["--output-root", str(stage)])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((stage / "events/generated.txt").is_file())
        self.assertEqual(list(self.source.iterdir()), [])
        result = self.cli(["--check", "--output-root", str(self.scratch / "unused")])
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.scratch / "unused").exists())

    def test_source_output_requires_write(self):
        for target in (self.source, self.source / "nested"):
            result = self.cli(["--output-root", str(target)])
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertEqual(list(self.source.iterdir()), [])
        result = self.cli(["--write"])
        self.assertEqual(result.returncode, 0, result.stderr)
        content = (self.source / "events/generated.txt").read_bytes()
        result = self.cli(["--check"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.source / "events/generated.txt").read_bytes(), content)

    def test_batch_validation_precedes_writes(self):
        for outputs in (
            {"a.txt": "a", "z/../../outside.txt": "bad"},
            {"a.txt": "a", "z/../a.txt": "alias"},
            {"a.txt": "a", "a.txt/child": "collision"},
        ):
            with self.assertRaises(ValueError):
                self.process(outputs, write=True)
            self.assertEqual(list(self.source.iterdir()), [])
        (self.source / "z.txt").write_text("parent file", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.process({"a.txt": "a", "z.txt/child": "bad"}, write=True)
        self.assertFalse((self.source / "a.txt").exists())

    def test_encoding_and_checkout_line_endings(self):
        self.assertEqual(encoded("x.yml", "\ufeffl_english:\r\n key:0 \"text\"\r\n"), b'\xef\xbb\xbfl_english:\n key:0 "text"\n')
        self.assertEqual(encoded("x.txt", "\ufeffkey = yes\r\n"), b"key = yes\n")
        target = self.source / "x.yml"
        before = b'\xef\xbb\xbfl_english:\r\n key:0 "text"\r\n'
        target.write_bytes(before)
        self.assertEqual(self.process({"x.yml": 'l_english:\n key:0 "text"\n'}), 0)
        self.assertEqual(target.read_bytes(), before)

    def test_stateful_renderer_fails_before_write(self):
        body = "global counter\ncounter += 1\nreturn {'events/generated.txt': str(counter)}"
        result = self.cli(["--write"], body)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("not deterministic", result.stderr)
        self.assertEqual(list(self.source.iterdir()), [])

    def test_upstream_manifest_detects_changed_inputs(self):
        upstream = self.scratch / "kr"
        (upstream / "common/country_leader").mkdir(parents=True)
        (upstream / "descriptor.mod").write_text('name="fixture"', encoding="utf-8")
        trait = upstream / "common/country_leader/traits.txt"
        trait.write_text("leader_traits = { fixture = {} }", encoding="utf-8")
        (self.source / "tools").mkdir()
        (self.source / "common/ideas").mkdir(parents=True)
        (self.source / "common/ideas/custom.txt").write_text("ideas = {}", encoding="utf-8")
        with patch.dict(os.environ, {"HOI4_KR_ROOT": str(upstream)}):
            files = inputs(self.source)
            self.assertIsNone(files["common/ideas/custom.txt"])
            manifest = self.source / "tools/kr_generation_baseline.json"
            manifest.write_text(json.dumps({"files": files}), encoding="utf-8")
            verify(self.source)
            before = hashlib.sha256(manifest.read_bytes()).hexdigest()
            trait.write_text("leader_traits = { changed = {} }", encoding="utf-8")
            with self.assertRaises(ValueError):
                verify(self.source)
            self.assertEqual(hashlib.sha256(manifest.read_bytes()).hexdigest(), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
