import csv
import json

from colors import SEKTOR_COLORS, TRAINER_COLORS
from session import Session, _ATHLETE_MAP


def entry_is_valid(entry: dict[str, object]) -> bool:
    return "date" in entry and "from" in entry and "text" in entry


if __name__ == "__main__":
    with open("input/chat.json", "r") as f:
        data = json.load(f)

    sessions: list[Session] = []
    for entry in data["messages"]:
        if not entry_is_valid(entry):
            continue
        athlete = _ATHLETE_MAP.get(entry.get("from_id", ""), "?")
        if athlete == "?":
            continue
        sessions.append(Session(entry["text"], entry["date"], athlete))

    fieldnames = ["date", "athlete", "gym", "city", "trainer"] + SEKTOR_COLORS + TRAINER_COLORS
    with open("output/sessions.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(s.to_dict() for s in sessions)

    print(f"Exported {len(sessions)} sessions to output/sessions.csv")
