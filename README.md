# top-k

[![CI](https://github.com/ChristosGoulas/top_k/actions/workflows/ci.yml/badge.svg)](https://github.com/ChristosGoulas/top_k/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A small implementation of **Fagin's Threshold Algorithm (TA)** for top-k query
processing, applied to 2017 NBA season stats.

## What it does

Given a set of stat categories (rebounds, assists, steals, blocks, points)
and a target `k`, the tool finds the `k` players with the highest combined
score across those categories — without necessarily reading every player's
full stat line.

Each `data/2017_<CATEGORY>.csv` file holds `(player_id, value)` pairs sorted
by value in descending order, mimicking a real top-k system where each
"source" only exposes a sorted stream of results (think: search engines
merging per-term relevance lists). The Threshold Algorithm exploits this
sorted order to stop early, as soon as it can prove no unseen player could
possibly beat the current top-k.

### How the algorithm works

At each round, one more entry is read from every selected category's sorted
list (**sorted access**). The first time a player shows up, its exact value
in every other selected list is looked up directly (**random access**), so
its true combined score is known immediately. The round's **threshold** is
the sum of the values just read from each list — no player not yet fully
seen can possibly score higher than that. Once the `k`-th best known score
is at least as high as the threshold, the top-k is final and the algorithm
stops, typically long before the input lists are exhausted.

## Usage

```bash
python top_k.py <k> <CATEGORY> [<CATEGORY> ...] [--verbose] [--data-dir DIR]
```

| Code  | Category |
|-------|----------|
| `TRB` | Rebounds |
| `AST` | Assists  |
| `STL` | Steals   |
| `BLK` | Blocks   |
| `PTS` | Points   |

Example — top 10 players by combined rebounds + points:

```bash
$ python top_k.py 10 TRB PTS

Top 10 players by TRB + PTS (2017 season):
 1. Russell Westbrook         score=1.774
 2. Karl-Anthony Towns        score=1.708
 3. Anthony Davis             score=1.614
 4. James Harden              score=1.512
 5. Hassan Whiteside          score=1.487
 6. DeMarcus Cousins          score=1.473
 7. Andre Drummond            score=1.432
 8. DeAndre Jordan            score=1.400
 9. Rudy Gobert               score=1.372
10. Giannis Antetokounmpo     score=1.343
```

Each category's contribution is normalized to `[0, 1]` (value divided by that
category's max), so combining categories with very different scales (e.g.
points vs. blocks) is meaningful. Pass `--verbose` to see how many rounds the
algorithm needs before it can stop early.

## Development

```bash
pip install -e .[dev]
pytest         # run tests
ruff check .   # lint
black --check .  # formatting
mypy top_k.py  # type checking
```

## Data

Stats are for the 2017 NBA season, sourced from
[Basketball-Reference](https://www.basketball-reference.com/).

## License

[MIT](LICENSE)
