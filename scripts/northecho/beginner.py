"""Small synthetic report fixtures for the isolated beginner pilot."""
from pathlib import Path


def prepare(workspace: Path, target: str, fixture: dict) -> None:
    if target.split(".")[0] not in {"b0", "b1"}:
        return
    reports = {
        "report.txt": f"Delivery report for {fixture['synthetic_user']}\nThree parcels arrived.\n",
        "weekend report.txt": f"Weekend report {fixture['fixture_id']}\nOne parcel arrived.\n",
    }
    for name, content in reports.items():
        (workspace / name).write_text(content, encoding="utf-8")
