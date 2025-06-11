# Okey Game Simulation

A professional, scalable Python simulation of a four-player Okey game.  Each
function is fully documented with informative docstrings.  This repository demonstrates:

- **Tile Generation**: Creates the full 106-tile set, including 52 unique tiles (0–51) and two fake Okey tiles (52), each duplicated twice.
- **Indicator Selection**: Randomly picks a ‘gösterge’ tile and computes its corresponding Okey tile with wrap-around logic.
- **Tile Distribution**: Shuffles and deals 15 tiles to one player and 14 to each of the remaining three.
- **Hand Evaluation**: Scores hands by detecting valid sequences (three consecutive numbers in the same color) and identical-tile pairs, substituting the fake Okey tile appropriately.
- **Winner Determination**: Identifies the player whose hand has the fewest ungrouped tiles (closest to winning).

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Core Concepts](#core-concepts)
- [Testing](#testing)
- [Logging and Configuration](#logging-and-configuration)


---

## Prerequisites

- Python 3.8 or higher

This project uses only standard library modules:

```plaintext
random
logging
collections
typing
``` 

---

## Installation

Clone the repository and (optionally) create a virtual environment:

```bash
git clone https://github.com/MustafaKorukmez/okey-game-simulation.git
cd okey-game-simulation
```

---

## Usage

Run the simulation:

```bash
python okey_game_simulation.py
```

You will see INFO-level logs for:

1. Selected indicator and Okey tile
2. Each player’s number of ungrouped tiles
3. The winning hand (fewest ungrouped tiles)

---

## Project Structure

```plaintext
okey-game-simulation/
├── okey_game_simulation.py   # Core simulation module
├── tests/                    # pytest test suite
│   └── test_okey_game_simulation.py
└── README.md                 # Project overview and instructions
```

---

## Core Concepts

1. **Tile Encoding**: Each tile index maps to a color and value:
   - 0–12: Yellow 1–13
   - 13–25: Blue 1–13
   - 26–38: Black 1–13
   - 39–51: Red 1–13
   - 52: Fake Okey

2. **Indicator Logic**:
   - Randomly select a non-fake tile as the indicator.
   - Compute the Okey tile by advancing the number (13 wraps to 1) within the same color.

3. **Hand Scoring**:
   - **Sequences**: Runs of three consecutive numbers per color.
   - **Pairs**: Two identical tile indices.
   - Fake Okey acts as a regular tile showing the face value ``FAKE_OKEY_FACE_INDEX``.
     It only becomes a joker if the indicator tile is the same value.

4. **Winner Determination**:
   - Calculate ungrouped tile count per hand.
   - The player with the lowest count is closest to winning.

---

## Testing

A comprehensive test suite is included under `tests/` using **pytest**. It covers:

- **Tile Generation**: Ensures 106 tiles and correct counts.
- **Color/Number Mapping**: Validates color and face value extraction.
- **Indicator/Okey Selection**: Verifies no fake Okey is chosen.
- **Tile Distribution**: Confirms correct hand sizes and integrity.
- **Hand Scoring**: Tests sequence detection, identical-tile pairs, and edge cases.

Run the tests with:

```bash
pytest --maxfail=1 --disable-warnings -q
```

---

## Logging and Configuration

- Uses Python’s built-in `logging` module at INFO level.
- Customize the log level or format by editing the `logging.basicConfig` call in `okey_game_simulation.py`.
- All public functions include comprehensive docstrings accessible via `help()`.

---
