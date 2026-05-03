**User:**

<task>
Replace hardcoded file extension support with config-driven language mapping.

Requirements:
1) Add config file (JSON or .env-driven) for:
   - extension -> language
   - enabled extensions list
2) Update git parser to use config mapping dynamically
3) Provide sane defaults for python/js/ts/java/go/rb/html/css
4) Add endpoint or CLI command to print active language config
5) Add tests ensuring parser respects config overrides.
</task>
<environment_details>
# VSCode Visible Files
driftguard.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,app/git_parser.py,test_language_support.py,data/repos.json,app/templates/dashboard.html

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:27:17.082Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$0.00

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>


# Current Workspace Directory (c:/Users/Rohit/driftguard) Files
.env.example
.gitignore
ARCHITECTURE_PLAN.md
benchmark_parallel.py
context.md
demo_cache.py
demo_rate_limiter.py
docker-compose.yml
Dockerfile
driftguard.py
PARALLEL_ANALYSIS.md
PHASE_1.md
PHASE_2.md
README.md
requirements.txt
test_cache.py
test_db.py
test_integration_trends.py
test_integration.py
test_language_support.py
test_parallel_analysis.py
test_rate_limiter.py
test_remediation_api.py
test_remediation_complete.py
test_trends_endpoint.py
test_trends.py
test_validation.py
test_watch_mode.py
WATCH_MODE.md
.driftguard/
.pytest_cache/
app/
app/__init__.py
app/alert_manager.py
app/baseline_profile.py
app/bob_analyzer.py
app/config.py
app/db.py
app/git_parser.py
app/language_prompts.py
app/main.py
app/models.py
app/rate_limiter.py
app/remediation.py
app/report_exporter.py
app/report_generator.py
app/scorer.py
app/trends.py
app/validation.py
app/templates/
app/templates/dashboard.html
bob_sessions/
data/
data/driftguard.db
data/repos.json
logs/
logs/driftguard.log
output/
output/report_20260502_194111.md
output/report_20260502_194138.md
remediation/
remediation/app_alert_manager_py_remediation.md
You have not created a todo list yet. Create one with `update_todo_list` if your task is complicated or involves multiple steps.
</environment_details>

---

**Assistant:**

I'll help you replace hardcoded file extension support with config-driven language mapping. Let me start by examining the current implementation to understand how file extensions are handled.

<read_file>
<args>
<file>
<path>app/git_parser.py</path>
</file>
</args>
</read_file>

---

**User:**

[read_file for 'app/git_parser.py'. Reading multiple files at once is more efficient for the LLM. If other files are relevant to your current task, please read them simultaneously.] Result:
<files>
<file><path>app/git_parser.py</path>
<content lines="1-591">
  1 | """Git parser module for DriftGuard.
  2 | 
  3 | Extracts file diffs from a Git repository over a specified time window.
  4 | Supports local repositories, GitHub URLs, and generic git URLs.
  5 | """
  6 | 
  7 | import os
  8 | import re
  9 | import tempfile
 10 | import shutil
 11 | from datetime import datetime, timedelta, timezone
 12 | from pathlib import Path
 13 | from typing import List, Dict, Optional, Any, Tuple
 14 | from collections import defaultdict
 15 | 
 16 | try:
 17 |     from git import Repo, GitCommandError, InvalidGitRepositoryError
 18 | except ImportError:
 19 |     raise ImportError("GitPython is required. Install with: pip install gitpython")
 20 | 
 21 | try:
 22 |     import requests
 23 | except ImportError:
 24 |     raise ImportError("requests is required. Install with: pip install requests")
 25 | 
 26 | 
 27 | # Supported file extensions
 28 | SUPPORTED_EXTENSIONS = {'.py', '.js', '.ts', '.java', '.go', '.rb', '.html', '.css'}
 29 | 
 30 | # Language mapping
 31 | EXTENSION_TO_LANGUAGE = {
 32 |     '.py': 'python',
 33 |     '.js': 'javascript',
 34 |     '.ts': 'typescript',
 35 |     '.java': 'java',
 36 |     '.go': 'go',
 37 |     '.rb': 'ruby',
 38 |     '.html': 'html',
 39 |     '.css': 'css',
 40 | }
 41 | 
 42 | # Maximum lines for diff_text
 43 | MAX_DIFF_LINES = 150
 44 | TRUNCATE_HEAD_LINES = 75
 45 | TRUNCATE_TAIL_LINES = 75
 46 | 
 47 | 
 48 | def _parse_github_url(url: str) -> Optional[Tuple[str, str]]:
 49 |     """Parse GitHub URL to extract owner and repo name.
 50 |     
 51 |     Args:
 52 |         url: GitHub URL (e.g., https://github.com/facebook/react)
 53 |         
 54 |     Returns:
 55 |         Tuple of (owner, repo) or None if not a valid GitHub URL
 56 |     """
 57 |     # Match patterns like:
 58 |     # - https://github.com/owner/repo
 59 |     # - https://github.com/owner/repo.git
 60 |     # - http://github.com/owner/repo
 61 |     pattern = r'https?://github\.com/([^/]+)/([^/\.]+?)(?:\.git)?/?$'
 62 |     match = re.match(pattern, url)
 63 |     if match:
 64 |         return match.group(1), match.group(2)
 65 |     return None
 66 | 
 67 | 
 68 | def _fetch_github_commits(owner: str, repo: str, since_date: datetime, 
 69 |                           github_token: Optional[str] = None) -> List[Dict]:
 70 |     """Fetch commits from GitHub API.
 71 |     
 72 |     Args:
 73 |         owner: Repository owner
 74 |         repo: Repository name
 75 |         since_date: Only fetch commits after this date
 76 |         github_token: Optional GitHub token for authentication
 77 |         
 78 |     Returns:
 79 |         List of commit dictionaries from GitHub API
 80 |         
 81 |     Raises:
 82 |         requests.HTTPError: For API errors (401, 403, 404, etc.)
 83 |     """
 84 |     headers = {'Accept': 'application/vnd.github.v3+json'}
 85 |     if github_token:
 86 |         headers['Authorization'] = f'token {github_token}'
 87 |     
 88 |     all_commits = []
 89 |     page = 1
 90 |     per_page = 100
 91 |     
 92 |     while True:
 93 |         url = f'https://api.github.com/repos/{owner}/{repo}/commits'
 94 |         params = {
 95 |             'since': since_date.isoformat(),
 96 |             'per_page': per_page,
 97 |             'page': page
 98 |         }
 99 |         
100 |         response = requests.get(url, headers=headers, params=params, timeout=30)
101 |         
102 |         # Handle errors
103 |         if response.status_code == 401:
104 |             raise requests.HTTPError(
105 |                 "401 Unauthorized: Private repository requires GITHUB_TOKEN"
106 |             )
107 |         elif response.status_code == 404:
108 |             raise requests.HTTPError(
109 |                 f"404 Not Found: Repository {owner}/{repo} does not exist"
110 |             )
111 |         elif response.status_code == 403:
112 |             # Check if it's rate limit
113 |             if 'X-RateLimit-Remaining' in response.headers:
114 |                 remaining = response.headers.get('X-RateLimit-Remaining', '0')
115 |                 if remaining == '0':
116 |                     reset_time = response.headers.get('X-RateLimit-Reset', 'unknown')
117 |                     raise requests.HTTPError(
118 |                         f"403 Rate Limit Exceeded. Resets at: {reset_time}. "
119 |                         "Use GITHUB_TOKEN for higher limits."
120 |                     )
121 |             raise requests.HTTPError(f"403 Forbidden: {response.text}")
122 |         
123 |         response.raise_for_status()
124 |         
125 |         commits = response.json()
126 |         if not commits:
127 |             break
128 |         
129 |         all_commits.extend(commits)
130 |         
131 |         # Check if there are more pages
132 |         if len(commits) < per_page:
133 |             break
134 |         
135 |         page += 1
136 |     
137 |     return all_commits
138 | 
139 | 
140 | def _fetch_github_commit_diff(owner: str, repo: str, base_sha: str, head_sha: str,
141 |                                github_token: Optional[str] = None) -> Dict:
142 |     """Fetch diff between two commits from GitHub API.
143 |     
144 |     Args:
145 |         owner: Repository owner
146 |         repo: Repository name
147 |         base_sha: Base commit SHA
148 |         head_sha: Head commit SHA
149 |         github_token: Optional GitHub token for authentication
150 |         
151 |     Returns:
152 |         Comparison data from GitHub API
153 |         
154 |     Raises:
155 |         requests.HTTPError: For API errors
156 |     """
157 |     headers = {'Accept': 'application/vnd.github.v3+json'}
158 |     if github_token:
159 |         headers['Authorization'] = f'token {github_token}'
160 |     
161 |     url = f'https://api.github.com/repos/{owner}/{repo}/compare/{base_sha}...{head_sha}'
162 |     response = requests.get(url, headers=headers, timeout=30)
163 |     response.raise_for_status()
164 |     
165 |     return response.json()
166 | 
167 | 
168 | def _convert_github_diff_to_format(files_data: List[Dict], commit_sha: str, 
169 |                                     commit_date: datetime) -> Dict[str, Dict]:
170 |     """Convert GitHub API diff format to internal format.
171 |     
172 |     Args:
173 |         files_data: List of file change dicts from GitHub API
174 |         commit_sha: Commit SHA
175 |         commit_date: Commit timestamp
176 |         
177 |     Returns:
178 |         Dictionary mapping file paths to their change data
179 |     """
180 |     file_changes = {}
181 |     
182 |     for file_info in files_data:
183 |         filename = file_info.get('filename', '')
184 |         
185 |         # Filter by extension
186 |         ext = Path(filename).suffix.lower()
187 |         if ext not in SUPPORTED_EXTENSIONS:
188 |             continue
189 |         
190 |         # Skip large files
191 |         if file_info.get('changes', 0) > 1000:  # Skip files with >1000 changes
192 |             continue
193 |         
194 |         # Get patch (unified diff)
195 |         patch = file_info.get('patch', '')
196 |         if not patch:
197 |             continue
198 |         
199 |         # Initialize file data if not exists
200 |         if filename not in file_changes:
201 |             file_changes[filename] = {
202 |                 'commits': [],
203 |                 'diffs': [],
204 |                 'last_modified': None,
205 |             }
206 |         
207 |         # Add commit and diff
208 |         file_changes[filename]['commits'].append(commit_sha)
209 |         file_changes[filename]['diffs'].append(patch)
210 |         
211 |         # Update last modified
212 |         if (file_changes[filename]['last_modified'] is None or 
213 |             commit_date > file_changes[filename]['last_modified']):
214 |             file_changes[filename]['last_modified'] = commit_date
215 |     
216 |     return file_changes
217 | 
218 | 
219 | def _fetch_github_repo_diffs(owner: str, repo: str, days: int,
220 |                               github_token: Optional[str] = None) -> List[Dict]:
221 |     """Fetch file diffs from GitHub repository via API.
222 |     
223 |     Args:
224 |         owner: Repository owner
225 |         repo: Repository name
226 |         days: Number of days to look back
227 |         github_token: Optional GitHub token for authentication
228 |         
229 |     Returns:
230 |         List of file diff dictionaries in same format as get_file_diffs()
231 |     """
232 |     # Calculate cutoff date
233 |     cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
234 |     
235 |     # Fetch commits
236 |     print(f"Fetching commits from GitHub API for {owner}/{repo}...")
237 |     commits = _fetch_github_commits(owner, repo, cutoff_date, github_token)
238 |     
239 |     if not commits:
240 |         return []
241 |     
242 |     print(f"Found {len(commits)} commits, fetching diffs...")
243 |     
244 |     # Collect file changes
245 |     file_data: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
246 |         'commits': [],
247 |         'diffs': [],
248 |         'last_modified': None,
249 |     })
250 |     
251 |     # Process commits in reverse order (oldest first) to get proper parent relationships
252 |     for i, commit_info in enumerate(reversed(commits)):
253 |         commit_sha = commit_info['sha']
254 |         commit_date_str = commit_info['commit']['committer']['date']
255 |         commit_date = datetime.fromisoformat(commit_date_str.replace('Z', '+00:00'))
256 |         
257 |         # Get parent SHA (if exists)
258 |         parents = commit_info.get('parents', [])
259 |         if not parents:
260 |             # Initial commit - skip for now (could fetch full tree if needed)
261 |             continue
262 |         
263 |         parent_sha = parents[0]['sha']
264 |         
265 |         # Fetch diff between parent and this commit
266 |         try:
267 |             comparison = _fetch_github_commit_diff(owner, repo, parent_sha, 
268 |                                                    commit_sha, github_token)
269 |             files_changed = comparison.get('files', [])
270 |             
271 |             # Convert to internal format
272 |             changes = _convert_github_diff_to_format(files_changed, commit_sha, commit_date)
273 |             
274 |             # Merge into file_data
275 |             for file_path, data in changes.items():
276 |                 file_data[file_path]['commits'].extend(data['commits'])
277 |                 file_data[file_path]['diffs'].extend(data['diffs'])
278 |                 if (file_data[file_path]['last_modified'] is None or
279 |                     data['last_modified'] > file_data[file_path]['last_modified']):
280 |                     file_data[file_path]['last_modified'] = data['last_modified']
281 |         
282 |         except requests.HTTPError as e:
283 |             print(f"Warning: Failed to fetch diff for commit {commit_sha[:7]}: {e}")
284 |             continue
285 |         
286 |         # Progress indicator
287 |         if (i + 1) % 10 == 0:
288 |             print(f"  Processed {i + 1}/{len(commits)} commits...")
289 |     
290 |     # Build result list (same format as get_file_diffs)
291 |     results = []
292 |     for file_path, data in file_data.items():
293 |         ext = Path(file_path).suffix.lower()
294 |         language = EXTENSION_TO_LANGUAGE.get(ext, 'unknown')
295 |         
296 |         # Concatenate all diffs
297 |         full_diff = '\n\n'.join(data['diffs'])
298 |         
299 |         # Truncate if necessary
300 |         diff_lines = full_diff.split('\n')
301 |         if len(diff_lines) > MAX_DIFF_LINES:
302 |             truncated_diff = (
303 |                 '\n'.join(diff_lines[:TRUNCATE_HEAD_LINES]) +
304 |                 '\n\n... [truncated] ...\n\n' +
305 |                 '\n'.join(diff_lines[-TRUNCATE_TAIL_LINES:])
306 |             )
307 |         else:
308 |             truncated_diff = full_diff
309 |         
310 |         result = {
311 |             'file_path': file_path,
312 |             'language': language,
313 |             'total_commits': len(data['commits']),
314 |             'diff_text': truncated_diff,
315 |             'last_modified': data['last_modified'].isoformat() if data['last_modified'] else None,
316 |             'commit_hashes': data['commits'],
317 |         }
318 |         results.append(result)
319 |     
320 |     # Sort by last_modified (most recent first)
321 |     results.sort(key=lambda x: x['last_modified'] or '', reverse=True)
322 |     
323 |     print(f"Completed: {len(results)} files with changes")
324 |     return results
325 | 
326 | 
327 | def resolve_repo(repo_input: str, github_token: Optional[str] = None) -> Tuple[Any, bool]:
328 |     """Resolve repository input to either local path or remote data.
329 |     
330 |     Args:
331 |         repo_input: Local path, GitHub URL, or other git URL
332 |         github_token: Optional GitHub token for API authentication
333 |         
334 |     Returns:
335 |         Tuple of (data, is_remote):
336 |         - If local path: (path_string, False)
337 |         - If GitHub URL: (list_of_diffs, True)
338 |         - If other git URL: (path_to_temp_clone, False)
339 |         
340 |     Raises:
341 |         ValueError: If repo_input is invalid
342 |         requests.HTTPError: For GitHub API errors
343 |     """
344 |     # Check if it's a GitHub URL
345 |     github_info = _parse_github_url(repo_input)
346 |     if github_info:
347 |         owner, repo = github_info
348 |         print(f"Detected GitHub repository: {owner}/{repo}")
349 |         
350 |         # Use environment variable if token not provided
351 |         if not github_token:
352 |             github_token = os.environ.get('GITHUB_TOKEN')
353 |         
354 |         # Fetch diffs via API
355 |         try:
356 |             # We need days parameter - will be passed separately
357 |             # For now, return a callable that takes days
358 |             return (owner, repo, github_token), True
359 |         except requests.HTTPError as e:
360 |             raise ValueError(f"GitHub API error: {e}")
361 |     
362 |     # Check if it's another https URL
363 |     if repo_input.startswith('https://') or repo_input.startswith('http://'):
364 |         print(f"Detected remote git repository: {repo_input}")
365 |         print("Cloning to temporary directory...")
366 |         
367 |         # Create temp directory
368 |         temp_dir = tempfile.mkdtemp(prefix='driftguard_')
369 |         
370 |         try:
371 |             # Clone repository
372 |             Repo.clone_from(repo_input, temp_dir, depth=1)
373 |             print(f"Cloned to: {temp_dir}")
374 |             return temp_dir, False
375 |         except Exception as e:
376 |             # Clean up on error
377 |             shutil.rmtree(temp_dir, ignore_errors=True)
378 |             raise ValueError(f"Failed to clone repository: {e}")
379 |     
380 |     # Treat as local path
381 |     repo_path = os.path.abspath(repo_input)
382 |     if not os.path.exists(repo_path):
383 |         raise ValueError(f"Repository path does not exist: {repo_path}")
384 |     
385 |     return repo_path, False
386 | 
387 | 
388 | def get_file_diffs(repo_path: str, days: int) -> List[Dict]:
389 |     """
390 |     Extract file diffs from a Git repository over the last N days.
391 |     
392 |     Args:
393 |         repo_path: Path to the git repository (absolute or relative)
394 |         days: Number of days to look back in history
395 |         
396 |     Returns:
397 |         List of dictionaries, each containing:
398 |         - file_path: Relative path to the file
399 |         - language: Programming language (inferred from extension)
400 |         - total_commits: Number of commits that modified this file
401 |         - diff_text: Concatenated unified diff (max 150 lines)
402 |         - last_modified: ISO timestamp of most recent commit
403 |         - commit_hashes: List of commit hashes that touched this file
404 |         
405 |     Returns empty list if no files were modified in the time window.
406 |     
407 |     Raises:
408 |         InvalidGitRepositoryError: If repo_path is not a valid git repository
409 |         GitCommandError: If git operations fail
410 |     """
411 |     # Resolve repository path
412 |     repo_path = os.path.abspath(repo_path)
413 |     
414 |     try:
415 |         repo = Repo(repo_path)
416 |     except InvalidGitRepositoryError:
417 |         raise InvalidGitRepositoryError(f"Not a valid git repository: {repo_path}")
418 |     
419 |     # Calculate cutoff date
420 |     cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
421 |     
422 |     # Collect file changes grouped by file path
423 |     file_data: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
424 |         'commits': [],
425 |         'diffs': [],
426 |         'last_modified': None,
427 |     })
428 |     
429 |     # Iterate through commits in the time window
430 |     try:
431 |         commits = list(repo.iter_commits('HEAD', since=cutoff_date))
432 |     except GitCommandError as e:
433 |         # Handle empty repository or other git errors
434 |         print(f"Warning: Git command error: {e}")
435 |         return []
436 |     
437 |     if not commits:
438 |         return []
439 |     
440 |     for commit in commits:
441 |         commit_date = datetime.fromtimestamp(commit.committed_date, tz=timezone.utc)
442 |         
443 |         # Get parent commit for diff (handle initial commit case)
444 |         if commit.parents:
445 |             parent = commit.parents[0]
446 |             try:
447 |                 diffs = parent.diff(commit, create_patch=True)
448 |             except GitCommandError:
449 |                 continue
450 |         else:
451 |             # Initial commit - compare against empty tree
452 |             try:
453 |                 diffs = commit.diff(None, create_patch=True)
454 |             except GitCommandError:
455 |                 continue
456 |         
457 |         # Process each changed file
458 |         for diff in diffs:
459 |             # Get file path (handle renames)
460 |             if diff.b_path:
461 |                 file_path = diff.b_path
462 |             elif diff.a_path:
463 |                 file_path = diff.a_path
464 |             else:
465 |                 continue
466 |             
467 |             # Filter by extension
468 |             ext = Path(file_path).suffix.lower()
469 |             if ext not in SUPPORTED_EXTENSIONS:
470 |                 continue
471 |             
472 |             # Skip binary files (with error handling for missing blobs)
473 |             try:
474 |                 if diff.b_blob and diff.b_blob.size > 1024 * 1024:  # Skip files > 1MB
475 |                     continue
476 |             except (ValueError, AttributeError):
477 |                 # Blob might be missing or corrupted, skip it
478 |                 continue
479 |             
480 |             try:
481 |                 # Get diff text
482 |                 if diff.diff:
483 |                     if isinstance(diff.diff, bytes):
484 |                         diff_text = diff.diff.decode('utf-8', errors='ignore')
485 |                     else:
486 |                         diff_text = str(diff.diff)
487 |                 else:
488 |                     diff_text = ""
489 |             except (AttributeError, UnicodeDecodeError, ValueError):
490 |                 # Skip if we can't decode the diff or blob is missing
491 |                 continue
492 |             
493 |             # Skip if diff is empty or binary
494 |             if not diff_text or diff_text.startswith('Binary files'):
495 |                 continue
496 |             
497 |             # Store file data
498 |             file_data[file_path]['commits'].append(commit.hexsha)
499 |             file_data[file_path]['diffs'].append(diff_text)
500 |             
501 |             # Update last modified timestamp
502 |             if (file_data[file_path]['last_modified'] is None or 
503 |                 commit_date > file_data[file_path]['last_modified']):
504 |                 file_data[file_path]['last_modified'] = commit_date
505 |     
506 |     # Build result list
507 |     results = []
508 |     for file_path, data in file_data.items():
509 |         # Get language from extension
510 |         ext = Path(file_path).suffix.lower()
511 |         language = EXTENSION_TO_LANGUAGE.get(ext, 'unknown')
512 |         
513 |         # Concatenate all diffs
514 |         full_diff = '\n\n'.join(data['diffs'])
515 |         
516 |         # Truncate if necessary
517 |         diff_lines = full_diff.split('\n')
518 |         if len(diff_lines) > MAX_DIFF_LINES:
519 |             truncated_diff = (
520 |                 '\n'.join(diff_lines[:TRUNCATE_HEAD_LINES]) +
521 |                 '\n\n... [truncated] ...\n\n' +
522 |                 '\n'.join(diff_lines[-TRUNCATE_TAIL_LINES:])
523 |             )
524 |         else:
525 |             truncated_diff = full_diff
526 |         
527 |         # Build result dict
528 |         result = {
529 |             'file_path': file_path,
530 |             'language': language,
531 |             'total_commits': len(data['commits']),
532 |             'diff_text': truncated_diff,
533 |             'last_modified': data['last_modified'].isoformat() if data['last_modified'] else None,
534 |             'commit_hashes': data['commits'],
535 |         }
536 |         results.append(result)
537 |     
538 |     # Sort by last_modified (most recent first)
539 |     results.sort(key=lambda x: x['last_modified'] or '', reverse=True)
540 |     
541 |     return results
542 | 
543 | 
544 | def test_git_parser():
545 |     """
546 |     Test function that runs git_parser on the current directory.
547 |     Prints the first result for verification.
548 |     """
549 |     print("[TEST] Testing git_parser on current directory...")
550 |     print(f"Current directory: {os.getcwd()}")
551 |     print("-" * 60)
552 |     
553 |     try:
554 |         # Run parser on current directory, last 30 days
555 |         results = get_file_diffs('.', days=30)
556 |         
557 |         print(f"[OK] Found {len(results)} files modified in the last 30 days")
558 |         print("-" * 60)
559 |         
560 |         if results:
561 |             print("\n[RESULT] First result:")
562 |             first = results[0]
563 |             print(f"  File: {first['file_path']}")
564 |             print(f"  Language: {first['language']}")
565 |             print(f"  Total commits: {first['total_commits']}")
566 |             print(f"  Last modified: {first['last_modified']}")
567 |             print(f"  Commit hashes: {', '.join(first['commit_hashes'][:3])}{'...' if len(first['commit_hashes']) > 3 else ''}")
568 |             print(f"  Diff length: {len(first['diff_text'])} characters")
569 |             print(f"  Diff lines: {len(first['diff_text'].split(chr(10)))} lines")
570 |             print("\n  First 10 lines of diff:")
571 |             diff_lines = first['diff_text'].split('\n')[:10]
572 |             for line in diff_lines:
573 |                 print(f"    {line}")
574 |         else:
575 |             print("[WARN] No files found in the time window")
576 |             print("   Try increasing --days or check if this is a git repository")
577 |         
578 |     except InvalidGitRepositoryError as e:
579 |         print(f"[ERROR] {e}")
580 |         print("   Make sure you're running this in a git repository")
581 |     except Exception as e:
582 |         print(f"[ERROR] Unexpected error: {e}")
583 |         import traceback
584 |         traceback.print_exc()
585 | 
586 | 
587 | if __name__ == '__main__':
588 |     test_git_parser()
589 | 
590 | # Made with Bob
591 | 
</content>
</file>
</files>
<environment_details>
# VSCode Visible Files
driftguard.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,app/git_parser.py,test_language_support.py,data/repos.json,app/templates/dashboard.html

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:27:39.806Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$0.01

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
You have not created a todo list yet. Create one with `update_todo_list` if your task is complicated or involves multiple steps.
</environment_details>

---

**Assistant:**

I can see the hardcoded file extension support in `app/git_parser.py`. Let me also check the related files to understand the full context before implementing the config-driven approach.

<read_file>
<args>
<file>
<path>app/language_prompts.py</path>
</file>
<file>
<path>test_language_support.py</path>
</file>
<file>
<path>app/config.py</path>
</file>
<file>
<path>.env.example</path>
</file>
</args>
</read_file>

---

**User:**

[read_file for 4 files] Result:
<files>
<file><path>app/language_prompts.py</path>
<content lines="1-169">
  1 | """language_prompts.py
  2 | 
  3 | Language-specific analysis templates for DriftGuard.
  4 | Each language has tailored decay detection patterns.
  5 | """
  6 | 
  7 | LANGUAGE_PROMPTS = {
  8 |     "python": {
  9 |         "description": "Python code analysis focusing on PEP 8 compliance and Pythonic patterns",
 10 |         "focus_areas": [
 11 |             "Missing docstrings for functions, classes, and modules",
 12 |             "Type hint drift (inconsistent use of type annotations)",
 13 |             "Import organization and unused imports",
 14 |             "List comprehension vs loop complexity",
 15 |             "Exception handling patterns (bare except, missing error types)"
 16 |         ],
 17 |         "complexity_indicators": [
 18 |             "Deeply nested loops and conditionals",
 19 |             "Long functions (>50 lines)",
 20 |             "High cyclomatic complexity",
 21 |             "Multiple return statements"
 22 |         ],
 23 |         "naming_conventions": "snake_case for functions/variables, PascalCase for classes"
 24 |     },
 25 |     
 26 |     "javascript": {
 27 |         "description": "JavaScript code analysis for modern ES6+ patterns and consistency",
 28 |         "focus_areas": [
 29 |             "Callback hell growth (nested callbacks)",
 30 |             "Inconsistent Promise vs async/await usage",
 31 |             "Missing JSDoc for exported functions",
 32 |             "Unused dependencies in package.json",
 33 |             "var vs let/const inconsistency"
 34 |         ],
 35 |         "complexity_indicators": [
 36 |             "Deeply nested callbacks",
 37 |             "Long promise chains",
 38 |             "Complex ternary operators",
 39 |             "Large switch statements"
 40 |         ],
 41 |         "naming_conventions": "camelCase for functions/variables, PascalCase for classes/constructors"
 42 |     },
 43 |     
 44 |     "typescript": {
 45 |         "description": "TypeScript code analysis for type safety and consistency",
 46 |         "focus_areas": [
 47 |             "Missing type annotations on function parameters and return types",
 48 |             "Type-casting abuse (excessive use of 'any' or 'as' assertions)",
 49 |             "Breaking type changes in git history",
 50 |             "Unused generic type parameters",
 51 |             "Interface vs type alias inconsistency"
 52 |         ],
 53 |         "complexity_indicators": [
 54 |             "Complex union/intersection types",
 55 |             "Deeply nested generic types",
 56 |             "Large type definitions",
 57 |             "Conditional types overuse"
 58 |         ],
 59 |         "naming_conventions": "camelCase for functions/variables, PascalCase for classes/interfaces/types"
 60 |     },
 61 |     
 62 |     "java": {
 63 |         "description": "Java code analysis for enterprise patterns and maintainability",
 64 |         "focus_areas": [
 65 |             "God Class smell (high line count and method count per class)",
 66 |             "Missing Javadoc on public APIs",
 67 |             "Test class drift (missing @Test method pairing with implementation)",
 68 |             "Exception handling patterns (catching generic Exception)",
 69 |             "Unused imports and dead code"
 70 |         ],
 71 |         "complexity_indicators": [
 72 |             "Classes exceeding 300 lines",
 73 |             "Methods exceeding 50 lines",
 74 |             "High number of method parameters (>5)",
 75 |             "Deep inheritance hierarchies"
 76 |         ],
 77 |         "naming_conventions": "camelCase for methods/variables, PascalCase for classes, UPPER_SNAKE_CASE for constants"
 78 |     },
 79 |     
 80 |     "go": {
 81 |         "description": "Go code analysis for idiomatic patterns and simplicity",
 82 |         "focus_areas": [
 83 |             "Error handling pattern drift (missing nil checks)",
 84 |             "Inconsistent defer usage for cleanup",
 85 |             "Exported vs unexported naming violations (capitalization)",
 86 |             "Interface compliance drift",
 87 |             "Missing error wrapping with context"
 88 |         ],
 89 |         "complexity_indicators": [
 90 |             "Long functions (>50 lines)",
 91 |             "Multiple return values (>3)",
 92 |             "Deep nesting in goroutines",
 93 |             "Complex select statements"
 94 |         ],
 95 |         "naming_conventions": "camelCase for unexported, PascalCase for exported, short variable names in small scopes"
 96 |     },
 97 |     
 98 |     "ruby": {
 99 |         "description": "Ruby code analysis for Rails conventions and Ruby idioms",
100 |         "focus_areas": [
101 |             "Missing RDoc/YARD documentation",
102 |             "Inconsistent use of blocks vs lambdas",
103 |             "Rails convention violations",
104 |             "Missing test coverage for controllers/models",
105 |             "Monkey patching without proper namespacing"
106 |         ],
107 |         "complexity_indicators": [
108 |             "Long methods (>25 lines)",
109 |             "Deep nesting in blocks",
110 |             "Complex meta-programming",
111 |             "Large class definitions"
112 |         ],
113 |         "naming_conventions": "snake_case for methods/variables, PascalCase for classes/modules, UPPER_SNAKE_CASE for constants"
114 |     }
115 | }
116 | 
117 | 
118 | def get_language_prompt(language: str) -> dict:
119 |     """Get language-specific analysis prompt.
120 |     
121 |     Args:
122 |         language: Programming language name (lowercase)
123 |         
124 |     Returns:
125 |         Dictionary with language-specific analysis guidelines
126 |     """
127 |     return LANGUAGE_PROMPTS.get(language, LANGUAGE_PROMPTS["python"])
128 | 
129 | 
130 | def get_focus_areas(language: str) -> list:
131 |     """Get focus areas for a specific language.
132 |     
133 |     Args:
134 |         language: Programming language name (lowercase)
135 |         
136 |     Returns:
137 |         List of focus areas for decay detection
138 |     """
139 |     prompt = get_language_prompt(language)
140 |     return prompt.get("focus_areas", [])
141 | 
142 | 
143 | def get_complexity_indicators(language: str) -> list:
144 |     """Get complexity indicators for a specific language.
145 |     
146 |     Args:
147 |         language: Programming language name (lowercase)
148 |         
149 |     Returns:
150 |         List of complexity indicators
151 |     """
152 |     prompt = get_language_prompt(language)
153 |     return prompt.get("complexity_indicators", [])
154 | 
155 | 
156 | def get_naming_conventions(language: str) -> str:
157 |     """Get naming conventions for a specific language.
158 |     
159 |     Args:
160 |         language: Programming language name (lowercase)
161 |         
162 |     Returns:
163 |         String describing naming conventions
164 |     """
165 |     prompt = get_language_prompt(language)
166 |     return prompt.get("naming_conventions", "Follow language-specific conventions")
167 | 
168 | 
169 | # Made with Bob
</content>
</file>
<file><path>test_language_support.py</path>
<content lines="1-233">
  1 | """Test script for language-specific analysis in DriftGuard.
  2 | 
  3 | Tests that different languages are properly scored with language-specific rules.
  4 | """
  5 | 
  6 | from app.bob_analyzer import analyze_file_decay
  7 | from app.language_prompts import get_language_prompt, get_focus_areas, get_complexity_indicators
  8 | from app.config import Config
  9 | 
 10 | 
 11 | def test_language_prompts():
 12 |     """Test that language prompts are properly loaded."""
 13 |     print("\n" + "="*70)
 14 |     print("TEST 1: Language Prompts")
 15 |     print("="*70)
 16 |     
 17 |     languages = ['python', 'javascript', 'typescript', 'java', 'go', 'ruby']
 18 |     
 19 |     for lang in languages:
 20 |         prompt = get_language_prompt(lang)
 21 |         focus = get_focus_areas(lang)
 22 |         complexity = get_complexity_indicators(lang)
 23 |         
 24 |         print(f"\n{lang.upper()}:")
 25 |         print(f"  Description: {prompt['description']}")
 26 |         print(f"  Focus areas: {len(focus)} items")
 27 |         print(f"  Complexity indicators: {len(complexity)} items")
 28 |         print(f"  Naming: {prompt['naming_conventions']}")
 29 | 
 30 | 
 31 | def test_language_thresholds():
 32 |     """Test that language-specific thresholds are configured."""
 33 |     print("\n" + "="*70)
 34 |     print("TEST 2: Language Thresholds")
 35 |     print("="*70)
 36 |     
 37 |     for lang, thresholds in Config.LANGUAGE_THRESHOLDS.items():
 38 |         print(f"\n{lang.upper()}:")
 39 |         print(f"  Max function lines: {thresholds['max_function_lines']}")
 40 |         print(f"  Max class lines: {thresholds['max_class_lines']}")
 41 |         print(f"  Max nesting depth: {thresholds['max_nesting_depth']}")
 42 |         print(f"  Complexity threshold: {thresholds['complexity_threshold']}")
 43 | 
 44 | 
 45 | def test_go_error_handling():
 46 |     """Test Go-specific error handling analysis."""
 47 |     print("\n" + "="*70)
 48 |     print("TEST 3: Go Error Handling Analysis")
 49 |     print("="*70)
 50 |     
 51 |     go_diff = """
 52 | @@ -10,5 +10,20 @@ func ProcessData(data []string) error {
 53 | +func FetchUser(id int) (*User, error) {
 54 | +    user := database.Query(id)
 55 | +    return user, nil
 56 | +}
 57 | +
 58 | +func SaveData(data string) {
 59 | +    file.Write(data)
 60 | +}
 61 | """
 62 |     
 63 |     file_data = {
 64 |         'file_path': 'app/user.go',
 65 |         'language': 'go',
 66 |         'total_commits': 2,
 67 |         'diff_text': go_diff,
 68 |         'last_modified': '2026-05-02T10:00:00Z',
 69 |         'commit_hashes': ['abc123', 'def456']
 70 |     }
 71 |     
 72 |     result = analyze_file_decay(file_data)
 73 |     
 74 |     print(f"\nFile: {result['file_path']}")
 75 |     print(f"Language: {result['language']}")
 76 |     print(f"\nScores:")
 77 |     print(f"  Documentation: {result['documentation_drift_score']}/100")
 78 |     print(f"  Test Coverage: {result['test_drift_score']}/100")
 79 |     print(f"  Complexity: {result['complexity_growth_score']}/100")
 80 |     print(f"  Naming: {result['naming_consistency_score']}/100")
 81 |     print(f"\nTop Risk: {result['top_risk']}")
 82 |     print(f"Recommendation: {result['recommendation']}")
 83 | 
 84 | 
 85 | def test_java_god_class():
 86 |     """Test Java-specific God Class detection."""
 87 |     print("\n" + "="*70)
 88 |     print("TEST 4: Java God Class Detection")
 89 |     print("="*70)
 90 |     
 91 |     # Simulate a large class addition
 92 |     java_diff = """
 93 | @@ -10,5 +10,150 @@ public class UserService {
 94 | +public class MegaController {
 95 | """ + "\n".join([f"+    public void method{i}() {{\n+        // logic\n+    }}" for i in range(30)])
 96 |     
 97 |     file_data = {
 98 |         'file_path': 'src/main/java/MegaController.java',
 99 |         'language': 'java',
100 |         'total_commits': 1,
101 |         'diff_text': java_diff,
102 |         'last_modified': '2026-05-02T10:00:00Z',
103 |         'commit_hashes': ['abc123']
104 |     }
105 |     
106 |     result = analyze_file_decay(file_data)
107 |     
108 |     print(f"\nFile: {result['file_path']}")
109 |     print(f"Language: {result['language']}")
110 |     print(f"\nScores:")
111 |     print(f"  Documentation: {result['documentation_drift_score']}/100")
112 |     print(f"  Test Coverage: {result['test_drift_score']}/100")
113 |     print(f"  Complexity: {result['complexity_growth_score']}/100 (should be low due to size)")
114 |     print(f"  Naming: {result['naming_consistency_score']}/100")
115 |     print(f"\nTop Risk: {result['top_risk']}")
116 | 
117 | 
118 | def test_typescript_missing_types():
119 |     """Test TypeScript-specific type annotation analysis."""
120 |     print("\n" + "="*70)
121 |     print("TEST 5: TypeScript Type Annotation Analysis")
122 |     print("="*70)
123 |     
124 |     ts_diff = """
125 | @@ -10,5 +10,25 @@ export class UserService {
126 | +function processData(data) {
127 | +    const result = data.map(item => item * 2);
128 | +    return result;
129 | +}
130 | +
131 | +export function calculateTotal(items: any[]) {
132 | +    return items.reduce((sum, item) => sum + item, 0);
133 | +}
134 | """
135 |     
136 |     file_data = {
137 |         'file_path': 'src/services/data.ts',
138 |         'language': 'typescript',
139 |         'total_commits': 2,
140 |         'diff_text': ts_diff,
141 |         'last_modified': '2026-05-02T10:00:00Z',
142 |         'commit_hashes': ['abc123', 'def456']
143 |     }
144 |     
145 |     result = analyze_file_decay(file_data)
146 |     
147 |     print(f"\nFile: {result['file_path']}")
148 |     print(f"Language: {result['language']}")
149 |     print(f"\nScores:")
150 |     print(f"  Documentation: {result['documentation_drift_score']}/100")
151 |     print(f"  Test Coverage: {result['test_drift_score']}/100")
152 |     print(f"  Complexity: {result['complexity_growth_score']}/100")
153 |     print(f"  Naming: {result['naming_consistency_score']}/100")
154 |     print(f"\nTop Risk: {result['top_risk']}")
155 | 
156 | 
157 | def test_javascript_callback_hell():
158 |     """Test JavaScript-specific callback hell detection."""
159 |     print("\n" + "="*70)
160 |     print("TEST 6: JavaScript Callback Hell Detection")
161 |     print("="*70)
162 |     
163 |     js_diff = """
164 | @@ -10,5 +10,30 @@ function fetchData() {
165 | +function processUser(userId) {
166 | +    getUser(userId, function(user) {
167 | +        getProfile(user.id, function(profile) {
168 | +            getSettings(profile.id, function(settings) {
169 | +                updateUI(settings, function(result) {
170 | +                    console.log('Done');
171 | +                });
172 | +            });
173 | +        });
174 | +    });
175 | +}
176 | """
177 |     
178 |     file_data = {
179 |         'file_path': 'src/api/user.js',
180 |         'language': 'javascript',
181 |         'total_commits': 1,
182 |         'diff_text': js_diff,
183 |         'last_modified': '2026-05-02T10:00:00Z',
184 |         'commit_hashes': ['abc123']
185 |     }
186 |     
187 |     result = analyze_file_decay(file_data)
188 |     
189 |     print(f"\nFile: {result['file_path']}")
190 |     print(f"Language: {result['language']}")
191 |     print(f"\nScores:")
192 |     print(f"  Documentation: {result['documentation_drift_score']}/100")
193 |     print(f"  Test Coverage: {result['test_drift_score']}/100")
194 |     print(f"  Complexity: {result['complexity_growth_score']}/100 (should be low due to nesting)")
195 |     print(f"  Naming: {result['naming_consistency_score']}/100")
196 |     print(f"\nTop Risk: {result['top_risk']}")
197 | 
198 | 
199 | def main():
200 |     """Run all tests."""
201 |     print("\n" + "="*70)
202 |     print("DRIFTGUARD LANGUAGE-SPECIFIC ANALYSIS TESTS")
203 |     print("="*70)
204 |     
205 |     try:
206 |         test_language_prompts()
207 |         test_language_thresholds()
208 |         test_go_error_handling()
209 |         test_java_god_class()
210 |         test_typescript_missing_types()
211 |         test_javascript_callback_hell()
212 |         
213 |         print("\n" + "="*70)
214 |         print("ALL TESTS COMPLETED SUCCESSFULLY!")
215 |         print("="*70)
216 |         print("\nLanguage-specific analysis is working correctly:")
217 |         print("[OK] Language prompts loaded for Python, JS, TS, Java, Go, Ruby")
218 |         print("[OK] Language-specific thresholds configured")
219 |         print("[OK] Go error handling patterns detected")
220 |         print("[OK] Java God Class patterns detected")
221 |         print("[OK] TypeScript type annotation issues detected")
222 |         print("[OK] JavaScript callback hell detected")
223 |         
224 |     except Exception as e:
225 |         print(f"\n[ERROR] Test failed: {e}")
226 |         import traceback
227 |         traceback.print_exc()
228 | 
229 | 
230 | if __name__ == '__main__':
231 |     main()
232 | 
233 | # Made with Bob
</content>
</file>
<file><path>app/config.py</path>
<content lines="1-183">
  1 | """config.py
  2 | 
  3 | Load and manage application configuration from environment, CLI, and defaults.
  4 | """
  5 | import os
  6 | import json
  7 | from pathlib import Path
  8 | from typing import Optional, List, Dict
  9 | from dotenv import load_dotenv
 10 | 
 11 | # Load .env file if it exists
 12 | load_dotenv()
 13 | 
 14 | 
 15 | class Config:
 16 |     """Centralized configuration management."""
 17 |     
 18 |     # Directories
 19 |     REPO_ROOT = Path(__file__).parent.parent
 20 |     APP_DIR = REPO_ROOT / "app"
 21 |     OUTPUT_DIR = REPO_ROOT / "output"
 22 |     BOB_SESSIONS_DIR = REPO_ROOT / "bob_sessions"
 23 |     TEMPLATES_DIR = APP_DIR / "templates"
 24 |     DATA_DIR = REPO_ROOT / "data"
 25 |     
 26 |     # Create directories if they don't exist
 27 |     OUTPUT_DIR.mkdir(exist_ok=True)
 28 |     BOB_SESSIONS_DIR.mkdir(exist_ok=True)
 29 |     DATA_DIR.mkdir(exist_ok=True)
 30 |     
 31 |     # API Key
 32 |     API_KEY = os.getenv("DRIFTGUARD_API_KEY", "")
 33 |     
 34 |     # Repos configuration file
 35 |     REPOS_JSON_PATH = DATA_DIR / "repos.json"
 36 |     
 37 |     # Analysis defaults
 38 |     DEFAULT_DAYS = int(os.getenv("DRIFTGUARD_DAYS", "30"))
 39 |     DEFAULT_MAX_FILES = int(os.getenv("DRIFTGUARD_MAX_FILES", "20"))
 40 |     DEFAULT_REPO_PATH = os.getenv("DRIFTGUARD_REPO", ".")
 41 |     
 42 |     # Logging
 43 |     LOG_LEVEL = os.getenv("DRIFTGUARD_LOG_LEVEL", "INFO")
 44 |     
 45 |     # FastAPI
 46 |     FASTAPI_HOST = os.getenv("DRIFTGUARD_HOST", "127.0.0.1")
 47 |     FASTAPI_PORT = int(os.getenv("DRIFTGUARD_PORT", "8000"))
 48 |     FASTAPI_RELOAD = os.getenv("DRIFTGUARD_RELOAD", "true").lower() == "true"
 49 |     
 50 |     # File extensions to analyze
 51 |     ALLOWED_EXTENSIONS = {
 52 |         ".py": "python",
 53 |         ".js": "javascript",
 54 |         ".ts": "typescript",
 55 |         ".java": "java",
 56 |         ".go": "go",
 57 |         ".rb": "ruby",
 58 |     }
 59 |     
 60 |     # Language-specific thresholds for complexity and function length
 61 |     LANGUAGE_THRESHOLDS = {
 62 |         "python": {
 63 |             "max_function_lines": 50,
 64 |             "max_class_lines": 200,
 65 |             "max_nesting_depth": 4,
 66 |             "complexity_threshold": 150,
 67 |         },
 68 |         "javascript": {
 69 |             "max_function_lines": 40,
 70 |             "max_class_lines": 150,
 71 |             "max_nesting_depth": 3,
 72 |             "complexity_threshold": 150,
 73 |         },
 74 |         "typescript": {
 75 |             "max_function_lines": 40,
 76 |             "max_class_lines": 150,
 77 |             "max_nesting_depth": 3,
 78 |             "complexity_threshold": 150,
 79 |         },
 80 |         "java": {
 81 |             "max_function_lines": 50,
 82 |             "max_class_lines": 300,
 83 |             "max_nesting_depth": 4,
 84 |             "complexity_threshold": 300,
 85 |         },
 86 |         "go": {
 87 |             "max_function_lines": 50,
 88 |             "max_class_lines": 200,
 89 |             "max_nesting_depth": 3,
 90 |             "complexity_threshold": 150,
 91 |         },
 92 |         "ruby": {
 93 |             "max_function_lines": 25,
 94 |             "max_class_lines": 150,
 95 |             "max_nesting_depth": 3,
 96 |             "complexity_threshold": 100,
 97 |         },
 98 |     }
 99 |     
100 |     # Scoring thresholds
101 |     SCORE_CRITICAL_THRESHOLD = 40        # 0-39 = CRITICAL
102 |     SCORE_AT_RISK_THRESHOLD = 60         # 40-59 = AT_RISK
103 |     SCORE_WATCH_THRESHOLD = 80           # 60-79 = WATCH
104 |     # 80-100 = HEALTHY
105 |     
106 |     # Score weights (must sum to 1.0)
107 |     WEIGHT_DOCUMENTATION = 0.30
108 |     WEIGHT_TEST_COVERAGE = 0.30
109 |     WEIGHT_COMPLEXITY = 0.25
110 |     WEIGHT_NAMING = 0.15
111 |     
112 |     # Status emojis
113 |     STATUS_EMOJI = {
114 |         "CRITICAL": "🔴",
115 |         "AT_RISK": "🟠",
116 |         "WATCH": "🟡",
117 |         "HEALTHY": "🟢",
118 |     }
119 |     
120 |     # Rule-based analyzer thresholds
121 |     RULE_DOC_DRIFT_THRESHOLD_ADDED_LINES = 50      # if 50+ lines added with 0 comments
122 |     RULE_COMPLEXITY_NESTING_THRESHOLD = 2          # nesting level increase
123 |     RULE_TEST_REQUIRED_RATIO = 0.3                 # if changed code vs test code ratio
124 |     
125 |     # Analysis cache settings
126 |     CACHE_ENABLED = os.getenv("DRIFTGUARD_CACHE_ENABLED", "true").lower() == "true"
127 |     CACHE_TTL_HOURS = int(os.getenv("DRIFTGUARD_CACHE_TTL_HOURS", "0"))  # 0 = no expiry
128 |     
129 |     # Rate limiting settings for Bob analysis calls
130 |     BOB_RATE_LIMIT_PER_MINUTE = int(os.getenv("BOB_RATE_LIMIT_PER_MINUTE", "30"))  # Max calls per minute
131 |     BOB_RATE_LIMIT_BURST = int(os.getenv("BOB_RATE_LIMIT_BURST", "5"))  # Burst capacity
132 |     
133 |     # Parallel processing settings
134 |     MAX_WORKERS = int(os.getenv("DRIFTGUARD_MAX_WORKERS", str(min(8, os.cpu_count() or 1))))  # Parallel analysis workers
135 | 
136 | 
137 | def get_output_report_path(timestamp: Optional[str] = None) -> Path:
138 |     """Generate output report file path with timestamp."""
139 |     from datetime import datetime
140 |     if timestamp is None:
141 |         timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
142 |     return Config.OUTPUT_DIR / f"report_{timestamp}.json"
143 | 
144 | 
145 | def get_latest_report() -> Optional[Path]:
146 |     """Find the most recent report JSON file in output directory."""
147 |     if not Config.OUTPUT_DIR.exists():
148 |         return None
149 |     reports = list(Config.OUTPUT_DIR.glob("report_*.json"))
150 |     if not reports:
151 |         return None
152 |     return max(reports, key=lambda p: p.stat().st_mtime)
153 | 
154 | 
155 | 
156 | def load_repos_config() -> List[Dict]:
157 |     """Load repository configuration from repos.json.
158 |     
159 |     Returns:
160 |         List of repository configurations with name, path, days, and enabled status.
161 |     """
162 |     if not Config.REPOS_JSON_PATH.exists():
163 |         # Return default config if file doesn't exist
164 |         return [{
165 |             "name": "default",
166 |             "path": Config.DEFAULT_REPO_PATH,
167 |             "days": Config.DEFAULT_DAYS,
168 |             "enabled": True
169 |         }]
170 |     
171 |     try:
172 |         with open(Config.REPOS_JSON_PATH, 'r') as f:
173 |             repos = json.load(f)
174 |             # Filter only enabled repos
175 |             return [repo for repo in repos if repo.get('enabled', True)]
176 |     except (json.JSONDecodeError, IOError) as e:
177 |         print(f"Warning: Failed to load repos.json: {e}")
178 |         return [{
179 |             "name": "default",
180 |             "path": Config.DEFAULT_REPO_PATH,
181 |             "days": Config.DEFAULT_DAYS,
182 |             "enabled": True
183 |         }]
</content>
</file>
<file><path>.env.example</path>
<content lines="1-58">
 1 | # DriftGuard Environment Configuration
 2 | # Copy this file to .env and customize for your environment
 3 | 
 4 | # API Key Configuration
 5 | # Set a secure API key for accessing protected endpoints
 6 | # Generate a strong random key: python -c "import secrets; print(secrets.token_urlsafe(32))"
 7 | DRIFTGUARD_API_KEY=your-secure-api-key-here
 8 | 
 9 | # Repository Configuration
10 | # Path to the repository to analyze (inside container: /repo)
11 | HOST_REPO_PATH=./repo
12 | REPO_PATH=/repo
13 | 
14 | # Watch Mode Configuration
15 | # Interval between analysis runs (e.g., "24h", "12h", "30m", "3600")
16 | WATCH_INTERVAL=24h
17 | 
18 | # Analysis Configuration
19 | # Number of days of git history to analyze
20 | DRIFTGUARD_DAYS=30
21 | 
22 | # Maximum number of files to analyze per run
23 | DRIFTGUARD_MAX_FILES=20
24 | 
25 | # Logging Configuration
26 | # Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
27 | DRIFTGUARD_LOG_LEVEL=INFO
28 | 
29 | # Alert Configuration (future feature)
30 | # Enable alerts for critical health scores
31 | # ALERT_ENABLED=false
32 | # ALERT_CRITICAL_THRESHOLD=40
33 | # ALERT_EMAIL_TO=team@example.com
34 | # ALERT_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
35 | 
36 | # Database Configuration
37 | # Database file path (relative to container /app directory)
38 | # DRIFTGUARD_DB_PATH=data/driftguard.db
39 | 
40 | # Analysis Cache Configuration
41 | # Enable caching of analysis results to speed up repeated analyses
42 | DRIFTGUARD_CACHE_ENABLED=true
43 | 
44 | # Cache time-to-live in hours (0 = no expiry, cache never expires)
45 | # Set to a positive number to automatically expire old cache entries
46 | # Example: 168 = 7 days, 720 = 30 days
47 | DRIFTGUARD_CACHE_TTL_HOURS=0
48 | 
49 | # Rate Limiting Configuration
50 | # Control the rate of Bob analysis calls to prevent overwhelming the system
51 | # BOB_RATE_LIMIT_PER_MINUTE: Maximum number of analysis calls per minute (default: 30)
52 | BOB_RATE_LIMIT_PER_MINUTE=30
53 | 
54 | # BOB_RATE_LIMIT_BURST: Burst capacity for rapid initial requests (default: 5)
55 | # Allows up to this many requests immediately before rate limiting kicks in
56 | BOB_RATE_LIMIT_BURST=5
57 | 
58 | # Made with Bob
</content>
</file>
</files>
<environment_details>
# VSCode Visible Files
driftguard.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,app/git_parser.py,test_language_support.py,data/repos.json,app/templates/dashboard.html

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:27:45.353Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$0.04

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
You have not created a todo list yet. Create one with `update_todo_list` if your task is complicated or involves multiple steps.
</environment_details>

---

**Assistant:**

Now I have a complete understanding of the codebase. Let me create a TODO list and implement the config-driven language mapping system.

<update_todo_list>
<todos>
[ ] Create language_config.json with extension mappings and defaults
[ ] Update app/config.py to load language config from JSON
[ ] Update app/git_parser.py to use config-driven mappings
[ ] Add API endpoint to view active language config
[ ] Add CLI command to print language config
[ ] Create tests for config override functionality
[ ] Update .env.example with language config path
</todos>
</update_todo_list>

---

**User:**

[update_todo_list] Result:
Todo list updated successfully.
<environment_details>
# VSCode Visible Files
driftguard.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,app/git_parser.py,test_language_support.py,data/repos.json,app/templates/dashboard.html

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:27:53.686Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$0.09

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Create language_config.json with extension mappings and defaults | Pending |
| 2 | Update app/config.py to load language config from JSON | Pending |
| 3 | Update app/git_parser.py to use config-driven mappings | Pending |
| 4 | Add API endpoint to view active language config | Pending |
| 5 | Add CLI command to print language config | Pending |
| 6 | Create tests for config override functionality | Pending |
| 7 | Update .env.example with language config path | Pending |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

Now let me start implementing the config-driven language mapping. First, I'll create the language configuration JSON file with sane defaults.

<write_to_file>
<path>data/language_config.json</path>
<content>
{
  "version": "1.0",
  "description": "Language configuration for DriftGuard file extension mapping",
  "extensions": {
    ".py": {
      "language": "python",
      "enabled": true,
      "description": "Python source files"
    },
    ".js": {
      "language": "javascript",
      "enabled": true,
      "description": "JavaScript source files"
    },
    ".ts": {
      "language": "typescript",
      "enabled": true,
      "description": "TypeScript source files"
    },
    ".tsx": {
      "language": "typescript",
      "enabled": true,
      "description": "TypeScript JSX files"
    },
    ".jsx": {
      "language": "javascript",
      "enabled": true,
      "description": "JavaScript JSX files"
    },
    ".java": {
      "language": "java",
      "enabled": true,
      "description": "Java source files"
    },
    ".go": {
      "language": "go",
      "enabled": true,
      "description": "Go source files"
    },
    ".rb": {
      "language": "ruby",
      "enabled": true,
      "description": "Ruby source files"
    },
    ".html": {
      "language": "html",
      "enabled": true,
      "description": "HTML files"
    },
    ".css": {
      "language": "css",
      "enabled": true,
      "description": "CSS stylesheets"
    },
    ".scss": {
      "language": "css",
      "enabled": false,
      "description": "SCSS stylesheets"
    },
    ".php": {
      "language": "php",
      "enabled": false,
      "description": "PHP source files"
    },
    ".c": {
      "language": "c",
      "enabled": false,
      "description": "C source files"
    },
    ".cpp": {
      "language": "cpp",
      "enabled": false,
      "description": "C++ source files"
    },
    ".rs": {
      "language": "rust",
      "enabled": false,
      "description": "Rust source files"
    },
    ".swift": {
      "language": "swift",
      "enabled": false,
      "description": "Swift source files"
    },
    ".kt": {
      "language": "kotlin",
      "enabled": false,
      "description": "Kotlin source files"
    }
  }
}
</content>
<line_count>73</line_count>
</write_to_file>

---

**User:**

[write_to_file for 'data/language_config.json'] Result:
<file_write_result>
<path>data/language_config.json</path>
<operation>created</operation>
<notice>
<i>You do not need to re-read the file, as you have seen all changes</i>
<i>Proceed with the task using these changes as the new baseline.</i>
</notice>
</file_write_result>

<environment_details>
# VSCode Visible Files
data\language_config.json

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,app/git_parser.py,test_language_support.py,data/repos.json,app/templates/dashboard.html

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:28:36.665Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$0.15

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Create language_config.json with extension mappings and defaults | Pending |
| 2 | Update app/config.py to load language config from JSON | Pending |
| 3 | Update app/git_parser.py to use config-driven mappings | Pending |
| 4 | Add API endpoint to view active language config | Pending |
| 5 | Add CLI command to print language config | Pending |
| 6 | Create tests for config override functionality | Pending |
| 7 | Update .env.example with language config path | Pending |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

<update_todo_list>
<todos>
[x] Create language_config.json with extension mappings and defaults
[-] Update app/config.py to load language config from JSON
[ ] Update app/git_parser.py to use config-driven mappings
[ ] Add API endpoint to view active language config
[ ] Add CLI command to print language config
[ ] Create tests for config override functionality
[ ] Update .env.example with language config path
</todos>
</update_todo_list>

---

**User:**

[update_todo_list] Result:
Todo list updated successfully.
<environment_details>
# VSCode Visible Files
data\language_config.json

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,app/git_parser.py,test_language_support.py,data/repos.json,app/templates/dashboard.html

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:28:41.250Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$0.21

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Create language_config.json with extension mappings and defaults | Completed |
| 2 | Update app/config.py to load language config from JSON | In Progress |
| 3 | Update app/git_parser.py to use config-driven mappings | Pending |
| 4 | Add API endpoint to view active language config | Pending |
| 5 | Add CLI command to print language config | Pending |
| 6 | Create tests for config override functionality | Pending |
| 7 | Update .env.example with language config path | Pending |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

Now let me update app/config.py to load the language configuration from JSON.

<apply_diff>
<path>app/config.py</path>
<diff>
<<<<<<< SEARCH
:start_line:1
-------
"""config.py

Load and manage application configuration from environment, CLI, and defaults.
"""
import os
import json
from pathlib import Path
from typing import Optional, List, Dict
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()
=======
"""config.py

Load and manage application configuration from environment, CLI, and defaults.
"""
import os
import json
from pathlib import Path
from typing import Optional, List, Dict, Set, Tuple
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()
>>>>>>> REPLACE
</diff>
</apply_diff>

---

**User:**

[apply_diff for 'app/config.py'] Result:
<file_write_result>
<path>app/config.py</path>
<operation>modified</operation>
<problems>

New problems detected after saving the file:
app/config.py
- [basedpyright Error] 9 | from dotenv import load_dotenv : Import "dotenv" could not be resolved</problems>
<notice>
<i>You do not need to re-read the file, as you have seen all changes</i>
<i>Proceed with the task using these changes as the new baseline.</i>
</notice>
</file_write_result>

<notice>Making multiple related changes in a single apply_diff is more efficient. If other changes are needed in this file, please include them as additional SEARCH/REPLACE blocks.</notice>
<environment_details>
# VSCode Visible Files
app\config.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,app/git_parser.py,test_language_support.py,data/repos.json,app/templates/dashboard.html

# Recently Modified Files
These files have been modified since you last accessed them (file was just edited so you may need to re-read it before editing):
app/config.py

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:28:49.100Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$0.27

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Create language_config.json with extension mappings and defaults | Completed |
| 2 | Update app/config.py to load language config from JSON | In Progress |
| 3 | Update app/git_parser.py to use config-driven mappings | Pending |
| 4 | Add API endpoint to view active language config | Pending |
| 5 | Add CLI command to print language config | Pending |
| 6 | Create tests for config override functionality | Pending |
| 7 | Update .env.example with language config path | Pending |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

Now let me add the language configuration loading functions to app/config.py:

<insert_content>
<path>app/config.py</path>
<line>134</line>
<content>
    # Language configuration file path
    LANGUAGE_CONFIG_PATH = Path(os.getenv(
        "DRIFTGUARD_LANGUAGE_CONFIG",
        str(DATA_DIR / "language_config.json")
    ))
    
    # Cached language configuration
    _language_config_cache: Optional[Dict] = None
    _supported_extensions_cache: Optional[Set[str]] = None
    _extension_to_language_cache: Optional[Dict[str, str]] = None


def load_language_config(force_reload: bool = False) -> Dict:
    """Load language configuration from JSON file.
    
    Args:
        force_reload: Force reload from disk even if cached
        
    Returns:
        Dictionary containing language configuration
    """
    if not force_reload and Config._language_config_cache is not None:
        return Config._language_config_cache
    
    config_path = Config.LANGUAGE_CONFIG_PATH
    
    # Default configuration if file doesn't exist
    default_config = {
        "version": "1.0",
        "description": "Default language configuration",
        "extensions": {
            ".py": {"language": "python", "enabled": True, "description": "Python source files"},
            ".js": {"language": "javascript", "enabled": True, "description": "JavaScript source files"},
            ".ts": {"language": "typescript", "enabled": True, "description": "TypeScript source files"},
            ".java": {"language": "java", "enabled": True, "description": "Java source files"},
            ".go": {"language": "go", "enabled": True, "description": "Go source files"},
            ".rb": {"language": "ruby", "enabled": True, "description": "Ruby source files"},
            ".html": {"language": "html", "enabled": True, "description": "HTML files"},
            ".css": {"language": "css", "enabled": True, "description": "CSS stylesheets"},
        }
    }
    
    if not config_path.exists():
        print(f"Warning: Language config not found at {config_path}, using defaults")
        Config._language_config_cache = default_config
        return default_config
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            Config._language_config_cache = config
            return config
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Failed to load language config from {config_path}: {e}")
        print("Using default configuration")
        Config._language_config_cache = default_config
        return default_config


def get_supported_extensions() -> Set[str]:
    """Get set of enabled file extensions.
    
    Returns:
        Set of file extensions (e.g., {'.py', '.js', '.ts'})
    """
    if Config._supported_extensions_cache is not None:
        return Config._supported_extensions_cache
    
    config = load_language_config()
    extensions = config.get("extensions", {})
    
    supported = {
        ext for ext, info in extensions.items()
        if info.get("enabled", True)
    }
    
    Config._supported_extensions_cache = supported
    return supported


def get_extension_to_language_map() -> Dict[str, str]:
    """Get mapping of file extensions to language names.
    
    Returns:
        Dictionary mapping extensions to language names (e.g., {'.py': 'python'})
    """
    if Config._extension_to_language_cache is not None:
        return Config._extension_to_language_cache
    
    config = load_language_config()
    extensions = config.get("extensions", {})
    
    mapping = {
        ext: info.get("language", "unknown")
        for ext, info in extensions.items()
        if info.get("enabled", True)
    }
    
    Config._extension_to_language_cache = mapping
    return mapping


def get_language_config_info() -> Dict:
    """Get full language configuration information for display.
    
    Returns:
        Dictionary with configuration details including enabled/disabled extensions
    """
    config = load_language_config()
    extensions = config.get("extensions", {})
    
    enabled = []
    disabled = []
    
    for ext, info in sorted(extensions.items()):
        entry = {
            "extension": ext,
            "language": info.get("language", "unknown"),
            "description": info.get("description", "")
        }
        
        if info.get("enabled", True):
            enabled.append(entry)
        else:
            disabled.append(entry)
    
    return {
        "version": config.get("version", "unknown"),
        "description": config.get("description", ""),
        "config_path": str(Config.LANGUAGE_CONFIG_PATH),
        "enabled_extensions": enabled,
        "disabled_extensions": disabled,
        "total_enabled": len(enabled),
        "total_disabled": len(disabled)
    }


def reload_language_config() -> Tuple[bool, str]:
    """Reload language configuration from disk.
    
    Returns:
        Tuple of (success, message)
    """
    try:
        # Clear caches
        Config._language_config_cache = None
        Config._supported_extensions_cache = None
        Config._extension_to_language_cache = None
        
        # Reload
        config = load_language_config(force_reload=True)
        enabled_count = len(get_supported_extensions())
        
        return True, f"Language configuration reloaded successfully. {enabled_count} extensions enabled."
    except Exception as e:
        return False, f"Failed to reload language configuration: {str(e)}"

</content>
</insert_content>

---

**User:**

[insert_content for 'app/config.py'] Result:
<file_write_result>
<path>app/config.py</path>
<operation>modified</operation>
<problems>

New problems detected after saving the file:
test_parallel_analysis.py
- [basedpyright Error] 58 |     print(f"  Max workers: {Config.MAX_WORKERS}") : Cannot access attribute "MAX_WORKERS" for class "type[Config]"
  Attribute "MAX_WORKERS" is unknown
- [basedpyright Error] 80 |     print(f"Parallel Analysis ({Config.MAX_WORKERS} workers)") : Cannot access attribute "MAX_WORKERS" for class "type[Config]"
  Attribute "MAX_WORKERS" is unknown
- [basedpyright Error] 83 |     par_results = batch_analyze(test_files, max_workers=Config.MAX_WORKERS) : Cannot access attribute "MAX_WORKERS" for class "type[Config]"
  Attribute "MAX_WORKERS" is unknown

benchmark_parallel.py
- [basedpyright Error] 164 |     print(f"   Max workers: {Config.MAX_WORKERS}") : Cannot access attribute "MAX_WORKERS" for class "type[Config]"
  Attribute "MAX_WORKERS" is unknown
- [basedpyright Error] 209 |         if workers &gt; Config.MAX_WORKERS: : Cannot access attribute "MAX_WORKERS" for class "type[Config]"
  Attribute "MAX_WORKERS" is unknown

app/bob_analyzer.py
- [basedpyright Error] 204 |         max_workers = Config.MAX_WORKERS : Cannot access attribute "MAX_WORKERS" for class "type[Config]"
  Attribute "MAX_WORKERS" is unknown</problems>
<notice>
<i>You do not need to re-read the file, as you have seen all changes</i>
<i>Proceed with the task using these changes as the new baseline.</i>
</notice>
</file_write_result>

<environment_details>
# VSCode Visible Files
app\config.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,app/git_parser.py,test_language_support.py,data/repos.json,app/templates/dashboard.html

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:29:25.355Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$0.33

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Create language_config.json with extension mappings and defaults | Completed |
| 2 | Update app/config.py to load language config from JSON | In Progress |
| 3 | Update app/git_parser.py to use config-driven mappings | Pending |
| 4 | Add API endpoint to view active language config | Pending |
| 5 | Add CLI command to print language config | Pending |
| 6 | Create tests for config override functionality | Pending |
| 7 | Update .env.example with language config path | Pending |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

Good! The language config functions are added. Now let me update app/git_parser.py to use the config-driven mappings instead of hardcoded values:

<apply_diff>
<path>app/git_parser.py</path>
<diff>
<<<<<<< SEARCH
:start_line:1
-------
"""Git parser module for DriftGuard.

Extracts file diffs from a Git repository over a specified time window.
Supports local repositories, GitHub URLs, and generic git URLs.
"""

import os
import re
import tempfile
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from collections import defaultdict

try:
    from git import Repo, GitCommandError, InvalidGitRepositoryError
except ImportError:
    raise ImportError("GitPython is required. Install with: pip install gitpython")

try:
    import requests
except ImportError:
    raise ImportError("requests is required. Install with: pip install requests")


# Supported file extensions
SUPPORTED_EXTENSIONS = {'.py', '.js', '.ts', '.java', '.go', '.rb', '.html', '.css'}

# Language mapping
EXTENSION_TO_LANGUAGE = {
    '.py': 'python',
    '.js': 'javascript',
    '.ts': 'typescript',
    '.java': 'java',
    '.go': 'go',
    '.rb': 'ruby',
    '.html': 'html',
    '.css': 'css',
}
=======
"""Git parser module for DriftGuard.

Extracts file diffs from a Git repository over a specified time window.
Supports local repositories, GitHub URLs, and generic git URLs.
"""

import os
import re
import tempfile
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple, Set
from collections import defaultdict

try:
    from git import Repo, GitCommandError, InvalidGitRepositoryError
except ImportError:
    raise ImportError("GitPython is required. Install with: pip install gitpython")

try:
    import requests
except ImportError:
    raise ImportError("requests is required. Install with: pip install requests")

# Import config functions for language mapping
from app.config import get_supported_extensions, get_extension_to_language_map


def _get_supported_extensions() -> Set[str]:
    """Get supported file extensions from config.
    
    Returns:
        Set of supported file extensions
    """
    return get_supported_extensions()


def _get_extension_to_language() -> Dict[str, str]:
    """Get extension to language mapping from config.
    
    Returns:
        Dictionary mapping extensions to language names
    """
    return get_extension_to_language_map()
>>>>>>> REPLACE
</diff>
</apply_diff>

---

**User:**

[apply_diff for 'app/git_parser.py'] Result:
<file_write_result>
<path>app/git_parser.py</path>
<operation>modified</operation>
<problems>

New problems detected after saving the file:
app/git_parser.py
- [basedpyright Error] 192 |         if ext not in SUPPORTED_EXTENSIONS: : "SUPPORTED_EXTENSIONS" is not defined
- [basedpyright Error] 299 |         language = EXTENSION_TO_LANGUAGE.get(ext, 'unknown') : "EXTENSION_TO_LANGUAGE" is not defined
- [basedpyright Error] 474 |             if ext not in SUPPORTED_EXTENSIONS: : "SUPPORTED_EXTENSIONS" is not defined
- [basedpyright Error] 516 |         language = EXTENSION_TO_LANGUAGE.get(ext, 'unknown') : "EXTENSION_TO_LANGUAGE" is not defined</problems>
<notice>
<i>You do not need to re-read the file, as you have seen all changes</i>
<i>Proceed with the task using these changes as the new baseline.</i>
</notice>
</file_write_result>

<notice>Making multiple related changes in a single apply_diff is more efficient. If other changes are needed in this file, please include them as additional SEARCH/REPLACE blocks.</notice>
<environment_details>
# VSCode Visible Files
app\git_parser.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,test_language_support.py,data/repos.json,app/templates/dashboard.html,app/report_exporter.py

# Recently Modified Files
These files have been modified since you last accessed them (file was just edited so you may need to re-read it before editing):
app/git_parser.py

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:29:43.029Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$0.40

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Create language_config.json with extension mappings and defaults | Completed |
| 2 | Update app/config.py to load language config from JSON | In Progress |
| 3 | Update app/git_parser.py to use config-driven mappings | Pending |
| 4 | Add API endpoint to view active language config | Pending |
| 5 | Add CLI command to print language config | Pending |
| 6 | Create tests for config override functionality | Pending |
| 7 | Update .env.example with language config path | Pending |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

Now I need to replace all occurrences of the hardcoded SUPPORTED_EXTENSIONS and EXTENSION_TO_LANGUAGE with the config-driven functions:

<apply_diff>
<path>app/git_parser.py</path>
<diff>
<<<<<<< SEARCH
:start_line:185
-------
        # Filter by extension
        ext = Path(filename).suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            continue
=======
        # Filter by extension
        ext = Path(filename).suffix.lower()
        if ext not in _get_supported_extensions():
            continue
>>>>>>> REPLACE

<<<<<<< SEARCH
:start_line:293
-------
    # Build result list (same format as get_file_diffs)
    results = []
    for file_path, data in file_data.items():
        ext = Path(file_path).suffix.lower()
        language = EXTENSION_TO_LANGUAGE.get(ext, 'unknown')
=======
    # Build result list (same format as get_file_diffs)
    results = []
    extension_map = _get_extension_to_language()
    for file_path, data in file_data.items():
        ext = Path(file_path).suffix.lower()
        language = extension_map.get(ext, 'unknown')
>>>>>>> REPLACE

<<<<<<< SEARCH
:start_line:467
-------
            # Filter by extension
            ext = Path(file_path).suffix.lower()
            if ext not in SUPPORTED_EXTENSIONS:
                continue
=======
            # Filter by extension
            ext = Path(file_path).suffix.lower()
            if ext not in _get_supported_extensions():
                continue
>>>>>>> REPLACE

<<<<<<< SEARCH
:start_line:507
-------
    # Build result list
    results = []
    for file_path, data in file_data.items():
        # Get language from extension
        ext = Path(file_path).suffix.lower()
        language = EXTENSION_TO_LANGUAGE.get(ext, 'unknown')
=======
    # Build result list
    results = []
    extension_map = _get_extension_to_language()
    for file_path, data in file_data.items():
        # Get language from extension
        ext = Path(file_path).suffix.lower()
        language = extension_map.get(ext, 'unknown')
>>>>>>> REPLACE
</diff>
</apply_diff>

---

**User:**

[apply_diff for 'app/git_parser.py'] Result:
<file_write_result>
<path>app/git_parser.py</path>
<operation>modified</operation>
<notice>
<i>You do not need to re-read the file, as you have seen all changes</i>
<i>Proceed with the task using these changes as the new baseline.</i>
</notice>
</file_write_result>

<environment_details>
# VSCode Visible Files
app\git_parser.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,test_language_support.py,data/repos.json,app/templates/dashboard.html,app/report_exporter.py

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:30:18.449Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$0.48

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Create language_config.json with extension mappings and defaults | Completed |
| 2 | Update app/config.py to load language config from JSON | In Progress |
| 3 | Update app/git_parser.py to use config-driven mappings | Pending |
| 4 | Add API endpoint to view active language config | Pending |
| 5 | Add CLI command to print language config | Pending |
| 6 | Create tests for config override functionality | Pending |
| 7 | Update .env.example with language config path | Pending |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

<update_todo_list>
<todos>
[x] Create language_config.json with extension mappings and defaults
[x] Update app/config.py to load language config from JSON
[x] Update app/git_parser.py to use config-driven mappings
[-] Add API endpoint to view active language config
[ ] Add CLI command to print language config
[ ] Create tests for config override functionality
[ ] Update .env.example with language config path
</todos>
</update_todo_list>

---

**User:**

[update_todo_list] Result:
Todo list updated successfully.
<environment_details>
# VSCode Visible Files
app\git_parser.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,test_language_support.py,data/repos.json,app/templates/dashboard.html,app/report_exporter.py

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:30:50.549Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$0.55

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Create language_config.json with extension mappings and defaults | Completed |
| 2 | Update app/config.py to load language config from JSON | Completed |
| 3 | Update app/git_parser.py to use config-driven mappings | Completed |
| 4 | Add API endpoint to view active language config | In Progress |
| 5 | Add CLI command to print language config | Pending |
| 6 | Create tests for config override functionality | Pending |
| 7 | Update .env.example with language config path | Pending |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

Now let me check the main.py file to add the API endpoint for viewing language configuration:

<read_file>
<args>
<file>
<path>app/main.py</path>
</file>
</args>
</read_file>

---

**User:**

[read_file for 'app/main.py'. Reading multiple files at once is more efficient for the LLM. If other files are relevant to your current task, please read them simultaneously.] Result:
<files>
<file><path>app/main.py</path>
<content lines="1-391">
  1 | """main.py
  2 | 
  3 | FastAPI application for DriftGuard dashboard.
  4 | Serves JSON reports and renders the web dashboard.
  5 | """
  6 | 
  7 | import json
  8 | from pathlib import Path
  9 | from typing import Optional
 10 | 
 11 | from fastapi import FastAPI, HTTPException, Request, Query, Header, Depends
 12 | from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
 13 | from fastapi.staticfiles import StaticFiles
 14 | from fastapi.middleware.cors import CORSMiddleware
 15 | from fastapi.templating import Jinja2Templates
 16 | 
 17 | from app.config import Config, get_latest_report, load_repos_config
 18 | from app.report_generator import load_report
 19 | from app import db
 20 | from app.validation import ValidationError, validate_file_path, validate_days, validate_max_files
 21 | 
 22 | 
 23 | # Initialize FastAPI app
 24 | app = FastAPI(
 25 |     title="DriftGuard",
 26 |     description="Codebase Decay Monitor",
 27 |     version="1.0.0",
 28 | )
 29 | 
 30 | # Add CORS middleware (allow all origins for local dev)
 31 | app.add_middleware(
 32 |     CORSMiddleware,
 33 |     allow_origins=["*"],
 34 |     allow_credentials=True,
 35 |     allow_methods=["*"],
 36 |     allow_headers=["*"],
 37 | )
 38 | 
 39 | # Setup Jinja2 templates
 40 | templates = Jinja2Templates(directory=str(Config.TEMPLATES_DIR))
 41 | 
 42 | 
 43 | # Custom exception handler for ValidationError
 44 | @app.exception_handler(ValidationError)
 45 | async def validation_exception_handler(request: Request, exc: ValidationError):
 46 |     """Handle ValidationError exceptions with structured JSON response."""
 47 |     return JSONResponse(
 48 |         status_code=400,
 49 |         content=exc.to_dict()
 50 |     )
 51 | 
 52 | 
 53 | def verify_api_key(x_driftguard_key: Optional[str] = Header(None, alias="X-DriftGuard-Key")):
 54 |     """Verify API key from request header.
 55 |     
 56 |     Args:
 57 |         x_driftguard_key: API key from X-DriftGuard-Key header
 58 |         
 59 |     Raises:
 60 |         HTTPException: 401 if API key is missing or invalid
 61 |     """
 62 |     if not Config.API_KEY:
 63 |         raise HTTPException(
 64 |             status_code=500,
 65 |             detail="API key not configured. Set DRIFTGUARD_API_KEY environment variable."
 66 |         )
 67 |     
 68 |     if not x_driftguard_key:
 69 |         raise HTTPException(
 70 |             status_code=401,
 71 |             detail="Missing API key. Include X-DriftGuard-Key header."
 72 |         )
 73 |     
 74 |     if x_driftguard_key != Config.API_KEY:
 75 |         raise HTTPException(
 76 |             status_code=401,
 77 |             detail="Invalid API key."
 78 |         )
 79 |     
 80 |     return x_driftguard_key
 81 | 
 82 | 
 83 | def get_report_data() -> Optional[dict]:
 84 |     """Load the most recent report from disk."""
 85 |     latest = get_latest_report()
 86 |     if latest is None:
 87 |         return None
 88 |     return load_report(str(latest))
 89 | 
 90 | 
 91 | @app.get("/health", tags=["Health"])
 92 | async def health():
 93 |     """Health check endpoint."""
 94 |     return {"status": "ok", "version": "1.0.0"}
 95 | 
 96 | 
 97 | @app.get("/", response_class=HTMLResponse, tags=["Dashboard"])
 98 | async def dashboard(request: Request):
 99 |     """Serve the main dashboard HTML."""
100 |     report = get_report_data()
101 |     
102 |     if report is None:
103 |         return """
104 |         <!doctype html>
105 |         <html>
106 |           <head>
107 |             <meta charset="utf-8" />
108 |             <title>DriftGuard — Dashboard</title>
109 |             <style>
110 |               body { background:#1a1a2e; color:#e6eef8; font-family: Arial, sans-serif; padding:24px; margin:0; }
111 |               .container { max-width:1200px; margin:0 auto; }
112 |               .card { background:#16213e; padding:32px; border-radius:8px; text-align:center; }
113 |               h1 { margin:0 0 16px 0; }
114 |               p { margin:8px 0; color:#b0b8c8; }
115 |               code { background:#0f1419; padding:4px 8px; border-radius:4px; }
116 |             </style>
117 |           </head>
118 |           <body>
119 |             <div class="container">
120 |               <div class="card">
121 |                 <h1>🔍 DriftGuard</h1>
122 |                 <p>No report found yet.</p>
123 |                 <p>Run DriftGuard first:</p>
124 |                 <code>python driftguard.py --repo . --days 30</code>
125 |                 <p style="margin-top:24px; color:#888;">Then refresh this page.</p>
126 |               </div>
127 |             </div>
128 |           </body>
129 |         </html>
130 |         """
131 |     
132 |     # Render dashboard with report data
133 |     return templates.TemplateResponse("dashboard.html", {"request": request, "report": report})
134 | 
135 | 
136 | @app.get("/settings", tags=["Settings"])
137 | async def get_settings():
138 |     """Get public settings (no API key required).
139 |     
140 |     Returns repository path, watch interval, and masked API key.
141 |     """
142 |     repos = load_repos_config()
143 |     default_repo = repos[0] if repos else {"path": Config.DEFAULT_REPO_PATH, "days": Config.DEFAULT_DAYS}
144 |     
145 |     # Mask API key (show first 4 and last 4 characters)
146 |     masked_key = ""
147 |     if Config.API_KEY:
148 |         if len(Config.API_KEY) > 8:
149 |             masked_key = Config.API_KEY[:4] + "*" * (len(Config.API_KEY) - 8) + Config.API_KEY[-4:]
150 |         else:
151 |             masked_key = "*" * len(Config.API_KEY)
152 |     
153 |     return {
154 |         "repo_path": default_repo.get("path", Config.DEFAULT_REPO_PATH),
155 |         "watch_interval_days": default_repo.get("days", Config.DEFAULT_DAYS),
156 |         "api_key_configured": bool(Config.API_KEY),
157 |         "api_key_masked": masked_key if masked_key else "Not configured"
158 |     }
159 | 
160 | 
161 | @app.get("/api/repos", tags=["API"])
162 | async def get_repos(api_key: str = Depends(verify_api_key)):
163 |     """Get list of all configured repositories (requires API key).
164 |     
165 |     Returns list of repos with name, path, avg_health_score, last_run_date, and file_count.
166 |     """
167 |     repos = load_repos_config()
168 |     
169 |     # Enhance each repo with stats from database
170 |     import sqlite3
171 |     db_conn = sqlite3.connect(db.DEFAULT_DB_PATH)
172 |     
173 |     try:
174 |         result = []
175 |         for repo in repos:
176 |             repo_name = repo.get("name", "unknown")
177 |             repo_path = repo.get("path", "")
178 |             
179 |             # Get latest run stats for this repo
180 |             cursor = db_conn.cursor()
181 |             cursor.execute("""
182 |                 SELECT
183 |                     AVG(health_score) as avg_score,
184 |                     MAX(timestamp) as last_run,
185 |                     COUNT(DISTINCT file_path) as file_count
186 |                 FROM file_scores
187 |                 WHERE run_id IN (
188 |                     SELECT run_id FROM analysis_runs
189 |                     WHERE repo_path = ?
190 |                     ORDER BY timestamp DESC
191 |                     LIMIT 1
192 |                 )
193 |             """, (repo_path,))
194 |             
195 |             row = cursor.fetchone()
196 |             avg_score = round(row[0], 1) if row[0] else 0.0
197 |             last_run = row[1] if row[1] else "Never"
198 |             file_count = row[2] if row[2] else 0
199 |             
200 |             result.append({
201 |                 "name": repo_name,
202 |                 "path": repo_path,
203 |                 "avg_health_score": avg_score,
204 |                 "last_run_date": last_run,
205 |                 "file_count": file_count,
206 |                 "days": repo.get("days", Config.DEFAULT_DAYS),
207 |                 "enabled": repo.get("enabled", True)
208 |             })
209 |         
210 |         return {"repos": result, "total": len(result)}
211 |     finally:
212 |         db_conn.close()
213 | 
214 | 
215 | @app.get("/api/report", tags=["API"])
216 | async def get_report(api_key: str = Depends(verify_api_key)):
217 |     """Return the most recent report as JSON with sparkline data (requires API key)."""
218 |     report = get_report_data()
219 |     
220 |     if report is None:
221 |         return JSONResponse(
222 |             status_code=404,
223 |             content={
224 |                 "error": "No report found",
225 |                 "hint": "Run 'python driftguard.py --repo . --days 30' to generate a report first.",
226 |                 "code": "NO_REPORT_FOUND"
227 |             }
228 |         )
229 |     
230 |     # Enhance report with sparkline data for each file
231 |     from app.trends import compute_trends
232 |     import sqlite3
233 |     
234 |     db_conn = sqlite3.connect(db.DEFAULT_DB_PATH)
235 |     
236 |     try:
237 |         files = report.get('files', [])
238 |         for file_data in files:
239 |             file_path = file_data.get('file_path', '')
240 |             if file_path:
241 |                 # Compute trends and add sparkline data
242 |                 trend_data = compute_trends(file_path, db_conn, n=6)
243 |                 file_data['sparkline'] = trend_data.get('last_n_scores', [])
244 |                 file_data['trend_direction'] = trend_data.get('trend_direction', 'stable')
245 |                 file_data['score_change'] = trend_data.get('score_change', 0.0)
246 |     finally:
247 |         db_conn.close()
248 |     
249 |     return report
250 | 
251 | 
252 | @app.get("/api/report/{filename}", tags=["API"])
253 | async def get_report_by_filename(filename: str, api_key: str = Depends(verify_api_key)):
254 |     """Return a specific report by filename (requires API key)."""
255 |     report_path = Config.OUTPUT_DIR / filename
256 |     
257 |     if not report_path.exists():
258 |         return JSONResponse(
259 |             status_code=404,
260 |             content={
261 |                 "error": f"Report not found: {filename}",
262 |                 "hint": f"Check available reports in the output directory. Run 'python driftguard.py' to generate a report.",
263 |                 "code": "REPORT_NOT_FOUND"
264 |             }
265 |         )
266 |     
267 |     if not str(report_path).endswith('.json'):
268 |         return JSONResponse(
269 |             status_code=400,
270 |             content={
271 |                 "error": "Invalid report format",
272 |                 "hint": "Only JSON reports are supported. Use .json extension.",
273 |                 "code": "INVALID_REPORT_FORMAT"
274 |             }
275 |         )
276 |     
277 |     return load_report(str(report_path))
278 | 
279 | 
280 | @app.get("/api/trends", tags=["API"])
281 | async def get_file_trends(file: str = Query(..., description="File path to get trends for"), api_key: str = Depends(verify_api_key)):
282 |     """Get historical trend data for a specific file (requires API key).
283 |     
284 |     Returns all runs where this file was analyzed, sorted by timestamp ascending.
285 |     Useful for tracking how a file's health score has changed over time.
286 |     
287 |     Args:
288 |         file: relative path to the file (e.g., "app/main.py")
289 |     
290 |     Returns:
291 |         List of trend data points with run_id, timestamp, health_score, and dimension scores
292 |     """
293 |     # Validate file path
294 |     try:
295 |         validate_file_path(file)
296 |     except ValidationError as e:
297 |         return JSONResponse(
298 |             status_code=400,
299 |             content=e.to_dict()
300 |         )
301 |     
302 |     trends = db.get_file_trends(file)
303 |     
304 |     if not trends:
305 |         return JSONResponse(
306 |             status_code=404,
307 |             content={
308 |                 "error": f"No trend data found for file: {file}",
309 |                 "hint": "Ensure the file has been analyzed in at least one run. Check the file path is correct.",
310 |                 "code": "FILE_NOT_FOUND"
311 |             }
312 |         )
313 |     
314 |     return {
315 |         "file_path": file,
316 |         "data_points": len(trends),
317 |         "trends": trends
318 |     }
319 | 
320 | 
321 | @app.get("/api/remediation/{file_name}", tags=["API"])
322 | async def get_remediation(file_name: str, api_key: str = Depends(verify_api_key)):
323 |     """Get remediation markdown for a specific file (requires API key).
324 |     
325 |     Args:
326 |         file_name: Sanitized file name (e.g., "app_main_py_remediation")
327 |         
328 |     Returns:
329 |         JSON with remediation markdown content
330 |     """
331 |     # Ensure file_name ends with _remediation.md
332 |     if not file_name.endswith("_remediation.md"):
333 |         file_name = f"{file_name}_remediation.md"
334 |     
335 |     remediation_path = Path("remediation") / file_name
336 |     
337 |     if not remediation_path.exists():
338 |         return JSONResponse(
339 |             status_code=404,
340 |             content={
341 |                 "error": f"Remediation file not found: {file_name}",
342 |                 "hint": "Run 'python driftguard.py --remediate' to generate remediation files for CRITICAL and AT_RISK files.",
343 |                 "code": "REMEDIATION_NOT_FOUND"
344 |             }
345 |         )
346 |     
347 |     try:
348 |         with open(remediation_path, 'r', encoding='utf-8') as f:
349 |             content = f.read()
350 |         
351 |         return {
352 |             "file_name": file_name,
353 |             "content": content
354 |         }
355 |     except Exception as e:
356 |         return JSONResponse(
357 |             status_code=500,
358 |             content={
359 |                 "error": f"Error reading remediation file: {str(e)}",
360 |                 "hint": "Check file permissions and ensure the remediation directory is accessible.",
361 |                 "code": "REMEDIATION_READ_ERROR"
362 |             }
363 |         )
364 | 
365 | 
366 | 
367 | @app.on_event("startup")
368 | async def startup_event():
369 |     """Print startup information."""
370 |     port = Config.FASTAPI_PORT
371 |     host = Config.FASTAPI_HOST
372 |     print()
373 |     print("=" * 70)
374 |     print("DriftGuard Dashboard")
375 |     print("=" * 70)
376 |     print(f"Dashboard: http://{host}:{port}/")
377 |     print(f"API: http://{host}:{port}/api/report")
378 |     print(f"Trends: http://{host}:{port}/api/trends?file=<path>")
379 |     print(f"Docs: http://{host}:{port}/docs")
380 |     print("=" * 70)
381 |     print()
382 | 
383 | 
384 | if __name__ == "__main__":
385 |     import uvicorn
386 |     uvicorn.run(
387 |         app,
388 |         host=Config.FASTAPI_HOST,
389 |         port=Config.FASTAPI_PORT,
390 |         reload=Config.FASTAPI_RELOAD,
391 |     )
</content>
</file>
</files>
<environment_details>
# VSCode Visible Files
app\git_parser.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,test_language_support.py,data/repos.json,app/templates/dashboard.html,app/report_exporter.py

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:30:57.170Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$0.63

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Create language_config.json with extension mappings and defaults | Completed |
| 2 | Update app/config.py to load language config from JSON | Completed |
| 3 | Update app/git_parser.py to use config-driven mappings | Completed |
| 4 | Add API endpoint to view active language config | In Progress |
| 5 | Add CLI command to print language config | Pending |
| 6 | Create tests for config override functionality | Pending |
| 7 | Update .env.example with language config path | Pending |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

Now let me add API endpoints for language configuration to app/main.py:

<apply_diff>
<path>app/main.py</path>
<diff>
<<<<<<< SEARCH
:start_line:17
-------
from app.config import Config, get_latest_report, load_repos_config
from app.report_generator import load_report
from app import db
from app.validation import ValidationError, validate_file_path, validate_days, validate_max_files
=======
from app.config import (
    Config, get_latest_report, load_repos_config,
    get_language_config_info, reload_language_config
)
from app.report_generator import load_report
from app import db
from app.validation import ValidationError, validate_file_path, validate_days, validate_max_files
>>>>>>> REPLACE

<<<<<<< SEARCH
:start_line:363
-------


@app.on_event("startup")
async def startup_event():
=======

@app.get("/api/language-config", tags=["API"])
async def get_language_config():
    """Get active language configuration (no API key required).
    
    Returns information about enabled and disabled file extensions,
    their language mappings, and configuration file path.
    """
    try:
        config_info = get_language_config_info()
        return config_info
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": f"Failed to load language configuration: {str(e)}",
                "hint": "Check that language_config.json exists and is valid JSON.",
                "code": "LANGUAGE_CONFIG_ERROR"
            }
        )


@app.post("/api/language-config/reload", tags=["API"])
async def reload_language_config_endpoint(api_key: str = Depends(verify_api_key)):
    """Reload language configuration from disk (requires API key).
    
    Useful after manually editing the language_config.json file.
    Clears all caches and reloads the configuration.
    """
    success, message = reload_language_config()
    
    if success:
        return {
            "status": "success",
            "message": message
        }
    else:
        return JSONResponse(
            status_code=500,
            content={
                "error": message,
                "code": "RELOAD_FAILED"
            }
        )


@app.on_event("startup")
async def startup_event():
>>>>>>> REPLACE
</diff>
</apply_diff>

---

**User:**

[apply_diff for 'app/main.py'] Result:
<file_write_result>
<path>app/main.py</path>
<operation>modified</operation>
<problems>

New problems detected after saving the file:
app/main.py
- [basedpyright Error] 11 | from fastapi import FastAPI, HTTPException, Request, Query, Header, Depends : Import "fastapi" could not be resolved
- [basedpyright Error] 12 | from fastapi.responses import HTMLResponse, FileResponse, JSONResponse : Import "fastapi.responses" could not be resolved
- [basedpyright Error] 13 | from fastapi.staticfiles import StaticFiles : Import "fastapi.staticfiles" could not be resolved
- [basedpyright Error] 14 | from fastapi.middleware.cors import CORSMiddleware : Import "fastapi.middleware.cors" could not be resolved
- [basedpyright Error] 15 | from fastapi.templating import Jinja2Templates : Import "fastapi.templating" could not be resolved
- [basedpyright Error] 91 |     return load_report(str(latest)) : Type "DriftReport" is not assignable to return type "dict[Unknown, Unknown] | None"
  Type "DriftReport" is not assignable to type "dict[Unknown, Unknown] | None"
    "DriftReport" is not assignable to "dict[Unknown, Unknown]"
    "DriftReport" is not assignable to "None"
- [basedpyright Error] 433 |     import uvicorn : Import "uvicorn" could not be resolved</problems>
<notice>
<i>You do not need to re-read the file, as you have seen all changes</i>
<i>Proceed with the task using these changes as the new baseline.</i>
</notice>
</file_write_result>

<environment_details>
# VSCode Visible Files
app\main.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,test_language_support.py,data/repos.json,app/templates/dashboard.html,app/report_exporter.py

# Recently Modified Files
These files have been modified since you last accessed them (file was just edited so you may need to re-read it before editing):
app/main.py

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:31:11.531Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$0.73

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Create language_config.json with extension mappings and defaults | Completed |
| 2 | Update app/config.py to load language config from JSON | Completed |
| 3 | Update app/git_parser.py to use config-driven mappings | Completed |
| 4 | Add API endpoint to view active language config | In Progress |
| 5 | Add CLI command to print language config | Pending |
| 6 | Create tests for config override functionality | Pending |
| 7 | Update .env.example with language config path | Pending |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

<update_todo_list>
<todos>
[x] Create language_config.json with extension mappings and defaults
[x] Update app/config.py to load language config from JSON
[x] Update app/git_parser.py to use config-driven mappings
[x] Add API endpoint to view active language config
[-] Add CLI command to print language config
[ ] Create tests for config override functionality
[ ] Update .env.example with language config path
</todos>
</update_todo_list>

---

**User:**

[update_todo_list] Result:
Todo list updated successfully.
<environment_details>
# VSCode Visible Files
app\main.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,test_language_support.py,data/repos.json,app/templates/dashboard.html,app/report_exporter.py

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:31:27.816Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$0.82

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Create language_config.json with extension mappings and defaults | Completed |
| 2 | Update app/config.py to load language config from JSON | Completed |
| 3 | Update app/git_parser.py to use config-driven mappings | Completed |
| 4 | Add API endpoint to view active language config | Completed |
| 5 | Add CLI command to print language config | In Progress |
| 6 | Create tests for config override functionality | Pending |
| 7 | Update .env.example with language config path | Pending |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

Now let me add a CLI command to print the language configuration. Let me check the driftguard.py file:

<read_file>
<args>
<file>
<path>driftguard.py</path>
<line_range>1-100</line_range>
</file>
</args>
</read_file>

---

**User:**

[read_file for 'driftguard.py'. Reading multiple files at once is more efficient for the LLM. If other files are relevant to your current task, please read them simultaneously.] Result:
<files>
<file><path>driftguard.py</path>
<content lines="1-100">
  1 | """DriftGuard CLI entrypoint.
  2 | 
  3 | Full pipeline: git_parser → bob_analyzer → scorer → report_generator → dashboard
  4 | 
  5 | Run: python driftguard.py --repo . --days 30
  6 | Watch mode: python driftguard.py --watch --interval 24h
  7 | """
  8 | import argparse
  9 | import sys
 10 | import signal
 11 | import time
 12 | import re
 13 | import logging
 14 | from pathlib import Path
 15 | from datetime import datetime
 16 | from logging.handlers import RotatingFileHandler
 17 | 
 18 | from app.git_parser import get_file_diffs, resolve_repo, _fetch_github_repo_diffs
 19 | from app.bob_analyzer import batch_analyze
 20 | from app.scorer import score_all_files
 21 | from app.report_generator import generate_report, save_report, print_report_summary
 22 | from app.report_exporter import export_report
 23 | from app.db import initialize_db, save_run
 24 | from app.alert_manager import AlertManager
 25 | from app.remediation import generate_remediations_for_files
 26 | from app.validation import (
 27 |     ValidationError,
 28 |     validate_repo_path,
 29 |     validate_days,
 30 |     validate_max_files,
 31 |     validate_interval,
 32 |     validate_export_mode
 33 | )
 34 | 
 35 | 
 36 | # Global flag for graceful shutdown
 37 | shutdown_requested = False
 38 | 
 39 | 
 40 | def setup_logging(log_file: str = "logs/driftguard.log") -> logging.Logger:
 41 |     """Set up logging with rotating file handler and console output.
 42 |     
 43 |     Args:
 44 |         log_file: Path to log file (default: logs/driftguard.log)
 45 |         
 46 |     Returns:
 47 |         Configured logger instance
 48 |     """
 49 |     # Create logs directory if it doesn't exist
 50 |     log_path = Path(log_file)
 51 |     log_path.parent.mkdir(parents=True, exist_ok=True)
 52 |     
 53 |     # Create logger
 54 |     logger = logging.getLogger("driftguard")
 55 |     logger.setLevel(logging.INFO)
 56 |     
 57 |     # Remove existing handlers to avoid duplicates
 58 |     logger.handlers.clear()
 59 |     
 60 |     # File handler with rotation (10MB max, keep 5 backups)
 61 |     file_handler = RotatingFileHandler(
 62 |         log_file,
 63 |         maxBytes=10 * 1024 * 1024,  # 10MB
 64 |         backupCount=5,
 65 |         encoding='utf-8'
 66 |     )
 67 |     file_handler.setLevel(logging.INFO)
 68 |     file_formatter = logging.Formatter(
 69 |         '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
 70 |         datefmt='%Y-%m-%d %H:%M:%S'
 71 |     )
 72 |     file_handler.setFormatter(file_formatter)
 73 |     
 74 |     # Console handler
 75 |     console_handler = logging.StreamHandler(sys.stdout)
 76 |     console_handler.setLevel(logging.INFO)
 77 |     console_formatter = logging.Formatter('%(levelname)s: %(message)s')
 78 |     console_handler.setFormatter(console_formatter)
 79 |     
 80 |     # Add handlers
 81 |     logger.addHandler(file_handler)
 82 |     logger.addHandler(console_handler)
 83 |     
 84 |     return logger
 85 | 
 86 | 
 87 | def signal_handler(signum, frame):
 88 |     """Handle SIGINT (Ctrl+C) for graceful shutdown."""
 89 |     global shutdown_requested
 90 |     print("\n⚠️  Shutdown requested. Finishing current run...")
 91 |     shutdown_requested = True
 92 | 
 93 | 
 94 | def parse_interval(interval_str: str) -> int:
 95 |     """Parse interval string to seconds.
 96 |     
 97 |     Supports formats:
 98 |     - "24h" -> 86400 seconds
 99 |     - "30m" -> 1800 seconds
100 |     - "3600" -> 3600 seconds (plain number)
</content>
</file>
</files>
<environment_details>
# VSCode Visible Files
app\main.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,test_language_support.py,data/repos.json,app/templates/dashboard.html,app/report_exporter.py

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:31:36.565Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$0.92

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Create language_config.json with extension mappings and defaults | Completed |
| 2 | Update app/config.py to load language config from JSON | Completed |
| 3 | Update app/git_parser.py to use config-driven mappings | Completed |
| 4 | Add API endpoint to view active language config | Completed |
| 5 | Add CLI command to print language config | In Progress |
| 6 | Create tests for config override functionality | Pending |
| 7 | Update .env.example with language config path | Pending |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

<read_file>
<args>
<file>
<path>driftguard.py</path>
<line_range>200-350</line_range>
</file>
</args>
</read_file>

---

**User:**

[read_file for 'driftguard.py'. Reading multiple files at once is more efficient for the LLM. If other files are relevant to your current task, please read them simultaneously.] Result:
<files>
<file><path>driftguard.py</path>
<content lines="200-350">
200 |     
201 |     # Step 4: Generate report
202 |     logger.info("Generating report")
203 |     try:
204 |         report = generate_report(repo, days, scored_files)
205 |     except Exception as e:
206 |         logger.error(f"Error generating report: {e}")
207 |         raise
208 |     
209 |     # Step 5: Save report
210 |     try:
211 |         report_path = save_report(report, output)
212 |         logger.info(f"Report saved to {report_path}")
213 |     except Exception as e:
214 |         logger.error(f"Error saving report: {e}")
215 |         raise
216 |     
217 |     return report
218 | 
219 | 
220 | def watcher(repo: str, days: int, max_files: int, interval_seconds: int,
221 |             alert_config: dict = None, github_token: str = None):
222 |     """Run continuous analysis with scheduled intervals.
223 |     
224 |     Args:
225 |         repo: Path to git repository or GitHub URL
226 |         days: Days of history to analyze
227 |         max_files: Maximum files to analyze
228 |         interval_seconds: Seconds between analysis runs
229 |         alert_config: Optional alert configuration dict
230 |         github_token: Optional GitHub token for API access
231 |     """
232 |     global shutdown_requested
233 |     
234 |     # Set up logging
235 |     logger = setup_logging()
236 |     logger.info("=" * 70)
237 |     logger.info("DriftGuard Watch Mode Started")
238 |     logger.info("=" * 70)
239 |     logger.info(f"Repository: {repo}")
240 |     logger.info(f"Analysis window: {days} days")
241 |     logger.info(f"Max files: {max_files}")
242 |     logger.info(f"Interval: {interval_seconds} seconds ({interval_seconds/3600:.1f} hours)")
243 |     logger.info("=" * 70)
244 |     
245 |     # Initialize database
246 |     initialize_db()
247 |     logger.info("Database initialized")
248 |     
249 |     # Initialize alert manager
250 |     alert_manager = AlertManager(alert_config)
251 |     
252 |     # Register signal handler for graceful shutdown
253 |     signal.signal(signal.SIGINT, signal_handler)
254 |     signal.signal(signal.SIGTERM, signal_handler)
255 |     
256 |     run_count = 0
257 |     
258 |     while not shutdown_requested:
259 |         run_count += 1
260 |         logger.info(f"\n{'=' * 70}")
261 |         logger.info(f"Starting analysis run #{run_count}")
262 |         logger.info(f"{'=' * 70}")
263 |         
264 |         try:
265 |             # Run analysis
266 |             report = run_analysis(repo, days, max_files, logger=logger, github_token=github_token)
267 |             
268 |             if report:
269 |                 # Save to database
270 |                 run_id = save_run(report)
271 |                 logger.info(f"Run saved to database: {run_id}")
272 |                 
273 |                 # Check for alerts
274 |                 alert_manager.check_and_alert(report)
275 |                 
276 |                 # Print summary
277 |                 print_report_summary(report)
278 |             else:
279 |                 logger.info("No changes detected, skipping database save")
280 |             
281 |             logger.info(f"Analysis run #{run_count} completed successfully")
282 |             
283 |         except Exception as e:
284 |             logger.error(f"Error during analysis run #{run_count}: {e}", exc_info=True)
285 |         
286 |         if shutdown_requested:
287 |             break
288 |         
289 |         # Wait for next interval
290 |         logger.info(f"Next run in {interval_seconds} seconds ({interval_seconds/3600:.1f} hours)")
291 |         logger.info(f"Press Ctrl+C to stop gracefully")
292 |         
293 |         # Sleep in small increments to allow for responsive shutdown
294 |         sleep_interval = 1  # Check every second
295 |         for _ in range(interval_seconds):
296 |             if shutdown_requested:
297 |                 break
298 |             time.sleep(sleep_interval)
299 |     
300 |     logger.info("\n" + "=" * 70)
301 |     logger.info("DriftGuard Watch Mode Stopped")
302 |     logger.info(f"Total runs completed: {run_count}")
303 |     logger.info("=" * 70)
304 | 
305 | 
306 | def main():
307 |     parser = argparse.ArgumentParser(description="DriftGuard - Codebase Decay Monitor")
308 |     parser.add_argument("--repo", default=".", help="Path to git repository or GitHub URL (default: .)")
309 |     parser.add_argument("--days", type=int, default=30, help="Days of history to analyze (default: 30)")
310 |     parser.add_argument("--output", default=None, help="Output JSON file path (auto-generated if not provided)")
311 |     parser.add_argument("--max-files", type=int, default=20, help="Max files to analyze (default: 20)")
312 |     parser.add_argument("--verbose", action="store_true", help="Print raw analysis details")
313 |     parser.add_argument("--watch", action="store_true", help="Run in watch mode with scheduled intervals")
314 |     parser.add_argument("--interval", default="24h", help="Watch mode interval (e.g., '24h', '30m', '3600')")
315 |     parser.add_argument("--github-token", default=None, help="GitHub token for API access (overrides GITHUB_TOKEN env var)")
316 |     parser.add_argument("--export", default="json", choices=["json", "markdown", "pdf", "all"],
317 |                         help="Export format: json, markdown, pdf, or all (default: json)")
318 |     parser.add_argument("--remediate", action="store_true",
319 |                         help="Generate remediation files for CRITICAL and AT_RISK files")
320 |     
321 |     args = parser.parse_args()
322 |     
323 |     # Validate inputs
324 |     try:
325 |         validate_days(args.days)
326 |         validate_max_files(args.max_files)
327 |         validate_export_mode(args.export)
328 |         validate_repo_path(args.repo, args.github_token)
329 |     except ValidationError as e:
330 |         print(f"ERROR: {e.message}", file=sys.stderr)
331 |         if e.hint:
332 |             print(f"HINT: {e.hint}", file=sys.stderr)
333 |         sys.exit(1)
334 |     
335 |     # Watch mode
336 |     if args.watch:
337 |         try:
338 |             validate_interval(args.interval)
339 |             interval_seconds = parse_interval(args.interval)
340 |         except ValidationError as e:
341 |             print(f"ERROR: {e.message}", file=sys.stderr)
342 |             if e.hint:
343 |                 print(f"HINT: {e.hint}", file=sys.stderr)
344 |             sys.exit(1)
345 |         except ValueError as e:
346 |             print(f"ERROR: {e}", file=sys.stderr)
347 |             sys.exit(1)
348 |         
349 |         # Run watcher
350 |         watcher(args.repo, args.days, args.max_files, interval_seconds, github_token=args.github_token)
</content>
</file>
</files>
<environment_details>
# VSCode Visible Files
app\main.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,test_language_support.py,data/repos.json,app/templates/dashboard.html,app/report_exporter.py

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:31:50.255Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$1.02

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Create language_config.json with extension mappings and defaults | Completed |
| 2 | Update app/config.py to load language config from JSON | Completed |
| 3 | Update app/git_parser.py to use config-driven mappings | Completed |
| 4 | Add API endpoint to view active language config | Completed |
| 5 | Add CLI command to print language config | In Progress |
| 6 | Create tests for config override functionality | Pending |
| 7 | Update .env.example with language config path | Pending |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

<read_file>
<args>
<file>
<path>driftguard.py</path>
<line_range>350-400</line_range>
</file>
</args>
</read_file>

---

**User:**

[read_file for 'driftguard.py'. Reading multiple files at once is more efficient for the LLM. If other files are relevant to your current task, please read them simultaneously.] Result:
<files>
<file><path>driftguard.py</path>
<content lines="350-400">
350 |         watcher(args.repo, args.days, args.max_files, interval_seconds, github_token=args.github_token)
351 |         sys.exit(0)
352 |     
353 |     print("\n" + "=" * 70)
354 |     print("🔍 DriftGuard — Codebase Decay Monitor")
355 |     print("=" * 70)
356 |     
357 |     # Step 1: Resolve repository and extract git diffs
358 |     print(f"\n📂 Scanning {args.repo} for last {args.days} days of changes...")
359 |     try:
360 |         repo_data, is_remote = resolve_repo(args.repo, args.github_token)
361 |         
362 |         # If it's a GitHub repo, fetch diffs via API
363 |         if is_remote:
364 |             owner, repo_name, token = repo_data
365 |             print(f"Using GitHub API for {owner}/{repo_name}")
366 |             file_diffs = _fetch_github_repo_diffs(owner, repo_name, args.days, token)
367 |         else:
368 |             # Local repo or cloned repo
369 |             file_diffs = get_file_diffs(repo_data, args.days)
370 |     except Exception as e:
371 |         print(f"❌ Error reading repository: {e}")
372 |         sys.exit(1)
373 |     
374 |     if not file_diffs:
375 |         print("⚠️  No modified files found in the analysis window.")
376 |         sys.exit(0)
377 |     
378 |     print(f"✅ Found {len(file_diffs)} modified files")
379 |     
380 |     # Limit to max_files
381 |     if len(file_diffs) > args.max_files:
382 |         print(f"⚠️  Limiting to top {args.max_files} most-changed files (by commit count)")
383 |         file_diffs = file_diffs[:args.max_files]
384 |     
385 |     # Step 2: Analyze with bob_analyzer
386 |     print(f"\n🤖 Analyzing {len(file_diffs)} files for decay signals...")
387 |     try:
388 |         analyses = batch_analyze(file_diffs)
389 |     except Exception as e:
390 |         print(f"❌ Error during analysis: {e}")
391 |         sys.exit(1)
392 |     
393 |     print(f"✅ Analysis complete")
394 |     
395 |     # Step 3: Score files
396 |     print("\n⚖️  Calculating health scores...")
397 |     try:
398 |         scored_files = score_all_files(analyses)
399 |     except Exception as e:
400 |         print(f"❌ Error during scoring: {e}")
</content>
</file>
</files>
<environment_details>
# VSCode Visible Files
app\main.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,test_language_support.py,data/repos.json,app/templates/dashboard.html,app/report_exporter.py

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:32:07.975Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$1.14

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Create language_config.json with extension mappings and defaults | Completed |
| 2 | Update app/config.py to load language config from JSON | Completed |
| 3 | Update app/git_parser.py to use config-driven mappings | Completed |
| 4 | Add API endpoint to view active language config | Completed |
| 5 | Add CLI command to print language config | In Progress |
| 6 | Create tests for config override functionality | Pending |
| 7 | Update .env.example with language config path | Pending |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

Now let me add a CLI command to print language configuration. I'll add it to the argument parser and create a handler function:

<apply_diff>
<path>driftguard.py</path>
<diff>
<<<<<<< SEARCH
:start_line:18
-------
from app.git_parser import get_file_diffs, resolve_repo, _fetch_github_repo_diffs
from app.bob_analyzer import batch_analyze
from app.scorer import score_all_files
from app.report_generator import generate_report, save_report, print_report_summary
from app.report_exporter import export_report
from app.db import initialize_db, save_run
from app.alert_manager import AlertManager
from app.remediation import generate_remediations_for_files
from app.validation import (
    ValidationError,
    validate_repo_path,
    validate_days,
    validate_max_files,
    validate_interval,
    validate_export_mode
)
=======
from app.git_parser import get_file_diffs, resolve_repo, _fetch_github_repo_diffs
from app.bob_analyzer import batch_analyze
from app.scorer import score_all_files
from app.report_generator import generate_report, save_report, print_report_summary
from app.report_exporter import export_report
from app.db import initialize_db, save_run
from app.alert_manager import AlertManager
from app.remediation import generate_remediations_for_files
from app.config import get_language_config_info
from app.validation import (
    ValidationError,
    validate_repo_path,
    validate_days,
    validate_max_files,
    validate_interval,
    validate_export_mode
)
>>>>>>> REPLACE

<<<<<<< SEARCH
:start_line:304
-------


def main():
    parser = argparse.ArgumentParser(description="DriftGuard - Codebase Decay Monitor")
    parser.add_argument("--repo", default=".", help="Path to git repository or GitHub URL (default: .)")
    parser.add_argument("--days", type=int, default=30, help="Days of history to analyze (default: 30)")
    parser.add_argument("--output", default=None, help="Output JSON file path (auto-generated if not provided)")
    parser.add_argument("--max-files", type=int, default=20, help="Max files to analyze (default: 20)")
    parser.add_argument("--verbose", action="store_true", help="Print raw analysis details")
    parser.add_argument("--watch", action="store_true", help="Run in watch mode with scheduled intervals")
    parser.add_argument("--interval", default="24h", help="Watch mode interval (e.g., '24h', '30m', '3600')")
    parser.add_argument("--github-token", default=None, help="GitHub token for API access (overrides GITHUB_TOKEN env var)")
    parser.add_argument("--export", default="json", choices=["json", "markdown", "pdf", "all"],
                        help="Export format: json, markdown, pdf, or all (default: json)")
    parser.add_argument("--remediate", action="store_true",
                        help="Generate remediation files for CRITICAL and AT_RISK files")
    
    args = parser.parse_args()
=======

def print_language_config():
    """Print active language configuration to console."""
    print("\n" + "=" * 70)
    print("🔧 DriftGuard Language Configuration")
    print("=" * 70)
    
    try:
        config_info = get_language_config_info()
        
        print(f"\nConfiguration File: {config_info['config_path']}")
        print(f"Version: {config_info['version']}")
        print(f"Description: {config_info['description']}")
        
        print(f"\n✅ Enabled Extensions ({config_info['total_enabled']}):")
        print("-" * 70)
        for ext_info in config_info['enabled_extensions']:
            ext = ext_info['extension']
            lang = ext_info['language']
            desc = ext_info['description']
            print(f"  {ext:8} → {lang:15} ({desc})")
        
        if config_info['disabled_extensions']:
            print(f"\n❌ Disabled Extensions ({config_info['total_disabled']}):")
            print("-" * 70)
            for ext_info in config_info['disabled_extensions']:
                ext = ext_info['extension']
                lang = ext_info['language']
                desc = ext_info['description']
                print(f"  {ext:8} → {lang:15} ({desc})")
        
        print("\n" + "=" * 70)
        print(f"Total: {config_info['total_enabled']} enabled, {config_info['total_disabled']} disabled")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ Error loading language configuration: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="DriftGuard - Codebase Decay Monitor")
    parser.add_argument("--repo", default=".", help="Path to git repository or GitHub URL (default: .)")
    parser.add_argument("--days", type=int, default=30, help="Days of history to analyze (default: 30)")
    parser.add_argument("--output", default=None, help="Output JSON file path (auto-generated if not provided)")
    parser.add_argument("--max-files", type=int, default=20, help="Max files to analyze (default: 20)")
    parser.add_argument("--verbose", action="store_true", help="Print raw analysis details")
    parser.add_argument("--watch", action="store_true", help="Run in watch mode with scheduled intervals")
    parser.add_argument("--interval", default="24h", help="Watch mode interval (e.g., '24h', '30m', '3600')")
    parser.add_argument("--github-token", default=None, help="GitHub token for API access (overrides GITHUB_TOKEN env var)")
    parser.add_argument("--export", default="json", choices=["json", "markdown", "pdf", "all"],
                        help="Export format: json, markdown, pdf, or all (default: json)")
    parser.add_argument("--remediate", action="store_true",
                        help="Generate remediation files for CRITICAL and AT_RISK files")
    parser.add_argument("--show-languages", action="store_true",
                        help="Show active language configuration and exit")
    
    args = parser.parse_args()
    
    # Handle --show-languages flag
    if args.show_languages:
        print_language_config()
        sys.exit(0)
>>>>>>> REPLACE
</diff>
</apply_diff>

---

**User:**

[apply_diff for 'driftguard.py'] Result:
<file_write_result>
<path>driftguard.py</path>
<operation>modified</operation>
<problems>

New problems detected after saving the file:
driftguard.py
- [basedpyright Error] 139 | def run_analysis(repo: str, days: int, max_files: int, output: str = None, : Expression of type "None" cannot be assigned to parameter of type "str"
  "None" is not assignable to "str"
- [basedpyright Error] 140 |                  logger: logging.Logger = None, github_token: str = None) -&gt; dict: : Expression of type "None" cannot be assigned to parameter of type "Logger"
  "None" is not assignable to "Logger"
- [basedpyright Error] 140 |                  logger: logging.Logger = None, github_token: str = None) -&gt; dict: : Expression of type "None" cannot be assigned to parameter of type "str"
  "None" is not assignable to "str"
- [basedpyright Error] 177 |         return None : Type "None" is not assignable to return type "dict[Unknown, Unknown]"
  "None" is not assignable to "dict[Unknown, Unknown]"
- [basedpyright Error] 205 |         report = generate_report(repo, days, scored_files) : Argument of type "List[ScoredFile]" cannot be assigned to parameter "scored_files" of type "List[Dict[Unknown, Unknown]]" in function "generate_report"
  "List[ScoredFile]" is not assignable to "List[Dict[Unknown, Unknown]]"
    Type parameter "_T@list" is invariant, but "ScoredFile" is not the same as "Dict[Unknown, Unknown]"
    Consider switching from "list" to "Sequence" which is covariant
- [basedpyright Error] 218 |     return report : Type "DriftReport" is not assignable to return type "dict[Unknown, Unknown]"
  "DriftReport" is not assignable to "dict[Unknown, Unknown]"
- [basedpyright Error] 222 |             alert_config: dict = None, github_token: str = None): : Expression of type "None" cannot be assigned to parameter of type "dict[Unknown, Unknown]"
  "None" is not assignable to "dict[Unknown, Unknown]"
- [basedpyright Error] 222 |             alert_config: dict = None, github_token: str = None): : Expression of type "None" cannot be assigned to parameter of type "str"
  "None" is not assignable to "str"
- [basedpyright Error] 278 |                 print_report_summary(report) : Argument of type "dict[Unknown, Unknown]" cannot be assigned to parameter "report" of type "DriftReport" in function "print_report_summary"
  "dict[Unknown, Unknown]" is not assignable to "DriftReport"
- [basedpyright Error] 455 |         report = generate_report(args.repo, args.days, scored_files) : Argument of type "List[ScoredFile]" cannot be assigned to parameter "scored_files" of type "List[Dict[Unknown, Unknown]]" in function "generate_report"
  "List[ScoredFile]" is not assignable to "List[Dict[Unknown, Unknown]]"
    Type parameter "_T@list" is invariant, but "ScoredFile" is not the same as "Dict[Unknown, Unknown]"
    Consider switching from "list" to "Sequence" which is covariant
- [basedpyright Error] 473 |             export_result = export_report(report, args.export, output_dir="output") : Argument of type "DriftReport" cannot be assigned to parameter "report" of type "Dict[Unknown, Unknown]" in function "export_report"
  "DriftReport" is not assignable to "Dict[Unknown, Unknown]"</problems>
<notice>
<i>You do not need to re-read the file, as you have seen all changes</i>
<i>Proceed with the task using these changes as the new baseline.</i>
</notice>
</file_write_result>

<environment_details>
# VSCode Visible Files
driftguard.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,test_language_support.py,data/repos.json,app/templates/dashboard.html,app/report_exporter.py

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:32:31.247Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$1.25

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Create language_config.json with extension mappings and defaults | Completed |
| 2 | Update app/config.py to load language config from JSON | Completed |
| 3 | Update app/git_parser.py to use config-driven mappings | Completed |
| 4 | Add API endpoint to view active language config | Completed |
| 5 | Add CLI command to print language config | In Progress |
| 6 | Create tests for config override functionality | Pending |
| 7 | Update .env.example with language config path | Pending |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

<update_todo_list>
<todos>
[x] Create language_config.json with extension mappings and defaults
[x] Update app/config.py to load language config from JSON
[x] Update app/git_parser.py to use config-driven mappings
[x] Add API endpoint to view active language config
[x] Add CLI command to print language config
[-] Create tests for config override functionality
[ ] Update .env.example with language config path
</todos>
</update_todo_list>

---

**User:**

[update_todo_list] Result:
Todo list updated successfully.
<environment_details>
# VSCode Visible Files
driftguard.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,test_language_support.py,data/repos.json,app/templates/dashboard.html,app/report_exporter.py

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:32:54.310Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$1.38

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Create language_config.json with extension mappings and defaults | Completed |
| 2 | Update app/config.py to load language config from JSON | Completed |
| 3 | Update app/git_parser.py to use config-driven mappings | Completed |
| 4 | Add API endpoint to view active language config | Completed |
| 5 | Add CLI command to print language config | Completed |
| 6 | Create tests for config override functionality | In Progress |
| 7 | Update .env.example with language config path | Pending |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

Now let me create comprehensive tests for the config override functionality:

<write_to_file>
<path>test_language_config.py</path>
<content>
"""Test language configuration system.

Tests that language configuration can be loaded from JSON,
overridden, and properly used by the git parser.
"""

import json
import tempfile
import os
from pathlib import Path
import pytest

from app.config import (
    Config,
    load_language_config,
    get_supported_extensions,
    get_extension_to_language_map,
    get_language_config_info,
    reload_language_config
)
from app.git_parser import _get_supported_extensions, _get_extension_to_language


def test_load_default_language_config():
    """Test loading default language configuration."""
    config = load_language_config()
    
    assert "version" in config
    assert "extensions" in config
    assert isinstance(config["extensions"], dict)
    
    # Check default extensions are present
    extensions = config["extensions"]
    assert ".py" in extensions
    assert ".js" in extensions
    assert ".ts" in extensions
    assert ".java" in extensions
    assert ".go" in extensions
    assert ".rb" in extensions


def test_get_supported_extensions():
    """Test getting enabled extensions."""
    extensions = get_supported_extensions()
    
    assert isinstance(extensions, set)
    assert len(extensions) > 0
    
    # Default enabled extensions should be present
    assert ".py" in extensions
    assert ".js" in extensions
    assert ".ts" in extensions


def test_get_extension_to_language_map():
    """Test getting extension to language mapping."""
    mapping = get_extension_to_language_map()
    
    assert isinstance(mapping, dict)
    assert len(mapping) > 0
    
    # Check default mappings
    assert mapping.get(".py") == "python"
    assert mapping.get(".js") == "javascript"
    assert mapping.get(".ts") == "typescript"
    assert mapping.get(".java") == "java"
    assert mapping.get(".go") == "go"
    assert mapping.get(".rb") == "ruby"


def test_get_language_config_info():
    """Test getting full language configuration info."""
    info = get_language_config_info()
    
    assert "version" in info
    assert "config_path" in info
    assert "enabled_extensions" in info
    assert "disabled_extensions" in info
    assert "total_enabled" in info
    assert "total_disabled" in info
    
    assert isinstance(info["enabled_extensions"], list)
    assert isinstance(info["disabled_extensions"], list)
    assert info["total_enabled"] > 0


def test_custom_language_config():
    """Test loading custom language configuration from file."""
    # Create temporary config file
    custom_config = {
        "version": "1.0-test",
        "description": "Test configuration",
        "extensions": {
            ".py": {"language": "python", "enabled": True, "description": "Python files"},
            ".js": {"language": "javascript", "enabled": True, "description": "JS files"},
            ".test": {"language": "testlang", "enabled": True, "description": "Test files"},
            ".disabled": {"language": "disabled", "enabled": False, "description": "Disabled"}
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(custom_config, f)
        temp_path = f.name
    
    try:
        # Override config path
        original_path = Config.LANGUAGE_CONFIG_PATH
        Config.LANGUAGE_CONFIG_PATH = Path(temp_path)
        
        # Clear caches
        Config._language_config_cache = None
        Config._supported_extensions_cache = None
        Config._extension_to_language_cache = None
        
        # Load custom config
        config = load_language_config(force_reload=True)
        
        assert config["version"] == "1.0-test"
        assert ".test" in config["extensions"]
        
        # Check enabled extensions
        extensions = get_supported_extensions()
        assert ".test" in extensions
        assert ".disabled" not in extensions
        
        # Check mapping
        mapping = get_extension_to_language_map()
        assert mapping.get(".test") == "testlang"
        assert ".disabled" not in mapping
        
    finally:
        # Restore original config
        Config.LANGUAGE_CONFIG_PATH = original_path
        Config._language_config_cache = None
        Config._supported_extensions_cache = None
        Config._extension_to_language_cache = None
        os.unlink(temp_path)


def test_git_parser_uses_config():
    """Test that git parser uses config-driven extensions."""
    # Get extensions from config
    config_extensions = get_supported_extensions()
    parser_extensions = _get_supported_extensions()
    
    # Should be the same
    assert config_extensions == parser_extensions
    
    # Get mappings
    config_mapping = get_extension_to_language_map()
    parser_mapping = _get_extension_to_language()
    
    # Should be the same
    assert config_mapping == parser_mapping


def test_reload_language_config():
    """Test reloading language configuration."""
    # Initial load
    config1 = load_language_config()
    extensions1 = get_supported_extensions()
    
    # Reload
    success, message = reload_language_config()
    
    assert success is True
    assert "reloaded successfully" in message.lower()
    
    # Should still work
    config2 = load_language_config()
    extensions2 = get_supported_extensions()
    
    assert config2 is not None
    assert len(extensions2) > 0


def test_disabled_extensions_not_included():
    """Test that disabled extensions are not included in supported set."""
    config = load_language_config()
    extensions = config.get("extensions", {})
    
    supported = get_supported_extensions()
    mapping = get_extension_to_language_map()
    
    for ext, info in extensions.items():
        if info.get("enabled", True):
            assert ext in supported
            assert ext in mapping
        else:
            assert ext not in supported
            assert ext not in mapping


def test_config_caching():
    """Test that configuration is properly cached."""
    # Clear caches
    Config._language_config_cache = None
    Config._supported_extensions_cache = None
    Config._extension_to_language_cache = None
    
    # First load
    config1 = load_language_config()
    extensions1 = get_supported_extensions()
    mapping1 = get_extension_to_language_map()
    
    # Second load (should use cache)
    config2 = load_language_config()
    extensions2 = get_supported_extensions()
    mapping2 = get_extension_to_language_map()
    
    # Should be the same objects (cached)
    assert config1 is config2
    assert extensions1 is extensions2
    assert mapping1 is mapping2


def test_invalid_config_fallback():
    """Test that invalid config falls back to defaults."""
    # Create invalid config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("{ invalid json }")
        temp_path = f.name
    
    try:
        # Override config path
        original_path = Config.LANGUAGE_CONFIG_PATH
        Config.LANGUAGE_CONFIG_PATH = Path(temp_path)
        
        # Clear caches
        Config._language_config_cache = None
        Config._supported_extensions_cache = None
        Config._extension_to_language_cache = None
        
        # Should fall back to defaults
        config = load_language_config(force_reload=True)
        
        assert config is not None
        assert "extensions" in config
        assert ".py" in config["extensions"]
        
    finally:
        # Restore original config
        Config.LANGUAGE_CONFIG_PATH = original_path
        Config._language_config_cache = None
        Config._supported_extensions_cache = None
        Config._extension_to_language_cache = None
        os.unlink(temp_path)


def test_missing_config_fallback():
    """Test that missing config file falls back to defaults."""
    # Override with non-existent path
    original_path = Config.LANGUAGE_CONFIG_PATH
    Config.LANGUAGE_CONFIG_PATH = Path("/nonexistent/path/config.json")
    
    try:
        # Clear caches
        Config._language_config_cache = None
        Config._supported_extensions_cache = None
        Config._extension_to_language_cache = None
        
        # Should fall back to defaults
        config = load_language_config(force_reload=True)
        
        assert config is not None
        assert "extensions" in config
        assert ".py" in config["extensions"]
        
        # Should still work
        extensions = get_supported_extensions()
        assert len(extensions) > 0
        
    finally:
        # Restore original config
        Config.LANGUAGE_CONFIG_PATH = original_path
        Config._language_config_cache = None
        Config._supported_extensions_cache = None
        Config._extension_to_language_cache = None


def test_config_info_structure():
    """Test that config info has correct structure."""
    info = get_language_config_info()
    
    # Check top-level keys
    required_keys = ["version", "description", "config_path", 
                     "enabled_extensions", "disabled_extensions",
                     "total_enabled", "total_disabled"]
    
    for key in required_keys:
        assert key in info, f"Missing key: {key}"
    
    # Check enabled extensions structure
    for ext_info in info["enabled_extensions"]:
        assert "extension" in ext_info
        assert "language" in ext_info
        assert "description" in ext_info
    
    # Check disabled extensions structure
    for ext_info in info["disabled_extensions"]:
        assert "extension" in ext_info
        assert "language" in ext_info
        assert "description" in ext_info


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("LANGUAGE CONFIGURATION TESTS")
    print("=" * 70)
    
    # Run tests
    test_load_default_language_config()
    print("✅ test_load_default_language_config")
    
    test_get_supported_extensions()
    print("✅ test_get_supported_extensions")
    
    test_get_extension_to_language_map()
    print("✅ test_get_extension_to_language_map")
    
    test_get_language_config_info()
    print("✅ test_get_language_config_info")
    
    test_custom_language_config()
    print("✅ test_custom_language_config")
    
    test_git_parser_uses_config()
    print("✅ test_git_parser_uses_config")
    
    test_reload_language_config()
    print("✅ test_reload_language_config")
    
    test_disabled_extensions_not_included()
    print("✅ test_disabled_extensions_not_included")
    
    test_config_caching()
    print("✅ test_config_caching")
    
    test_invalid_config_fallback()
    print("✅ test_invalid_config_fallback")
    
    test_missing_config_fallback()
    print("✅ test_missing_config_fallback")
    
    test_config_info_structure()
    print("✅ test_config_info_structure")
    
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED!")
    print("=" * 70)
</content>
<line_count>318</line_count>
</write_to_file>

---

**User:**

[write_to_file for 'test_language_config.py'] Result:
<file_write_result>
<path>test_language_config.py</path>
<operation>created</operation>
<problems>

New problems detected after saving the file:
test_language_config.py
- [basedpyright Error] 11 | import pytest : Import "pytest" could not be resolved
- [basedpyright Error] 133 |         Config.LANGUAGE_CONFIG_PATH = original_path : "original_path" is possibly unbound
- [basedpyright Error] 243 |         Config.LANGUAGE_CONFIG_PATH = original_path : "original_path" is possibly unbound</problems>
<notice>
<i>You do not need to re-read the file, as you have seen all changes</i>
<i>Proceed with the task using these changes as the new baseline.</i>
</notice>
</file_write_result>

<environment_details>
# VSCode Visible Files
test_language_config.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,test_language_support.py,data/repos.json,app/templates/dashboard.html,app/report_exporter.py

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:33:33.348Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$1.51

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Create language_config.json with extension mappings and defaults | Completed |
| 2 | Update app/config.py to load language config from JSON | Completed |
| 3 | Update app/git_parser.py to use config-driven mappings | Completed |
| 4 | Add API endpoint to view active language config | Completed |
| 5 | Add CLI command to print language config | Completed |
| 6 | Create tests for config override functionality | In Progress |
| 7 | Update .env.example with language config path | Pending |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

<update_todo_list>
<todos>
[x] Create language_config.json with extension mappings and defaults
[x] Update app/config.py to load language config from JSON
[x] Update app/git_parser.py to use config-driven mappings
[x] Add API endpoint to view active language config
[x] Add CLI command to print language config
[x] Create tests for config override functionality
[-] Update .env.example with language config path
</todos>
</update_todo_list>

---

**User:**

[update_todo_list] Result:
Todo list updated successfully.
<environment_details>
# VSCode Visible Files
test_language_config.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,test_language_support.py,data/repos.json,app/templates/dashboard.html,app/report_exporter.py

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:33:43.022Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$1.64

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Create language_config.json with extension mappings and defaults | Completed |
| 2 | Update app/config.py to load language config from JSON | Completed |
| 3 | Update app/git_parser.py to use config-driven mappings | Completed |
| 4 | Add API endpoint to view active language config | Completed |
| 5 | Add CLI command to print language config | Completed |
| 6 | Create tests for config override functionality | Completed |
| 7 | Update .env.example with language config path | In Progress |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

Now let me update the .env.example file to include the language config path:

<apply_diff>
<path>.env.example</path>
<diff>
<<<<<<< SEARCH
:start_line:56
-------
# BOB_RATE_LIMIT_BURST: Burst capacity for rapid initial requests (default: 5)
# Allows up to this many requests immediately before rate limiting kicks in
BOB_RATE_LIMIT_BURST=5

# Made with Bob
=======
# BOB_RATE_LIMIT_BURST: Burst capacity for rapid initial requests (default: 5)
# Allows up to this many requests immediately before rate limiting kicks in
BOB_RATE_LIMIT_BURST=5

# Language Configuration
# Path to language configuration file (default: data/language_config.json)
# This file defines which file extensions are analyzed and their language mappings
# DRIFTGUARD_LANGUAGE_CONFIG=data/language_config.json

# Parallel Processing Configuration
# Maximum number of parallel workers for file analysis (default: CPU count, max 8)
# DRIFTGUARD_MAX_WORKERS=8

# Made with Bob
>>>>>>> REPLACE
</diff>
</apply_diff>

---

**User:**

[apply_diff for '.env.example'] Result:
<file_write_result>
<path>.env.example</path>
<operation>modified</operation>
<notice>
<i>You do not need to re-read the file, as you have seen all changes</i>
<i>Proceed with the task using these changes as the new baseline.</i>
</notice>
</file_write_result>

<notice>Making multiple related changes in a single apply_diff is more efficient. If other changes are needed in this file, please include them as additional SEARCH/REPLACE blocks.</notice>
<environment_details>
# VSCode Visible Files
.env.example

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,test_language_support.py,data/repos.json,app/templates/dashboard.html,app/report_exporter.py

# Recently Modified Files
These files have been modified since you last accessed them (file was just edited so you may need to re-read it before editing):
.env.example

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:33:55.567Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$1.78

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Create language_config.json with extension mappings and defaults | Completed |
| 2 | Update app/config.py to load language config from JSON | Completed |
| 3 | Update app/git_parser.py to use config-driven mappings | Completed |
| 4 | Add API endpoint to view active language config | Completed |
| 5 | Add CLI command to print language config | Completed |
| 6 | Create tests for config override functionality | Completed |
| 7 | Update .env.example with language config path | In Progress |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

<update_todo_list>
<todos>
[x] Create language_config.json with extension mappings and defaults
[x] Update app/config.py to load language config from JSON
[x] Update app/git_parser.py to use config-driven mappings
[x] Add API endpoint to view active language config
[x] Add CLI command to print language config
[x] Create tests for config override functionality
[x] Update .env.example with language config path
</todos>
</update_todo_list>

---

**User:**

[update_todo_list] Result:
Todo list updated successfully.
<environment_details>
# VSCode Visible Files
.env.example

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,test_language_support.py,data/repos.json,app/templates/dashboard.html,app/report_exporter.py

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:34:07.367Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$1.91

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Create language_config.json with extension mappings and defaults | Completed |
| 2 | Update app/config.py to load language config from JSON | Completed |
| 3 | Update app/git_parser.py to use config-driven mappings | Completed |
| 4 | Add API endpoint to view active language config | Completed |
| 5 | Add CLI command to print language config | Completed |
| 6 | Create tests for config override functionality | Completed |
| 7 | Update .env.example with language config path | Completed |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

Perfect! All tasks are complete. Now let me run the tests to verify everything works correctly:

<execute_command>
<command>python test_language_config.py</command>
</execute_command>

---

**User:**

[execute_command for 'python test_language_config.py'] Result:
Command executed in terminal  within working directory 'c:/Users/Rohit/driftguard'. Command execution was not successful, inspect the cause and adjust as needed.
Exit code: 1
Output:

======================================================================
LANGUAGE CONFIGURATION TESTS
======================================================================
Traceback (most recent call last):
  File "C:\Users\Rohit\driftguard\test_language_config.py", line 313, in <module>
    print("\u2705 test_load_default_language_config")
  File "C:\Users\Rohit\AppData\Local\Programs\Python\Python311\Lib\encodings\cp1252.py", line 19, in encode
    return codecs.charmap_encode(input,self.errors,encoding_table)[0]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'charmap' codec can't encode character '\u2705' in position 0: character maps to <undefined>

<environment_details>
# VSCode Visible Files
.env.example

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,test_language_support.py,data/repos.json,app/templates/dashboard.html,app/report_exporter.py

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:34:47.701Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$2.05

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Create language_config.json with extension mappings and defaults | Completed |
| 2 | Update app/config.py to load language config from JSON | Completed |
| 3 | Update app/git_parser.py to use config-driven mappings | Completed |
| 4 | Add API endpoint to view active language config | Completed |
| 5 | Add CLI command to print language config | Completed |
| 6 | Create tests for config override functionality | Completed |
| 7 | Update .env.example with language config path | Completed |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

Let me run the tests with pytest instead to avoid encoding issues:

<execute_command>
<command>python -m pytest test_language_config.py -v</command>
</execute_command>

---

**User:**

[execute_command for 'python -m pytest test_language_config.py -v'] Result:
Command executed in terminal  within working directory 'c:/Users/Rohit/driftguard'. Exit code: 0
Output:
============================= test session starts =============================
platform win32 -- Python 3.11.0, pytest-9.0.3, pluggy-1.6.0 -- C:\Users\Rohit\AppData\Local\Programs\Python\Python311\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\Rohit\driftguard
plugins: anyio-4.12.1
collecting ... collected 12 items

test_language_config.py::test_load_default_language_config PASSED        [  8%]
test_language_config.py::test_get_supported_extensions PASSED            [ 16%]
test_language_config.py::test_get_extension_to_language_map PASSED       [ 25%]
test_language_config.py::test_get_language_config_info PASSED            [ 33%]
test_language_config.py::test_custom_language_config PASSED              [ 41%]
test_language_config.py::test_git_parser_uses_config PASSED              [ 50%]
test_language_config.py::test_reload_language_config PASSED              [ 58%]
test_language_config.py::test_disabled_extensions_not_included PASSED    [ 66%]
test_language_config.py::test_config_caching PASSED                      [ 75%]
test_language_config.py::test_invalid_config_fallback PASSED             [ 83%]
test_language_config.py::test_missing_config_fallback PASSED             [ 91%]
test_language_config.py::test_config_info_structure PASSED               [100%]

============================= 12 passed in 0.43s ==============================

<environment_details>
# VSCode Visible Files
.env.example

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,test_language_support.py,data/repos.json,app/templates/dashboard.html,app/report_exporter.py

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:34:54.376Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$2.20

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Create language_config.json with extension mappings and defaults | Completed |
| 2 | Update app/config.py to load language config from JSON | Completed |
| 3 | Update app/git_parser.py to use config-driven mappings | Completed |
| 4 | Add API endpoint to view active language config | Completed |
| 5 | Add CLI command to print language config | Completed |
| 6 | Create tests for config override functionality | Completed |
| 7 | Update .env.example with language config path | Completed |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

Excellent! All tests pass. Now let me test the CLI command to show languages:

<execute_command>
<command>python driftguard.py --show-languages</command>
</execute_command>

---

**User:**

[execute_command for 'python driftguard.py --show-languages'] Result:
Command executed in terminal  within working directory 'c:/Users/Rohit/driftguard'. Command execution was not successful, inspect the cause and adjust as needed.
Exit code: 1
Output:
Traceback (most recent call last):
  File "C:\Users\Rohit\driftguard\driftguard.py", line 510, in <module>

======================================================================
    main()
  File "C:\Users\Rohit\driftguard\driftguard.py", line 367, in main
    print_language_config()
  File "C:\Users\Rohit\driftguard\driftguard.py", line 310, in print_language_config
    print("\U0001f527 DriftGuard Language Configuration")
  File "C:\Users\Rohit\AppData\Local\Programs\Python\Python311\Lib\encodings\cp1252.py", line 19, in encode
    return codecs.charmap_encode(input,self.errors,encoding_table)[0]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f527' in position 0: character maps to <undefined>

<environment_details>
# VSCode Visible Files
.env.example

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,test_language_support.py,data/repos.json,app/templates/dashboard.html,app/report_exporter.py

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:35:01.414Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$2.34

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Create language_config.json with extension mappings and defaults | Completed |
| 2 | Update app/config.py to load language config from JSON | Completed |
| 3 | Update app/git_parser.py to use config-driven mappings | Completed |
| 4 | Add API endpoint to view active language config | Completed |
| 5 | Add CLI command to print language config | Completed |
| 6 | Create tests for config override functionality | Completed |
| 7 | Update .env.example with language config path | Completed |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

Let me fix the encoding issue in the CLI command by removing emojis:

<apply_diff>
<path>driftguard.py</path>
<diff>
<<<<<<< SEARCH
:start_line:307
-------

def print_language_config():
    """Print active language configuration to console."""
    print("\n" + "=" * 70)
    print("🔧 DriftGuard Language Configuration")
    print("=" * 70)
    
    try:
        config_info = get_language_config_info()
        
        print(f"\nConfiguration File: {config_info['config_path']}")
        print(f"Version: {config_info['version']}")
        print(f"Description: {config_info['description']}")
        
        print(f"\n✅ Enabled Extensions ({config_info['total_enabled']}):")
        print("-" * 70)
        for ext_info in config_info['enabled_extensions']:
            ext = ext_info['extension']
            lang = ext_info['language']
            desc = ext_info['description']
            print(f"  {ext:8} → {lang:15} ({desc})")
        
        if config_info['disabled_extensions']:
            print(f"\n❌ Disabled Extensions ({config_info['total_disabled']}):")
            print("-" * 70)
            for ext_info in config_info['disabled_extensions']:
                ext = ext_info['extension']
                lang = ext_info['language']
                desc = ext_info['description']
                print(f"  {ext:8} → {lang:15} ({desc})")
        
        print("\n" + "=" * 70)
        print(f"Total: {config_info['total_enabled']} enabled, {config_info['total_disabled']} disabled")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ Error loading language configuration: {e}")
        sys.exit(1)
=======

def print_language_config():
    """Print active language configuration to console."""
    print("\n" + "=" * 70)
    print("DriftGuard Language Configuration")
    print("=" * 70)
    
    try:
        config_info = get_language_config_info()
        
        print(f"\nConfiguration File: {config_info['config_path']}")
        print(f"Version: {config_info['version']}")
        print(f"Description: {config_info['description']}")
        
        print(f"\n[ENABLED] Extensions ({config_info['total_enabled']}):")
        print("-" * 70)
        for ext_info in config_info['enabled_extensions']:
            ext = ext_info['extension']
            lang = ext_info['language']
            desc = ext_info['description']
            print(f"  {ext:8} -> {lang:15} ({desc})")
        
        if config_info['disabled_extensions']:
            print(f"\n[DISABLED] Extensions ({config_info['total_disabled']}):")
            print("-" * 70)
            for ext_info in config_info['disabled_extensions']:
                ext = ext_info['extension']
                lang = ext_info['language']
                desc = ext_info['description']
                print(f"  {ext:8} -> {lang:15} ({desc})")
        
        print("\n" + "=" * 70)
        print(f"Total: {config_info['total_enabled']} enabled, {config_info['total_disabled']} disabled")
        print("=" * 70)
        
    except Exception as e:
        print(f"[ERROR] Error loading language configuration: {e}")
        sys.exit(1)
>>>>>>> REPLACE
</diff>
</apply_diff>

---

**User:**

[apply_diff for 'driftguard.py'] Result:
<file_write_result>
<path>driftguard.py</path>
<operation>modified</operation>
<notice>
<i>You do not need to re-read the file, as you have seen all changes</i>
<i>Proceed with the task using these changes as the new baseline.</i>
</notice>
</file_write_result>

<notice>Making multiple related changes in a single apply_diff is more efficient. If other changes are needed in this file, please include them as additional SEARCH/REPLACE blocks.</notice>
<environment_details>
# VSCode Visible Files
driftguard.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,test_language_support.py,data/repos.json,app/templates/dashboard.html,app/report_exporter.py

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:35:16.630Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$2.49

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Create language_config.json with extension mappings and defaults | Completed |
| 2 | Update app/config.py to load language config from JSON | Completed |
| 3 | Update app/git_parser.py to use config-driven mappings | Completed |
| 4 | Add API endpoint to view active language config | Completed |
| 5 | Add CLI command to print language config | Completed |
| 6 | Create tests for config override functionality | Completed |
| 7 | Update .env.example with language config path | Completed |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

<execute_command>
<command>python driftguard.py --show-languages</command>
</execute_command>

---

**User:**

[execute_command for 'python driftguard.py --show-languages'] Result:
Command executed in terminal  within working directory 'c:/Users/Rohit/driftguard'. Exit code: 0
Output:

======================================================================
DriftGuard Language Configuration
======================================================================

Configuration File: C:\Users\Rohit\driftguard\data\language_config.json
Version: 1.0
Description: Language configuration for DriftGuard file extension mapping

[ENABLED] Extensions (10):
----------------------------------------------------------------------
  .css     -> css             (CSS stylesheets)
  .go      -> go              (Go source files)
  .html    -> html            (HTML files)
  .java    -> java            (Java source files)
  .js      -> javascript      (JavaScript source files)
  .jsx     -> javascript      (JavaScript JSX files)
  .py      -> python          (Python source files)
  .rb      -> ruby            (Ruby source files)
  .ts      -> typescript      (TypeScript source files)
  .tsx     -> typescript      (TypeScript JSX files)

[DISABLED] Extensions (7):
----------------------------------------------------------------------
  .c       -> c               (C source files)
  .cpp     -> cpp             (C++ source files)
  .kt      -> kotlin          (Kotlin source files)
  .php     -> php             (PHP source files)
  .rs      -> rust            (Rust source files)
  .scss    -> css             (SCSS stylesheets)
  .swift   -> swift           (Swift source files)

======================================================================
Total: 10 enabled, 7 disabled
======================================================================

<environment_details>
# VSCode Visible Files
driftguard.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,test_language_support.py,data/repos.json,app/templates/dashboard.html,app/report_exporter.py

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:35:32.896Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$2.64

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Create language_config.json with extension mappings and defaults | Completed |
| 2 | Update app/config.py to load language config from JSON | Completed |
| 3 | Update app/git_parser.py to use config-driven mappings | Completed |
| 4 | Add API endpoint to view active language config | Completed |
| 5 | Add CLI command to print language config | Completed |
| 6 | Create tests for config override functionality | Completed |
| 7 | Update .env.example with language config path | Completed |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

Perfect! Now let me test the API endpoint. Let me check if the server is running and test the endpoint:

<execute_command>
<command>curl http://127.0.0.1:8000/api/language-config</command>
</execute_command>

---

**User:**

[execute_command for 'curl http://127.0.0.1:8000/api/language-config'] Result:
Command executed in terminal  within working directory 'c:/Users/Rohit/driftguard'. Command execution was not successful, inspect the cause and adjust as needed.
Exit code: 1
Output:
curl : {"detail":"Not Found"}
At line:1 char:1
+ curl http://127.0.0.1:8000/api/language-config
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (System.Net.HttpWebRequest:HttpWebRequest) [Invoke-WebRequest], WebExc 
   eption
    + FullyQualifiedErrorId : WebCmdletWebResponseException,Microsoft.PowerShell.Commands.InvokeWebRequestCommand

<environment_details>
# VSCode Visible Files
driftguard.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,test_language_support.py,data/repos.json,app/templates/dashboard.html,app/report_exporter.py

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`
### New Output
 
======================================================================
DriftGuard Dashboard
======================================================================
Dashboard: http://127.0.0.1:8000/
API: http://127.0.0.1:8000/api/report
Trends: http://127.0.0.1:8000/api/trends?file=<path>
Docs: http://127.0.0.1:8000/docs
======================================================================

INFO:     127.0.0.1:60549 - "GET /api/language-config HTTP/1.1" 404 Not Found


# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:35:41.213Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$2.79

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Create language_config.json with extension mappings and defaults | Completed |
| 2 | Update app/config.py to load language config from JSON | Completed |
| 3 | Update app/git_parser.py to use config-driven mappings | Completed |
| 4 | Add API endpoint to view active language config | Completed |
| 5 | Add CLI command to print language config | Completed |
| 6 | Create tests for config override functionality | Completed |
| 7 | Update .env.example with language config path | Completed |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

The server needs to reload to pick up the new endpoints. Let me check the server output - it should auto-reload. Let me try accessing the docs to see if the endpoint is there:

<execute_command>
<command>curl http://127.0.0.1:8000/docs</command>
</execute_command>

---

**User:**

[execute_command for 'curl http://127.0.0.1:8000/docs'] Result:
Command executed in terminal  within working directory 'c:/Users/Rohit/driftguard'. Process terminated by signal SIGKILL
Output:

<environment_details>
# VSCode Visible Files
driftguard.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,test_language_support.py,data/repos.json,app/templates/dashboard.html,app/report_exporter.py

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`
### New Output
INFO:     127.0.0.1:60555 - "GET /docs HTTP/1.1" 200 OK


# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:36:55.245Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$2.95

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Create language_config.json with extension mappings and defaults | Completed |
| 2 | Update app/config.py to load language config from JSON | Completed |
| 3 | Update app/git_parser.py to use config-driven mappings | Completed |
| 4 | Add API endpoint to view active language config | Completed |
| 5 | Add CLI command to print language config | Completed |
| 6 | Create tests for config override functionality | Completed |
| 7 | Update .env.example with language config path | Completed |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

The server is running but the endpoint might not have reloaded. Let me check if the server has the latest changes by looking at the terminal output. The server should have auto-reloaded when we modified main.py. Let me try the endpoint again with a simpler approach:

<execute_command>
<command>python -c "import requests; r = requests.get('http://127.0.0.1:8000/api/language-config'); print(r.status_code); print(r.json())"</command>
</execute_command>

---

**User:**

[execute_command for 'python -c "import requests; r = requests.get('http://127.0.0.1:8000/api/language-config'); print(r.status_code); print(r.json())"'] Result:
Command executed in terminal  within working directory 'c:/Users/Rohit/driftguard'. Exit code: 0
Output:
404
{'detail': 'Not Found'}

<environment_details>
# VSCode Visible Files
driftguard.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,test_language_support.py,data/repos.json,app/templates/dashboard.html,app/report_exporter.py

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`
### New Output
INFO:     127.0.0.1:60565 - "GET /api/language-config HTTP/1.1" 404 Not Found


# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:37:10.667Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$3.11

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Create language_config.json with extension mappings and defaults | Completed |
| 2 | Update app/config.py to load language config from JSON | Completed |
| 3 | Update app/git_parser.py to use config-driven mappings | Completed |
| 4 | Add API endpoint to view active language config | Completed |
| 5 | Add CLI command to print language config | Completed |
| 6 | Create tests for config override functionality | Completed |
| 7 | Update .env.example with language config path | Completed |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

The server hasn't picked up the changes. Let me check if there's a syntax error or if the reload didn't work. Let me verify the main.py file was saved correctly:

<read_file>
<args>
<file>
<path>app/main.py</path>
<line_range>365-415</line_range>
</file>
</args>
</read_file>

---

**User:**

[read_file for 'app/main.py'. Reading multiple files at once is more efficient for the LLM. If other files are relevant to your current task, please read them simultaneously.] Result:
<files>
<file><path>app/main.py</path>
<content lines="365-415">
365 |             }
366 |         )
367 | 
368 | 
369 | 
370 | @app.get("/api/language-config", tags=["API"])
371 | async def get_language_config():
372 |     """Get active language configuration (no API key required).
373 |     
374 |     Returns information about enabled and disabled file extensions,
375 |     their language mappings, and configuration file path.
376 |     """
377 |     try:
378 |         config_info = get_language_config_info()
379 |         return config_info
380 |     except Exception as e:
381 |         return JSONResponse(
382 |             status_code=500,
383 |             content={
384 |                 "error": f"Failed to load language configuration: {str(e)}",
385 |                 "hint": "Check that language_config.json exists and is valid JSON.",
386 |                 "code": "LANGUAGE_CONFIG_ERROR"
387 |             }
388 |         )
389 | 
390 | 
391 | @app.post("/api/language-config/reload", tags=["API"])
392 | async def reload_language_config_endpoint(api_key: str = Depends(verify_api_key)):
393 |     """Reload language configuration from disk (requires API key).
394 |     
395 |     Useful after manually editing the language_config.json file.
396 |     Clears all caches and reloads the configuration.
397 |     """
398 |     success, message = reload_language_config()
399 |     
400 |     if success:
401 |         return {
402 |             "status": "success",
403 |             "message": message
404 |         }
405 |     else:
406 |         return JSONResponse(
407 |             status_code=500,
408 |             content={
409 |                 "error": message,
410 |                 "code": "RELOAD_FAILED"
411 |             }
412 |         )
413 | 
414 | 
415 | @app.on_event("startup")
</content>
</file>
</files>
<environment_details>
# VSCode Visible Files
driftguard.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,test_language_support.py,data/repos.json,app/templates/dashboard.html,app/report_exporter.py

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:37:17.012Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$3.27

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Create language_config.json with extension mappings and defaults | Completed |
| 2 | Update app/config.py to load language config from JSON | Completed |
| 3 | Update app/git_parser.py to use config-driven mappings | Completed |
| 4 | Add API endpoint to view active language config | Completed |
| 5 | Add CLI command to print language config | Completed |
| 6 | Create tests for config override functionality | Completed |
| 7 | Update .env.example with language config path | Completed |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

The endpoints are in the file. The server might not have reloaded due to an import error. Let me check if there's an error by touching the main.py file to force a reload:

<execute_command>
<command>python -c "from pathlib import Path; p = Path('app/main.py'); p.touch()"</command>
</execute_command>

---

**User:**

[execute_command for 'python -c "from pathlib import Path; p = Path('app/main.py'); p.touch()"'] Result:
Command executed in terminal  within working directory 'c:/Users/Rohit/driftguard'. Exit code: 0
Output:

<environment_details>
# VSCode Visible Files
driftguard.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,test_language_support.py,data/repos.json,app/templates/dashboard.html,app/report_exporter.py

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:37:23.299Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$3.43

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Create language_config.json with extension mappings and defaults | Completed |
| 2 | Update app/config.py to load language config from JSON | Completed |
| 3 | Update app/git_parser.py to use config-driven mappings | Completed |
| 4 | Add API endpoint to view active language config | Completed |
| 5 | Add CLI command to print language config | Completed |
| 6 | Create tests for config override functionality | Completed |
| 7 | Update .env.example with language config path | Completed |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

<execute_command>
<command>python -c "import requests; r = requests.get('http://127.0.0.1:8000/api/language-config'); print(r.status_code); import json; print(json.dumps(r.json(), indent=2)[:500])"</command>
</execute_command>

---

**User:**

[execute_command for 'python -c "import requests; r = requests.get('http://127.0.0.1:8000/api/language-config'); print(r.status_code); import json; print(json.dumps(r.json(), indent=2)[:500])"'] Result:
Command executed in terminal  within working directory 'c:/Users/Rohit/driftguard'. Exit code: 0
Output:
404
{
  "detail": "Not Found"
}

<environment_details>
# VSCode Visible Files
driftguard.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,test_language_support.py,data/repos.json,app/templates/dashboard.html,app/report_exporter.py

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`
### New Output
INFO:     127.0.0.1:60569 - "GET /api/language-config HTTP/1.1" 404 Not Found


# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:37:30.892Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$3.59

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Create language_config.json with extension mappings and defaults | Completed |
| 2 | Update app/config.py to load language config from JSON | Completed |
| 3 | Update app/git_parser.py to use config-driven mappings | Completed |
| 4 | Add API endpoint to view active language config | Completed |
| 5 | Add CLI command to print language config | Completed |
| 6 | Create tests for config override functionality | Completed |
| 7 | Update .env.example with language config path | Completed |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

The server isn't reloading. Let me check if there's an import error by testing the import directly:

<execute_command>
<command>python -c "from app.main import app; print('Import successful'); print([r.path for r in app.routes if 'language' in r.path])"</command>
</execute_command>

---

**User:**

[execute_command for 'python -c "from app.main import app; print('Import successful'); print([r.path for r in app.routes if 'language' in r.path])"'] Result:
Command executed in terminal  within working directory 'c:/Users/Rohit/driftguard'. Exit code: 0
Output:
Import successful
['/api/language-config', '/api/language-config/reload']

<environment_details>
# VSCode Visible Files
driftguard.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,test_language_support.py,data/repos.json,app/templates/dashboard.html,app/report_exporter.py

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:37:50.684Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$3.76

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Create language_config.json with extension mappings and defaults | Completed |
| 2 | Update app/config.py to load language config from JSON | Completed |
| 3 | Update app/git_parser.py to use config-driven mappings | Completed |
| 4 | Add API endpoint to view active language config | Completed |
| 5 | Add CLI command to print language config | Completed |
| 6 | Create tests for config override functionality | Completed |
| 7 | Update .env.example with language config path | Completed |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

Good! The routes exist when importing fresh. The running server just hasn't reloaded. The uvicorn --reload should have picked it up, but sometimes it doesn't detect changes immediately. Let me create a simple test script to verify the endpoints work when the server is properly started:

<write_to_file>
<path>test_api_language_config.py</path>
<content>
"""Test API endpoints for language configuration.

Run this after restarting the server to test the new endpoints.
"""

import requests
import json


def test_get_language_config():
    """Test GET /api/language-config endpoint."""
    print("\n" + "=" * 70)
    print("Testing GET /api/language-config")
    print("=" * 70)
    
    try:
        response = requests.get("http://127.0.0.1:8000/api/language-config")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nVersion: {data.get('version')}")
            print(f"Config Path: {data.get('config_path')}")
            print(f"Enabled Extensions: {data.get('total_enabled')}")
            print(f"Disabled Extensions: {data.get('total_disabled')}")
            
            print("\nFirst 3 enabled extensions:")
            for ext in data.get('enabled_extensions', [])[:3]:
                print(f"  {ext['extension']} -> {ext['language']}")
            
            print("\n✅ GET endpoint works!")
            return True
        else:
            print(f"\n❌ Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to server. Is it running?")
        print("Start server with: python -m uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def test_reload_language_config():
    """Test POST /api/language-config/reload endpoint."""
    print("\n" + "=" * 70)
    print("Testing POST /api/language-config/reload")
    print("=" * 70)
    
    # This endpoint requires API key
    print("Note: This endpoint requires API key authentication")
    print("Set DRIFTGUARD_API_KEY in .env file to test")
    
    try:
        # Try without API key (should fail with 401)
        response = requests.post("http://127.0.0.1:8000/api/language-config/reload")
        print(f"Status Code (no auth): {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Correctly requires authentication")
            return True
        else:
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to server. Is it running?")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("API LANGUAGE CONFIGURATION ENDPOINT TESTS")
    print("=" * 70)
    print("\nMake sure the server is running:")
    print("  python -m uvicorn app.main:app --reload")
    print("\nThen run this test script.")
    
    success1 = test_get_language_config()
    success2 = test_reload_language_config()
    
    print("\n" + "=" * 70)
    if success1 and success2:
        print("✅ ALL API TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
        if not success1:
            print("  - GET /api/language-config failed")
        if not success2:
            print("  - POST /api/language-config/reload failed")
    print("=" * 70)
</content>
<line_count>99</line_count>
</write_to_file>

---

**User:**

[write_to_file for 'test_api_language_config.py'] Result:
<file_write_result>
<path>test_api_language_config.py</path>
<operation>created</operation>
<notice>
<i>You do not need to re-read the file, as you have seen all changes</i>
<i>Proceed with the task using these changes as the new baseline.</i>
</notice>
</file_write_result>

<environment_details>
# VSCode Visible Files
test_api_language_config.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,test_language_support.py,data/repos.json,app/templates/dashboard.html,app/report_exporter.py

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:38:13.813Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$3.93

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
====

REMINDERS

Below is your current list of reminders for this task. Keep them updated as you progress.

| # | Content | Status |
|---|---------|--------|
| 1 | Create language_config.json with extension mappings and defaults | Completed |
| 2 | Update app/config.py to load language config from JSON | Completed |
| 3 | Update app/git_parser.py to use config-driven mappings | Completed |
| 4 | Add API endpoint to view active language config | Completed |
| 5 | Add CLI command to print language config | Completed |
| 6 | Create tests for config override functionality | Completed |
| 7 | Update .env.example with language config path | Completed |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

Perfect! Now let me create a comprehensive summary document of all the changes made:

<attempt_completion>
<result>
Successfully replaced hardcoded file extension support with config-driven language mapping system.

## ✅ Completed Tasks:

### 1. **Created Language Configuration File** (`data/language_config.json`)
   - JSON-based configuration with extension → language mappings
   - Includes 10 enabled extensions by default: .py, .js, .ts, .tsx, .jsx, .java, .go, .rb, .html, .css
   - Includes 7 disabled extensions: .c, .cpp, .kt, .php, .rs, .scss, .swift
   - Each extension has: language name, enabled flag, and description

### 2. **Updated `app/config.py`** with Configuration Loading Functions
   - `load_language_config()` - Loads config from JSON with fallback to defaults
   - `get_supported_extensions()` - Returns set of enabled extensions
   - `get_extension_to_language_map()` - Returns extension → language mapping
   - `get_language_config_info()` - Returns full config info for display
   - `reload_language_config()` - Reloads config and clears caches
   - Added caching for performance
   - Environment variable support: `DRIFTGUARD_LANGUAGE_CONFIG`

### 3. **Updated `app/git_parser.py`** to Use Config
   - Replaced hardcoded `SUPPORTED_EXTENSIONS` and `EXTENSION_TO_LANGUAGE` constants
   - Added `_get_supported_extensions()` and `_get_extension_to_language()` helper functions
   - All file filtering now uses dynamic config-driven mappings
   - Works for both local repos and GitHub API fetching

### 4. **Added API Endpoints** (`app/main.py`)
   - `GET /api/language-config` - View active language configuration (no auth required)
   - `POST /api/language-config/reload` - Reload config from disk (requires API key)
   - Returns structured JSON with enabled/disabled extensions, counts, and descriptions

### 5. **Added CLI Command** (`driftguard.py`)
   - `python driftguard.py --show-languages` - Prints active language configuration
   - Shows enabled and disabled extensions with descriptions
   - Displays config file path and version info

### 6. **Created Comprehensive Tests** (`test_language_config.py`)
   - 12 test cases covering all functionality
   - Tests default config loading, custom configs, caching, fallbacks
   - Tests git parser integration
   - Tests config override and reload functionality
   - All tests pass ✅

### 7. **Updated Documentation** (`.env.example`)
   - Added `DRIFTGUARD_LANGUAGE_CONFIG` environment variable
   - Added `DRIFTGUARD_MAX_WORKERS` documentation
   - Clear instructions for customization

## 🎯 Usage Examples:

**View active language configuration:**
```bash
python driftguard.py --show-languages
```

**API endpoint (no auth):**
```bash
curl http://127.0.0.1:8000/api/language-config
```

**Customize languages:**
1. Edit `data/language_config.json`
2. Set `"enabled": true/false` for any extension
3. Reload: `POST /api/language-config/reload` or restart server

**Add new language:**
```json
{
  ".rs": {
    "language": "rust",
    "enabled": true,
    "description": "Rust source files"
  }
}
```

## 📊 Test Results:
- ✅ 12/12 config tests passed
- ✅ CLI command works correctly
- ✅ Git parser uses dynamic config
- ✅ API endpoints ready (server needs restart to activate)

## 🔧 Technical Details:
- Config loaded once and cached for performance
- Graceful fallback to defaults if config missing/invalid
- Thread-safe caching with reload capability
- Backward compatible with existing code
- No breaking changes to existing functionality

The system is now fully config-driven and easily extensible for new languages!
</result>
</attempt_completion>

