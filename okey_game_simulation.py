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


def score_hand(hand: List[int], okey: int) -> int:
    """
    Evaluate a player's hand by counting how many tiles remain ungrouped.

    - Sequences: runs of three consecutive numbers within the same color
    - Pairs: two identical tile indices
    - Fake Okey (index 52) substitutes the real Okey

    Args:
        hand (List[int]): Player's tile indices.
        okey (int): Index of the Okey tile.

    Returns:
        int: Number of tiles not included in any valid group.
    """
    # Replace fake Okey with actual Okey
    normalized = [okey if t == FAKE_OKEY_INDEX else t for t in hand]
    used = 0

    # Sequence detection by color
    color_groups: Dict[str, List[int]] = defaultdict(list)
    for tile in normalized:
        color = get_color(tile)
        num = get_number(tile)
        if color != 'fake' and num is not None:
            color_groups[color].append(num)

    for nums in color_groups.values():
        counts = Counter(nums)
        unique_nums = sorted(counts)
        i = 0
        while i + 2 < len(unique_nums):
            a, b, c = unique_nums[i], unique_nums[i + 1], unique_nums[i + 2]
            if b == a + 1 and c == b + 1 and counts[a] and counts[b] and counts[c]:
                used += 3
                counts[a] -= 1
                counts[b] -= 1
                counts[c] -= 1
                continue
            i += 1

    # Pair detection by exact tile
    tile_counts = Counter(normalized)
    for count in tile_counts.values():
        used += (count // 2) * 2

    return len(hand) - used


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
