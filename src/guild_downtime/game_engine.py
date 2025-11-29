import difflib
import json
import math
import os
import random
import time
from pathlib import Path

# ============================================================
# Paths (repo-friendly)
# - This file is expected at: src/guild_downtime/game_engine.py
# - Saves are stored in: <repo_root>/data/saves/<guild_slug>.json
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]
SAVE_DIR = BASE_DIR / "data" / "saves"
SAVE_DIR.mkdir(parents=True, exist_ok=True)

# Default save file if none is specified (legacy / single-guild usage)
DEFAULT_SAVE_FILE = SAVE_DIR / "Cacciatori_di_Taglie.json"

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

GAME_DATABASE = {
    # --- SQUADRE ---
    "Accolito": {"MO": 4, "Influenza": 4, "Magia": 4},
    "Apprendista": {"MO": 4, "Influenza": 4, "Magia": 4},
    "Arcieri": {"MO": 6, "Influenza": 6, "Manodopera": 6},
    "Arcieri a Cavallo": {"MO": 8, "Influenza": 8, "Manodopera": 8},
    "Arcieri Scelti": {"MO": 7, "Influenza": 7, "Manodopera": 7},
    "Artigiani": {"MO": 4, "Manodopera": 4, "Merci": 4},
    "Burocrati": {"MO": 4, "Influenza": 4},
    "Cavalleria": {"MO": 7, "Influenza": 7, "Manodopera": 7},
    "Guardie": {"MO": 2, "Influenza": 2, "Manodopera": 2},
    "Guardie Scelte": {"MO": 4, "Influenza": 4, "Manodopera": 4},
    "Guidatori": {"MO": 2, "Manodopera": 2, "Merci": 2},
    "Lacchè": {"Influenza": 2, "Manodopera": 2},
    "Lavoranti": {"MO": 2, "Manodopera": 2},
    "Malioso": {"MO": 7, "Influenza": 7, "Magia": 7},
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
    "Bagno": {"MO": 3, "Influenza": 3},
    "Banchina": {"MO": 12, "Influenza": 12, "Manodopera": 12, "Merci": 12},
    "Bar": {"MO": 10, "Influenza": 10},
    "Biblioteca": {"MO": 8, "Influenza": 8},
    "Biblioteca Magica": {"MO": 12, "Influenza": 12, "Magia": 12},
    "Birrificio": {"MO": 10, "Influenza": 10},
    "Camera da Letto": {"MO": 3, "Influenza": 3},
    "Campo Sportivo": {"MO": 10, "Influenza": 10},
    "Casello": {"MO": 4, "Merci": 4},
    "Cortile": {"MO": 5, "Influenza": 5, "Magia": 5, "Manodopera": 5, "Merci": 5},
    "Cripta": {"MO": 5, "Influenza": 5, "Magia": 5},
    "Cucina": {"MO": 4, "Merci": 4},
    "Deposito": {"MO": 2},
    "Dojo": {"MO": 8, "Influenza": 8, "Manodopera": 8},
    "Dormitori": {"MO": 8, "Manodopera": 8},
    "Falsa Facciata": {"MO": 2, "Merci": 2},
    "Forgia": {"MO": 10, "Merci": 10},
    "Fossa": {"MO": 1, "Manodopera": 1},
    "Giardino": {"MO": 8, "Merci": 8},
    "Guardiola": {"MO": 4, "Merci": 4},
    "Habitat": {"MO": 12, "Influenza": 12},
    "Infermeria": {"MO": 8, "Influenza": 8},
    "Labirinto": {"MO": 5, "Influenza": 5},
    "Laboratorio Alchemico": {"MO": 10, "Magia": 10, "Merci": 10},
    "Laboratorio Artigiano": {"MO": 10, "Influenza": 10, "Merci": 10},
    "Laboratorio di Conceria": {"MO": 10, "Merci": 10},
    "Lavanderia": {"MO": 3, "Merci": 3},
    "Officina Meccanica": {"MO": 10, "Manodopera": 10, "Merci": 10},
    "Postazione di Lavoro": {"MO": 8, "Influenza": 8, "Merci": 8},
    "Posto di Guardia": {"MO": 4, "Merci": 4},
    "Recinto per Animali": {"MO": 8, "Manodopera": 8, "Merci": 8},
    "Reliquiario": {"MO": 5, "Influenza": 5},
    "Sala Cerimoniale": {
        "MO": 10,
        "Influenza": 10,
        "Magia": 10,
        "Manodopera": 10,
        "Merci": 10,
    },
    "Sala Comune": {"MO": 7, "Influenza": 7},
    "Sala da Ballo": {"MO": 10, "Influenza": 10},
    "Sala da Gioco": {"MO": 10},
    "Sala dei Trofei": {"MO": 5, "Influenza": 5},
    "Sala del Trono": {"Influenza": 15},
    "Sala della Mola": {"MO": 8, "Merci": 8},
    "Sala delle Evocazioni": {"Magia": 3},
    "Salotto": {"Influenza": 4},
    "Sauna": {"MO": 3, "Influenza": 3},
    "Scriptorium": {"MO": 5, "Influenza": 5, "Magia": 5, "Manodopera": 5, "Merci": 5},
    "Serra": {"MO": 12, "Influenza": 12, "Merci": 12},
    "Specola": {"MO": 5, "Influenza": 5, "Magia": 5},
    "Stallaggio": {"MO": 8, "Manodopera": 8, "Merci": 8},
    "Stamperia": {"MO": 8, "Influenza": 8, "Manodopera": 8, "Merci": 8},
    "Stanza da Cucito": {"MO": 10, "Influenza": 10, "Merci": 10},
    "Stanza della Cova": {"MO": 5, "Merci": 5},
    "Stanza dello Scrutamento": {"MO": 2, "Influenza": 2},
    "Statua": {"MO": 1, "Influenza": 1},
    "Terreno Agricolo": {"MO": 10, "Merci": 10},
    "Terreno Sepolcrale": {"MO": 4, "Influenza": 4},
    "Trasgressori": {"MO": 2, "Influenza": 2, "Merci": 2},
    "Vetrina": {"MO": 5, "Influenza": 5, "Manodopera": 5, "Merci": 5},
}

DEFAULT_GUILD_CONFIG = {
    "name": "Compagnia Mercenaria del Grifone",
    "rooms": [
        {"name": "Armeria", "type": "Stanza", "bonuses": {"Manodopera": 2}, "qty": 1},
        {"name": "Camerata", "type": "Stanza", "bonuses": {"Manodopera": 2}, "qty": 1},
    ],
    "teams": [
        {
            "name": "Arcieri Scelti",
            "type": "Squadra",
            "bonuses": {"MO": 7, "Influenza": 7, "Manodopera": 7},
            "qty": 1,
        },
        {
            "name": "Soldati Scelti",
            "type": "Squadra",
            "bonuses": {"MO": 6, "Influenza": 6, "Manodopera": 6},
            "qty": 1,
        },
        {
            "name": "Sacerdote",
            "type": "Squadra",
            "bonuses": {"MO": 7, "Magia": 7, "Influenza": 7},
            "qty": 1,
        },
    ],
}

# ==========================================
# SUPPORT CLASSES
# ==========================================


class DiceRoller:
    @staticmethod
    def roll_die(sides, bonus=0, reason="Tiro generico", silent=False):
        roll = random.randint(1, sides)
        total = roll + bonus
        sign = "+" if bonus >= 0 else ""
        log_str = f"d{sides}: [{roll}] {sign}{bonus} = {total}"

        if not silent:
            if "generico" not in reason:
                print(f"\n🎲 {reason}")
            print(f"   > {log_str}")
            time.sleep(0.1)

        return total, roll, log_str

    @staticmethod
    def skill_check(
        skill_options, dc, bank_ref, silent=False, extra_bonus=0, return_log_only=False
    ):
        if isinstance(skill_options, str):
            skill_options = [skill_options]

        best_skill = skill_options[0]
        best_mod = -99

        if not silent and not return_log_only:
            print(f"\n⚠️  RICHIESTA PROVA: {', '.join(skill_options)} (CD {dc})")

        for skill in skill_options:
            key = skill
            val = bank_ref.character_stats.get(key, 0)
            if val > best_mod:
                best_mod = val
                best_skill = key

        final_mod = best_mod + extra_bonus
        mod_str = f"+{final_mod}" if final_mod >= 0 else f"{final_mod}"

        if not silent and not return_log_only:
            extra_txt = f" (Bonus Extra +{extra_bonus})" if extra_bonus else ""
            print(f"   💡 Skill: {best_skill} ({mod_str}){extra_txt}")

        roll = random.randint(1, 20)
        total = roll + final_mod

        is_success = False
        result_desc = "FALLITO"

        if roll == 20:
            is_success = True
            result_desc = "CRITICO (Nat 20)"
        elif total >= dc:
            is_success = True
            result_desc = "SUPERATO"
        else:
            is_success = False
            result_desc = "FALLITO"

        log_check_str = (
            f"{best_skill} d20[{roll}]{mod_str} = {total} vs CD {dc} ({result_desc})"
        )

        if not silent and not return_log_only:
            icon = "🌟" if roll == 20 else ("✅" if is_success else "❌")
            print(f"   {icon} {result_desc}!")

        if return_log_only:
            return is_success, log_check_str
        else:
            bank_ref.add_log(f"CHECK: {log_check_str}")
            return is_success


class DowntimeUnit:
    def __init__(self, name, unit_type, bonuses, qty=1):
        self.name = name
        self.unit_type = unit_type
        self.bonuses = bonuses
        self.qty = qty

    def get_bonus_for_resource(self, resource_type):
        base = self.bonuses.get(resource_type, 0)
        return base * self.qty

    def to_dict(self):
        return {
            "name": self.name,
            "type": self.unit_type,
            "bonuses": self.bonuses,
            "qty": self.qty,
        }


class Guild:
    def __init__(self, name):
        self.name = name
        self.units = []
        self.active_effects = []

    def add_unit(self, unit):
        for existing in self.units:
            if existing.name == unit.name:
                existing.qty += 1
                print(
                    f"Unità {unit.name} esistente trovata. Quantità aumentata a {existing.qty}."
                )
                return
        self.units.append(unit)

    def add_effect(self, name, bonus_val, duration_days):
        self.active_effects.append(
            {"name": name, "bonus": bonus_val, "days_left": duration_days}
        )

    def process_daily_effects(self):
        active = []
        expired = []
        for eff in self.active_effects:
            eff["days_left"] -= 1
            if eff["days_left"] > 0:
                active.append(eff)
            else:
                expired.append(eff["name"])
        self.active_effects = active
        return expired

    def calculate_total_bonus(self, resource_type):
        total = 0
        details = []
        for unit in self.units:
            b = unit.get_bonus_for_resource(resource_type)
            if b > 0:
                total += b
                details.append(f"{unit.name} (x{unit.qty}): +{b}")
        for eff in self.active_effects:
            total += eff["bonus"]
            details.append(f"EFFETTO [{eff['name']}]: +{eff['bonus']}")
        return total, details


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

        # Individual save file for this bank / guild
        self.save_file = Path(save_file) if save_file is not None else DEFAULT_SAVE_FILE

    def modify(self, resource, amount, reason=""):
        """
        Gestisce l'aggiunta/rimozione di risorse e applica i Costi di Conseguimento (GP).
        Restituisce (amount_effettivo, costo_gp).
        """
        cost_gp = 0.0
        actual_amount = amount

        # Se stiamo GUADAGNANDO capitale (non MO), c'è un costo in MO
        if amount > 0 and resource in EARN_COSTS and resource != "MO":
            unit_cost = EARN_COSTS[resource]
            total_cost = amount * unit_cost

            # Controllo Fondi
            if self.resources["MO"] >= total_cost:
                self.resources["MO"] = round(self.resources["MO"] - total_cost, 2)
                cost_gp = total_cost
            else:
                affordable_amount = int(self.resources["MO"] // unit_cost)
                actual_cost = affordable_amount * unit_cost
                self.resources["MO"] = round(self.resources["MO"] - actual_cost, 2)

                actual_amount = affordable_amount
                cost_gp = actual_cost

        # Applica modifica
        if resource == "MO":
            new_val = self.resources[resource] + actual_amount
            self.resources[resource] = round(max(0.0, new_val), 2)
        else:
            new_val = self.resources[resource] + actual_amount
            self.resources[resource] = int(max(0, new_val))

        return actual_amount, cost_gp

    def add_log(self, text):
        prefix = f"Giorno {self.day_counter}:"
        self.history.append(f"{prefix} {text}")
        if len(self.history) > 200:
            self.history.pop(0)

    def save_state(self, guild: Guild):
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


def handle_mercenary_event(d100, engine, silent=False):
    bank = engine.bank
    guild = engine.guild

    if not silent:
        print(f"\n🚨 EVENTO SCATTATO! (Tiro d100: {d100})")

    name_evt = "Sconosciuto"
    check_str = "-"
    result_str = "Nessun effetto"

    # 01-15 Risultati impressionanti
    if 1 <= d100 <= 15:
        name_evt = "Risultati Impressionanti"
        if not silent:
            print(f"📜 {name_evt}")
        inf, _, _ = DiceRoller.roll_die(4, 0, silent=True)
        man, _, _ = DiceRoller.roll_die(2, 0, silent=True)
        days, _, _ = DiceRoller.roll_die(6, 0, silent=True)

        bank.resources["Influenza"] += inf
        bank.resources["Manodopera"] += man

        guild.add_effect("Risultati Impressionanti (+10)", 10, days)
        check_str = "-"
        result_str = f"+{inf} Inf, +{man} Man, Buff +10 ({days}gg)"

    # 16-25 Guadagno inaspettato
    elif 16 <= d100 <= 25:
        name_evt = "Guadagno Inaspettato"
        if not silent:
            print(f"📜 {name_evt}")
        d10, _, _ = DiceRoller.roll_die(10, 0, silent=True)
        mo = d10 * 10
        merci, _, _ = DiceRoller.roll_die(6, 0, silent=True)

        bank.resources["MO"] += mo
        bank.resources["Magia"] += 1
        bank.resources["Merci"] += merci

        check_str = "-"
        result_str = f"+{mo} MO, +1 Magia, +{merci} Merci"

    # 26-50 Rissa
    elif 26 <= d100 <= 50:
        name_evt = "Rissa"
        if not silent:
            print(f"📜 {name_evt}")
        success, log_chk = DiceRoller.skill_check(
            ["Intimidire", "Professione (soldato)"],
            20,
            bank,
            silent,
            return_log_only=True,
        )
        check_str = log_chk
        if success:
            result_str = "Sedata. Nessuna perdita."
        else:
            li, _, _ = DiceRoller.roll_die(4, 0, silent=True)
            lm, _, _ = DiceRoller.roll_die(2, 0, silent=True)
            bank.modify("Influenza", -li)
            bank.modify("Manodopera", -lm)
            result_str = f"FALLITO. Persi {li} Inf, {lm} Man."

    # 51-70 Rivalità
    elif 51 <= d100 <= 70:
        name_evt = "Rivalità"
        if not silent:
            print(f"📜 {name_evt}")
        d_dur, _, str_d = DiceRoller.roll_die(10, 0, silent=True)
        guild.add_effect("Rivalità (-5)", -5, d_dur)
        d_ch, _, str_ch = DiceRoller.roll_die(100, 0, silent=True)
        extra_res = ""
        if d_ch > 50:
            loss, _, str_loss = DiceRoller.roll_die(4, 0, silent=True)
            bank.modify("Influenza", -loss)
            extra_res = f" | Danno Extra: -{loss} Inf (d100[{d_ch}]>50, d4[{loss}])"
        else:
            extra_res = f" | Nessun danno extra (d100[{d_ch}]<=50)"
        check_str = f"Durata ({str_d.split(':')[1].strip()}), Chance ({str_ch.split(':')[1].strip()}){extra_res}"
        result_str = f"Penalità -5 per {d_dur}gg"

    # 71-80 Scandalo
    elif 71 <= d100 <= 80:
        name_evt = "Scandalo"
        if not silent:
            print(f"📜 {name_evt}")
        d1, _, _ = DiceRoller.roll_die(4, 0, silent=True)
        d2, _, _ = DiceRoller.roll_die(4, 0, silent=True)
        days = d1 + d2
        guild.add_effect("Scandalo (-5)", -5, days)
        li, _, _ = DiceRoller.roll_die(2, 0, silent=True)
        bank.modify("Influenza", -li)
        check_str = f"Durata 2d4[{d1}+{d2}]={days}"
        result_str = f"Penalità -5 ({days}gg). Persi {li} Inf."

    # 81-85 Duello
    elif 81 <= d100 <= 85:
        name_evt = "Duello"
        if not silent:
            print(f"📜 {name_evt}")
        success, log_chk = DiceRoller.skill_check(
            "Professione (soldato)", 25, bank, silent, return_log_only=True
        )
        check_str = log_chk
        if success:
            guild.add_effect("Vittoria Duello (+2)", 2, 7)
            result_str = "VITTORIA. Buff +2 (7gg)."
        else:
            lm, _, _ = DiceRoller.roll_die(2, 0, silent=True)
            bank.modify("Manodopera", -lm)
            result_str = f"SCONFITTA. Persi {lm} Man."

    # 86-95 Scisma
    elif 86 <= d100 <= 95:
        name_evt = "Scisma"
        if not silent:
            print(f"📜 {name_evt}")
        success, log_chk = DiceRoller.skill_check(
            ["Diplomazia", "Intimidire", "Professione (soldato)"],
            20,
            bank,
            silent,
            return_log_only=True,
        )
        check_str = log_chk
        if success:
            bank.modify("Manodopera", -1)
            result_str = "EVITATO. -1 Man (Epurazione)."
        else:
            li, _, _ = DiceRoller.roll_die(2, 0, silent=True)
            lm, _, _ = DiceRoller.roll_die(2, 0, silent=True)
            bank.modify("Manodopera", -lm)
            bank.modify("Influenza", -li)
            result_str = f"AVVENUTO. Persi {li} Inf, {lm} Man."

    # 96-100 Ammutinamento
    elif 96 <= d100 <= 100:
        name_evt = "Ammutinamento"
        if not silent:
            print(f"📜 {name_evt}")

        bonus_inf = 0
        used_inf_str = ""
        if bank.resources["Influenza"] >= 5:
            bank.modify("Influenza", -5)
            bonus_inf = 5
            used_inf_str = " (Spesi 5 Inf -> Bonus +5)"
            if not silent:
                print("   💎 Spesi 5 Influenza per bonus +5.")

        success, log_chk = DiceRoller.skill_check(
            ["Combattimento", "Intimidire", "Professione (soldato)"],
            25,
            bank,
            silent,
            extra_bonus=bonus_inf,
            return_log_only=True,
        )
        check_str = f"{log_chk}{used_inf_str}"

        if success:
            bank.modify("Manodopera", -1)
            result_str = "SEDATO. -1 Man."
        else:
            bank.guild_control_lost = True
            result_str = "CATASTROFE: Controllo Perso."
            if not silent:
                print("\n   💀 HAI PERSO IL CONTROLLO DELLA GILDA!")

    bank.add_log(f"EVENTO ({d100} -> {name_evt})")
    bank.add_log(f"CHECK: {check_str}")
    bank.add_log(f"RISULTATO: {result_str}")


# ==========================================
# GAME ENGINE
# ==========================================


class GameEngine:
    def __init__(self, save_file=None, guild_name=None):
        """
        save_file: path of the JSON used for this guild.
        guild_name: name to use when creating a new guild (ignored if a save exists).
        """
        self.bank = ResourceBank(save_file=save_file)
        saved = self.bank.load_state()

        if saved:
            # Load existing guild
            name = saved.get("guild_name", DEFAULT_GUILD_CONFIG["name"])
            self.guild = Guild(name)
            self.bank.resources = saved["resources"]
            self.bank.character_stats = saved.get(
                "character_stats", self.bank.character_stats
            )
            self.bank.day_counter = saved["day_counter"]
            self.bank.event_chance = saved["event_chance"]
            self.bank.history = saved["history"]
            self.bank.guild_control_lost = saved.get("guild_control_lost", False)
            self.guild.active_effects = saved.get("active_effects", [])

            # Merge stats (add new default keys if missing)
            saved_stats = saved.get("character_stats", {})
            for k, v in self.bank.character_stats.items():
                if k not in saved_stats:
                    saved_stats[k] = v
            self.bank.character_stats = saved_stats

            for u in saved["guild_units"]:
                qty = u.get("qty", 1)
                self.guild.add_unit(
                    DowntimeUnit(u["name"], u["type"], u["bonuses"], qty)
                )
        else:
            # Create new guild from default config
            name = guild_name or DEFAULT_GUILD_CONFIG["name"]
            self.guild = Guild(name)
            for t in DEFAULT_GUILD_CONFIG["teams"]:
                qty = t.get("qty", 1)
                self.guild.add_unit(
                    DowntimeUnit(t["name"], t["type"], t["bonuses"], qty)
                )
            for r in DEFAULT_GUILD_CONFIG["rooms"]:
                qty = r.get("qty", 1)
                self.guild.add_unit(
                    DowntimeUnit(r["name"], r["type"], r["bonuses"], qty)
                )

        self.days_absent = 0

    def clear(self):
        os.system("cls" if os.name == "nt" else "clear")

    def header(self):
        self.clear()
        status = "🔴 CONTROLLO PERSO" if self.bank.guild_control_lost else "🟢 ATTIVA"
        print(
            f"=== GIORNO {self.bank.day_counter} | {self.guild.name} | STATO: {status} ==="
        )
        res = self.bank.resources
        res_line = (
            f"💰 MO: {res['MO']:.2f} | 🗣️ Inf: {res['Influenza']} | ✨ Mag: {res['Magia']} | "
            f"🔨 Man: {res['Manodopera']} | 📦 Mer: {res['Merci']}"
        )
        print(res_line)
        s = self.bank.character_stats
        stats_line = (
            f"👤 [STATS] Dipl: +{s.get('Diplomazia', 0)} | Ragg: +{s.get('Raggirare', 0)} | "
            f"Prof(Sold): +{s.get('Professione (soldato)', 0)} | Intim: +{s.get('Intimidire', 0)} | Aut: +{s.get('Autorità', 0)}"
        )
        print(stats_line)
        teams = [
            f"{u.name} x{u.qty}" for u in self.guild.units if u.unit_type == "Squadra"
        ]
        rooms = [
            f"{u.name} x{u.qty}" for u in self.guild.units if u.unit_type != "Squadra"
        ]
        print(f"\n⚔️  SQUADRE: {', '.join(teams) if teams else 'Nessuna'}")
        print(f"🏰 STANZE:  {', '.join(rooms) if rooms else 'Nessuna'}")
        if self.guild.active_effects:
            print("\n✨ EFFETTI ATTIVI:")
            for eff in self.guild.active_effects:
                print(f"   * {eff['name']}: {eff['days_left']} giorni rimasti")
        print("=" * 60)

    def ask_location(self):
        print("\n🌍 SEI NELLA CITTÀ DELLA GILDA OGGI? (s/n)")
        if input("> ").lower() == "s":
            self.days_absent = 0
        else:
            try:
                self.days_absent = int(input("Da quanti giorni sei via? "))
                if self.days_absent < 0:
                    self.days_absent = 0
            except:
                self.days_absent = 0

    def attempt_regain_control(self, silent=False):
        dc = max(0, self.days_absent - 10)
        bonus = self.bank.character_stats.get("Autorità", 4)

        if not silent:
            print("\n🔒 TENTATIVO DI RIPRENDERE IL CONTROLLO")
            print(f"   Tiro: d20 + Autorità ({bonus}) vs CD {dc}")

        total, natural, _ = DiceRoller.roll_die(20, bonus, "Tiro Controllo", silent)
        success = total >= dc
        result_str = "SUCCESSO" if success else "FALLIMENTO"

        self.bank.add_log(
            f"CHECK: TIRO CONTROLLO {total} (d20[{natural}]+{bonus}) vs CD {dc} -> {result_str}"
        )

        if success:
            self.bank.guild_control_lost = False
            self.bank.event_chance = 20
            if not silent:
                print("   🎉 CONTROLLO RIPRESO! La gilda torna operativa.")
        else:
            if not silent:
                print("   🔒 FALLITO. La gilda resta bloccata.")

        return success

    def process_event(self, silent=False):
        if self.bank.guild_control_lost:
            return False
        roll, _, _ = DiceRoller.roll_die(100, 0, "Check Probabilità Evento", silent)
        threshold = self.bank.event_chance
        if not silent:
            print(f"   (Soglia attuale: {threshold}%)")

        if roll <= threshold:
            self.bank.event_chance = 20
            ev_roll, _, _ = DiceRoller.roll_die(100, 0, "Tabella Mercenari", silent)
            handle_mercenary_event(ev_roll, self, silent)
            return True
        else:
            self.bank.event_chance = min(95, self.bank.event_chance + 5)
            if not silent:
                print("   ✅ Nessun evento.")
            return False

    def run_simulation(self):
        self.header()
        print("\n--- SIMULAZIONE MULTI-GIORNO ---")
        try:
            days = int(input("Quanti giorni vuoi simulare? "))
            if days <= 0:
                return
        except:
            return

        start_res = self.bank.resources.copy()

        is_leaving = False
        if self.days_absent == 0:
            print(f"\nPartirai lasciando la città durante questi {days} giorni? (s/n)")
            if input("> ").lower() == "s":
                is_leaving = True
                print(
                    "   [INFO] I giorni di assenza verranno contati a partire da oggi."
                )
        else:
            print(
                f"\n   [INFO] Sei già via da {self.days_absent} giorni. Il conteggio continuerà."
            )

        print("\nStrategia:")
        print("[U] Uniforme (MO -> Mer -> Inf...)")
        print("[F] Focalizzata (Una risorsa)")
        strat = input("> ").lower()

        target_res = None
        res_cycle = ["MO", "Merci", "Influenza", "Magia", "Manodopera"]

        if strat == "f":
            for i, r in enumerate(res_cycle, 1):
                print(f"[{i}] {r}")
            try:
                target_res = res_cycle[int(input("> ")) - 1]
            except:
                return

        print("\nMetodo Dadi:")
        print("[1] Prendi 10")
        print("[2] Tira d20")
        sim_mode = input("> ")

        print(f"\nAvvio simulazione {days} giorni...")
        self.bank.add_log(f"--- INIZIO SIMULAZIONE {days} GIORNI ---")

        events_happened = 0
        total_spent_gp = 0

        for _ in range(days):
            if self.days_absent > 0 or is_leaving:
                self.days_absent += 1

            if self.bank.guild_control_lost:
                if self.attempt_regain_control(silent=True):
                    self.bank.day_counter += 1
                    continue
                else:
                    self.bank.day_counter += 1
                    continue

            if self.process_event(silent=True):
                events_happened += 1
                if self.bank.guild_control_lost:
                    self.bank.day_counter += 1
                    continue

            self.guild.process_daily_effects()

            if strat == "u":
                daily_res = res_cycle[self.bank.day_counter % 5]
            else:
                daily_res = target_res

            bonus, _ = self.guild.calculate_total_bonus(daily_res)

            if bonus == 0:
                roll = 10
            else:
                roll = random.randint(1, 20) if sim_mode == "2" else 10

            total_roll = roll + bonus
            earned = math.floor(total_roll / 10)
            if daily_res == "MO":
                earned = total_roll / 10

            actual_earned, cost_gp = self.bank.modify(daily_res, earned)
            total_spent_gp += cost_gp

            if actual_earned > 0:
                cost_str = f" (Costo {cost_gp} mo)" if cost_gp > 0 else ""
                self.bank.add_log(f"ATTIVITÀ: {daily_res} +{actual_earned}{cost_str}")
            elif earned > 0 and actual_earned == 0:
                self.bank.add_log(
                    f"ATTIVITÀ: {daily_res} FALLITA (Fondi Insufficienti)"
                )

            self.bank.day_counter += 1

        net_gains = {k: v - start_res[k] for k, v in self.bank.resources.items()}

        self.bank.add_log(
            f"--- FINE SIMULAZIONE (Netto: {net_gains}, Spese: {total_spent_gp}) ---"
        )
        self.bank.save_state(self.guild)

        print("\n--- FINE SIMULAZIONE ---")
        print(f"Eventi accaduti: {events_happened}")
        print(f"SPESE OPERATIVE (Costi conseguimento): {total_spent_gp} mo")
        print("\nBILANCIO NETTO (Finale - Iniziale):")
        for k, v in net_gains.items():
            fmt = f"{v:.2f}" if k == "MO" else f"{v}"
            print(f"  - {k}: {fmt}")

        if self.bank.guild_control_lost:
            print(
                "\n⚠️ ATTENZIONE: La simulazione è terminata con la Gilda fuori controllo!"
            )
        input("\nPremi INVIO...")

    def generate_capital_single(self):
        if self.bank.guild_control_lost:
            print("\n⛔ CONTROLLO PERSO! Azione bloccata.")
            if input("Tenti di riprendere il controllo? (s/n) ") == "s":
                self.attempt_regain_control()
                self.bank.day_counter += 1
                self.bank.save_state(self.guild)
            return

        print("\n--- ATTIVITÀ GIORNALIERA ---")
        opts = ["MO", "Merci", "Influenza", "Magia", "Manodopera"]
        for i, r in enumerate(opts, 1):
            tot, _ = self.guild.calculate_total_bonus(r)
            print(f"[{i}] {r} (+{tot})")

        try:
            idx = int(input("\nScelta (1-5): ")) - 1
            res_type = opts[idx]
        except:
            return

        bonus, details = self.guild.calculate_total_bonus(res_type)

        print(f"\n📊 CALCOLO: +{bonus}")
        for d in details:
            print(f"   + {d}")

        print("\n[INVIO] Prendi 10 | [T] Tira dado")
        choice = input("> ").lower()

        if choice == "t":
            total, roll, _ = DiceRoller.roll_die(20, bonus, f"Generazione {res_type}")
            log_chk = f"d20[{roll}]+{bonus}"
        else:
            total = 10 + bonus
            log_chk = f"Take10+{bonus}"
            print(f"\n🔢 CALCOLO: 10 + {bonus} = {total}")

        earned = math.floor(total / 10)
        if res_type == "MO":
            earned = total / 10

        actual_earned, cost_gp = self.bank.modify(res_type, earned)

        cost_log = f" (Costo {cost_gp} mo)" if cost_gp > 0 else ""
        if earned > actual_earned:
            print(
                f"⚠️ Fondi insufficienti per tutto il guadagno. Ottenuto solo {actual_earned}."
            )
            cost_log += " [CAP FONDI]"

        self.bank.add_log(f"ATTIVITÀ ({res_type})")
        self.bank.add_log(f"CHECK: {log_chk} = {total}")
        self.bank.add_log(f"RISULTATO: +{actual_earned} {res_type}{cost_log}")

        print(f"\n🎉 RISULTATO: +{actual_earned} {res_type}")
        if cost_gp > 0:
            print(f"💸 SPESI: {cost_gp} mo")

        self.bank.day_counter += 1
        self.bank.save_state(self.guild)
        input("\n[INVIO] per chiudere giorno...")

    def add_unit_smart(self):
        self.header()
        print("\n--- AGGIUNGI UNITÀ ---")
        query = input("Nome unità: ").strip()
        matches = difflib.get_close_matches(
            query, list(GAME_DATABASE.keys()), n=1, cutoff=0.6
        )

        if matches:
            found = matches[0]
            data = GAME_DATABASE[found]
            print(f"✅ Trovato: {found} | Bonus: {data}")
            u_type = (
                "Squadra"
                if any(
                    x in found for x in ["Soldati", "Arcieri", "Sacerdote", "Lacchè"]
                )
                else "Stanza"
            )
            try:
                qty = int(input("Quantità (1): ") or 1)
            except:
                qty = 1
            self.guild.add_unit(DowntimeUnit(found, u_type, data, qty))
            self.bank.save_state(self.guild)
            print("Salvato.")
        else:
            print("❌ Non trovato.")
        input("...")

    def edit_units_menu(self):
        self.header()
        print("\n--- MODIFICA UNITÀ ---")
        for i, u in enumerate(self.guild.units, 1):
            print(f"[{i}] {u.name} (x{u.qty})")
        try:
            idx = int(input("\nScegli (0 esci): ")) - 1
            if idx < 0:
                return
            u = self.guild.units[idx]
            nq = int(input(f"Nuova quantità per {u.name}: "))
            if nq <= 0:
                self.guild.units.pop(idx)
            else:
                u.qty = nq
            self.bank.save_state(self.guild)
        except:
            pass

    def edit_stats_menu(self):
        self.header()
        print("\n--- MODIFICA STATISTICHE ---")
        keys = list(self.bank.character_stats.keys())
        for i, k in enumerate(keys, 1):
            print(f"[{i}] {k}: {self.bank.character_stats[k]}")
        try:
            idx = int(input("Scegli: ")) - 1
            k = keys[idx]
            self.bank.character_stats[k] = int(input(f"Nuovo valore per {k}: "))
            self.bank.save_state(self.guild)
        except:
            pass

    def manual_mod(self):
        res = input("\nRisorsa: ")
        if res in self.bank.resources:
            try:
                qty = float(input("Quantità: "))
                self.bank.modify(res, qty)
                motivo = input("Motivo: ")
                self.bank.add_log(
                    f"MANUALE: {res} {'+' if qty > 0 else ''}{qty} ({motivo})"
                )
                self.bank.save_state(self.guild)
            except:
                pass

    def menu(self):
        while True:
            self.header()
            print("\n1. ☀️  GIORNO SINGOLO")
            print("2. ⏩ SIMULAZIONE")
            print("3. ➕ Aggiungi Unità")
            print("4. 🔢 Modifica Quantità")
            print("5. 👤 Modifica Statistiche")
            print("6. ✏️  Gestione Risorse")
            print("7. 📜 Storico")
            print("8. 🚪 Esci")

            c = input("\nScelta: ")
            if c == "1":
                self.ask_location()

                if self.bank.guild_control_lost:
                    print("\n⛔ ATTENZIONE: La gilda è fuori controllo!")
                    if input("Tenti il controllo? (s/n) ") == "s":
                        self.attempt_regain_control()
                        self.bank.day_counter += 1
                        self.bank.save_state(self.guild)
                else:
                    self.process_event()
                    self.guild.process_daily_effects()
                    if not self.bank.guild_control_lost:
                        self.generate_capital_single()
                    else:
                        self.bank.day_counter += 1
                        self.bank.save_state(self.guild)
                        input("Giorno perso per Ammutinamento...")

            elif c == "2":
                self.run_simulation()
            elif c == "3":
                self.add_unit_smart()
            elif c == "4":
                self.edit_units_menu()
            elif c == "5":
                self.edit_stats_menu()
            elif c == "6":
                self.manual_mod()
            elif c == "7":
                print("\n".join(self.bank.history[-30:]))
                input("...")
            elif c == "8":
                break


if __name__ == "__main__":
    app = GameEngine()
    app.menu()
