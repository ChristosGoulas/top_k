"""Top-k query processing over per-category NBA 2017 stat leaderboards.

Each ``data/2017_<CATEGORY>.csv`` file is a list of ``(player_id, value)``
pairs, sorted by value in descending order. Given a set of categories and a
target ``k``, this tool finds the k players with the highest combined score
(the sum of each category's value, normalized against that category's
maximum) without reading every list to the end.

It does so with Fagin's Threshold Algorithm (TA): at each round we pull one
more entry from every selected category's sorted list (sorted access) and,
the first time a player is seen, look up its exact value in the other lists
(random access) to compute its true combined score right away. The round's
threshold is the sum of the values just read from each list -- no unseen
player can possibly score higher than that. Once the k-th best known score
is at least as high as the threshold, the top-k is final and we can stop
without reading the remaining lists to the end.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

CATEGORIES = {
    "TRB": "Rebounds",
    "AST": "Assists",
    "STL": "Steals",
    "BLK": "Blocks",
    "PTS": "Points",
}

DEFAULT_DATA_DIR = Path(__file__).parent / "data"


def load_category(data_dir: Path, category: str) -> list[tuple[str, int]]:
    """Load a category's (player_id, value) pairs, sorted descending by value."""
    path = data_dir / f"2017_{category}.csv"
    with path.open(newline="") as f:
        rows = [(player_id, int(value)) for player_id, value in csv.reader(f)]
    rows.sort(key=lambda row: row[1], reverse=True)
    return rows


def normalize(rows: list[tuple[str, int]]) -> list[tuple[str, float]]:
    """Scale values in a category to [0, 1] by dividing by the category max."""
    if not rows:
        return []
    max_value = rows[0][1]
    return [(player_id, value / max_value) for player_id, value in rows]


def load_player_names(data_dir: Path) -> dict[str, str]:
    """Map player id -> player name, read from the combined 2017_ALL.csv file."""
    path = data_dir / "2017_ALL.csv"
    with path.open(newline="") as f:
        reader = csv.reader(f)
        next(reader)  # header
        return {player_id: name for player_id, name, *_ in reader}


def threshold_algorithm(
    streams: list[list[tuple[str, float]]], k: int, verbose: bool = False
) -> list[tuple[str, float]]:
    """Return the top-k (player_id, score) pairs across the given streams.

    Each stream must already be sorted by score in descending order.
    """
    num_streams = len(streams)
    # Random-access lookup per stream, used to fetch a player's exact score
    # in a list as soon as it's first seen in any other list.
    lookups = [dict(stream) for stream in streams]
    positions = [0] * num_streams
    scores: dict[str, float] = {}

    round_number = 0
    while True:
        round_number += 1
        threshold = 0.0
        active_streams = 0
        for i, stream in enumerate(streams):
            if positions[i] >= len(stream):
                continue
            active_streams += 1
            player_id, score = stream[positions[i]]
            positions[i] += 1
            threshold += score
            if player_id not in scores:
                scores[player_id] = sum(
                    lookup.get(player_id, 0.0) for lookup in lookups
                )

        if active_streams == 0:
            break

        if verbose:
            print(f"round {round_number}: {len(scores)} candidates seen so far")

        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        if len(ranked) >= k and ranked[k - 1][1] >= threshold:
            if verbose:
                print(f"stopped early after {round_number} rounds")
            return ranked[:k]

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    return ranked[:k]


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError(f"k must be a positive integer, got {value}")
    return parsed


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("k", type=_positive_int, help="number of top results to return")
    parser.add_argument(
        "categories",
        nargs="+",
        choices=CATEGORIES,
        help=f"stat categories to combine: {', '.join(CATEGORIES)}",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="directory containing the 2017_*.csv files (default: %(default)s)",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="print progress of the algorithm"
    )
    args = parser.parse_args(argv)
    if len(set(args.categories)) != len(args.categories):
        parser.error("duplicate categories are not allowed")
    return args


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    streams = [
        normalize(load_category(args.data_dir, category))
        for category in args.categories
    ]
    player_names = load_player_names(args.data_dir)

    results = threshold_algorithm(streams, args.k, verbose=args.verbose)

    categories_label = " + ".join(args.categories)
    print(f"\nTop {args.k} players by {categories_label} (2017 season):")
    for rank, (player_id, score) in enumerate(results, start=1):
        name = player_names.get(player_id, f"<unknown id {player_id}>")
        print(f"{rank:>2}. {name:<25} score={score:.3f}")


if __name__ == "__main__":
    main()
