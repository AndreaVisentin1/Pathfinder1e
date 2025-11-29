# Pathfinder 1e – Downtime Guild Manager

A small terminal-based tool to manage **Pathfinder 1e Ultimate Campaign / Downtime** for a guild-like organization.

It is currently focused on a **mercenary / bounty-hunter style guild**, but the code is structured so you can extend it to other guild types by changing configuration and data.

The program handles day-by-day activities, random mercenary events, resource generation, and long-term simulations.

---

## Features

### Core gameplay

- **Single-day activity**
  - Choose which resource the guild focuses on for the day:
    - `MO` (gold pieces)
    - `Goods` (`Merci`)
    - `Influence` (`Influenza`)
    - `Magic` (`Magia`)
    - `Labor` (`Manodopera`)
  - Automatically applies bonuses from:
    - **Teams** (e.g. Soldiers, Archers, Priests)
    - **Rooms** (e.g. Armory, Dormitory)
    - **Active effects** (temporary buffs/debuffs)

- **Multi-day simulation**
  - Run an automated simulation over a number of days.
  - Choose strategy:
    - **Uniform** rotation of resources.
    - **Focused** on a single resource.
  - Choose dice mode:
    - **Take 10**
    - **Roll d20**
  - The engine:
    - Resolves random events.
    - Applies daily effects and resource generation.
    - Tracks total gains and operational costs.

- **Random mercenary events**
  - Event chance increases daily, then resets after an event.
  - Examples:
    - Brawls
    - Rivalries
    - Scandals
    - Duels
    - Schisms
    - Mutinies
  - Events can:
    - Add/remove resources.
    - Apply temporary positive/negative effects to the guild.
    - Potentially cause you to **lose control** of the guild.

### Guild & resources

- Track the guild’s:
  - **Name**
  - **Teams** (`Squadra`) and **Rooms** (`Stanza`) with quantities and bonuses.
  - **Resources**:
    - MO (gold)
    - Goods (`Merci`)
    - Influence (`Influenza`)
    - Magic (`Magia`)
    - Labor (`Manodopera`)
  - **Character stats** (Diplomacy, Bluff, Profession (soldier), Intimidate, Combat, Authority).
  - **Active effects** with duration and bonus/malus.

- **Events and activities are logged** with a day counter and can be reviewed in the in-game history.

### Control system

- Some events (e.g. mutiny) can cause the guild to **lose control**.
- While control is lost:
  - Many actions are blocked.
  - You must attempt to regain control with a roll based on **Authority** and days absent.

---

## Project structure

Expected repository layout:

```text
Pathfinder1e/
├─ src/
│  └─ guild_downtime/
│     └─ game_engine.py
├─ scripts/
│  └─ run_bounty_guild.py
└─ data/
   └─ saves/
      ├─ Cacciatori_di_Taglie.json      (example save file)
      └─ <other_guilds>.json
