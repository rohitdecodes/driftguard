"""DriftGuard CLI entrypoint (minimal scaffold).

Run: python driftguard.py --repo . --days 30
"""
import argparse
from datetime import datetime


def main():
    parser = argparse.ArgumentParser(description="DriftGuard — Codebase Decay Monitor")
    parser.add_argument("--repo", default='.', help="Path to git repository")
    parser.add_argument("--days", type=int, default=30, help="Number of days of history to analyze")
    parser.add_argument("--output", default=None, help="Output JSON file path")
    parser.add_argument("--max-files", type=int, default=20, help="Max files to analyze")
    parser.add_argument("--verbose", action="store_true", help="Print raw analysis")
    args = parser.parse_args()

    print("🔍 DriftGuard — Codebase Decay Monitor")
    print(f"Scanning {args.repo} for last {args.days} days of changes...")
    print(f"(This is a scaffold CLI. Implement modules: git_parser, bob_analyzer, scorer)")
    print(f"Run timestamp: {datetime.utcnow().isoformat()}Z")


if __name__ == '__main__':
    main()
