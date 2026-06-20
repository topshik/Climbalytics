# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Run the ETL script
uv run python convert_to_db.py
```

There are no tests or linting configured.

## What this project does

Climbalytics is a single-script ETL pipeline that converts a Telegram group chat export (`input/chat.json`) into a structured CSV (`output/sessions.csv`) of bouldering sessions.

The Telegram group "Трассы" is a private chat where two athletes (Катя and Антон) log completed climbing routes by color and count after each gym visit. The script parses those freeform Russian-language messages and normalizes them into tabular data.

## Architecture: `convert_to_db.py`

The entire codebase is one file. Data flows:

1. **Input**: `input/chat.json` — a Telegram chat export. Each relevant message has `date`, `from_id`, and `text` fields.
2. **`Session` class**: parses a single message's text into structured route counts. Constructor calls `_parse_gym_and_routes()` then `_detect_trainer()`.
3. **Output**: `output/sessions.csv` — one row per session with columns for date, athlete, gym, city, trainer, and one column per canonical color.

### Color normalization

Routes are counted by color. The canonical color scale is Sektor44's (9 Russian-named colors: белый through чёрный). Two challenges:

- **Morphological variation**: Russian adjectives inflect by case/gender/number ("желтые", "желтая" → "жёлтый"). `normalize_text()` uses `pymorphy2` to lemmatize color adjectives to nominative singular masculine before any parsing happens.
- **Per-gym color remapping**: Each non-Sektor gym uses different colors or level numbers. `_GYM_COLOR_MAP` maps gym-local colors to Sektor equivalents (e.g. Puls "фиолетовый" → "жёлтый"). Element and Urban Apes use "уровень N" level syntax instead of colors.

### Gym detection

- If the first token of the message is already a canonical color, the gym is **Sektor44** (no header line).
- Otherwise, the first line is the gym name. `clean_gym_name()` strips city suffixes and applies `_GYM_ALIASES` to handle informal names (e.g. "лаба" → "Climb Lab").

### Python 3.13 compatibility

`pymorphy2` uses `inspect.getargspec` which was removed in Python 3.11. The script monkey-patches it at import time:
```python
inspect.getargspec = lambda f: inspect.getfullargspec(f)[:4]
```
This must remain at the top of the file before `pymorphy2` is imported.
