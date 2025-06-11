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
from collections import Counter, defaultdict
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


Tile = Tuple[int, str]


def _generate_all_groups(tiles: List[Tile], jokers: List[Tile]) -> List[List[Tile]]:
    """Generate candidate groups of tiles using jokers as wildcards."""
    groups: List[List[Tile]] = []

    num_to_tiles: Dict[int, List[Tile]] = defaultdict(list)
    color_to_nums: Dict[str, set] = defaultdict(set)
    for t in tiles:
        num_to_tiles[t[0]].append(t)
        color_to_nums[t[1]].add(t[0])

    # Full SET groups (same number, different colors)
    for num, same_num_tiles in num_to_tiles.items():
        unique_tiles: List[Tile] = []
        seen_colors = set()
        for t in same_num_tiles:
            if t[1] not in seen_colors:
                seen_colors.add(t[1])
                unique_tiles.append(t)
        for target_size in (3, 4):
            missing = target_size - len(unique_tiles)
            if 0 <= missing <= len(jokers) and len(unique_tiles) + len(jokers) >= 3:
                groups.append(unique_tiles + jokers[:missing])

    # Full RUN groups (same color, consecutive numbers)
    for color, nums in color_to_nums.items():
        nums = sorted(nums)
        for target_size in (3, 4):
            for start in range(1, 14 - target_size + 1):
                window = list(range(start, start + target_size))
                present = [(n, color) for n in window if n in nums]
                missing = target_size - len(present)
                if 0 <= missing <= len(jokers) and len(present) >= 1:
                    groups.append(present + jokers[:missing])

    # Partial SET groups (2 tiles, same number)
    for num, same_num_tiles in num_to_tiles.items():
        if len(same_num_tiles) >= 2:
            groups.append(same_num_tiles[:2])

    # Partial RUN groups (2 tiles, same color)
    for color, nums in color_to_nums.items():
        sorted_nums = sorted(nums)
        for i in range(len(sorted_nums) - 1):
            if sorted_nums[i + 1] - sorted_nums[i] == 1:
                groups.append([(sorted_nums[i], color), (sorted_nums[i + 1], color)])

    unique: List[List[Tile]] = []
    seen = set()
    for g in groups:
        key = tuple(sorted(g))
        if key not in seen:
            seen.add(key)
            unique.append(g)
    return unique


def _find_best_grouping(hand: List[Tile], okey_tile: Optional[Tile] = None) -> Tuple[List[List[Tile]], List[Tile]]:
    """Use backtracking to find grouping that leaves fewest tiles ungrouped."""
    jokers = [t for t in hand if okey_tile is not None and t == okey_tile]
    tiles = [t for t in hand if t not in jokers]

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


def score_hand(hand: List[int], okey: int) -> int:
    """Return the number of ungrouped tiles in ``hand`` using an exhaustive grouping strategy."""

    def as_tile(idx: int) -> Tile:
        tile_index = okey if idx == FAKE_OKEY_INDEX else idx
        num = get_number(tile_index)
        color = get_color(tile_index)
        return (num or 0, color)

    tiles = [as_tile(t) for t in hand]
    joker_tile = as_tile(okey)

    _, remaining = _find_best_grouping(tiles, okey_tile=joker_tile)
    return len(remaining)


def main() -> None:
    """
    Execute the Okey simulation and log results.
    """
    tiles = generate_tiles()
    indicator, okey_tile = select_indicator_and_okey(tiles)
    hands = distribute_tiles(tiles)

    logger.info(f"Indicator : {indicator} -> {get_color(indicator)}-{get_number(indicator)}")
    logger.info(f"Okey tile: {okey_tile} -> {get_color(okey_tile)}-{get_number(okey_tile)}")

    scores = []
    for idx, hand in enumerate(hands, start=1):
        remaining = score_hand(hand, okey_tile)
        scores.append((idx, remaining))
        logger.info(f"Player {idx}: {remaining} ungrouped tiles")

    winner = min(scores, key=lambda x: x[1])
    logger.info(f"Best hand: Player {winner[0]} with {winner[1]} ungrouped tiles")


if __name__ == '__main__':
    main()
