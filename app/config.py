"""config.py

Load and manage application configuration from environment, CLI, and defaults.
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()


class Config:
    """Centralized configuration management."""
    
    # Directories
    REPO_ROOT = Path(__file__).parent.parent
    APP_DIR = REPO_ROOT / "app"
    OUTPUT_DIR = REPO_ROOT / "output"
    BOB_SESSIONS_DIR = REPO_ROOT / "bob_sessions"
    TEMPLATES_DIR = APP_DIR / "templates"
    
    # Create directories if they don't exist
    OUTPUT_DIR.mkdir(exist_ok=True)
    BOB_SESSIONS_DIR.mkdir(exist_ok=True)
    
    # Analysis defaults
    DEFAULT_DAYS = int(os.getenv("DRIFTGUARD_DAYS", "30"))
    DEFAULT_MAX_FILES = int(os.getenv("DRIFTGUARD_MAX_FILES", "20"))
    DEFAULT_REPO_PATH = os.getenv("DRIFTGUARD_REPO", ".")
    
    # Logging
    LOG_LEVEL = os.getenv("DRIFTGUARD_LOG_LEVEL", "INFO")
    
    # FastAPI
    FASTAPI_HOST = os.getenv("DRIFTGUARD_HOST", "127.0.0.1")
    FASTAPI_PORT = int(os.getenv("DRIFTGUARD_PORT", "8000"))
    FASTAPI_RELOAD = os.getenv("DRIFTGUARD_RELOAD", "true").lower() == "true"
    
    # File extensions to analyze
    ALLOWED_EXTENSIONS = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".java": "java",
    }
    
    # Scoring thresholds
    SCORE_CRITICAL_THRESHOLD = 40        # 0-39 = CRITICAL
    SCORE_AT_RISK_THRESHOLD = 60         # 40-59 = AT_RISK
    SCORE_WATCH_THRESHOLD = 80           # 60-79 = WATCH
    # 80-100 = HEALTHY
    
    # Score weights (must sum to 1.0)
    WEIGHT_DOCUMENTATION = 0.30
    WEIGHT_TEST_COVERAGE = 0.30
    WEIGHT_COMPLEXITY = 0.25
    WEIGHT_NAMING = 0.15
    
    # Status emojis
    STATUS_EMOJI = {
        "CRITICAL": "🔴",
        "AT_RISK": "🟠",
        "WATCH": "🟡",
        "HEALTHY": "🟢",
    }
    
    # Rule-based analyzer thresholds
    RULE_DOC_DRIFT_THRESHOLD_ADDED_LINES = 50      # if 50+ lines added with 0 comments
    RULE_COMPLEXITY_NESTING_THRESHOLD = 2          # nesting level increase
    RULE_TEST_REQUIRED_RATIO = 0.3                 # if changed code vs test code ratio


def get_output_report_path(timestamp: Optional[str] = None) -> Path:
    """Generate output report file path with timestamp."""
    from datetime import datetime
    if timestamp is None:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return Config.OUTPUT_DIR / f"report_{timestamp}.json"


def get_latest_report() -> Optional[Path]:
    """Find the most recent report JSON file in output directory."""
    if not Config.OUTPUT_DIR.exists():
        return None
    reports = list(Config.OUTPUT_DIR.glob("report_*.json"))
    if not reports:
        return None
    return max(reports, key=lambda p: p.stat().st_mtime)
