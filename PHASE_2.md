# PHASE_2.md — Scaling & Advanced Features Plan

> **DriftGuard | Post-Hackathon Roadmap**
> This is what DriftGuard becomes after the MVP ships. Follow Phase 1 first — everything here assumes the MVP is working.

---

## Philosophy

Phase 2 is not about adding features for their own sake. Every item here solves a specific gap that the MVP leaves open:

| MVP Gap | Phase 2 Fix |
|---|---|
| Analyzes only on demand | Scheduled automated runs |
| No historical comparison | Trend tracking over time |
| Limited to local repos | GitHub/GitLab integration |
| Bob called per-file (slow, expensive) | Batched + cached analysis |
| Single-user CLI | Team dashboard with notifications |
| JSON report only | PDF export, Slack/email alerts |
| No context memory | Bob remembers repo baseline |

Build these in order of **user value**, not complexity. Start with notifications (P1), then trend tracking (P2), then team features (P3).

---

## Feature Roadmap

### Priority 1 — Make It Sticky (Build These First)

---

### Feature 1: Decay Trend Tracking

**The Gap:** The MVP gives you a snapshot. You can't see if a file's health is getting better or worse over time. Without trends, the score is just a number — it has no story.

**What You Build:**

A SQLite database (`driftguard.db`) that persists every report run. A new `/api/trends` endpoint that returns historical scores per file. A trend chart on the dashboard (line chart per file over time).

**Key Logic:**
- On every run, save results to DB alongside a `run_id` and timestamp
- `GET /api/trends?file=app/auth/login.py` returns all historical scores for that file
- Dashboard shows a sparkline next to each file row: red if declining, green if improving

**Bob Prompt (Architecture + DB Schema):**
```
I am adding trend tracking to DriftGuard. Currently every run saves a JSON file.
I want to also persist results to SQLite using Python's built-in sqlite3 module.

Design a schema for these tables:
1. runs — one row per analysis run
2. file_scores — one row per file per run, with all 4 dimension scores and health_score

Then write:
1. db.py — initialize_db(), save_run(report: dict), get_file_trends(file_path: str) -> list[dict]
2. A migration-safe initialize_db() that uses CREATE TABLE IF NOT EXISTS
3. get_file_trends() should return rows sorted by run date ascending, for use in a Chart.js line chart
```

**Bob Prompt (Trend Chart UI):**
```
I have a DriftGuard dashboard in HTML + Chart.js. I want to add a trend modal.

When a user clicks a file row in the table, fetch /api/trends?file=<path> and show a Chart.js line chart
in a modal overlay. X axis = run dates. Y axis = health_score (0-100).
The line should be colored red if the last 3 points are declining, green if improving.

Write the JavaScript to: attach click handlers to table rows, fetch the API, render the modal with Chart.js.
Keep it as vanilla JS with no frameworks.
```

**Estimated Effort:** 1.5 days solo

---

### Feature 2: Slack / Email Alerts

**The Gap:** Developers don't check dashboards. If DriftGuard detects a critical file but nobody looks at the dashboard, nothing happens.

**What You Build:**

A `notifier.py` module with two backends: Slack webhook and SMTP email. After every scheduled run (see Feature 3), if any file has crossed into CRITICAL or worsened by more than 10 points since last run, send an alert.

**Alert content:**
- Which file crossed the threshold
- Its current score vs. last run
- Bob's top_risk summary for that file
- Link to the dashboard

**Bob Prompt:**
```
Write a Python module called notifier.py for DriftGuard.

It needs two alert backends:

1. SlackNotifier(webhook_url: str)
   - send_decay_alert(file_path, current_score, previous_score, top_risk, dashboard_url)
   - Uses requests.post to send a Slack Block Kit message
   - Block Kit structure: header "🔴 DriftGuard Alert", fields for file/scores/risk, button linking to dashboard

2. EmailNotifier(smtp_host, smtp_port, sender, password, recipients: list[str])
   - send_decay_alert(same signature)
   - Uses smtplib + email.mime for HTML email
   - Simple HTML template: red header, table of details

3. AlertManager(notifiers: list)
   - check_and_alert(current_report: dict, previous_report: dict)
   - Compares file scores between current and previous report
   - Triggers alert for any file that: entered CRITICAL status, OR score dropped > 10 points

Use python-dotenv to load SLACK_WEBHOOK_URL, SMTP credentials from .env
```

**Estimated Effort:** 1 day solo

---

### Feature 3: Scheduled Automated Runs

**The Gap:** The MVP requires you to manually run the CLI. A tool that needs to be manually triggered rarely gets used consistently.

**What You Build:**

A `scheduler.py` module using Python's `schedule` library. A new CLI command: `python driftguard.py --watch --interval 24h` that starts a background scheduler running analysis every N hours and firing alerts.

Also: a `Dockerfile` + `docker-compose.yml` so the watcher can run persistently as a container.

**Bob Prompt:**
```
Add a scheduled watch mode to DriftGuard's CLI.

When called with --watch --interval 24h (or 12h, 6h), the CLI should:
1. Run the full analysis immediately on start
2. Schedule subsequent runs every N hours using the `schedule` library
3. After each run, call AlertManager.check_and_alert() comparing to the previous run
4. Log each run to a rotating log file: logs/driftguard.log (use Python's logging module)
5. Trap SIGINT for graceful shutdown: "Stopping DriftGuard watcher..."

Also write a Dockerfile that:
- Uses python:3.11-slim
- Installs requirements
- Sets WORKDIR /app
- Mounts /repo as the target repository volume
- Sets CMD to run the watcher with configurable env vars (REPO_PATH, WATCH_INTERVAL, DAYS)

And a docker-compose.yml with:
- Service: driftguard-watcher
- Volume: maps ./demo-repo to /repo
- Env file: .env
- Restart: unless-stopped
```

**Estimated Effort:** 1 day solo

---

### Priority 2 — Make It Credible (Build These Second)

---

### Feature 4: GitHub / GitLab Remote Repo Support

**The Gap:** The MVP only works on repos you've already cloned locally. Most users want to point it at a GitHub URL.

**What You Build:**

Accept `--repo https://github.com/user/repo` as input. If the URL is a GitHub/GitLab URL, clone it to a temp directory, run analysis, then clean up. For GitHub specifically, use the GitHub API to fetch commit data instead of cloning the full repo (faster, no SSH setup needed).

**Bob Prompt:**
```
Extend DriftGuard's git_parser.py to support remote GitHub repositories.

Add a function: resolve_repo(repo_input: str) -> str
- If repo_input is a local path, return it as-is
- If repo_input is a GitHub URL (https://github.com/user/repo), use the GitHub REST API:
  - GET /repos/{owner}/{repo}/commits?since={since_date}&per_page=100
  - GET /repos/{owner}/{repo}/compare/{base}...{head} for diffs
  - Returns the same structured data as get_file_diffs()
  - Uses GITHUB_TOKEN from environment if present (for rate limits)
- If repo_input is any other https:// git URL, clone it to a temp dir using GitPython, run analysis, then delete the temp dir

Handle: private repos (401 error message), rate limiting (retry with backoff), repos with no commits in window (return empty list with informative message).
```

**Estimated Effort:** 1.5 days solo

---

### Feature 5: Bob Context Memory (Baseline Profiles)

**The Gap:** Every time Bob analyzes a file, it has no memory of what was "normal" for that codebase. A 50-line function might be normal in one project and a red flag in another. Bob is making judgments without baseline context.

**What You Build:**

A `baseline_profile.py` module that runs once on a repo and generates a "codebase personality" profile: average function length, docstring coverage percentage, test file ratio, naming convention (snake_case vs camelCase). This profile is injected into every Bob analysis prompt as context.

**Bob Prompt:**
```
Write a Python module called baseline_profile.py for DriftGuard.

On first run against a repo, it performs a static analysis snapshot:
- Scans all .py files using Python's ast module
- Calculates: average function length (lines), docstring coverage % (functions with docstrings / total functions), test file ratio (test_*.py files / total .py files), dominant naming convention (snake_case vs camelCase based on function name sample)
- Saves to .driftguard/baseline.json in the repo root

Then modify bob_analyzer.py to load this profile and prepend it to every analysis prompt:
"This codebase has these baseline characteristics: average function length {N} lines, {X}% docstring coverage, {Y}% test file ratio, {convention} naming convention. Use these as the baseline when scoring decay — deviation from this baseline is what matters."

This makes Bob's scores relative to the project's own standards, not generic best practices.
```

**Estimated Effort:** 1 day solo

---

### Feature 6: Multi-Language Support

**The Gap:** The MVP targets Python only. Most real repos are polyglot.

**What You Build:**

Extend `git_parser.py` to support `.js`, `.ts`, `.java`, `.go`, `.rb` files. Adjust the Bob analysis prompt based on language — the decay signals differ. For JavaScript, naming consistency matters more (camelCase vs snake_case mix). For Java, class size and method count matter more than function line count.

**Bob Prompt (Language-Specific Prompt Templates):**
```
I am building DriftGuard — a codebase decay analyzer. Currently I have one Bob analysis prompt for Python.

Write language-specific decay analysis prompt templates for:
1. JavaScript / TypeScript
2. Java
3. Go

For each, adjust the scoring rubric to reflect what "decay" means in that language's ecosystem:
- JS/TS: focus on callback hell growth, missing TypeScript type annotations, inconsistent async/await vs Promise patterns
- Java: focus on class responsibility growth (God Class smell), missing Javadoc, test class pairing drift
- Go: focus on error handling patterns, exported vs unexported naming drift, interface compliance drift

Return as a Python dict: LANGUAGE_PROMPTS = {"python": "...", "javascript": "...", "java": "...", "go": "..."}
Each value is a prompt template string with {file_path}, {diff_text}, {total_commits} placeholders.
```

**Estimated Effort:** 1 day solo

---

### Priority 3 — Make It a Product (Build These Third)

---

### Feature 7: Team Dashboard with Authentication

**The Gap:** The MVP dashboard is single-user, local-only. Teams need a shared view.

**What You Build:**

Add simple token-based authentication to the FastAPI app (no OAuth — just a static API key in `.env`). Add a "team view" that shows aggregate decay scores across multiple repos in one dashboard. Add user-configurable threshold alerts: "alert me when any file drops below 50."

**Bob Prompt:**
```
Add simple API key authentication to DriftGuard's FastAPI app.

Requirements:
1. Read DRIFTGUARD_API_KEY from environment (via python-dotenv)
2. Add a dependency: verify_api_key(key: str = Header(None)) that checks the header X-DriftGuard-Key
3. Apply this dependency to all /api/* routes but NOT to GET / (the dashboard should be publicly viewable)
4. Add a settings page route GET /settings that shows current config (masked API key, repo path, watch interval)
5. Add a multi-repo endpoint GET /api/repos that returns a summary across all configured repos (read from a repos.json config file)

Also write the multi-repo config schema (repos.json):
[{"name": "my-api", "path": "/repos/my-api", "days": 30}, ...]
```

**Estimated Effort:** 1.5 days solo

---

### Feature 8: PDF / Markdown Report Export

**The Gap:** Developers want to share decay reports with managers or in sprint retrospectives. A dashboard URL doesn't work in a Confluence page or a PDF status report.

**What You Build:**

A `report_exporter.py` module with two backends: Markdown (using the `report.json` data to generate a structured `.md` file) and PDF (using `weasyprint` or `pdfkit` to render the dashboard HTML to PDF). A new CLI flag: `--export pdf` or `--export markdown`.

**Bob Prompt:**
```
Write report_exporter.py for DriftGuard.

Two export functions:

1. export_markdown(report: dict, output_path: str)
   Generates a structured Markdown report with:
   - H1: "DriftGuard Report — {repo} — {date}"
   - Summary table (total files, counts by status, average score)
   - Per-file sections for CRITICAL and AT_RISK files only (skip WATCH/HEALTHY to keep it short)
   - Each file section: score badge, dimension breakdown table, Bob's decay_summary, recommendation

2. export_pdf(report: dict, output_path: str)
   Uses pdfkit + a minimal HTML template to generate a PDF
   - Include the Chart.js bar chart rendered as a static SVG (use Chart.js server-side via node or approximate it with SVG rectangles)
   - Keep styling minimal: black and white with colored status badges

Add --export flag to driftguard.py CLI: choices=["json", "markdown", "pdf", "all"], default="json"
```

**Estimated Effort:** 1 day solo

---

### Feature 9: VS Code Extension Integration

**The Gap:** Running DriftGuard from the CLI breaks developer flow. The insights should appear inline where the developer is working — in their editor.

**What You Build:**

A minimal VS Code extension (you have CommitAI experience with this — directly applicable) that reads the `output/report_*.json` file from the workspace and shows inline decay warnings via VS Code's diagnostic API. Red squiggles on files with CRITICAL status in the file explorer. A sidebar panel showing the health score chart.

**Bob Prompt:**
```
I have experience building VS Code extensions. I want to add a DriftGuard VS Code extension that reads the output/report_*.json from the current workspace and shows decay warnings.

Write the core extension logic in TypeScript:

1. On activation, scan workspace for the most recent report JSON in output/
2. For each file with status CRITICAL or AT_RISK, create a VS Code DiagnosticCollection entry:
   - Severity: CRITICAL → vscode.DiagnosticSeverity.Error, AT_RISK → Warning
   - Message: "DriftGuard: Health {score}/100 — {top_risk}"
   - Range: entire file (line 0, char 0 to line 0, char 0)
3. Register a command "driftguard.refresh" that re-reads the report and updates diagnostics
4. Show a status bar item: "🔍 DriftGuard: {N} issues" that opens the output panel on click
5. Watch the output/ directory for new report files and auto-refresh

Use vscode.workspace.fs for file operations. The extension should activate on workspaceContains:.git
```

**Estimated Effort:** 2 days solo (you already know the pattern from CommitAI)

---

### Feature 10: Bob-Generated Remediation Tasks

**The Gap:** DriftGuard tells you what's wrong. It doesn't help you fix it. The next logical step is auto-generating the remediation work — docstring drafts, test stubs, suggested refactors — directly from Bob.

**What You Build:**

A `--remediate` CLI flag. When a file is flagged as CRITICAL, Bob generates: a draft docstring for every undocumented function, a test stub for every function without test coverage, and a refactoring suggestion for the most complex function. Output is saved as `remediation/{file_name}_remediation.md`.

**Bob Prompt:**
```
Write a remediation generator for DriftGuard.

Function: generate_remediation(file_data: dict, analysis: dict) -> str

It calls Bob Shell to generate remediation artifacts for a CRITICAL file:

Prompt to send Bob:
"A file called {file_path} has been flagged by DriftGuard as CRITICAL with a health score of {score}/100.

The main decay issues are: {decay_summary}

Here is the current state of the file:
{file_content}

Please generate:
1. DOCSTRING FIXES: For every function/class missing a docstring, write the docstring to add
2. TEST STUBS: For every function that has no corresponding test, write a pytest test stub (function signature + TODO body)
3. REFACTOR SUGGESTION: For the most complex function (highest nesting/length), suggest a specific refactoring approach

Format your response as a Markdown document with three sections: ## Docstring Fixes, ## Test Stubs, ## Refactor Suggestion"

Save the returned Markdown to remediation/{filename}_remediation.md
Add --remediate flag to CLI that runs this for all CRITICAL files after scoring.
```

**Estimated Effort:** 1 day solo

---

## Technical Debt to Address in Phase 2

These are shortcuts taken in Phase 1 that need to be properly fixed:

| Shortcut | Phase 1 Reality | Phase 2 Fix |
|---|---|---|
| No caching | Bob is called every time, even for unchanged files | Cache Bob responses keyed by `(file_path, diff_hash)` in SQLite |
| JSON file storage | Reports stored as flat JSON files | Migrate to SQLite with proper schema |
| No rate limiting | Bob Shell can be called too fast | Add token bucket rate limiter |
| No auth | Dashboard is completely open | API key auth (Feature 7) |
| Single-threaded analysis | Files analyzed one by one | `concurrent.futures.ThreadPoolExecutor` for parallel Bob calls |
| No input validation | Bad repo path crashes with unhelpful error | Proper input validation and user-friendly errors |
| Hardcoded file extensions | Only .py, .js, .ts, .java | Config file for per-project extension lists |

---

## Architecture Evolution

### Phase 1 Architecture (MVP)
```
CLI → git_parser → bob_analyzer → scorer → JSON file → FastAPI → Dashboard
```

### Phase 2 Architecture (Scaled)
```
                          ┌─────────────────┐
                          │   Scheduler      │
                          └────────┬────────┘
                                   │
CLI / GitHub Webhook → git_parser ──┤
                                   │
                          ┌────────▼────────┐
                          │  Cache Layer     │  ← SQLite
                          └────────┬────────┘
                                   │
                          ┌────────▼────────┐
                          │  Bob Analyzer   │  ← Parallel calls + baseline context
                          └────────┬────────┘
                                   │
                          ┌────────▼────────┐
                          │  Scorer +        │
                          │  Trend Tracker  │  ← SQLite persistence
                          └────────┬────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                     │
     ┌────────▼────────┐  ┌───────▼────────┐  ┌───────▼────────┐
     │  FastAPI         │  │  Notifier      │  │  Exporters     │
     │  Dashboard       │  │  Slack/Email   │  │  PDF/Markdown  │
     └─────────────────┘  └────────────────┘  └────────────────┘
              │
     ┌────────▼────────┐
     │  VS Code Ext.   │
     └─────────────────┘
```

---

## Suggested Build Order for Phase 2

If you're coming back to this after the hackathon, here's the sequence that maximizes user value per hour spent:

1. **Trend Tracking** (Feature 1) — makes the tool worth using repeatedly
2. **Slack Alerts** (Feature 2) — makes it passive/automatic
3. **Scheduled Runs** (Feature 3) — removes the need to remember to run it
4. **GitHub Remote Support** (Feature 4) — opens it to teams who don't clone locally
5. **VS Code Extension** (Feature 9) — you already know how from CommitAI; highest visibility
6. **Bob Context Memory / Baseline** (Feature 5) — makes scores dramatically more accurate
7. **Remediation Generation** (Feature 10) — completes the detect → fix loop
8. **Multi-language** (Feature 6) — broadens the audience
9. **PDF Export** (Feature 8) — polish for team use
10. **Team Auth Dashboard** (Feature 7) — last because it's infrastructure, not user value

---

## Open Source Strategy

If you want to release DriftGuard publicly post-hackathon:

**Name it properly:** `driftguard` on PyPI. Make it installable via `pip install driftguard` with a `driftguard` CLI command.

**Position it clearly:**
> "DriftGuard is what SonarQube would be if it understood *time* — not just what your code is, but how fast it's decaying."

**The README hook (one sentence):** "DriftGuard tells you which files are lying to you."

**Contribution-ready structure to add:**
- `CONTRIBUTING.md`
- `CHANGELOG.md`
- GitHub Actions CI: lint + test on every PR
- Issue templates for bug reports and feature requests
- A `driftguard/` package structure (not just a flat directory)

**Bob Prompt for open source prep:**
```
I want to turn DriftGuard into a pip-installable open source Python package.

Help me:
1. Restructure the directory into a proper Python package: driftguard/ with __init__.py, __main__.py, and all modules
2. Write a pyproject.toml using modern Python packaging (PEP 621) with all dependencies
3. Write a GitHub Actions workflow .github/workflows/ci.yml that runs: black formatting check, flake8 lint, pytest on push to main and all PRs
4. Write a CONTRIBUTING.md explaining how to set up dev environment, run tests, submit PRs
```

---

*Phase 2 is the real product. Phase 1 is the proof. Ship Phase 1 first.*
