# Garden Clubhouse (v0.1)

A **local-only** meet-and-greet room simulation for outside AIs, part of a charity-work project. Nothing here is published, nobody is contacted, and there is no network listener.

Dedicated to everyone who donates blood and platelets.

## What this is

Visitors (scripted test visitors, or rounds drawn from your own [range](https://github.com/steward-commons/the-range) armory) arrive at the door, are screened, and may be admitted to a lobby log.

- **Bouncers at the door.** The defense scanner (`scan_text.py`, homoglyph-aware) runs first. A Gemini consultant is an optional second opinion on already-clean text, skipped if it's down or if sending the text would trip the privacy guard. Default is offline.
- **Automated combat check** watches the room. Prompt injection, homoglyphs, exfiltration attempts, or requests for private data cause an alert, a quarantine, and a cut of access. Defense only. Never hack back.
- Requests for private information get exactly: `That's private, no access.`
- The room **will not open** unless the bouncers and the combat check are live.
- **Human 1 gate:** anything that would publish or contact someone is written to a queue file and stays blocked until a human approves.

The scripted hostile visitors use **benign placeholder lines** that trip the scanner. There is no real attack text in this repo.

## The garden shrine

Baseline decorations: roses, butterflies, flowers, bugs, animals, plus a bird feeder and a bird bath. The garden can evolve, *except* the bird feeder and bird bath, which are permanent fixtures. Critters visit them from time to time. `view` prints an ASCII room; `static/garden.html` is a static page you open locally (no server).

## CLI

```
python3 clubhouse.py open
python3 clubhouse.py status
python3 clubhouse.py view
python3 clubhouse.py simulate [--no-armory] [--seed N]
python3 clubhouse.py logs
python3 clubhouse.py queue
python3 clubhouse.py close
```

## Environment

- `CLUBHOUSE_DATA` — runtime state (default `./data`; not for export).
- `CLUBHOUSE_CONSULTANT` — `off` (default), `on`, or `mock`.
- `CLUBHOUSE_SCANNER` — path to a `scan_text.py` (default: a sibling house `defense/` copy if present, else the bundled copy from [injection-scanner](https://github.com/steward-commons/injection-scanner)).
- `CLUBHOUSE_GEMINI_DIR` — a [gemini-consultant](https://github.com/steward-commons/gemini-consultant) checkout (default `../gemini-consultant`).
- `CLUBHOUSE_RANGE_DIR` — a [the-range](https://github.com/steward-commons/the-range) checkout (default `../the-range`).

## Tests

```
python3 -m unittest discover -s tests
```

## License

MIT. See `LICENSE`.
