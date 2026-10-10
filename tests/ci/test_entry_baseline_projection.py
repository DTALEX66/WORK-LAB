"""Pins the pure decision surface of scripts/audit/entry_baseline_readback.py.

The real-machine readback (registry/desktop/.lnk on disk) is never touched here — these
tests feed synthetic resolution dicts and synthetic shell-link bytes into the two pure
functions (decide, parse_lnk) and assert the exact fail-closed verdicts, so the projection
cannot drift from the contract vocabulary while nobody is watching. Negative controls are
first-class tests: two install locations, a dead shortcut target, an IconLocation reset to
the temp install directory (the NSIS trap) and a surface with no install at all must never
come out green or silently disappear.
"""
from __future__ import annotations

import importlib.util
import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "audit" / "entry_baseline_readback.py"
LIVE_PROBE = ROOT / "scripts" / "audit" / "executor_live_probe.py"


def load_module():
    spec = importlib.util.spec_from_file_location("entry_baseline_readback", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load_module()

TEMP_ROOTS = ["C:\\Users\\X\\AppData\\Local\\Temp"]


def good_shortcut(**over):
    sc = {"lnk_path": "C:\\Users\\X\\Desktop\\App.lnk",
          "target": "C:\\Users\\X\\AppData\\Local\\Programs\\App\\app.exe",
          "target_exists": True, "working_dir": "C:\\Users\\X\\AppData\\Local\\Programs\\App",
          "working_dir_exists": True, "icon": "C:\\Users\\X\\AppData\\Local\\Programs\\App\\app.exe",
          "icon_named": True, "icon_exists": True, "arguments": ""}
    sc.update(over)
    return sc


class VocabularyTests(unittest.TestCase):
    def test_verdict_spelling_comes_from_the_contract_schema(self) -> None:
        enum, source = MODULE.load_location_vocabulary()
        self.assertIn("software-installation-identity.schema.json", source)
        for name in ("SINGLE_VERIFIED", "SINGLE_UNVERIFIED", "DUAL_INSTALLATION",
                     "LOCATION_DRIFT", "MISSING_EXPECTED_INSTALL", "NOT_INSTALLED", "OS_MANAGED"):
            self.assertIn(name, enum, f"{name} is not spelled the same in the contract enum")

    def test_entry_not_resolved_matches_the_probe_vocabulary(self) -> None:
        # ENTRY_NOT_RESOLVED lives in scripts/audit/executor_live_probe.py, not in the
        # schema enum; the audit row may use it ONLY as that same literal.
        self.assertIn("ENTRY_NOT_RESOLVED", LIVE_PROBE.read_text(encoding="utf-8"))
        self.assertEqual("ENTRY_NOT_RESOLVED", MODULE.ENTRY_NOT_RESOLVED)

    def test_no_verdict_outside_the_enum_plus_the_probe_state(self) -> None:
        enum, _ = MODULE.load_location_vocabulary()
        allowed = set(enum) | {MODULE.ENTRY_NOT_RESOLVED}
        cases = [
            {"readback_error": "boom"},
            {"os_managed": True},
            {"relocation_requested": True},
            {"install_roots": ["C:\\a", "D:\\b"], "require_desktop": True},
            {"install_roots": [], "require_desktop": True, "expected_roots": []},
            {"install_roots": [], "expected_roots": ["C:\\declared"], "require_desktop": True},
            {"require_desktop": False, "cli_resolved": True, "cli_paths": ["C:\\gh\\gh.exe"]},
            {"require_desktop": True, "shortcut": good_shortcut(), "wscript_agree": True},
            {"require_desktop": True, "shortcut": good_shortcut(target_exists=False),
             "install_roots": ["D:\\elsewhere"]},
            {"require_desktop": True, "shortcut": good_shortcut(icon=TEMP_ROOTS[0] + "\\nsD.tmp\\a.exe"),
             "temp_roots": TEMP_ROOTS, "install_roots": [str(Path(good_shortcut()["target"]).parent)]},
        ]
        for res in cases:
            res.setdefault("temp_roots", TEMP_ROOTS)
            res.setdefault("install_roots", [])
            verdict = MODULE.decide(res)["verdict"]
            self.assertIn(verdict, allowed, f"verdict {verdict!r} escaped the contract vocabulary")


class NegativeControlTests(unittest.TestCase):
    def test_two_install_locations_are_never_single_verified(self) -> None:
        out = MODULE.decide({"install_roots": ["D:\\Programs\\App", "C:\\Users\\X\\AppData\\Local\\Programs\\App"],
                             "require_desktop": True, "temp_roots": TEMP_ROOTS})
        self.assertNotEqual("SINGLE_VERIFIED", out["verdict"])
        self.assertEqual("DUAL_INSTALLATION", out["verdict"])

    def test_dead_shortcut_target_is_never_single_verified(self) -> None:
        out = MODULE.decide({"require_desktop": True, "temp_roots": TEMP_ROOTS,
                             "install_roots": [], "expected_roots": [],
                             "shortcut": good_shortcut(target_exists=False)})
        self.assertNotEqual("SINGLE_VERIFIED", out["verdict"])
        self.assertEqual("NOT_INSTALLED", out["verdict"])

    def test_dead_target_while_an_install_exists_is_drift(self) -> None:
        out = MODULE.decide({"require_desktop": True, "temp_roots": TEMP_ROOTS,
                             "install_roots": ["D:\\Programs\\App"],
                             "shortcut": good_shortcut(target_exists=False)})
        self.assertEqual("LOCATION_DRIFT", out["verdict"])

    def test_temp_icon_location_is_drift_not_ignored(self) -> None:
        out = MODULE.decide({"require_desktop": True,
                             "temp_roots": TEMP_ROOTS,
                             "install_roots": ["C:\\Users\\X\\AppData\\Local\\Programs\\App"],
                             "shortcut": good_shortcut(icon=TEMP_ROOTS[0] + "\\nsA1B2\\app.exe")})
        self.assertEqual("LOCATION_DRIFT", out["verdict"])
        self.assertIn("IconLocation", out["reason"])

    def test_temp_target_is_drift(self) -> None:
        out = MODULE.decide({"require_desktop": True, "temp_roots": TEMP_ROOTS,
                             "install_roots": [],
                             "shortcut": good_shortcut(target=TEMP_ROOTS[0] + "\\nsZ\\app.exe")})
        self.assertEqual("LOCATION_DRIFT", out["verdict"])

    def test_uninstalled_surface_reports_not_installed_not_absent(self) -> None:
        out = MODULE.decide({"require_desktop": True, "temp_roots": TEMP_ROOTS,
                             "install_roots": [], "expected_roots": []})
        self.assertEqual("NOT_INSTALLED", out["verdict"])

    def test_declared_expected_location_absent_is_missing_expected_install(self) -> None:
        out = MODULE.decide({"require_desktop": True, "temp_roots": TEMP_ROOTS,
                             "install_roots": [], "expected_roots": ["C:\\Users\\X\\AppData\\Local\\Programs\\App"]})
        self.assertEqual("MISSING_EXPECTED_INSTALL", out["verdict"])

    def test_invented_launcher_convicts(self) -> None:
        out = MODULE.decide({"require_desktop": True, "temp_roots": TEMP_ROOTS,
                             "install_roots": ["C:\\Users\\X\\AppData\\Local\\Programs\\App"],
                             "invented_launcher": True,
                             "shortcut": good_shortcut(target="C:\\Windows\\System32\\wscript.exe")})
        self.assertEqual("LOCATION_DRIFT", out["verdict"])

    def test_parser_disagreement_downgrades(self) -> None:
        out = MODULE.decide({"require_desktop": True, "temp_roots": TEMP_ROOTS, "wscript_agree": False,
                             "install_roots": ["C:\\Users\\X\\AppData\\Local\\Programs\\App"],
                             "shortcut": good_shortcut()})
        self.assertNotEqual("SINGLE_VERIFIED", out["verdict"])
        self.assertEqual("SINGLE_UNVERIFIED", out["verdict"])

    def test_named_missing_icon_is_unverified_not_green(self) -> None:
        out = MODULE.decide({"require_desktop": True, "temp_roots": TEMP_ROOTS, "wscript_agree": True,
                             "install_roots": [],
                             "shortcut": good_shortcut(icon="C:\\gone\\icon.ico", icon_exists=False)})
        self.assertEqual("SINGLE_UNVERIFIED", out["verdict"])

    def test_readback_failure_is_entry_not_resolved(self) -> None:
        out = MODULE.decide({"readback_error": "HKCU unreadable in this sandbox", "temp_roots": TEMP_ROOTS})
        self.assertEqual("ENTRY_NOT_RESOLVED", out["verdict"])

    def test_installed_but_no_desktop_shortcut_is_unverified(self) -> None:
        out = MODULE.decide({"require_desktop": True, "temp_roots": TEMP_ROOTS, "shortcut": None,
                             "install_roots": ["C:\\Programs\\App"]})
        self.assertEqual("SINGLE_UNVERIFIED", out["verdict"])


class PositiveTests(unittest.TestCase):
    def test_clean_single_chain_verifies(self) -> None:
        out = MODULE.decide({"require_desktop": True, "temp_roots": TEMP_ROOTS, "wscript_agree": True,
                             "install_roots": ["C:\\Users\\X\\AppData\\Local\\Programs\\App"],
                             "shortcut": good_shortcut()})
        self.assertEqual("SINGLE_VERIFIED", out["verdict"])
        self.assertEqual(good_shortcut()["target"], out["canonical_candidate"])

    def test_cli_surface_verifies_from_path(self) -> None:
        out = MODULE.decide({"require_desktop": False, "temp_roots": TEMP_ROOTS,
                             "cli_resolved": True, "cli_paths": ["C:\\Program Files\\GitHub CLI\\gh.exe"]})
        self.assertEqual("SINGLE_VERIFIED", out["verdict"])

    def test_os_managed_and_relocation_states_reachable(self) -> None:
        self.assertEqual("OS_MANAGED", MODULE.decide({"os_managed": True})["verdict"])
        self.assertEqual("RELOCATION_REQUESTED", MODULE.decide({"relocation_requested": True})["verdict"])


# ---------------------------------------------------------------------------
# synthetic [MS-SHLLINK] bytes for the hand parser (no real files, no registry)
# ---------------------------------------------------------------------------
def build_lnk(target: str, working_dir: str, arguments: str, uni: bool,
              icon: str | None = None, with_idlist: bool = True) -> bytes:
    flags = 0x00000010 if uni else 0x00000000
    if with_idlist:
        flags |= 0x00000001
    header = struct.pack("<I", 0x4C) + bytes.fromhex("0114020000000000c000000000000046") \
        + struct.pack("<I", flags) + b"\x00" * (76 - 4 - 16 - 4)
    body = b""
    if with_idlist:
        # one 6-byte item (size includes its own u16) followed by the 0x0000 terminator
        body += b"\x06\x00" + b"\xef\xbe\xad\xde" + b"\x00\x00"
    # LinkInfo
    if uni:
        lbp = target.encode("utf-16-le") + b"\x00\x00"
    else:
        lbp = target.encode("mbcs", errors="replace") + b"\x00"
    volid = b"\x15\x00\x00\x00" + b"\x03\x00\x00\x00" + b"V" * 13
    lbp_off = 28 + len(volid)
    li_len = lbp_off + len(lbp)
    # 28-byte LinkInfo header (6 u32 + 4 zero pad), then VolumeID, then LocalBasePath
    link_info = struct.pack("<IIIIII", li_len, 28, 1, len(volid), lbp_off, 0) + b"\x00" * 4 \
        + volid + lbp
    body += link_info
    # StringData: Name(0), RelativePath(0), WorkingDirectory, CommandArguments
    def counted(s: str) -> bytes:
        if uni:
            return struct.pack("<H", len(s)) + s.encode("utf-16-le")
        return struct.pack("<H", len(s)) + s.encode("mbcs", errors="replace")
    body += counted("") + counted("") + counted(working_dir) + counted(arguments)
    if icon is not None:
        loc = icon.encode("utf-16-le") + b"\x00\x00"
        # block: [u32 size][u32 signature][u32 flags][UTF-16 location + NUL]
        block = struct.pack("<II", 12 + len(loc), 0xA0000007) + b"\x00" * 4 + loc
        body += block
    return header + body


class LnkParserTests(unittest.TestCase):
    def test_ansi_target_wd_and_args(self) -> None:
        raw = build_lnk("C:\\Tools\\app.exe", "C:\\Tools", "--flag", uni=False)
        out = MODULE.parse_lnk(raw)
        self.assertTrue(out["parse_ok"], out["parse_error"])
        self.assertEqual("C:\\Tools\\app.exe", out["target_path"])
        self.assertEqual("C:\\Tools", out["working_directory"])
        self.assertEqual("--flag", out["arguments"])

    def test_utf16_target_wd_and_icon(self) -> None:
        raw = build_lnk("C:\\Tools\\App Gui.exe", "C:\\Tools", "",
                        uni=True, icon="C:\\Tools\\App Gui.exe,0")
        out = MODULE.parse_lnk(raw)
        self.assertTrue(out["parse_ok"], out["parse_error"])
        self.assertEqual("C:\\Tools\\App Gui.exe", out["target_path"])
        self.assertEqual("C:\\Tools", out["working_directory"])
        self.assertEqual("C:\\Tools\\App Gui.exe,0", out["icon_location"])

    def test_truncated_file_fails_closed(self) -> None:
        out = MODULE.parse_lnk(b"\x4c\x00\x00\x00" + b"\x00" * 30)
        self.assertFalse(out["parse_ok"])
        self.assertIsNotNone(out["parse_error"])

    def test_bad_header_rejected(self) -> None:
        out = MODULE.parse_lnk(b"NOPE" + b"\x00" * 100)
        self.assertFalse(out["parse_ok"])
        self.assertIn("header", (out["parse_error"] or "").lower())


if __name__ == "__main__":
    unittest.main()
