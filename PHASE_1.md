# PHASE_1.md — 48-Hour MVP Build Plan

> **DriftGuard | IBM Bob Dev Day Hackathon 2026**
> Solo build. Every step has a Bob prompt. Follow in order. Don't skip.

---

## 🎯 MVP Definition — "What Does Done Look Like?"

You are done with the MVP when:
1. `python driftguard.py --repo . --days 30` runs without error on any local Git repo
2. It produces a JSON report with health scores per file
3. `uvicorn app.main:app` serves a dashboard at `localhost:8000` showing the scores
4. You have ≥ 4 exported Bob sessions in `bob_sessions/`
5. You can demo the full flow (CLI → JSON → Dashboard) in under 3 minutes

Everything beyond this is Phase 2. Don't chase Phase 2 in 48 hours.

---

## 💰 Bobcoin Budget (40 coins total)

| Step | Estimated Cost | Notes |
|---|---|---|
| Step 1: Planning + /init | 3–4 coins | Do once, export immediately |
| Step 2: Git parser code gen | 3–4 coins | One focused Code mode task |
| Step 3: Bob Shell integration | 4–5 coins | Your most complex step |
| Step 4: Prompt engineering | 3–4 coins | Ask mode — cheap |
| Step 5: Scorer code gen | 2–3 coins | Straightforward logic |
| Step 6: CLI code gen | 2–3 coins | Quick Code mode task |
| Step 7: FastAPI backend | 3–4 coins | Code mode |
| Step 8: Dashboard | 2–3 coins | Code mode, HTML/JS |
| Demo runs (×3) | 6–8 coins | Save these |
| Buffer | 5 coins | Debugging help |
| **Total** | **~37–43 coins** | Tight but doable |

**⚠️ Bobcoin Rules:**
- Never ask Bob something you can Google in 2 minutes
- Always save Bob's output before closing a task — regenerating wastes coins
- Export every task session immediately. Do not wait until submission day.
- Use Ask mode (cheapest) for questions, Code mode for generation, Plan mode once at the start

---

## ⚠️ Top 5 Common Mistakes to Avoid

1. **Trying to run Bob Shell inside Docker** — run it on your host machine, not in a container
2. **Sending entire files to Bob** — Bob has context limits. Send diffs only (< 200 lines per call)
3. **Not saving Bob session exports** — do it after EVERY step. Not at the end.
4. **Over-engineering the scorer** — a simple weighted average is enough for the demo. Don't build ML.
5. **Analyzing too many files per run** — limit to files changed in the last N days. 10–20 files max for demo.

---

## Hour 0–1: Environment + Account Setup

**Goal:** Have Bob IDE running, linked to your hackathon team, repo created, `bob_sessions/` ready.

### ✅ Tasks
- [ ] Check email for IBM hackathon invite → accept → create IBMid
- [ ] Download and install Bob IDE from `bob.ibm.com`
- [ ] Sign in to Bob IDE → Settings → switch team to `ibm-coding-challenge-xxx`
- [ ] Confirm Bobcoins show 40 in Settings
- [ ] Create public GitHub repo: `driftguard`
- [ ] Clone locally: `git clone https://github.com/yourusername/driftguard`
- [ ] Create folder structure: `mkdir -p app/templates bob_sessions sample_reports`
- [ ] Create empty `requirements.txt`, `driftguard.py`, `app/__init__.py`
- [ ] Initial commit and push

### ⏱ Time: 45–60 min

---

## Step 1: Project Planning with Bob

**Goal:** Use Bob's Plan mode to architect the project, generate AGENTS.md, and get a build checklist. This is your first Bob session — make it count.

**Technical Explanation:** Bob's `/init` command generates an `AGENTS.md` file that gives Bob persistent context about your project across all future sessions. Running it first makes every subsequent Bob interaction smarter and cheaper.

### ✅ Tasks
- [ ] Open Bob IDE → select your `driftguard` folder as workspace
- [ ] Switch to **Plan mode**
- [ ] Run the planning prompt below
- [ ] After output: switch to your terminal, run `/init` in Bob Shell
- [ ] Save `AGENTS.md` to repo root
- [ ] **Export this session immediately** → `bob_sessions/session_01_planning_export.md` + screenshot

### ⏱ Time: 30–45 min

### 🤖 IBM Bob Prompt (Plan Mode)

```
I am building DriftGuard — a developer tool that detects codebase decay by analyzing Git commit history over time.

Here is the architecture:
1. A Python CLI (driftguard.py) accepts --repo path and --days N as arguments
2. A git_parser.py module uses GitPython to extract commits from the last N days and get per-file diffs
3. A bob_analyzer.py module calls Bob Shell in non-interactive mode (subprocess) with each file's diff and receives a structured decay analysis
4. A scorer.py module calculates a Health Score (0-100) per file across 4 dimensions: documentation drift, test drift, complexity growth, naming consistency
5. A report_generator.py builds a JSON report from the scored results
6. A FastAPI app (app/main.py) serves the JSON report as a visual dashboard using HTML + Chart.js

Please:
1. Validate this architecture — identify any issues or missing pieces
2. Define the exact data flow (what object each module passes to the next)
3. Define the schema for the intermediate data objects (commit data, diff data, bob_analysis result, scored_file, final_report)
4. Identify the 3 highest-risk implementation challenges for a solo developer in 48 hours
5. Suggest the build order for the 8 modules above
```

### 📤 Expected Output
- Validated architecture with data flow
- 4–5 data schemas (Python TypedDict or dict structure)
- Risk list with mitigation strategies
- Ordered build checklist

---

## Step 2: Git Commit Parsing

**Goal:** Build `git_parser.py` — extract recent commits, get modified files, generate diffs.

**Technical Explanation:** GitPython gives you a Python API over git. You'll use `repo.iter_commits()` with a since filter, then for each commit get the diff against its parent. The output is a list of `{file_path, diff_text, commit_hash, commit_date, author}` objects.

### ✅ Tasks
- [ ] `pip install gitpython` → add to `requirements.txt`
- [ ] Create `app/git_parser.py`
- [ ] Use Bob prompt below to generate the core parsing logic
- [ ] Test it manually: `python -c "from app.git_parser import get_file_diffs; print(get_file_diffs('.', 7))"`
- [ ] Verify output structure matches what you need for Bob analysis
- [ ] Handle edge cases: empty repos, files with binary diffs, initial commits
- [ ] **Export Bob session** → `bob_sessions/session_02_git_parser_export.md`

### ⏱ Time: 1.5–2 hours

### 🤖 IBM Bob Prompt (Code Mode)

```
Write a Python module called git_parser.py using GitPython for DriftGuard.

It needs one main function: get_file_diffs(repo_path: str, days: int) -> list[dict]

Each returned dict should have this structure:
{
  "file_path": str,           # relative path like "app/auth/login.py"
  "language": str,            # inferred from extension: "python", "javascript", etc.
  "total_commits": int,       # how many times this file was changed in the window
  "diff_text": str,           # concatenated unified diff of all changes (max 150 lines — truncate if longer)
  "last_modified": str,       # ISO timestamp of most recent commit touching this file
  "commit_hashes": list[str]  # list of commit hashes that touched this file
}

Requirements:
- Filter to only .py, .js, .ts, .java files (skip images, lockfiles, etc.)
- If diff_text exceeds 150 lines, include first 75 and last 75 lines with a "... [truncated] ..." marker
- Skip binary files gracefully
- Handle the case where a file has only one commit (no parent diff available)
- Return an empty list (not an error) if no files were modified in the window

Also write a simple test function test_git_parser() that runs on the current directory and prints the first result.
```

### 📤 Expected Output
- Complete `git_parser.py` with `get_file_diffs()` function
- Edge case handling (binary files, single commits, empty results)
- A test function you can run immediately

---

## Step 3: IBM Bob Shell Integration

**Goal:** Build `bob_analyzer.py` — call Bob Shell in non-interactive mode, parse the structured response.

**Technical Explanation:** Bob Shell supports non-interactive mode: `bob -p "your prompt here"`. You call this via Python's `subprocess.run()`, capture stdout, and parse Bob's response. The challenge is (a) crafting a prompt that reliably returns structured JSON and (b) handling Bob's response format, which includes context text around the actual answer.

This is your **most critical module** and the most important Bob session for your submission.

### ✅ Tasks
- [ ] Verify Bob Shell is installed: `bob --version` in terminal
- [ ] Test a manual non-interactive call: `bob -p "Say hello in JSON format: {message: 'hello'}"` — confirm it works
- [ ] Create `app/bob_analyzer.py`
- [ ] Use Bob prompt below to generate the integration logic
- [ ] Test with one real diff from your git_parser output
- [ ] Confirm the JSON parsing is robust (Bob sometimes adds explanation text around JSON)
- [ ] Add a fallback: if Bob's response can't be parsed as JSON, return a default "analysis unavailable" object rather than crashing
- [ ] **Export Bob session** → `bob_sessions/session_03_bob_analyzer_export.md`

### ⏱ Time: 2–3 hours (this is the hardest step)

### 🤖 IBM Bob Prompt (Code Mode)

```
Write a Python module called bob_analyzer.py for DriftGuard.

It calls IBM Bob Shell in non-interactive mode to analyze code diffs for signs of decay.

Main function: analyze_file_decay(file_data: dict) -> dict
- file_data is the dict structure from git_parser.py (has file_path, diff_text, total_commits, language)
- Calls Bob Shell via subprocess: bob -p "<constructed prompt>"
- Parses Bob's response and returns a structured decay analysis

The function should:
1. Build a decay analysis prompt (see template below)
2. Run: result = subprocess.run(['bob', '-p', prompt], capture_output=True, text=True, timeout=60)
3. Parse result.stdout to extract JSON (Bob may wrap JSON in explanation text — use regex or json.loads with error handling to find and extract the JSON block)
4. Return the parsed analysis dict, or a default dict if parsing fails

The decay analysis prompt template to use:
"""
You are analyzing a code diff for signs of technical decay. Analyze the following diff and return ONLY a JSON object with this exact structure — no explanation, no markdown, just the raw JSON:

{
  "documentation_drift_score": <integer 0-100, where 0=severe drift, 100=no drift>,
  "test_drift_score": <integer 0-100>,
  "complexity_growth_score": <integer 0-100, where 0=severe complexity increase, 100=no growth>,
  "naming_consistency_score": <integer 0-100>,
  "decay_summary": "<2-3 sentence plain English explanation of the main decay signals>",
  "top_risk": "<single most concerning decay pattern observed>",
  "recommendation": "<one specific action to address the highest risk>"
}

Scoring guide:
- documentation_drift: Did logic change without docstring/comment updates? 0=massive undocumented changes, 100=all changes documented
- test_drift: Were tests updated when implementation changed? 0=implementation changed, no tests touched, 100=tests updated or added
- complexity_growth: Did functions grow longer, add nesting, or gain parameters? 0=severe complexity increase, 100=complexity unchanged or reduced
- naming_consistency: Are new identifiers consistent with the existing naming conventions? 0=many inconsistencies, 100=perfectly consistent

File: {file_path}
Language: {language}
Commits in window: {total_commits}
Diff:
{diff_text}
"""

Also write: batch_analyze(file_diffs: list[dict]) -> list[dict]
- Calls analyze_file_decay for each file
- Adds a 2-second sleep between calls to avoid rate issues
- Prints progress: "Analyzing file N/M: <filename>"
- Returns list of analysis results, each merged with the original file_data dict
```

### 📤 Expected Output
- `bob_analyzer.py` with `analyze_file_decay()` and `batch_analyze()` functions
- Robust JSON extraction from Bob's response
- Graceful fallback for failed analyses
- Progress indicator for batch mode

---

## Step 4: Prompt Engineering Refinement

**Goal:** Test and refine your Bob analysis prompt to get reliable, well-structured JSON output.

**Technical Explanation:** LLM prompts need iteration. Your first prompt will work ~70% of the time. This step is about finding the failure modes (Bob adds markdown, Bob returns explanation text, scores are outside 0-100 range) and hardening your prompt and parser against them.

### ✅ Tasks
- [ ] Run `analyze_file_decay()` on 5 different real diffs from your repo
- [ ] Inspect raw Bob output for each — identify any parsing failures
- [ ] Switch to Bob **Ask mode** → use prompt below to get prompt improvement suggestions
- [ ] Update your prompt in `bob_analyzer.py` based on Bob's feedback
- [ ] Re-test on the same 5 diffs — all should now parse cleanly
- [ ] **Export this Ask mode session** → `bob_sessions/session_04_prompt_engineering_export.md`

### ⏱ Time: 1–1.5 hours

### 🤖 IBM Bob Prompt (Ask Mode)

```
I am calling you via Bob Shell in non-interactive mode from a Python subprocess. My goal is to get you to return a JSON object reliably every time, without wrapping text or markdown code blocks.

Here is my current prompt template (the part sent to you):

[paste your current analyze_file_decay prompt here]

I've observed these failure modes:
1. Sometimes you wrap the JSON in ```json ... ``` markdown blocks
2. Sometimes you add a sentence of explanation before or after the JSON
3. Occasionally score values are strings instead of integers

Please suggest:
1. Prompt changes that maximize the likelihood you return raw JSON only
2. A Python regex pattern I can use to reliably extract the JSON object from your response even if it's wrapped in text
3. A validation function that checks the returned dict has all required keys and correct types, and fills in defaults if not
```

### 📤 Expected Output
- Improved prompt wording
- Regex pattern for JSON extraction
- Validation/sanitization function for the response dict

---

## Step 5: Health Scoring System

**Goal:** Build `scorer.py` — convert Bob's 4 dimension scores into a single weighted Health Score.

**Technical Explanation:** Simple weighted average. Documentation drift and test drift are weighted higher because they represent the most dangerous form of decay (code doing something different from what anyone thinks). The scorer also assigns a status label and generates a priority rank across all files.

### ✅ Tasks
- [ ] Create `app/scorer.py`
- [ ] Use Bob prompt below to generate the scoring logic
- [ ] Verify: a file with doc_drift=20, test_drift=15, complexity=50, naming=80 should score ~35 (Critical)
- [ ] Add a `rank_files()` function that sorts files by health score ascending (worst first)
- [ ] Add status labels: 0-39 CRITICAL, 40-59 AT_RISK, 60-79 WATCH, 80-100 HEALTHY

### ⏱ Time: 45 min

### 🤖 IBM Bob Prompt (Code Mode)

```
Write a Python module called scorer.py for DriftGuard.

It takes the output of bob_analyzer.py (a list of dicts, each with bob analysis scores) and calculates a final health score per file.

Weights:
- documentation_drift_score: 30%
- test_drift_score: 30%
- complexity_growth_score: 25%
- naming_consistency_score: 15%

Functions needed:

1. calculate_health_score(analysis: dict) -> dict
   Returns the same dict with added fields:
   - "health_score": int (0-100, weighted average of the 4 dimensions)
   - "status": str ("CRITICAL" / "AT_RISK" / "WATCH" / "HEALTHY")
   - "status_emoji": str ("🔴" / "🟠" / "🟡" / "🟢")

2. score_all_files(analyses: list[dict]) -> list[dict]
   Applies calculate_health_score to each file and returns sorted list (lowest health_score first)

3. generate_summary(scored_files: list[dict]) -> dict
   Returns:
   {
     "total_files": int,
     "critical_count": int,
     "at_risk_count": int,
     "watch_count": int,
     "healthy_count": int,
     "average_health_score": float,
     "worst_file": str,  # file_path of lowest score
     "best_file": str    # file_path of highest score
   }

Include a brief docstring on each function.
```

### 📤 Expected Output
- `scorer.py` with all 3 functions
- Correct weighted average math
- Proper status label boundaries

---

## Step 6: CLI Entrypoint

**Goal:** Build `driftguard.py` — the CLI tool that wires all modules together.

**Technical Explanation:** The CLI is the glue layer. It calls git_parser → bob_analyzer → scorer → report_generator in sequence, prints a summary to terminal, and saves a JSON report. This is also what you'll run live in the demo video.

### ✅ Tasks
- [ ] Create root-level `driftguard.py`
- [ ] Use Bob prompt below to generate CLI logic
- [ ] Test: `python driftguard.py --repo . --days 14`
- [ ] Confirm JSON report is saved to `output/report_{timestamp}.json`
- [ ] Confirm terminal output shows a clean summary table
- [ ] **Export this session** → `bob_sessions/session_05_cli_export.md`

### ⏱ Time: 1 hour

### 🤖 IBM Bob Prompt (Code Mode)

```
Write the main CLI entrypoint driftguard.py for DriftGuard.

It should use argparse with these arguments:
- --repo: path to git repository (default: ".")
- --days: number of days of history to analyze (default: 30, type: int)
- --output: output JSON file path (default: auto-generated as "output/report_YYYYMMDD_HHMMSS.json")
- --max-files: max number of files to analyze (default: 20, to control Bobcoin usage)
- --verbose: flag, print Bob's raw analysis for each file

Execution flow:
1. Print banner: "🔍 DriftGuard — Codebase Decay Monitor"
2. Print: "Scanning {repo} for last {days} days of changes..."
3. Call get_file_diffs(repo_path, days) from git_parser
4. If 0 files found, print message and exit
5. If files > max_files, print warning and take the top max_files by total_commits (most-changed first)
6. Print: "Analyzing {N} files with IBM Bob..."
7. Call batch_analyze(file_diffs) from bob_analyzer
8. Call score_all_files(analyses) from scorer
9. Build final report dict: {"repo": repo_path, "analysis_window_days": days, "analyzed_at": ISO timestamp, "files": scored_files, "summary": generate_summary(scored_files)}
10. Save report to output file (create output/ directory if it doesn't exist)
11. Print a formatted summary table to terminal with columns: File | Score | Status | Top Risk
12. Print: "✅ Full report saved to {output_path}"
13. Print: "🚀 Start dashboard: uvicorn app.main:app --reload"

Handle errors gracefully: if Bob Shell is not installed, print a helpful error message.
```

### 📤 Expected Output
- Working CLI that runs end-to-end
- Clean terminal output with summary table
- JSON report saved to `output/` folder

---

## Step 7: FastAPI Backend

**Goal:** Build `app/main.py` — serve the most recent report as a REST API and render the dashboard.

**Technical Explanation:** The FastAPI app does two things: serves the JSON report data as `/api/report` (consumed by Chart.js), and renders the dashboard HTML via Jinja2 at `/`. It also needs a `/analyze` POST endpoint so you can trigger a new analysis from the browser (important for the demo).

### ✅ Tasks
- [ ] `pip install fastapi uvicorn jinja2 python-multipart` → add to requirements.txt
- [ ] Create `app/main.py` using Bob prompt below
- [ ] Create `app/templates/` folder
- [ ] Verify: `uvicorn app.main:app --reload` starts without error
- [ ] Verify: `GET /api/report` returns JSON from the last saved report
- [ ] **Export this session** → `bob_sessions/session_06_fastapi_export.md`

### ⏱ Time: 1.5 hours

### 🤖 IBM Bob Prompt (Code Mode)

```
Write app/main.py for DriftGuard — a FastAPI application.

Routes needed:

1. GET / 
   - Finds the most recent JSON report file in the output/ directory
   - Loads it and renders app/templates/dashboard.html using Jinja2
   - Passes the report data as template context
   - If no report exists, renders a "Run DriftGuard first" message

2. GET /api/report
   - Returns the most recent report JSON directly
   - Returns 404 with helpful message if no report exists

3. GET /api/report/{filename}
   - Returns a specific report file by filename

4. GET /health
   - Returns {"status": "ok", "version": "1.0.0"}

Helper functions needed:
- get_latest_report() -> dict | None: scans output/ directory, finds most recent .json file by timestamp in filename, loads and returns it

Use:
- from fastapi import FastAPI, HTTPException
- from fastapi.templating import Jinja2Templates
- from fastapi.staticfiles import StaticFiles
- from fastapi.responses import HTMLResponse

Add CORS middleware (allow all origins for local dev).
Include a startup message printed to console showing the dashboard URL.
```

### 📤 Expected Output
- Working FastAPI app with 4 routes
- Jinja2 template integration
- Report file discovery logic

---

## Step 8: Dashboard Frontend

**Goal:** Build `app/templates/dashboard.html` — visual health map with Chart.js.

**Technical Explanation:** A single HTML file rendered server-side via Jinja2. It receives the report JSON as template context and renders: a summary stats bar at top, a horizontal bar chart of all files by health score (Chart.js), and a scrollable table of files with decay details. Keep it simple — you're judged on functionality, not beauty.

### ✅ Tasks
- [ ] Create `app/templates/dashboard.html` using Bob prompt below
- [ ] Open browser at `http://localhost:8000` — verify dashboard loads with your report data
- [ ] Verify the bar chart renders correctly with color coding (red/orange/yellow/green)
- [ ] Verify the file table shows: filename, score, status, top risk, recommendation
- [ ] Test with at least one real report from your own repo
- [ ] **Export this session** → `bob_sessions/session_07_dashboard_export.md`

### ⏱ Time: 1.5–2 hours

### 🤖 IBM Bob Prompt (Code Mode)

```
Write a Jinja2 HTML template for DriftGuard's dashboard: app/templates/dashboard.html

It receives this Jinja2 context:
- report: the full report dict (see structure in README)
- report.summary: {total_files, critical_count, at_risk_count, watch_count, healthy_count, average_health_score, worst_file, best_file}
- report.files: list of scored file dicts (file_path, health_score, status, status_emoji, dimensions, bob_analysis, top_risk, recommendation, total_commits)

Design requirements:
1. Header: "🔍 DriftGuard" + repo name + analysis date + "Last N days"
2. Summary bar: 4 stat cards showing CRITICAL count (red), AT_RISK (orange), WATCH (yellow), HEALTHY (green) + average score
3. Bar chart: horizontal Chart.js bar chart of ALL files, sorted by health_score ascending (worst at top). Bar color = red if <40, orange if <60, yellow if <80, green otherwise.
4. File table: scrollable table with columns: File Path | Score | Status | Top Risk | Recommendation | Commits
5. Footer: "Powered by IBM Bob" + timestamp

Technical requirements:
- Use Chart.js from CDN (https://cdn.jsdelivr.net/npm/chart.js)
- No external CSS frameworks — use inline styles with a dark background (#1a1a2e), card background (#16213e), accent colors matching the status colors
- The chart labels should show only the filename (not full path) for readability
- Table rows should be color-coded by status
- Make the bar chart container max-height: 400px with overflow scroll if many files
- Use {{ variable }} Jinja2 syntax for all dynamic values
- Use {{ report.files | tojson }} to pass data to Chart.js JavaScript

If no report data: show a centered message "Run DriftGuard first: python driftguard.py --repo . --days 30"
```

### 📤 Expected Output
- Complete single-file HTML dashboard
- Working Chart.js bar chart with color coding
- Summary stats cards
- File detail table
- Renders correctly in browser at localhost:8000

---

## Hour 40–45: Integration Test + Bug Fixes

**Goal:** Run the full pipeline end-to-end on a real repo and fix anything broken.

### ✅ Tasks
- [ ] Run: `python driftguard.py --repo . --days 30 --max-files 10`
- [ ] Verify JSON report is generated in `output/`
- [ ] Run: `uvicorn app.main:app --reload`
- [ ] Open browser at `localhost:8000` — verify dashboard loads
- [ ] Fix any bugs (use Bob for debugging with the prompt below)
- [ ] Run on one more repo (a public GitHub repo you cloned) — verify it works there too

### ⏱ Time: 2–3 hours

### 🤖 IBM Bob Prompt (Ask Mode — use when you hit a bug)

```
I am building DriftGuard. I'm getting this error:

[paste the full error traceback here]

This happens when I run: [paste the command]

Here is the relevant code from [filename]:
[paste the function with the bug]

Please:
1. Identify the root cause
2. Show the corrected code
3. Explain why the fix works
```

---

## Hour 45–47: Demo Preparation

**Goal:** Prepare the exact demo you'll record for the video submission.

### ✅ Tasks
- [ ] Clone a clean public repo to use as demo target (suggestion: your own `CommitAI` or `openenv-email-triage` — you know them well)
- [ ] Run DriftGuard on it: `python driftguard.py --repo /path/to/demo-repo --days 60`
- [ ] Verify the report has at least 2-3 AT_RISK or CRITICAL files (real repos do)
- [ ] Open dashboard — confirm it looks good for screen recording
- [ ] Write your video script (see below)
- [ ] Do one dry run of the demo — time it at under 2:45 (leaves buffer for the 3-min limit)

### Video Script (3 Minutes)

```
0:00–0:25 — Hook
"Every developer has experienced this: you look at old code and have no idea 
what it actually does anymore. Comments are wrong. Tests don't match the logic. 
Function names lie. This is codebase decay — and it's invisible until production breaks."

0:25–0:45 — Your Solution
"DriftGuard detects decay before it becomes a crisis. It analyzes your Git 
history, sends every file diff to IBM Bob, and Bob tells you exactly how far 
each file has drifted from being maintainable."

0:45–2:30 — Live Demo
- Show terminal: run driftguard.py command
- Watch it run (show Bob processing)
- Open browser: show dashboard with the bar chart
- Click on the worst file — show Bob's detailed analysis
- Briefly show Bob IDE in background with a task running

2:30–3:00 — Close
"Built in 48 hours using IBM Bob as the core development partner — 
from architecture planning to code generation to the analysis engine itself. 
DriftGuard makes codebase decay visible, measurable, and actionable."
```

### ⏱ Time: 1 hour

---

## Hour 47–48: Submission Finalization

### ✅ Final Checklist

**Repository:**
- [ ] `bob_sessions/` has ≥ 4 exported sessions (screenshots + .md files for each)
- [ ] `AGENTS.md` is in repo root (generated by Bob /init)
- [ ] `README.md` is complete and accurate
- [ ] `requirements.txt` is complete
- [ ] Repo is PUBLIC on GitHub
- [ ] All code is committed and pushed

**Deliverables:**
- [ ] Video recorded (Loom or OBS) — under 3 minutes — URL is shareable
- [ ] Problem + Solution statement written (≤500 words, use README structure)
- [ ] IBM Bob usage statement written (list every mode used and what for)
- [ ] Submission form filled at `ibmdevday-bob.bemyapp.com`
- [ ] Confirmation email received

**Time:** Submit before 10:00 AM ET May 3 (≈10:30 PM IST May 3)

---

## Bob Sessions Export Checklist

After each step, export the Bob session before moving on:

| Session | File to Create | Bob Mode Used |
|---|---|---|
| session_01 | `bob_sessions/session_01_planning_export.md` | Plan |
| session_02 | `bob_sessions/session_02_git_parser_export.md` | Code |
| session_03 | `bob_sessions/session_03_bob_analyzer_export.md` | Code |
| session_04 | `bob_sessions/session_04_prompt_engineering_export.md` | Ask |
| session_05 | `bob_sessions/session_05_cli_export.md` | Code |
| session_06 | `bob_sessions/session_06_fastapi_export.md` | Code |
| session_07 | `bob_sessions/session_07_dashboard_export.md` | Code |

**How to export:** Bob IDE → Views → More Actions → History → select task → click Export icon → save `.md` file + take screenshot of the task consumption summary.
