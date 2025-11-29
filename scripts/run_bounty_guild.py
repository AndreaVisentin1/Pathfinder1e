import sys
from pathlib import Path

# Determine project root: .../Pathfinder1e
ROOT_DIR = Path(__file__).resolve().parents[1]

# Add src/ to sys.path so that "guild_downtime" can be imported
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from guild_downtime.game_engine import GameEngine


def main():
    engine = GameEngine()
    engine.main_menu()


if __name__ == "__main__":
    main()
