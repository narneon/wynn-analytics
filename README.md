# Wynn Analytics

A large-scale Wynncraft raid analytics pipeline focused on tracking raid participation, archetype trends, skill point distributions, and long-term gameplay patterns.

The project continuously polls Wynncraft player data, computes hourly raid deltas, stores historical raid activity in BigQuery, and generates automated visual daily and weekly reports delivered directly to Discord. Historical data can also be queried to generate dashboards for arbitrary reporting periods.

---

# Features

## Hourly Raid Tracking

The tracker continuously:

* Polls online player data from the Wynncraft API
* Detects raid completion deltas
* Tracks per-character raid activity
* Preserves historical raid progression over time

---

## Archetype Analytics

The pipeline records:

* Archetype usage
* Unique player counts
* Completion totals
* Average skill point distributions
* Completion-adjusted participation

---

## Ultimate Usage Tracking

Daily analysis also tracks archetype ultimate usage rates by:

* Fetching ability trees
* Detecting equipped ultimates
* Aggregating per-archetype ultimate adoption

Players with hidden character data are automatically excluded from ultimate lookups.

---

## Automated Reports

The system automatically generates both daily and weekly raid analytics reports.

Daily reports:

* Aggregate the previous day's raid activity
* Calculate current ultimate usage through Wynncraft ability-tree data
* Store historical digest rows in BigQuery
* Generate five raid-specific dashboard images
* Upload the dashboards directly to Discord

Weekly reports:

* Aggregate raid activity across the weekly reporting window
* Calculate completions, player counts, and skill point averages from historical hourly data
* Calculate historical ultimate usage from stored daily digest data
* Generate five weekly raid dashboards
* Upload the dashboards directly to Discord

Historical dashboards can also be generated for arbitrary multi-day reporting periods without making additional Wynncraft API requests.

The dashboard includes:

* Class participation pie charts
* Archetype completion comparisons
* Skill point radar charts
* Ultimate usage panels
* Historical trend visualizations

## Example Daily Dashboard

![Daily Dashboard](docs/sample_digest.png)

Artwork assets created by @.dwagonic
---

# Architecture

```text
Wynncraft API
    ↓
Online Player Polling
    ↓
Hourly Raid Delta Tracking
    ↓
SQLite State Cache
    ↓
BigQuery Historical Storage
    ├───────────────┐
    ↓               ↓
Daily Digest    Historical Aggregation
    ↓               ↓
Ultimate API    Stored Daily Ultimate Data
Checks              ↓
    └───────┬───────┘
            ↓
    Pillow Dashboard Rendering
            ↓
      Discord Reporting
```

---

# Tech Stack

## Backend

* Python
* asyncio
* aiohttp

## Storage

* BigQuery
* SQLite

## Reporting

* Pillow
* Discord Webhooks

## Infrastructure

* Google Cloud VM
* systemd

---

# Data Stored

## Hourly Raid Data

The system stores:

* Player ID
* Character ID
* Archetype
* Skill points
* Timestamp
* Per-raid completion deltas

## Daily Digest Data

Daily summaries include:

* Raid
* Archetype
* Unique players
* Total completions
* Average skill points
* Ultimate usage counts

---

# Discord Reporting

The project supports:

* Automatic daily report posting
* Existing forum-thread integration
* Multi-image dashboard uploads
* Scheduled digest generation

---

# Configuration

Example environment variables:

```env
GCP_PROJECT_ID=
BQ_DATASET=
BQ_RAID_TABLE=hourly_raid_data
BQ_ONLINE_TABLE=online_player_count
BQ_DAILY_TABLE=daily_raid_data

WYNN_API_KEYS=
DISCORD_WEBHOOK_URL=

DAILY_DIGEST_HOUR_UTC=17
DAILY_DIGEST_MINUTE_UTC=30

WEEKLY_DIGEST_WEEKDAY=4
WEEKLY_DIGEST_HOUR_UTC=18
WEEKLY_DIGEST_MINUTE_UTC=30

REPORT_OUTPUT_DIR=data/reports```
```

---

# Running Locally

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Run Main Scraper

```bash
python -m src.main
```

## Run Reporting Tests

Daily digest:

```bash
python -m src.scripts.daily_digest_test
```

Weekly digest:

```bash
python -m src.scripts.weekly_digest_test
```

Arbitrary period digest:
```bash
python -m src.scripts.period_digest_test
```

## Generate a Historical Period Report

```bash
python -m src.scripts.period_digest --start 2026-09-01 --end 2026-09-07 --label "Weekly"
```

---

# Deployment

Production runs on a Google Cloud VM using systemd.

Deployment is managed through the `wynn-analytics` command.

## Deploy Latest Version

```bash
wynn-analytics deploy
```

The deployment process:

1. Pauses the scraper
2. Fetches the latest `origin/main`
3. Resets tracked repository files to `origin/main`
4. Activates the Python virtual environment
5. Installs or updates dependencies
6. Restarts the systemd service
7. Resumes the scraper

Production deployments treat `origin/main` as authoritative. Any tracked local changes on the VM are discarded during deployment.

## Service Management

Check the service status:

```bash
wynn-analytics status
```

View live logs:

```bash
wynn-analytics logs
```

Pause data collection:

```bash
wynn-analytics pause
```

Resume data collection:

```bash
wynn-analytics unpause
```

Restart the service:

```bash
wynn-analytics restart
```

---

# Current Focus

Current development priorities include:

* Individual Ability tree node tracking

---
