import json
import sys
from pathlib import Path

# Root del progetto: .../Pathfinder1e
ROOT_DIR = Path(__file__).resolve().parents[1]

# Aggiungi src/ al sys.path
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from guild_downtime.game_engine import GameEngine

# Cartella salvataggi (replica logica di game_engine.py)
SAVE_DIR = ROOT_DIR / "data" / "saves"
SAVE_DIR.mkdir(parents=True, exist_ok=True)


def slugify(name: str) -> str:
    """Crea uno slug semplice per il nome file della gilda."""
    s = name.strip().lower().replace(" ", "_")
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789_"
    slug = "".join(ch for ch in s if ch in allowed)
    if not slug:
        slug = "gilda"
    base = slug
    i = 2
    path = SAVE_DIR / f"{slug}.json"
    # Evita di sovrascrivere salvataggi esistenti
    while path.exists():
        slug = f"{base}_{i}"
        path = SAVE_DIR / f"{slug}.json"
        i += 1
    return slug


def list_saved_guilds():
    """Restituisce lista di (nome_gilda, path_file)."""
    guilds = []
    for path in sorted(SAVE_DIR.glob("*.json")):
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            name = data.get("guild_name", path.stem)
        except Exception:
            name = path.stem
        guilds.append((name, path))
    return guilds


def choose_guild():
    """Menu iniziale: scegli gilda salvata o creane una nuova."""
    while True:
        guilds = list_saved_guilds()

        print("=== SELEZIONE GILDA DI DOWNTIME ===\n")
        if guilds:
            print("Gilde salvate:")
            for i, (name, path) in enumerate(guilds, 1):
                print(f"[{i}] {name} ({path.name})")
        else:
            print("Nessun salvataggio trovato in data/saves/.")

        new_idx = len(guilds) + 1
        print(f"\n[{new_idx}] Crea nuova gilda")
        print("[0] Esci")

        choice = input("\nScelta: ").strip()
        if not choice.isdigit():
            continue
        choice = int(choice)

        if choice == 0:
            return None, None

        if 1 <= choice <= len(guilds):
            name, path = guilds[choice - 1]
            return path, None

        if choice == new_idx:
            new_name = input("Nome della nuova gilda (invio per default): ").strip()
            if not new_name:
                new_name = "Compagnia Mercenaria del Grifone"
            slug = slugify(new_name)
            path = SAVE_DIR / f"{slug}.json"
            print(f"\nCreerò la gilda '{new_name}' nel file: {path.name}")
            return path, new_name


def main():
    save_file, new_name = choose_guild()
    if save_file is None:
        print("Uscita.")
        return

    # Se il file esiste -> carica; se non esiste -> crea gilda nuova con quel nome
    engine = GameEngine(save_file=save_file, guild_name=new_name)
    engine.menu()


if __name__ == "__main__":
    main()
