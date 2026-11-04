import os
import tempfile
import unittest
from unittest import mock

from hobo import diagnose, updates


class DiagnoseTests(unittest.TestCase):
    def test_report_is_written_even_when_every_usb_step_fails(self):
        with mock.patch("usb.core.find", side_effect=RuntimeError("no libusb")), \
                mock.patch.object(diagnose, "_run", return_value="(stub)"):
            with tempfile.TemporaryDirectory() as d:
                path = diagnose.write_report(os.path.join(d, "r.txt"), context={"link": "none"})
                text = open(path, encoding="utf-8").read()
        for needle in ("DIAGNOSTIC REPORT", "APP AND SYSTEM", "link: none", "FAIL", "END OF REPORT"):
            self.assertIn(needle, text)

    def test_default_path_is_a_text_file_with_a_timestamp(self):
        p = diagnose.default_path()
        self.assertTrue(os.path.basename(p).startswith("Unhoused-diagnostics-"))
        self.assertTrue(p.endswith(".txt"))

    def test_version_comparison(self):
        self.assertTrue(updates.is_newer("1.0.16", "1.0.15"))
        self.assertTrue(updates.is_newer("v1.1.0", "1.0.99"))
        self.assertFalse(updates.is_newer("1.0.15", "1.0.15"))
        self.assertFalse(updates.is_newer("junk", "1.0.15"))


if __name__ == "__main__":
    unittest.main()
