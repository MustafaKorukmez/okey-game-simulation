"""
Simulation of a four-player Okey game:
- Generates and shuffles a complete set of 106 tiles
- Selects an indicator and its corresponding Okey tile
- Distributes tiles to players (one player receives 15, the rest 14)
- Evaluates each hand for sequences and identical-tile pairs
- Determines which hand is closest to winning (fewest ungrouped tiles)
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


def generate_tiles() -> List[int]:
    """
    Build the complete set of 106 Okey tiles.

    Each tile index from 0 to 51 appears twice, plus two fake Okey tiles (index 52).

    Returns:
        List[int]: Unshuffled list of all tile indices.
    """
    return [i for i in range(53) for _ in range(2)]


def get_color(tile_index: int) -> str:
    """
    Determine the color category of a tile based on its index.

    Args:
        tile_index (int): Tile index (0–52).

    Returns:
        str: One of 'yellow', 'blue', 'black', 'red', or 'fake'.
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
    """
    Extract the numeric value (1–13) from a tile index.

    Args:
        tile_index (int): Tile index (0–52).

    Returns:
        Optional[int]: Numeric face value or None for a fake Okey.
    """
    if tile_index == FAKE_OKEY_INDEX:
        return None
    return (tile_index % 13) + 1


def select_indicator_and_okey(tiles: List[int]) -> Tuple[int, int]:
    """
    Randomly choose the indicator tile and compute its paired Okey tile.

    Args:
        tiles (List[int]): List of tile indices.

    Returns:
        Tuple[int, int]: (indicator_index, okey_index)
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
    """
    Shuffle and allocate tiles to each player.

    Args:
        tiles (List[int]): List of all tile indices.

    Returns:
        List[List[int]]: Nested list for each player's hand.
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
    """Generate candidate groups of tiles using jokers as wildcards.

    Only groups of size 3 or 4 are considered. Each group can contain at most
    one joker from ``jokers``.
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


def _is_double_run(hand: List[int], okey: int) -> bool:
    """Return True if ``hand`` consists of seven pairs (double-run)."""
    counts: Dict[int, int] = defaultdict(int)
    for t in hand:
        counts[t] += 1

    jokers = counts.pop(okey, 0) + counts.pop(FAKE_OKEY_INDEX, 0)

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
    """Use backtracking to find grouping that leaves fewest tiles ungrouped."""
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


def score_hand(hand: List[int], okey: int, *, log_details: bool = False) -> int:
    """Return the number of ungrouped tiles in ``hand`` using an exhaustive grouping strategy."""

    if _is_double_run(hand, okey):
        if log_details:
            logger.info("Hand is a double-run (7 pairs)")
        return 0

    def as_tile(unique_id: int, idx: int) -> Tile:
        tile_index = okey if idx == FAKE_OKEY_INDEX else idx
        num = get_number(tile_index)
        color = get_color(tile_index)
        is_joker = idx == FAKE_OKEY_INDEX or idx == okey
        return (num or 0, color, unique_id, is_joker)

    tiles = [as_tile(i, t) for i, t in enumerate(hand)]

    groups, remaining = _find_best_grouping(tiles)

    if log_details:
        formatted_groups = ["- " + ", ".join(f"{t[1]}-{t[0]}" for t in grp) for grp in groups]
        logger.info("Groups:\n" + "\n".join(formatted_groups))
        logger.info("Ungrouped: " + ", ".join(f"{t[1]}-{t[0]}" for t in remaining))

    return len(remaining)


def main() -> None:
    """
    Execute the Okey simulation and log results.
    """
    tiles = generate_tiles()
    indicator, okey_tile = select_indicator_and_okey(tiles)
    tiles.remove(indicator)
    hands = distribute_tiles(tiles)

    logger.info(f"Indicator : {indicator} -> {get_color(indicator)}-{get_number(indicator)}")
    logger.info(f"Okey tile: {okey_tile} -> {get_color(okey_tile)}-{get_number(okey_tile)}")

    scores = []
    for idx, hand in enumerate(hands, start=1):
        remaining = score_hand(hand, okey_tile, log_details=True)
        scores.append((idx, remaining))
        logger.info(f"Player {idx}: {remaining} ungrouped tiles")

    winner = min(scores, key=lambda x: x[1])
    logger.info(f"Best hand: Player {winner[0]} with {winner[1]} ungrouped tiles")


if __name__ == '__main__':
    main()
