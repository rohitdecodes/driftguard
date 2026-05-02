"""models.py

Data schemas for DriftGuard pipeline using TypedDict for clean, serializable types.
All intermediate and final data structures used across modules.
"""
from typing import TypedDict, List, Optional
from datetime import datetime


# ============================================================================
# GIT PARSER OUTPUT SCHEMAS
# ============================================================================

class FileDiff(TypedDict, total=False):
    """Output from git_parser.get_file_diffs() - one per modified file."""
    file_path: str              # relative path: "app/auth/login.py"
    language: str               # "python", "javascript", etc.
    total_commits: int          # commits touching this file in window
    diff_text: str              # unified diff (max 150 lines)
    last_modified: str          # ISO timestamp of most recent commit
    commit_hashes: List[str]    # list of commit SHAs


# ============================================================================
# BOB ANALYZER OUTPUT SCHEMAS
# ============================================================================

class DecayMetrics(TypedDict, total=False):
    """The 4 decay dimensions scored by bob_analyzer."""
    documentation_drift_score: int      # 0-100: did docs/comments keep up with code?
    test_drift_score: int               # 0-100: did tests keep up with implementation?
    complexity_growth_score: int        # 0-100: did complexity explode?
    naming_consistency_score: int       # 0-100: do new names match conventions?


class AnalysisResult(TypedDict, total=False):
    """Output from bob_analyzer.analyze_file_decay() - decay analysis for one file."""
    file_path: str                      # from input file_data
    language: str                       # from input file_data
    total_commits: int                  # from input file_data
    diff_text: str                      # from input file_data (truncated)
    last_modified: str                  # from input file_data
    commit_hashes: List[str]            # from input file_data
    
    documentation_drift_score: int      # 0-100
    test_drift_score: int               # 0-100
    complexity_growth_score: int        # 0-100
    naming_consistency_score: int       # 0-100
    decay_summary: str                  # 2-3 sentence explanation
    top_risk: str                       # single most concerning pattern
    recommendation: str                 # one specific action to address


# ============================================================================
# SCORER OUTPUT SCHEMAS
# ============================================================================

class DimensionScore(TypedDict, total=False):
    """Per-dimension breakdown in final scored file."""
    documentation_drift: int
    test_drift: int
    complexity_growth: int
    naming_consistency: int


class ScoredFile(TypedDict, total=False):
    """Output from scorer.score_all_files() - one file with health score."""
    file_path: str
    language: str
    total_commits: int
    diff_text: str
    last_modified: str
    commit_hashes: List[str]
    
    documentation_drift_score: int
    test_drift_score: int
    complexity_growth_score: int
    naming_consistency_score: int
    decay_summary: str
    top_risk: str
    recommendation: str
    
    health_score: int                   # weighted average: 0-100
    status: str                         # "CRITICAL" | "AT_RISK" | "WATCH" | "HEALTHY"
    status_emoji: str                   # "🔴" | "🟠" | "🟡" | "🟢"


# ============================================================================
# REPORT SCHEMAS
# ============================================================================

class RepoSummary(TypedDict, total=False):
    """Aggregate statistics for a full report."""
    total_files: int
    critical_count: int         # status == CRITICAL
    at_risk_count: int          # status == AT_RISK
    watch_count: int            # status == WATCH
    healthy_count: int          # status == HEALTHY
    average_health_score: float
    worst_file: str             # file_path with lowest score
    best_file: str              # file_path with highest score


class DriftReport(TypedDict, total=False):
    """Final JSON report returned by report_generator and served by FastAPI."""
    repo: str                           # repo_path
    analysis_window_days: int           # days argument
    analyzed_at: str                    # ISO timestamp when analysis ran
    files: List[ScoredFile]             # all scored files, sorted by health_score asc
    summary: RepoSummary


# ============================================================================
# CONFIGURATION SCHEMAS
# ============================================================================

class CLIConfig(TypedDict, total=False):
    """Parsed CLI arguments from argparse."""
    repo: str                   # default: "."
    days: int                   # default: 30
    output: Optional[str]       # default: auto-generated
    max_files: int              # default: 20
    verbose: bool               # default: False


class AppConfig(TypedDict, total=False):
    """Application configuration loaded from environment."""
    repo_path: str
    analysis_days: int
    max_files_per_run: int
    output_dir: str
    log_level: str              # DEBUG, INFO, WARNING, ERROR
