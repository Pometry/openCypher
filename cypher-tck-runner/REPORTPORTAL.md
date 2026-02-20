# ReportPortal – Setup & Usage Guide

ReportPortal gives you **trend analysis**, **unique error clustering**, and **failure categorisation** on top of the openCypher TCK test suite. Every `make tck-report` streams results live to your local RP instance.

---

## Prerequisites

| Tool | Version |
|------|---------|
| Docker & Docker Compose | v2+ |
| Python | 3.10+ |
| Node.js | 18+ (for the HTML report) |

## Quick Start (< 5 minutes)

```bash
cd openCypher/cypher-tck-runner

# 1. Start the ReportPortal stack (first boot takes ~60s)
make rp-start

# 2. Install the Python RP agent + local TCK package
make rp-install
pip install -e .

# 3. Open the UI and create the project
make rp-open
```

### First-Time UI Setup

1. **Log in** – `superadmin` / `erebus`
2. **Create project** – Top-left menu → **Administrate** → **Projects** → **Add New Project** → name it exactly **`raphtory_tck`**
3. **Generate API key** – Click your avatar (top-right) → **Profile** → **API Keys** → **Generate Key** → copy it
4. **Paste into config** – Edit `features/behave.ini`:
   ```ini
   [report_portal]
   api_key = <your key here>
   ```

### Run Tests

```bash
make tck-report
```

You should see `[RP] Streaming results to ReportPortal` at the start of the Behave output. Results appear in real-time under **Launches** → **openCypher TCK**.

> **Note:** The local HTML report (`report/index.html`) is still generated every run as a fallback.

---

## Comparing Launches (Diff Between Versions)

After running tests multiple times (e.g. before and after a code change), you can compare launches to see what improved or regressed:

1. Go to **Launches** → select **two launches** using the checkboxes on the right
2. Click **Actions** → **Compare** (top-right)
3. RP shows a side-by-side breakdown of passed/failed/skipped counts per feature

For a test-level diff:
1. Click into a launch → go to a specific test suite (feature)
2. Click the **History** tab on any test item to see how it changed across launches
3. Use the **Filter** bar to show only "To Investigate" items to focus on new failures

---

## Viewing Unique Errors

After a launch finishes, the analyzer automatically clusters failures into unique error groups.

1. Go to **Launches** → click **openCypher TCK #N**
2. Click the **Unique Errors** tab (or append `/uniqueErrors` to the URL)

> **Known UI quirk:** The Analyzer settings may say "Service analyzer is not running" even when it is healthy. Ignore this.

---

## Makefile Targets

| Target | Description |
|--------|-------------|
| `make tck-report` | Run TCK with progress bar, stream to RP, generate HTML report |
| `make tck-report-verbose` | Same but with full scenario-by-scenario output |
| `make tck-report-full` | Rebuild Raphtory from source first, then run TCK |
| `make rp-start` | Start the ReportPortal Docker stack |
| `make rp-stop` | Stop & remove all RP containers |
| `make rp-open` | Open the RP UI in your browser |
| `make rp-install` | `pip install behave-reportportal` |

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'cypher_tck'`
The local TCK package isn't installed. Run:
```bash
pip install -e .    # from cypher-tck-runner/
```

### `[RP] Connected …` message doesn't appear
- Check `features/behave.ini` has a valid `api_key` (not the placeholder)
- Ensure RP is running: `docker compose -f docker-compose.rp.yml -p reportportal ps`
- Verify the project exists: the `project` value in `behave.ini` must match the project name in RP exactly

### Blank page at `http://localhost:8080`
Use `http://localhost:8080/ui/` (trailing slash required).

### "Service analyzer is not running"
This is a UI-only bug. Verify the container is healthy:
```bash
docker compose -f docker-compose.rp.yml -p reportportal ps analyzer
```

---

## Stopping / Cleaning Up

```bash
make rp-stop              # stops containers
# To remove stored data too:
docker volume rm $(docker volume ls -q --filter name=reportportal)
```
