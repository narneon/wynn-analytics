# Wynncraft Analytics Pipeline

A lightweight async analytics pipeline for tracking hourly Wynncraft raid activity.

This project continuously polls Wynncraft APIs, tracks online player activity, computes hourly raid completion deltas per character, classifies archetypes from ability trees, and stores analytics data in BigQuery for later reporting and visualization.

---

# Features

* Async API polling with `aiohttp`
* Multi-key API throughput scaling
* Hourly raid delta tracking
* Character-level raid analytics
* Archetype classification from ability trees
* BigQuery storage backend
* Lightweight SQLite operational state
* Pause/resume support
* Dry-run support for testing
* Long-running single-process architecture

---

# Tech Stack

| Component      | Technology            |
| -------------- | --------------------- |
| Language       | Python                |
| Runtime        | Asyncio               |
| HTTP Client    | aiohttp               |
| Database       | BigQuery              |
| Local State    | SQLite                |
| Hosting Target | Google Compute Engine |
| VM Target      | e2-micro              |

---

# Project Structure

```text
player-tracker/
├── src/
│   ├── api/
│   │   └── wynn_api.py
│   │
│   ├── collectors/
│   │   ├── online_players.py
│   │   ├── raid_tracker.py
│   │   └── archetype_classifier.py
│   │
│   ├── config/
│   │   └── settings.py
│   │
│   ├── database/
│   │   ├── bigquery_client.py
│   │   └── sqlite_store.py
│   │
│   ├── utils/
│   │   └── logging_utils.py
│   │
│   ├── Scripts/
│   │   ├── test_wynn_api.py
│   │   ├── test_online_players.py
│   │   ├── test_raid_tracker.py
│   │   └── test_archetype_api_flow.py
│   │
│   └── main.py
│
├── data/
│   ├── logs/
│   ├── players.db
│   └── PAUSE
│
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

---

# Data Flow

```text
Wynncraft API
    ↓
Online player polling
    ↓
SQLite seen-player tracking
    ↓
Hourly player scans
    ↓
Raid delta computation
    ↓
Ability tree fetch
    ↓
Archetype classification
    ↓
BigQuery inserts
    ↓
Future Discord reporting/charts
```

---

# Database Tables

## hourly_raid_data

Stores character-level hourly raid deltas.

### Columns

| Column       | Description                    |
| ------------ | ------------------------------ |
| player_id    | Player UUID                    |
| character_id | Character UUID                 |
| player_name  | Username                       |
| timestamp    | UTC timestamp                  |
| archetype    | Classified archetype           |
| str          | Strength skill points          |
| dex          | Dexterity skill points         |
| int          | Intelligence skill points      |
| def          | Defence skill points           |
| agi          | Agility skill points           |
| nog_delta    | Nest of the Grootslangs delta  |
| nol_delta    | Orphion's Nexus of Light delta |
| tcc_delta    | The Canyon Colossus delta      |
| tna_delta    | The Nameless Anomaly delta     |
| wtp_delta    | The Wartorn Palace delta       |

### Notes

* Partitioned by `DAY(timestamp)`
* Partition filter required
* Only rows with at least one nonzero raid delta are inserted
* Baseline scans initialize local state without inserting rows
* `archetype` is nullable

---

## online_player_count

Stores periodic online player totals.

### Columns

| Column       | Description          |
| ------------ | -------------------- |
| timestamp    | UTC timestamp        |
| player_count | Total online players |

---

# Local SQLite State

SQLite is used only for operational state.

It stores:

* Seen players during the current hour
* Most recent known raid totals per character

SQLite is NOT the source of truth.
BigQuery is the permanent analytics store.

---

# Environment Variables

Example `.env`:

```env
# Wynn API Keys
WYNN_API_KEYS=key1,key2,key3,key4,key5

# BigQuery
GOOGLE_APPLICATION_CREDENTIALS=../../service-account.json
BQ_PROJECT_ID=your-project-id
BQ_DATASET=your_dataset
BQ_RAID_TABLE=hourly_raid_data
BQ_ONLINE_TABLE=online_player_count

# Runtime
ONLINE_POLL_SECONDS=300
GLOBAL_CONCURRENCY=40
DRY_RUN=true

# Pause file
PAUSE_FILE=data/PAUSE
```

---

# Installation

## 1. Create Virtual Environment

```bash
python -m venv .venv
```

Activate:

### Windows

```bash
.venv\Scripts\activate
```

### Linux/macOS

```bash
source .venv/bin/activate
```

---

## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 3. Configure Environment

Create:

```text
.env
```

Add your API keys and BigQuery configuration.

---

# Running Tests

## Wynn API Parsing

```bash
python -m src.scripts.test_wynn_api
```

## Online Player Collection

```bash
python -m src.scripts.test_online_players
```

## Raid Tracker

```bash
python -m src.scripts.test_raid_tracker
```

## Archetype Flow

```bash
python -m src.scripts.test_archetype_api_flow
```

---

# Running the Scraper

```bash
python -m src.main
```

---

# Pause / Resume

Pause the scraper:

### Linux/macOS

```bash
touch data/PAUSE
```

### Windows PowerShell

```powershell
New-Item data/PAUSE
```

Resume:

### Linux/macOS

```bash
rm data/PAUSE
```

### Windows PowerShell

```powershell
Remove-Item data/PAUSE
```

---

# Dry Run Mode

Set:

```env
DRY_RUN=true
```

This will:

* Run the full pipeline
* Poll APIs
* Compute deltas
* Update SQLite
* Run archetype classification
* Skip BigQuery writes

Useful for long-duration stability testing.

---

# Archetype Classification

Archetypes are inferred from the Wynncraft abilities endpoint.

The classifier:

1. Fetches ability tree data
2. Extracts ability IDs
3. Matches IDs against archetype marker sets
4. Selects the highest-scoring archetype

Unknown or hidden builds return `NULL`.

---

# Operational Notes

* Designed primarily for network I/O workloads
* Intended to run on a single low-resource VM
* Async architecture avoids heavy threading requirements
* BigQuery inserts are batched
* Ability trees are only fetched for characters with nonzero raid deltas

---

# Planned Future Features

* Discord reporting
* Automated chart generation
* Historical analytics dashboards
* Materialized BigQuery views
* Advanced archetype heuristics
* Activity heatmaps
* Per-raid trend analys
