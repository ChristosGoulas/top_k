import pytest

from top_k import (
    load_category,
    load_player_names,
    normalize,
    parse_args,
    threshold_algorithm,
)


def test_normalize_scales_by_max():
    rows = [("a", 100), ("b", 50), ("c", 25)]
    assert normalize(rows) == [("a", 1.0), ("b", 0.5), ("c", 0.25)]


def test_normalize_empty():
    assert normalize([]) == []


def test_load_category_sorts_descending(tmp_path):
    path = tmp_path / "2017_PTS.csv"
    path.write_text("1,10\n2,30\n3,20\n")
    rows = load_category(tmp_path, "PTS")
    assert rows == [("2", 30), ("3", 20), ("1", 10)]


def test_load_player_names(tmp_path):
    path = tmp_path / "2017_ALL.csv"
    path.write_text(
        "id,Player,Tm,TRB,AST,STL,BLK,PTS\n1,Alex Abrines,OKC,86,40,37,8,406\n"
    )
    names = load_player_names(tmp_path)
    assert names == {"1": "Alex Abrines"}


def _brute_force_top_k(streams, k):
    totals = {}
    for stream in streams:
        for player_id, score in stream:
            totals[player_id] = totals.get(player_id, 0.0) + score
    ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
    return ranked[:k]


@pytest.mark.parametrize("k", [1, 2, 3])
def test_threshold_algorithm_matches_brute_force(k):
    streams = [
        [("a", 1.0), ("b", 0.8), ("c", 0.5), ("d", 0.1)],
        [("c", 1.0), ("a", 0.6), ("d", 0.4), ("b", 0.2)],
    ]
    assert threshold_algorithm(streams, k) == _brute_force_top_k(streams, k)


def test_threshold_algorithm_handles_missing_entries():
    streams = [
        [("a", 1.0), ("b", 0.9), ("c", 0.1)],
        [("b", 1.0), ("a", 0.2)],
    ]
    assert threshold_algorithm(streams, 1) == [("b", 1.9)]


def test_threshold_algorithm_k_larger_than_candidates():
    streams = [[("a", 1.0)], [("a", 1.0)]]
    assert threshold_algorithm(streams, 5) == [("a", 2.0)]


def test_parse_args_rejects_non_positive_k():
    with pytest.raises(SystemExit):
        parse_args(["0", "PTS"])


def test_parse_args_rejects_duplicate_categories():
    with pytest.raises(SystemExit):
        parse_args(["3", "PTS", "PTS"])
