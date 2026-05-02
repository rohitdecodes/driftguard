"""git_parser.py

Extract recent file diffs from a git repository using GitPython.
Provides get_file_diffs(repo_path: str, days: int) -> list[dict]
"""
from datetime import datetime, timedelta, timezone
import os
from typing import List, Dict

from git import Repo, NULL_TREE


ALLOWED_EXT = {'.py': 'python', '.js': 'javascript', '.ts': 'typescript', '.java': 'java'}


def _infer_language(path: str) -> str:
    _, ext = os.path.splitext(path.lower())
    return ALLOWED_EXT.get(ext, 'other')


def _truncate_diff(diff_text: str, max_lines: int = 150) -> str:
    lines = diff_text.splitlines()
    if len(lines) <= max_lines:
        return '\n'.join(lines)
    head = lines[:75]
    tail = lines[-75:]
    return '\n'.join(head + ['... [truncated] ...'] + tail)


def get_file_diffs(repo_path: str, days: int) -> List[Dict]:
    repo = Repo(repo_path)
    since_dt = datetime.now(timezone.utc) - timedelta(days=days)
    since_iso = since_dt.isoformat()

    file_map = {}  # path -> {'commits': set(), 'diffs': [str], 'last_modified': datetime}

    try:
        commits = list(repo.iter_commits(since=since_iso))
    except TypeError:
        # Some GitPython versions expect since as a string; fall back to iterating recent commits
        commits = list(repo.iter_commits())

    for commit in commits:
        commit_dt = commit.committed_datetime
        parent = commit.parents[0] if commit.parents else NULL_TREE
        try:
            diffs = commit.diff(parent, create_patch=True)
        except Exception:
            continue

        for diff in diffs:
            path = diff.b_path or diff.a_path
            if not path:
                continue
            _, ext = os.path.splitext(path.lower())
            if ext not in ALLOWED_EXT:
                continue
            # try to get unified diff text
            try:
                raw = diff.diff
                if raw is None:
                    # binary or non-text
                    continue
                diff_text = raw.decode('utf-8', errors='replace')
            except Exception:
                continue

            entry = file_map.setdefault(path, {'commits': set(), 'diffs': [], 'last_modified': None})
            entry['commits'].add(commit.hexsha)
            entry['diffs'].append(diff_text)
            if entry['last_modified'] is None or commit_dt > entry['last_modified']:
                entry['last_modified'] = commit_dt

    results = []
    for path, data in file_map.items():
        language = _infer_language(path)
        total_commits = len(data['commits'])
        combined = '\n'.join(data['diffs'])
        truncated = _truncate_diff(combined, max_lines=150)
        last_mod_iso = data['last_modified'].astimezone(timezone.utc).isoformat() if data['last_modified'] else None
        results.append({
            'file_path': path,
            'language': language,
            'total_commits': total_commits,
            'diff_text': truncated,
            'last_modified': last_mod_iso,
            'commit_hashes': list(data['commits']),
        })

    # sort by total_commits descending
    results.sort(key=lambda r: r['total_commits'], reverse=True)
    return results


def test_git_parser():
    print('Running test_git_parser on current directory...')
    res = get_file_diffs('.', 7)
    if not res:
        print('No file diffs found in the last 7 days.')
        return
    from pprint import pprint
    pprint(res[0])


if __name__ == '__main__':
    test_git_parser()
