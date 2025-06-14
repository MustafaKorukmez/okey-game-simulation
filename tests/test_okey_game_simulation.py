import sys
import os
import pytest

# Ensure project root is in path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from okey_game_simulation import (
    generate_tiles,
    get_color,
    get_number,
    select_indicator_and_okey,
    distribute_tiles,
    score_hand,
    FAKE_OKEY_INDEX,
    FAKE_OKEY_FACE_INDEX,
    TILES_PER_PLAYER,
)


def test_generate_tiles_count_and_distribution():
    """
    Verify that generate_tiles() produces exactly 106 tiles,
    with each tile index 0-51 appearing twice and the fake Okey index appearing twice.
    """
    tiles = generate_tiles()
    # Total count
    assert len(tiles) == 106
    # Check occurrences
    for idx in range(52):
        assert tiles.count(idx) == 2, f"Tile {idx} count is not 2"
    assert tiles.count(FAKE_OKEY_INDEX) == 2, "Fake Okey count is not 2"


def test_get_color_and_number():
    """
    Ensure get_color() and get_number() map indices to correct colors and numbers,
    and handle fake Okey properly.
    """
    # Yellow
    assert get_color(0) == 'yellow' and get_number(0) == 1
    assert get_color(12) == 'yellow' and get_number(12) == 13
    # Blue
    assert get_color(13) == 'blue' and get_number(13) == 1
    assert get_color(25) == 'blue' and get_number(25) == 13
    # Black
    assert get_color(26) == 'black' and get_number(26) == 1
    assert get_color(38) == 'black' and get_number(38) == 13
    # Red
    assert get_color(39) == 'red' and get_number(39) == 1
    assert get_color(51) == 'red' and get_number(51) == 13
    # Fake Okey
    assert get_color(FAKE_OKEY_INDEX) == 'fake'
    assert get_number(FAKE_OKEY_INDEX) is None


def test_select_indicator_and_okey_never_fake():
    """
    Confirm select_indicator_and_okey() never picks the fake Okey as indicator or Okey.
    """
    deck = generate_tiles()
    for _ in range(20):
        indicator, okey = select_indicator_and_okey(deck)
        assert indicator != FAKE_OKEY_INDEX, "Indicator is fake Okey"
        assert okey != FAKE_OKEY_INDEX, "Okey is fake Okey"
        assert 0 <= okey < FAKE_OKEY_INDEX, "Okey index out of valid range"


def test_distribute_tiles_counts_and_completeness():
    """
    Verify distribute_tiles() deals correct counts and that
    dealt tiles are a subset of the original deck with no duplicates.
    """
    deck = list(range(106))
    hands = distribute_tiles(deck.copy())
    # Four hands and correct per-player counts
    assert len(hands) == 4
    assert len(hands[0]) == TILES_PER_PLAYER[0]
    for hand in hands[1:]:
        assert len(hand) == TILES_PER_PLAYER[1]
    # Integrity checks
    dealt = [tile for hand in hands for tile in hand]
    assert len(dealt) == sum(TILES_PER_PLAYER), "Incorrect total dealt tiles"
    assert set(dealt).issubset(set(deck)), "Dealt tiles outside original deck"
    assert len(dealt) == len(set(dealt)), "Duplicate tiles found in hands"


def test_score_hand_sequence_only():
    """A hand with a single run should leave the other tiles ungrouped."""
    hand = [0, 1, 2, 13, 13]
    leftover = score_hand(hand, okey=FAKE_OKEY_INDEX, indicator=FAKE_OKEY_FACE_INDEX)
    assert leftover == 2


def test_score_hand_no_groups():
    """
    A hand containing four tiles of the same number but different colors forms
    a valid set, leaving no tiles ungrouped.
    """
    hand = [0, 13, 26, 39]
    leftover = score_hand(hand, okey=FAKE_OKEY_INDEX, indicator=FAKE_OKEY_FACE_INDEX)
    assert leftover == 0, f"Expected 0 leftover, got {leftover}"


def test_duplicate_tiles_used_separately():
    """Duplicate tiles may remain if they exceed set size."""
    hand = [0, 0, 13, 26, 39]
    leftover = score_hand(hand, okey=FAKE_OKEY_INDEX, indicator=FAKE_OKEY_FACE_INDEX)
    assert leftover == 1


def test_double_run_detection():
    """Hand of seven identical pairs should score zero."""
    hand = [0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6]
    leftover = score_hand(hand, okey=FAKE_OKEY_INDEX, indicator=FAKE_OKEY_FACE_INDEX)
    assert leftover == 0


def test_multiple_jokers_limit_one_per_group():
    """Only one joker can be used in a single group."""
    hand = [0, 1, 52, 52]
    leftover = score_hand(hand, okey=FAKE_OKEY_INDEX, indicator=FAKE_OKEY_FACE_INDEX)
    assert leftover == 1


def test_fake_okey_normal_when_indicator_differs():
    """Fake Okey behaves as its face tile when indicator does not match."""
    hand = [0, 2, 4, 52]
    # indicator different from face index so 52 acts as 0
    leftover = score_hand(hand, okey=1, indicator=FAKE_OKEY_FACE_INDEX + 1)
    assert leftover == 4


def test_fake_okey_joker_when_indicator_matches():
    """Fake Okey becomes a joker when indicator equals its face value."""
    hand = [0, 2, 4, 52]
    leftover = score_hand(hand, okey=1, indicator=FAKE_OKEY_FACE_INDEX)
    assert leftover == 1
