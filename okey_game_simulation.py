"""Okey game simulator for four players.

The module provides helper functions to:
    - build and shuffle the full 106-tile deck,
    - determine the indicator (``gösterge``) and the matching Okey tile,
    - deal tiles to each player,
    - evaluate hands by forming valid sets and runs,
    - report which player is closest to winning.

Run the module as a script to execute a single simulation.
"""
import logging
import random
from collections import defaultdict
from itertools import combinations, product
from typing import List, Tuple, Dict, Optional

# Configure logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s:%(message)s")
logger = logging.getLogger(__name__)

# Constants
NUM_PLAYERS: int = 4
TILES_PER_PLAYER: List[int] = [15, 14, 14, 14]
FAKE_OKEY_INDEX: int = 52
# Face value printed on the Fake Okey tiles. In many physical sets this is a
# specific regular tile (e.g. yellow-1). The Fake Okey only becomes a joker if
# the indicator tile matches this face; otherwise it behaves exactly as this
# regular tile.
FAKE_OKEY_FACE_INDEX: int = 0


def generate_tiles() -> List[int]:
    """Return the full Okey tile deck as a list of indices.

    The deck contains two copies of each tile index ``0`` to ``51`` and two
    fake Okey tiles (index ``52``). The returned list is not shuffled.
    """
    return [i for i in range(53) for _ in range(2)]


def get_color(tile_index: int) -> str:
    """Return the color category of ``tile_index``.

    Parameters
    ----------
    tile_index : int
        Numerical index of the tile (``0``–``52``).

    Returns
    -------
    str
        One of ``"yellow"``, ``"blue"``, ``"black"``, ``"red"`` or ``"fake"``.
    """
    if tile_index == FAKE_OKEY_INDEX:
        return 'fake'
    if 0 <= tile_index <= 12:
        return 'yellow'
    if 13 <= tile_index <= 25:
        return 'blue'
    if 26 <= tile_index <= 38:
        return 'black'
    return 'red'


def get_number(tile_index: int) -> Optional[int]:
    """Return the face value encoded by ``tile_index``.

    Parameters
    ----------
    tile_index : int
        Tile index in the range ``0``–``52``.

    Returns
    -------
    Optional[int]
        An integer between ``1`` and ``13`` or ``None`` if ``tile_index``
        refers to the fake Okey tile.
    """
    if tile_index == FAKE_OKEY_INDEX:
        return None
    return (tile_index % 13) + 1


def select_indicator_and_okey(tiles: List[int]) -> Tuple[int, int]:
    """Pick the indicator tile and derive its corresponding Okey tile.

    Parameters
    ----------
    tiles : List[int]
        Collection of tile indices to select from.

    Returns
    -------
    Tuple[int, int]
        ``(indicator_index, okey_index)`` where ``okey_index`` is the tile that
        acts as a joker for the chosen indicator.
    """
    valid_tiles = [t for t in tiles if t != FAKE_OKEY_INDEX]
    indicator = random.choice(valid_tiles)
    base_color = get_color(indicator)
    base_number = get_number(indicator)  # type: ignore

    next_number = 1 if base_number == 13 else base_number + 1  # type: ignore
    color_offset = {'yellow': 0, 'blue': 13, 'black': 26, 'red': 39}[base_color]
    okey = color_offset + (next_number - 1)

    return indicator, okey


def distribute_tiles(tiles: List[int]) -> List[List[int]]:
    """Shuffle ``tiles`` and deal them according to ``TILES_PER_PLAYER``.

    Parameters
    ----------
    tiles : List[int]
        The complete deck of tiles.

    Returns
    -------
    List[List[int]]
        A list containing each player's hand.
    """
    random.shuffle(tiles)
    hands: List[List[int]] = []
    start = 0
    for count in TILES_PER_PLAYER:
        hands.append(tiles[start:start + count])
        start += count
    return hands


Tile = Tuple[int, str, int, bool]


def _generate_all_groups(tiles: List[Tile], jokers: List[Tile]) -> List[List[Tile]]:
    """Return all possible groups of ``tiles`` using jokers as wildcards.

    The function produces set and run candidates of length three or four. No
    candidate contains more than one joker from ``jokers``.
    """
    groups: List[List[Tile]] = []

    num_to_tiles: Dict[int, List[Tile]] = defaultdict(list)
    color_num_to_tiles: Dict[str, Dict[int, List[Tile]]] = defaultdict(lambda: defaultdict(list))
    for t in tiles:
        num_to_tiles[t[0]].append(t)
        color_num_to_tiles[t[1]][t[0]].append(t)

    # Full SET groups (same number, different colors)
    for num, same_num_tiles in num_to_tiles.items():
        color_groups: Dict[str, List[Tile]] = defaultdict(list)
        for t in same_num_tiles:
            color_groups[t[1]].append(t)
        colors = list(color_groups.keys())
        for target_size in (3, 4):
            if len(colors) + min(len(jokers), 1) < target_size:
                continue
            for color_subset in combinations(colors, min(len(colors), target_size)):
                if len(color_subset) + min(len(jokers), 1) < target_size:
                    continue
                tile_lists = [color_groups[c] for c in color_subset]
                for combo in product(*tile_lists):
                    missing = target_size - len(combo)
                    if 0 <= missing <= 1 and missing <= len(jokers):
                        groups.append(list(combo) + jokers[:missing])

    # Full RUN groups (same color, consecutive numbers)
    for color, num_map in color_num_to_tiles.items():
        nums = sorted(num_map.keys())
        for target_size in (3, 4):
            for start in range(1, 14 - target_size + 1):
                window = list(range(start, start + target_size))
                present_tiles = [num_map[n][0] for n in window if n in num_map]
                missing = target_size - len(present_tiles)
                if 0 <= missing <= 1 and missing <= len(jokers) and len(present_tiles) >= target_size - 1:
                    groups.append(present_tiles + jokers[:missing])


    unique: List[List[Tile]] = []
    seen = set()
    for g in groups:
        key = tuple(sorted(g))
        if key not in seen:
            seen.add(key)
            unique.append(g)
    return unique


def _is_double_run(hand: List[int], okey: int, indicator: int) -> bool:
    """Check whether ``hand`` forms a double run of seven pairs."""
    counts: Dict[int, int] = defaultdict(int)
    jokers = 0
    for t in hand:
        if t == FAKE_OKEY_INDEX:
            if indicator == FAKE_OKEY_FACE_INDEX:
                jokers += 1
            else:
                counts[FAKE_OKEY_FACE_INDEX] += 1
        elif t == okey:
            jokers += 1
        else:
            counts[t] += 1

    pairs = 0
    singles = []
    for c in counts.values():
        pairs += c // 2
        if c % 2:
            singles.append(1)

    if len(singles) > jokers:
        return False
    pairs += len(singles)
    jokers -= len(singles)
    pairs += jokers // 2

    return pairs == 7 and pairs * 2 == len(hand)


def _find_best_grouping(hand: List[Tile]) -> Tuple[List[List[Tile]], List[Tile]]:
    """Search all valid groupings and return the one with the fewest leftovers.

    The function performs a backtracking search across all possible set and run
    combinations generated by ``_generate_all_groups``.
    """
    jokers = [t for t in hand if t[3]]
    tiles = [t for t in hand if not t[3]]

    all_groups = _generate_all_groups(tiles, jokers)

    best_groups: List[List[Tile]] = []
    best_remaining: List[Tile] = hand[:]

    def backtrack(chosen: List[List[Tile]], used: List[Tile]) -> None:
        nonlocal best_groups, best_remaining
        remaining = [t for t in hand if t not in used]
        if len(remaining) < len(best_remaining):
            best_remaining = remaining[:]
            best_groups = chosen[:]
        for g in all_groups:
            if any(tile in used for tile in g):
                continue
            backtrack(chosen + [g], used + g)

    backtrack([], [])
    return best_groups, best_remaining


def score_hand(hand: List[int], okey: int, indicator: int, *, log_details: bool = False) -> int:
    """Evaluate ``hand`` and return the number of tiles left ungrouped.

    The function builds every possible grouping of sets and runs while
    respecting joker usage rules. If ``log_details`` is ``True`` the chosen
    groups and remaining tiles are logged via ``logger``.
    """

    if _is_double_run(hand, okey, indicator):
        if log_details:
            logger.info("Hand is a double-run (7 pairs)")
        return 0

    def as_tile(unique_id: int, idx: int) -> Tile:
        if idx == FAKE_OKEY_INDEX:
            if indicator == FAKE_OKEY_FACE_INDEX:
                tile_index = okey
                is_joker = True
            else:
                tile_index = FAKE_OKEY_FACE_INDEX
                is_joker = False
        elif idx == okey:
            tile_index = idx
            is_joker = True
        else:
            tile_index = idx
            is_joker = False
        num = get_number(tile_index)
        color = get_color(tile_index)
        return (num or 0, color, unique_id, is_joker)

    tiles = [as_tile(i, t) for i, t in enumerate(hand)]

    groups, remaining = _find_best_grouping(tiles)

    if log_details:
        formatted_groups = ["- " + ", ".join(f"{t[1]}-{t[0]}" for t in grp) for grp in groups]
        logger.info("Groups:\n" + "\n".join(formatted_groups))
        logger.info("Ungrouped: " + ", ".join(f"{t[1]}-{t[0]}" for t in remaining))

    return len(remaining)


def main() -> None:
    """Run the simulation once and print summary information."""
    tiles = generate_tiles()
    indicator, okey_tile = select_indicator_and_okey(tiles)
    tiles.remove(indicator)
    hands = distribute_tiles(tiles)

    logger.info(f"Indicator : {indicator} -> {get_color(indicator)}-{get_number(indicator)}")
    logger.info(f"Okey tile: {okey_tile} -> {get_color(okey_tile)}-{get_number(okey_tile)}")

    scores = []
    for idx, hand in enumerate(hands, start=1):
        remaining = score_hand(hand, okey_tile, indicator, log_details=True)
        scores.append((idx, remaining))
        logger.info(f"Player {idx}: {remaining} ungrouped tiles")

    winner = min(scores, key=lambda x: x[1])
    logger.info(f"Best hand: Player {winner[0]} with {winner[1]} ungrouped tiles")


if __name__ == '__main__':
    main()
