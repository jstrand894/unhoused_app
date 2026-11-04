"""App version and change history, read from version.json.

version.json is bumped by scripts/hooks/pre-commit on every commit: the patch number goes up, and the notes in
"pending" move into a new "history" entry for that version. To describe a change, add a line to "pending".
"""
import json
import os

__author__ = "Jackson Strand"

try:
    with open(os.path.join(os.path.dirname(__file__), "version.json"), encoding="utf-8") as _f:
        _data = json.load(_f)
except (OSError, ValueError):
    _data = {}

__version__ = _data.get("version", "0.0.0")
HISTORY = _data.get("history", [])      # newest first: [{"version", "date", "changes": [...]}]


def notes_for(version):
    for entry in HISTORY:
        if entry.get("version") == version:
            return entry.get("changes", [])
    return []
