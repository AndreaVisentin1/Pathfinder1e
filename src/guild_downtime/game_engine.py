# ============================================================
# NOTE DI INTEGRAZIONE NEL PROGETTO
#
# - Questo file è pensato per essere collocato in: src/guild_downtime/game_engine.py
# - I salvataggi vengono scritti in: <radice_progetto>/data/saves/
# - Per questa gilda il file di default è: data/saves/Cacciatori_di_Taglie.json
# - Per usare un altro file/gilda all'interno del progetto:
#       from guild_downtime.game_engine import ResourceBank, DATA_DIR
#       bank = ResourceBank(DATA_DIR / "Nome_Altra_Gilda.json")
# - Oppure, per un percorso completamente personalizzato:
#       from pathlib import Path
#       bank = ResourceBank(Path("percorso/personalizzato.json"))
# - È consigliabile creare uno script di avvio in scripts/, ad esempio:
#       scripts/run_bounty_guild.py -> istanzia GameEngine() e chiama menu().
# - Se vuoi separare configurazioni iniziali e salvataggi:
#       * configs/ contiene i template iniziali delle gilde.
#       * data/saves/ contiene solo gli stati di gioco salvati.
# ============================================================

import difflib
import json
import os
import random
import time
from pathlib import Path

# Percorsi base per i salvataggi (radice del repo = ../../ rispetto a questo file)
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data" / "saves"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# File di salvataggio di default per questa gilda (Cacciatori di Taglie)
DEFAULT_SAVE_FILE = DATA_DIR / "Cacciatori_di_Taglie.json"


# ==========================================
# DATABASE REGOLE (Fonte: Golarion Insider)
# ==========================================

# Costi per GUADAGNARE 1 punto di risorsa (Dimezzato rispetto all'acquisto)
EARN_COSTS = {
    "Merci": 10,
    "Manodopera": 10,
    "Influenza": 15,
    "Magia": 50,
    "MO": 0,  # Generare monete è gratis
}

# Costi per ACQUISTARE 1 punto di risorsa
BUY_COSTS = {
    "Merci": 20,
    "Manodopera": 20,
    "Influenza": 30,
    "Magia": 100,
    "MO": 1,  # 1 MO = 1 MO, solo per completezza
}

# Target DC per i Tiri di Controllo Esecutivo (Giorno di Gestione)
CONTROL_DC_TABLE = {
    "Facile": 10,
    "Medio": 15,
    "Difficile": 20,
    "Molto Difficile": 25,
    "Estremo": 30,
}

# Target DC per i Tiri di Evento (Eventi Casuali)
EVENT_DC_TABLE = {
    "Minore": 10,
    "Moderato": 15,
    "Grave": 20,
    "Disastroso": 25,
}

# Lista degli EVENTI CASUALI possibili (semplificati e adattati)
RANDOM_EVENTS = [
    {
        "name": "Donazione Inaspettata",
        "description": "Un ricco benefattore dona fondi alla gilda.",
        "resource": "MO",
        "amount": 50,
    },
    {
        "name": "Richiesta di Aiuto",
        "description": "Una comunità in pericolo chiede l'aiuto della gilda. "
        "Se accettata, aumenta l'Influenza.",
        "resource": "Influenza",
        "amount": 2,
    },
    {
        "name": "Incidente sul Lavoro",
        "description": "Un incidente causa costi imprevisti in Magia o Manodopera.",
        "resource": "Manodopera",
        "amount": -2,
    },
    {
        "name": "Scandalo",
        "description": "Un membro della gilda è coinvolto in uno scandalo pubblico.",
        "resource": "Influenza",
        "amount": -3,
    },
    {
        "name": "Affari Fiorenti",
        "description": "Un periodo di intensa attività porta profitti extra.",
        "resource": "MO",
        "amount": 30,
    },
]

# Effetti ricorrenti di Gilda
GUILD_EFFECTS = {
    "Bonus Reclutamento": {
        "description": "La gilda ha una rete di contatti che facilita il reclutamento.",
        "influenza_bonus": 2,
    },
    "Reputazione Temeraria": {
        "description": "La gilda è famosa per prendere missioni troppo rischiose.",
        "event_chance_bonus": 10,
    },
}

# Tipologie di Squadre e Stanze con i relativi costi di costruzione (semplificato)
SQUAD_ROOMS_COSTS = {
    # --- SQUADRE ---
    "Agente": {"MO": 2, "Influenza": 2},
    "Artigiani": {"MO": 2, "Manodopera": 2, "Merci": 2},
    "Guardia del Corpo": {"MO": 4, "Influenza": 4, "Manodopera": 4},
    "Informatori": {"MO": 1, "Influenza": 1},
    "Mercenari": {"MO": 3, "Influenza": 3, "Manodopera": 3},
    "Spie": {"MO": 2, "Influenza": 2},
    "Cavalleria": {"MO": 7, "Influenza": 7, "Manodopera": 7},
    "Criminali": {"MO": 1, "Influenza": 1, "Merci": 1},
    "Cultisti": {"MO": 2, "Influenza": 2, "Magia": 2},
    "Guaritori": {"MO": 3, "Magia": 3, "Manodopera": 3},
    "Mendicanti": {"MO": 1, "Influenza": 1},
    "Marinai": {"MO": 2, "Manodopera": 2, "Merci": 2},
    "Rapinatori": {"MO": 4, "Influenza": 4, "Merci": 4},
    "Sacerdote": {"MO": 7, "Influenza": 7, "Magia": 7},
    "Saggio": {"MO": 5, "Influenza": 5},
    "Soldati": {"MO": 5, "Influenza": 5, "Manodopera": 5},
    "Soldati Scelti": {"MO": 6, "Influenza": 6, "Manodopera": 6},
    "Tagliaborse": {"MO": 3, "Manodopera": 3, "Merci": 3},
    "Trasgressori": {"MO": 2, "Influenza": 2, "Merci": 2},
    # --- STANZE ---
    "Alloggi": {"MO": 12},
    "Altare": {"Influenza": 3},
    "Arena da Combattimento": {"MO": 15, "Influenza": 15},
    "Auditorium": {"MO": 15, "Influenza": 15},
    "Aula": {"MO": 8, "Influenza": 8, "Magia": 8, "Manodopera": 8, "Merci": 8},
    "Bottega": {"MO": 10, "Merci": 10, "Manodopera": 10},
    "Caserma": {"MO": 10, "Manodopera": 10},
    "Cella": {"MO": 4, "Manodopera": 4},
    "Cimitero": {"MO": 10, "Manodopera": 10},
    "Cucina": {"MO": 6, "Manodopera": 6, "Merci": 6},
    "Dispensa": {"MO": 5, "Merci": 5},
    "Dormitorio": {"MO": 8, "Manodopera": 8},
    "Infermeria": {"MO": 12, "Magia": 12},
    "Laboratorio": {"MO": 12, "Magia": 12, "Merci": 12},
    "Magazzino": {"MO": 6, "Merci": 6},
    "Palestra": {"MO": 8, "Manodopera": 8},
    "Sala Comune": {"MO": 8, "Influenza": 8},
    "Sala del Consiglio": {"MO": 18, "Influenza": 18, "Magia": 18},
    "Santuario": {"MO": 15, "Influenza": 15, "Magia": 15},
    "Stalla": {"MO": 10, "Manodopera": 10},
    "Studio": {"MO": 8, "Influenza": 8, "Magia": 8},
}

# Configurazione di Default della Gilda di Cacciatori di Taglie
DEFAULT_GUILD_CONFIG = {
    "name": "Gilda dei Cacciatori di Taglie",
    "description": "Una gilda specializzata nella cattura di criminali ricercati, "
    "mostri pericolosi e bersagli ad alto rischio.",
    "starting_resources": {
        "MO": 100.0,
        "Merci": 5,
        "Influenza": 3,
        "Magia": 0,
        "Manodopera": 4,
    },
    "starting_units": [
        {
            "name": "Mercenari",
            "type": "Squadra",
            "bonuses": {"MO": 3, "Influenza": 3, "Manodopera": 3},
            "qty": 1,
        },
        {
            "name": "Informatori",
            "type": "Squadra",
            "bonuses": {"Influenza": 2},
            "qty": 1,
        },
        {
            "name": "Guardia del Corpo",
            "type": "Squadra",
            "bonuses": {"MO": 4, "Influenza": 4, "Manodopera": 4},
            "qty": 1,
        },
        {
            "name": "Alloggi",
            "type": "Stanza",
            "bonuses": {"MO": 0},
            "qty": 1,
        },
    ],
}

# ==========================================
# CLASSI DI SUPPORTO
# ==========================================


class DiceRoller:
    @staticmethod
    def roll_die(sides, bonus=0, reason="Tiro generico", silent=False):
        roll = random.randint(1, sides)
        total = roll + bonus
        sign = "+" if bonus >= 0 else ""
        if not silent:
            print(
                f"\n[TIRO] {reason}: 1d{sides}{sign}{bonus} = {roll} {sign} {bonus} = {total}"
            )
        return total, roll

    @staticmethod
    def roll_dice_pool(num_dice, sides, bonus_per_die=0, reason="Pool di dadi"):
        rolls = [random.randint(1, sides) for _ in range(num_dice)]
        total = sum(rolls) + num_dice * bonus_per_die
        sign = "+" if bonus_per_die >= 0 else ""
        print(
            f"\n[POOL] {reason}: {num_dice}d{sides}{sign}{bonus_per_die} "
            f"= {rolls} {sign} {num_dice * bonus_per_die} -> Totale: {total}"
        )
        return total, rolls


class Unit:
    def __init__(self, name, unit_type, bonuses, quantity=1):
        self.name = name
        self.unit_type = unit_type  # "Squadra" o "Stanza"
        self.bonuses = (
            bonuses  # dict di bonus per risorsa es: {"MO": 2, "Influenza": 1}
        )
        self.quantity = quantity

    def to_dict(self):
        return {
            "name": self.name,
            "unit_type": self.unit_type,
            "bonuses": self.bonuses,
            "quantity": self.quantity,
        }

    @staticmethod
    def from_dict(data):
        """
        Build a Unit from a dict.

        Supports both:
        - new format:  name, unit_type, bonuses, quantity
        - old format:  name, type, bonuses, qty
        """
        name = data.get("name", "Unnamed unit")
        unit_type = data.get("unit_type") or data.get("type") or "Unknown"
        bonuses = data.get("bonuses", {})
        quantity = data.get("quantity", data.get("qty", 1))

        return Unit(
            name=name,
            unit_type=unit_type,
            bonuses=bonuses,
            quantity=quantity,
        )


class Guild:
    def __init__(
        self,
        name,
        description,
        starting_resources,
        starting_units=None,
        active_effects=None,
    ):
        self.name = name
        self.description = description
        self.resources = starting_resources.copy()
        self.units = []
        self.active_effects = active_effects if active_effects is not None else []

        if starting_units:
            for u in starting_units:
                self.add_unit(
                    u["name"], u["type"], u["bonuses"], quantity=u.get("qty", 1)
                )

    def add_unit(self, name, unit_type, bonuses, quantity=1):
        self.units.append(Unit(name, unit_type, bonuses, quantity))

    def apply_effects(self, bank):
        for effect_name in self.active_effects:
            effect = GUILD_EFFECTS.get(effect_name)
            if not effect:
                continue
            if "influenza_bonus" in effect:
                bank.modify("Influenza", effect["influenza_bonus"], effect_name)
            if "event_chance_bonus" in effect:
                bank.event_chance += effect["event_chance_bonus"]
                bank.add_history_entry(
                    f"[EFFETTO] {effect_name}: probabilità eventi +{effect['event_chance_bonus']}%."
                )

    def describe(self):
        print(f"\n=== {self.name} ===")
        print(self.description)
        print("\n[Unità attive]:")
        if not self.units:
            print("  Nessuna unità attiva.")
        else:
            for u in self.units:
                print(
                    f"  - {u.name} ({u.unit_type}) x{u.quantity} | Bonus: {u.bonuses}"
                )
        if self.active_effects:
            print("\n[Effetti di Gilda attivi]:")
            for eff in self.active_effects:
                desc = GUILD_EFFECTS.get(eff, {}).get("description", "")
                print(f"  - {eff}: {desc}")


class ResourceBank:
    def __init__(self, save_file=None):
        self.resources = {
            "MO": 0.0,
            "Merci": 0,
            "Influenza": 0,
            "Magia": 0,
            "Manodopera": 0,
        }
        self.character_stats = {
            "Diplomazia": 6,
            "Raggirare": 4,
            "Professione (soldato)": 0,
            "Intimidire": 0,
            "Combattimento": 0,
            "Autorità": 4,
        }
        self.day_counter = 1
        self.event_chance = 20
        self.history = []
        self.guild_control_lost = False

        # Path del file di salvataggio per questa istanza
        # - se save_file è None -> usa DEFAULT_SAVE_FILE (Cacciatori_di_Taglie)
        # - altrimenti usa il path passato (per altre gilde o percorsi custom)
        self.save_file = Path(save_file) if save_file is not None else DEFAULT_SAVE_FILE

    def modify(self, resource, amount, reason=""):
        """
        Gestisce l'aggiunta/rimozione di risorse e applica i Costi di Conseguimento (GP).
        Restituisce (amount_effettivo, costo_gp).
        """
        if resource not in self.resources:
            raise ValueError(f"Risorsa sconosciuta: {resource}")

        original_amount = amount
        actual_amount = amount
        cost_gp = 0

        # Se stiamo GUADAGNANDO capitale (non MO), c'è un costo in MO
        if amount > 0 and resource in EARN_COSTS and resource != "MO":
            unit_cost = EARN_COSTS[resource]
            total_cost = amount * unit_cost

            # Controllo Fondi
            if self.resources["MO"] >= total_cost:
                # Ho i soldi
                self.resources["MO"] = round(self.resources["MO"] - total_cost, 2)
                cost_gp = total_cost
            else:
                # Non ho abbastanza soldi: riduco il guadagno a ciò che posso permettermi
                affordable_amount = int(self.resources["MO"] // unit_cost)
                actual_cost = affordable_amount * unit_cost
                self.resources["MO"] = round(self.resources["MO"] - actual_cost, 2)

                # Aggiorno le variabili di ritorno
                actual_amount = affordable_amount
                cost_gp = actual_cost

                # Se reason non è vuota, segnalo il cap nel log (opzionale, gestito fuori)

        # Applicazione modifica risorsa target
        if resource == "MO":
            new_val = self.resources[resource] + actual_amount
        else:
            new_val = self.resources[resource] + actual_amount

        # Le risorse (eccetto MO) non possono scendere sotto 0
        if resource != "MO":
            new_val = max(0, new_val)

        self.resources[resource] = round(new_val, 2)

        # Log dell'operazione
        if reason:
            if original_amount != actual_amount:
                self.add_history_entry(
                    f"[RISORSE] {reason}: {resource} {original_amount:+} "
                    f"(effettivo: {actual_amount:+}, costo in MO: {cost_gp}). "
                    f"Nuovo totale {resource} = {self.resources[resource]}"
                )
            else:
                self.add_history_entry(
                    f"[RISORSE] {reason}: {resource} {actual_amount:+} "
                    f"(costo in MO: {cost_gp}). Nuovo totale {resource} = {self.resources[resource]}"
                )

        return actual_amount, cost_gp

    def gain_resource(self, resource, amount, reason="Guadagno risorsa"):
        """Wrapper per guadagnare risorse: usa modify in modalità 'gain'."""
        return self.modify(resource, amount, reason=reason)

    def spend_resource(self, resource, amount, reason="Spesa risorsa"):
        """Wrapper per spendere risorse (amount positivo, internamente convertito in negativo)."""
        return self.modify(resource, -abs(amount), reason=reason)

    def set_character_stat(self, stat_name, value):
        if stat_name not in self.character_stats:
            raise ValueError(f"Statistiche sconosciute: {stat_name}")
        self.character_stats[stat_name] = value
        self.add_history_entry(f"[STATS] {stat_name} impostata a {value}.")

    def add_history_entry(self, entry):
        timestamp = time.strftime("%d/%m/%Y %H:%M:%S")
        self.history.append(f"[{timestamp}] {entry}")
        # Manteniamo al massimo 200 voci per non gonfiare il file
        if len(self.history) > 200:
            self.history.pop(0)

    def save_state(self, guild):
        data = {
            "resources": self.resources,
            "character_stats": self.character_stats,
            "day_counter": self.day_counter,
            "event_chance": self.event_chance,
            "history": self.history,
            "guild_control_lost": self.guild_control_lost,
            "guild_name": guild.name,
            "guild_units": [u.to_dict() for u in guild.units],
            "active_effects": guild.active_effects,
        }
        with self.save_file.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def load_state(self):
        if not self.save_file.exists():
            return None
        with self.save_file.open("r", encoding="utf-8") as f:
            return json.load(f)


# ==========================================
# EVENTI MERCENARI
# ==========================================


def handle_mercenary_event(d100_roll, bank, guild):
    """
    Gestisce un evento casuale basato su un tiro d100, adattato al tema
    della Gilda di Cacciatori di Taglie.
    """
    if d100_roll <= 20:
        event = {
            "name": "Taglia Facile",
            "description": "Un bersaglio minore viene catturato senza troppi problemi.",
            "resource": "MO",
            "amount": 20,
        }
    elif d100_roll <= 40:
        event = {
            "name": "Taglia Importante",
            "description": "Un criminale ricercato di medio profilo viene catturato.",
            "resource": "MO",
            "amount": 40,
        }
    elif d100_roll <= 60:
        event = {
            "name": "Perdita di Equipaggiamento",
            "description": "Durante una missione, parte dell'equipaggiamento viene perso.",
            "resource": "Merci",
            "amount": -2,
        }
    elif d100_roll <= 80:
        event = {
            "name": "Feriti in Missione",
            "description": "Alcuni membri vengono feriti e richiedono cure.",
            "resource": "Manodopera",
            "amount": -2,
        }
    else:
        event = {
            "name": "Caccia al Mostro Leggendario",
            "description": "Una missione estremamente pericolosa, ma remunerativa.",
            "resource": "MO",
            "amount": 60,
        }

    print(f"\n[EVENTO CASUALE - MERCENARI] {event['name']}")
    print(event["description"])
    bank.modify(event["resource"], event["amount"], event["name"])
    return event


def handle_influence_event(d100_roll, bank, guild):
    """
    Gestisce un evento casuale legato all'Influenza.
    """
    if d100_roll <= 25:
        event = {
            "name": "Voci Favorevoli",
            "description": "La popolazione parla bene della gilda.",
            "resource": "Influenza",
            "amount": 2,
        }
    elif d100_roll <= 50:
        event = {
            "name": "Critiche Pubbliche",
            "description": "Un nobile o un'organizzazione critica la gilda.",
            "resource": "Influenza",
            "amount": -2,
        }
    elif d100_roll <= 75:
        event = {
            "name": "Richiesta Ufficiale",
            "description": "Le autorità chiedono l'intervento della gilda su un caso delicato.",
            "resource": "Influenza",
            "amount": 3,
        }
    else:
        event = {
            "name": "Scandalo Interno",
            "description": "Uno scandalo coinvolge un membro della gilda.",
            "resource": "Influenza",
            "amount": -4,
        }

    print(f"\n[EVENTO CASUALE - INFLUENZA] {event['name']}")
    print(event["description"])
    bank.modify(event["resource"], event["amount"], event["name"])
    return event


def handle_magic_event(d100_roll, bank, guild):
    """
    Gestisce un evento casuale legato alla Magia.
    """
    if d100_roll <= 30:
        event = {
            "name": "Ritrovamento di Tomo Arcano",
            "description": "Un tomo di magia viene ritrovato inaspettatamente.",
            "resource": "Magia",
            "amount": 1,
        }
    elif d100_roll <= 60:
        event = {
            "name": "Incidente Magico",
            "description": "Un esperimento va storto e le risorse magiche vengono consumate.",
            "resource": "Magia",
            "amount": -1,
        }
    elif d100_roll <= 85:
        event = {
            "name": "Aiuto di un Mago",
            "description": "Un mago decide di aiutare la gilda temporaneamente.",
            "resource": "Magia",
            "amount": 2,
        }
    else:
        event = {
            "name": "Rottura di Sigillo",
            "description": "Un sigillo magico difettoso causa gravi perdite.",
            "resource": "Magia",
            "amount": -2,
        }

    print(f"\n[EVENTO CASUALE - MAGIA] {event['name']}")
    print(event["description"])
    bank.modify(event["resource"], event["amount"], event["name"])
    return event


# ==========================================
# FUNZIONI DI UTILITY
# ==========================================


def clear_console():
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


def print_header(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60 + "\n")


def choose_from_list(prompt, options):
    """
    Permette di scegliere un'opzione da una lista con fuzzy search.
    """
    while True:
        print(prompt)
        for i, opt in enumerate(options, start=1):
            print(f"  {i}. {opt}")
        print("  0. Annulla")

        choice = input("\nScelta: ").strip()
        if choice == "0":
            return None
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(options):
                return options[idx - 1]

        # Fuzzy match
        matches = difflib.get_close_matches(choice, options, n=1, cutoff=0.4)
        if matches:
            print(f"Forse intendevi: {matches[0]} ?")
            confirm = input("Confermare? (s/n): ").strip().lower()
            if confirm == "s":
                return matches[0]

        print("Scelta non valida. Riprova.\n")


def prompt_int(prompt, default=None, min_val=None, max_val=None):
    while True:
        s = input(prompt).strip()
        if not s and default is not None:
            return default
        if not s:
            print("Inserisci un valore numerico.")
            continue
        if not s.lstrip("-").isdigit():
            print("Inserisci un numero intero.")
            continue
        val = int(s)
        if min_val is not None and val < min_val:
            print(f"Il valore minimo consentito è {min_val}.")
            continue
        if max_val is not None and val > max_val:
            print(f"Il valore massimo consentito è {max_val}.")
            continue
        return val


def prompt_float(prompt, default=None, min_val=None, max_val=None):
    while True:
        s = input(prompt).strip().replace(",", ".")
        if not s and default is not None:
            return default
        if not s:
            print("Inserisci un valore numerico.")
            continue
        try:
            val = float(s)
        except ValueError:
            print("Inserisci un numero (usa . o , per i decimali).")
            continue
        if min_val is not None and val < min_val:
            print(f"Il valore minimo consentito è {min_val}.")
            continue
        if max_val is not None and val > max_val:
            print(f"Il valore massimo consentito è {max_val}.")
            continue
        return val


def press_enter_to_continue():
    input("\nPremi INVIO per continuare...")


# ==========================================
# SISTEMA DI GESTIONE GIORNALIERA
# ==========================================


class DowntimeDay:
    def __init__(self, bank, guild):
        self.bank = bank
        self.guild = guild

    def run_day(self):
        clear_console()
        print_header(f"Giorno di Gestione #{self.bank.day_counter}")
        self.guild.describe()
        self.print_resources()
        self.print_stats()

        # Applicazione effetti di gilda all'inizio del giorno
        if self.guild.active_effects:
            print("\n[Effetti di Gilda attivi]")
            for eff in self.guild.active_effects:
                desc = GUILD_EFFECTS.get(eff, {}).get("description", "")
                print(f"  - {eff}: {desc}")
            apply = (
                input("\nApplicare effetti di gilda per questo giorno? (s/n) [s]: ")
                .strip()
                .lower()
            )
            if apply in ("", "s", "si"):
                self.guild.apply_effects(self.bank)

        while True:
            print("\nAzioni possibili per questo giorno:")
            print("  1. Gestione Risorse (Guadagna/Spendi/Compra)")
            print("  2. Gestione Unità (Squadre/Stanze)")
            print("  3. Giorno di Controllo Esecutivo")
            print("  4. Tirare un Evento Casuale")
            print("  5. Modificare Statistiche Personaggio")
            print("  6. Visualizzare Registro Eventi")
            print("  7. Fine del Giorno")
            print("  0. Annulla e torna al menu principale")

            choice = input("\nScelta: ").strip()

            if choice == "1":
                self.manage_resources()
            elif choice == "2":
                self.manage_units()
            elif choice == "3":
                self.run_control_check()
            elif choice == "4":
                self.run_random_event()
            elif choice == "5":
                self.modify_character_stats()
            elif choice == "6":
                self.show_history()
            elif choice == "7":
                self.end_day()
                break
            elif choice == "0":
                print("Annullato. Ritorno al menu principale.")
                break
            else:
                print("Scelta non valida. Riprova.")

    def print_resources(self):
        print("\n[Risorse Attuali]")
        for k, v in self.bank.resources.items():
            print(f"  - {k}: {v}")

    def print_stats(self):
        print("\n[Statistiche del Personaggio / Gestore della Gilda]")
        for k, v in self.bank.character_stats.items():
            print(f"  - {k}: {v}")

    # -------------------------------------------------------
    # Gestione Risorse
    # -------------------------------------------------------

    def manage_resources(self):
        while True:
            clear_console()
            print_header("Gestione Risorse")
            self.print_resources()
            print("\nAzioni:")
            print("  1. Guadagna Risorsa (Downtime: Guadagnare Capitale)")
            print("  2. Spendi Risorsa")
            print("  3. Compra Capitale (convertendo MO in altre risorse)")
            print("  0. Torna indietro")

            choice = input("\nScelta: ").strip()
            if choice == "1":
                self.action_earn_resource()
            elif choice == "2":
                self.action_spend_resource()
            elif choice == "3":
                self.action_buy_capital()
            elif choice == "0":
                break
            else:
                print("Scelta non valida. Riprova.")

    def action_earn_resource(self):
        print_header("Guadagnare Risorsa")
        print("Scegli la risorsa da guadagnare:")
        resources = list(self.bank.resources.keys())
        chosen = choose_from_list("Risorse disponibili:", resources)
        if not chosen:
            return

        base_amount = prompt_int(
            f"Inserisci la quantità di {chosen} da guadagnare: ", min_val=1
        )

        # Applichiamo un tiro di abilità per simulare il downtime
        print("\nScegli l'abilità usata per guadagnare la risorsa:")
        stats = list(self.bank.character_stats.keys())
        stat = choose_from_list("Statistiche disponibili:", stats)
        if not stat:
            return

        bonus = self.bank.character_stats[stat]
        total, roll = DiceRoller.roll_die(
            20,
            bonus,
            reason=f"Guadagnare {chosen} usando {stat}",
        )

        # DC base 15, modificabile
        dc = 15
        print(f"DC base per l'azione: {dc}")
        if total >= dc:
            amount = base_amount
            print(
                f"Successo! Guadagni {amount} {chosen} (prima dei costi in GP, se applicabili)."
            )
            self.bank.modify(
                chosen,
                amount,
                reason=f"Guadagnare {chosen} (Downtime, successo tiro abilità)",
            )
        else:
            print(
                "Fallimento nel tiro di abilità: nessuna risorsa guadagnata "
                "(ma non perdi MO se il tiro fallisce)."
            )
            self.bank.add_history_entry(
                f"[DOWNTIME] Tentativo di guadagnare {chosen} usando {stat} fallito (1d20 + {bonus} = {total} vs DC {dc})."
            )

        press_enter_to_continue()

    def action_spend_resource(self):
        print_header("Spendere Risorsa")
        print("Scegli la risorsa da spendere:")
        resources = list(self.bank.resources.keys())
        chosen = choose_from_list("Risorse disponibili:", resources)
        if not chosen:
            return

        max_spendable = int(self.bank.resources[chosen]) if chosen != "MO" else None
        if chosen != "MO":
            print(f"Puoi spendere al massimo {max_spendable} {chosen}.")
        amount = prompt_int(
            f"Inserisci la quantità di {chosen} da spendere: ",
            min_val=1,
            max_val=max_spendable if max_spendable is not None else None,
        )

        self.bank.spend_resource(chosen, amount, reason="Spesa manuale di risorsa")
        print(f"Hai speso {amount} {chosen}.")
        press_enter_to_continue()

    def action_buy_capital(self):
        print_header("Comprare Capitale")
        print("Puoi convertire MO in altre risorse in base alla tabella BUY_COSTS.")
        print("Costi per 1 punto di risorsa:")
        for res, cost in BUY_COSTS.items():
            if res == "MO":
                continue
            print(f"  - {res}: {cost} MO")

        print(f"\nHai attualmente {self.bank.resources['MO']} MO.")
        resource = choose_from_list(
            "Scegli la risorsa da comprare:", [r for r in BUY_COSTS.keys() if r != "MO"]
        )
        if not resource:
            return

        cost_per_point = BUY_COSTS[resource]
        max_points = int(self.bank.resources["MO"] // cost_per_point)
        if max_points <= 0:
            print(
                "Non hai abbastanza MO per comprare nemmeno 1 punto di questa risorsa."
            )
            press_enter_to_continue()
            return

        print(f"Puoi comprare fino a {max_points} punti di {resource}.")
        amount = prompt_int(
            f"Quanti punti di {resource} vuoi comprare?: ",
            min_val=1,
            max_val=max_points,
        )

        total_cost = amount * cost_per_point
        self.bank.resources["MO"] = round(self.bank.resources["MO"] - total_cost, 2)
        self.bank.resources[resource] += amount
        self.bank.add_history_entry(
            f"[ACQUISTO CAPITALE] Acquistati {amount} punti di {resource} per {total_cost} MO."
        )

        print(f"Hai acquistato {amount} {resource} per {total_cost} MO.")
        press_enter_to_continue()

    # -------------------------------------------------------
    # Gestione Unità (Squadre e Stanze)
    # -------------------------------------------------------

    def manage_units(self):
        while True:
            clear_console()
            print_header("Gestione Unità (Squadre e Stanze)")
            self.print_units()

            print("\nAzioni:")
            print("  1. Recluta/Costruisci nuova Unità")
            print("  2. Aumenta quantità di Unità esistente")
            print("  3. Riduci quantità di Unità esistente")
            print("  0. Torna indietro")

            choice = input("\nScelta: ").strip()
            if choice == "1":
                self.action_recruit_unit()
            elif choice == "2":
                self.action_increase_unit()
            elif choice == "3":
                self.action_decrease_unit()
            elif choice == "0":
                break
            else:
                print("Scelta non valida. Riprova.")

    def print_units(self):
        print("\n[Unità attuali della Gilda]")
        if not self.guild.units:
            print("  Nessuna unità reclutata o stanza costruita.")
            return
        for i, u in enumerate(self.guild.units, start=1):
            print(f"  {i}. {u.name} ({u.unit_type}) x{u.quantity} | Bonus: {u.bonuses}")

    def action_recruit_unit(self):
        clear_console()
        print_header("Recluta/Costruisci nuova Unità")
        print(
            "Puoi reclutare una Squadra o costruire una Stanza, se hai le risorse necessarie."
        )

        options = list(SQUAD_ROOMS_COSTS.keys())
        chosen = choose_from_list(
            "Scegli una Squadra o una Stanza da reclutare/costruire:", options
        )
        if not chosen:
            return

        cost = SQUAD_ROOMS_COSTS[chosen]
        print(f"\nCosti per {chosen}:")
        for res, c in cost.items():
            print(f"  - {res}: {c}")

        # Controllo risorse sufficienti
        for res, c in cost.items():
            if self.bank.resources[res] < c:
                print(f"\nNon hai abbastanza {res} per reclutare/costruire {chosen}.")
                press_enter_to_continue()
                return

        # Sottraiamo i costi
        for res, c in cost.items():
            self.bank.resources[res] -= c

        # Determiniamo se è Squadra o Stanza (semplifichiamo: se esiste nel DB squadre o stanze)
        if chosen in [
            "Agente",
            "Artigiani",
            "Guardia del Corpo",
            "Informatori",
            "Mercenari",
            "Spie",
            "Cavalleria",
            "Criminali",
            "Cultisti",
            "Guaritori",
            "Mendicanti",
            "Marinai",
            "Rapinatori",
            "Sacerdote",
            "Saggio",
            "Soldati",
            "Soldati Scelti",
            "Tagliaborse",
            "Trasgressori",
        ]:
            unit_type = "Squadra"
        else:
            unit_type = "Stanza"

        # Bonus generici di esempio
        bonuses = {}
        if unit_type == "Squadra":
            bonuses["MO"] = 2
            bonuses["Influenza"] = 1
        else:
            bonuses["MO"] = 1

        self.guild.add_unit(chosen, unit_type, bonuses)
        self.bank.add_history_entry(
            f"[UNITÀ] Reclutata/Costruita nuova unità: {chosen} ({unit_type})."
        )

        print(f"Hai reclutato/costruito {chosen} ({unit_type}).")
        press_enter_to_continue()

    def action_increase_unit(self):
        if not self.guild.units:
            print("\nNon hai unità da aumentare.")
            press_enter_to_continue()
            return

        print_header("Aumenta quantità di Unità esistente")
        self.print_units()
        idx = prompt_int(
            "\nSeleziona il numero dell'unità da aumentare: ",
            min_val=1,
            max_val=len(self.guild.units),
        )
        unit = self.guild.units[idx - 1]

        qty = prompt_int("Di quanto aumentare la quantità?: ", min_val=1)
        unit.quantity += qty
        self.bank.add_history_entry(
            f"[UNITÀ] Aumentata quantità di {unit.name} di {qty}. Totale: {unit.quantity}."
        )
        print(f"Quantità di {unit.name} aumentata di {qty}.")
        press_enter_to_continue()

    def action_decrease_unit(self):
        if not self.guild.units:
            print("\nNon hai unità da ridurre.")
            press_enter_to_continue()
            return

        print_header("Riduci quantità di Unità esistente")
        self.print_units()
        idx = prompt_int(
            "\nSeleziona il numero dell'unità da ridurre: ",
            min_val=1,
            max_val=len(self.guild.units),
        )
        unit = self.guild.units[idx - 1]

        max_remove = unit.quantity
        qty = prompt_int(
            f"Di quanto ridurre la quantità? (attuale: {unit.quantity}): ",
            min_val=1,
            max_val=max_remove,
        )
        unit.quantity -= qty
        if unit.quantity <= 0:
            self.bank.add_history_entry(
                f"[UNITÀ] L'unità {unit.name} è stata sciolta/rimossa."
            )
            self.guild.units.remove(unit)
            print(f"L'unità {unit.name} è stata rimossa del tutto.")
        else:
            self.bank.add_history_entry(
                f"[UNITÀ] Ridotta quantità di {unit.name} di {qty}. Totale: {unit.quantity}."
            )
            print(f"Quantità di {unit.name} ridotta di {qty}.")

        press_enter_to_continue()

    # -------------------------------------------------------
    # Giorno di Controllo Esecutivo
    # -------------------------------------------------------

    def run_control_check(self):
        clear_console()
        print_header("Giorno di Controllo Esecutivo")

        print("Scegli la difficoltà del Controllo Esecutivo:")
        diff = choose_from_list(
            "Difficoltà disponibili:", list(CONTROL_DC_TABLE.keys())
        )
        if not diff:
            return

        dc = CONTROL_DC_TABLE[diff]
        print(f"\nDC per il Controllo Esecutivo: {dc}")

        # Scegliamo una statistica di leadership
        print(
            "\nScegli la statistica principale usata per il controllo (es. Autorità):"
        )
        stat = choose_from_list("Statistiche:", list(self.bank.character_stats.keys()))
        if not stat:
            return
        bonus = self.bank.character_stats[stat]

        total, roll = DiceRoller.roll_die(
            20,
            bonus,
            reason=f"Controllo Esecutivo usando {stat}",
        )

        if total >= dc:
            print("Successo nel Controllo Esecutivo!")
            self.bank.add_history_entry(
                f"[CONTROLLO ESECUTIVO] Successo (1d20 + {bonus} = {total} vs DC {dc})."
            )
            # Effetto base: piccolo bonus alle risorse
            self.bank.modify("MO", 10, "Bonus Controllo Esecutivo (successo)")
            self.bank.modify("Influenza", 1, "Bonus Controllo Esecutivo (successo)")
        else:
            print("Fallimento nel Controllo Esecutivo.")
            self.bank.add_history_entry(
                f"[CONTROLLO ESECUTIVO] Fallimento (1d20 + {bonus} = {total} vs DC {dc})."
            )
            # Effetto negativo moderato
            self.bank.modify(
                "Influenza", -1, "Penalità Controllo Esecutivo (fallimento)"
            )

        press_enter_to_continue()

    # -------------------------------------------------------
    # Eventi Casuali
    # -------------------------------------------------------

    def run_random_event(self):
        clear_console()
        print_header("Evento Casuale")

        print(
            "Scegli il tipo di evento da tirare o lascia che il sistema decida basandosi sulla probabilità."
        )
        print("  1. Evento Mercenario (MO / Manodopera / rischi)")
        print("  2. Evento di Influenza")
        print("  3. Evento di Magia")
        print("  4. Evento Generico (lista semplificata)")
        print("  0. Annulla")

        choice = input("\nScelta: ").strip()

        if choice == "0":
            return

        d100_roll = random.randint(1, 100)
        print(f"\nTiro d100 per l'evento: {d100_roll}")

        if choice == "1":
            handle_mercenary_event(d100_roll, self.bank, self.guild)
        elif choice == "2":
            handle_influence_event(d100_roll, self.bank, self.guild)
        elif choice == "3":
            handle_magic_event(d100_roll, self.bank, self.guild)
        elif choice == "4":
            self.run_generic_random_event(d100_roll)
        else:
            print("Scelta non valida.")
            return

        press_enter_to_continue()

    def run_generic_random_event(self, d100_roll):
        # Scegli un evento dalla lista RANDOM_EVENTS in base al tiro
        idx = min(len(RANDOM_EVENTS) - 1, d100_roll // (100 // len(RANDOM_EVENTS)))
        event = RANDOM_EVENTS[idx]

        print(f"\n[EVENTO CASUALE] {event['name']}")
        print(event["description"])
        self.bank.modify(event["resource"], event["amount"], event["name"])
        return event

    # -------------------------------------------------------
    # Modifica Statistiche Personaggio
    # -------------------------------------------------------

    def modify_character_stats(self):
        clear_console()
        print_header("Modifica Statistiche del Personaggio")
        self.print_stats()

        stat = choose_from_list(
            "Scegli la statistica da modificare:",
            list(self.bank.character_stats.keys()),
        )
        if not stat:
            return

        val = prompt_int(
            f"Inserisci il nuovo valore per {stat}: ", min_val=-10, max_val=50
        )
        self.bank.set_character_stat(stat, val)
        print(f"{stat} è ora {val}.")
        press_enter_to_continue()

    # -------------------------------------------------------
    # Registro Eventi e Fine Giorno
    # -------------------------------------------------------

    def show_history(self):
        clear_console()
        print_header("Registro Eventi (ultimi 200)")
        if not self.bank.history:
            print("Nessun evento registrato.")
        else:
            for entry in self.bank.history:
                print(entry)
        press_enter_to_continue()

    def end_day(self):
        self.bank.day_counter += 1
        self.bank.add_history_entry("[FINE GIORNO] Fine del giorno di gestione.")
        print("Giorno concluso.")
        press_enter_to_continue()


# ==========================================
# INTERFACCIA PRINCIPALE
# ==========================================


class GameEngine:
    def __init__(self, save_file=None):
        # Inizializza la banca risorse con il file di salvataggio
        self.bank = ResourceBank(save_file=save_file)
        saved = self.bank.load_state()

        if saved:
            # Rebuild guild from save file
            name = saved.get("guild_name", DEFAULT_GUILD_CONFIG["name"])
            starting_resources = saved.get(
                "resources", DEFAULT_GUILD_CONFIG["starting_resources"]
            )
            units_data = saved.get("guild_units", [])

            # Backward-compat for active_effects:
            # - new format: list[str]
            # - old format: list[dict{name, bonus, days_left}]
            raw_active_effects = saved.get("active_effects", [])
            if raw_active_effects and isinstance(raw_active_effects[0], dict):
                active_effects = [
                    e.get("name")
                    for e in raw_active_effects
                    if isinstance(e, dict) and "name" in e
                ]
            else:
                active_effects = raw_active_effects
            description = DEFAULT_GUILD_CONFIG["description"]
            self.guild = Guild(
                name=name,
                description=description,
                starting_resources=starting_resources,
                starting_units=None,
                active_effects=active_effects,
            )
            self.bank.resources = saved.get(
                "resources", DEFAULT_GUILD_CONFIG["starting_resources"]
            )
            self.bank.character_stats = saved.get(
                "character_stats", self.bank.character_stats
            )
            self.bank.day_counter = saved.get("day_counter", 1)
            self.bank.event_chance = saved.get("event_chance", 20)
            self.bank.history = saved.get("history", [])
            self.bank.guild_control_lost = saved.get("guild_control_lost", False)

            for u_data in units_data:
                self.guild.units.append(Unit.from_dict(u_data))

            self.bank.add_history_entry("[SISTEMA] Salvataggio caricato correttamente.")
        else:
            # Nuova gilda di default
            cfg = DEFAULT_GUILD_CONFIG
            self.guild = Guild(
                name=cfg["name"],
                description=cfg["description"],
                starting_resources=cfg["starting_resources"],
                starting_units=cfg["starting_units"],
            )
            self.bank.resources = cfg["starting_resources"].copy()
            self.bank.add_history_entry("[SISTEMA] Nuova gilda creata.")

    def main_menu(self):
        while True:
            clear_console()
            print_header("Gilda dei Cacciatori di Taglie - Gestione Downtime")
            self.guild.describe()
            print("\n[Stato Gilda]")
            for k, v in self.bank.resources.items():
                print(f"  - {k}: {v}")
            print(f"\nGiorno di gestione attuale: {self.bank.day_counter}")
            print(f"Probabilità base Evento Casuale: {self.bank.event_chance}%")

            print("\nAzioni principali:")
            print("  1. Inizia/Gestisci un Giorno di Downtime")
            print("  2. Forza un Evento Casuale")
            print("  3. Visualizza Registro Eventi")
            print("  4. Salva Manualmente e Continua")
            print("  5. Salva ed Esci")
            print("  0. Esci SENZA salvare")

            choice = input("\nScelta: ").strip()

            if choice == "1":
                day = DowntimeDay(self.bank, self.guild)
                day.run_day()
                # Dopo un giorno, possibilmente far scattare un evento casuale
                self.maybe_trigger_random_event()
            elif choice == "2":
                day = DowntimeDay(self.bank, self.guild)
                day.run_random_event()
            elif choice == "3":
                day = DowntimeDay(self.bank, self.guild)
                day.show_history()
            elif choice == "4":
                self.save()
                print("Salvataggio completato.")
                press_enter_to_continue()
            elif choice == "5":
                self.save()
                print("Salvataggio completato. Uscita...")
                break
            elif choice == "0":
                confirm = (
                    input("Sei sicuro di voler uscire SENZA salvare? (s/n): ")
                    .strip()
                    .lower()
                )
                if confirm == "s":
                    print("Uscita senza salvataggio.")
                    break
            else:
                print("Scelta non valida. Riprova.")
                press_enter_to_continue()

    def save(self):
        self.bank.save_state(self.guild)

    def maybe_trigger_random_event(self):
        """
        Dopo ogni giorno, c'è una certa probabilità che si verifichi un evento casuale,
        basata su self.bank.event_chance.
        """
        chance = self.bank.event_chance
        roll = random.randint(1, 100)
        print(f"\n[CHECK EVENTO CASUALE] Probabilità {chance}%, tiro d100 = {roll}")
        if roll <= chance:
            print("Un evento casuale si verifica!")
            day = DowntimeDay(self.bank, self.guild)
            day.run_random_event()
            # Facoltativo: dopo un evento, ridurre leggermente la probabilità o altro
        else:
            print("Nessun evento casuale oggi.")
        press_enter_to_continue()


def main():
    engine = GameEngine()
    engine.main_menu()


if __name__ == "__main__":
    main()
