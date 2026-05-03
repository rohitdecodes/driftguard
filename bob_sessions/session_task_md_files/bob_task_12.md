**User:**

<task>
Add rate limiting around Bob analysis calls in DriftGuard.

Requirements:
1) Implement token-bucket rate limiter class:
   - configurable tokens per minute
   - thread-safe
2) Apply limiter in batch analysis so each Bob call acquires a token
3) Config options:
   - BOB_RATE_LIMIT_PER_MINUTE (default 30)
   - BOB_RATE_LIMIT_BURST (default 5)
4) On throttle wait, log useful message:
   - "Rate limiter waiting Xs before next Bob request"
5) Add tests for burst behavior and refill behavior.
</task>
<environment_details>
# VSCode Visible Files
demo_cache.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,app/git_parser.py,test_language_support.py,data/repos.json,app/templates/dashboard.html

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T14:58:31.852Z
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
context.md
demo_cache.py
docker-compose.yml
Dockerfile
driftguard.py
PHASE_1.md
PHASE_2.md
README.md
requirements.txt
test_cache.py
test_db.py
test_integration_trends.py
test_integration.py
test_language_support.py
test_remediation_api.py
test_remediation_complete.py
test_trends_endpoint.py
test_trends.py
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
app/remediation.py
app/report_exporter.py
app/report_generator.py
app/scorer.py
app/trends.py
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

I'll help you add rate limiting around Bob analysis calls in DriftGuard. Let me start by examining the current codebase structure to understand how Bob analysis is implemented.

<read_file>
<args>
<file>
<path>app/bob_analyzer.py</path>
</file>
<file>
<path>app/config.py</path>
</file>
<file>
<path>driftguard.py</path>
</file>
</args>
</read_file>

---

**User:**

[read_file for 'app/bob_analyzer.py', 'app/config.py', 'driftguard.py'] Result:
<files>
<file><path>app/bob_analyzer.py</path>
<content lines="1-570">
  1 | """bob_analyzer.py
  2 | 
  3 | Rule-based code decay analyzer for DriftGuard.
  4 | Analyzes file diffs using heuristics (no external APIs/LLMs).
  5 | """
  6 | 
  7 | import re
  8 | from typing import List, Dict, Optional
  9 | from app.models import FileDiff, AnalysisResult
 10 | from app.config import Config
 11 | from app.baseline_profile import load_baseline, format_baseline_summary
 12 | from app.language_prompts import get_language_prompt, get_focus_areas, get_complexity_indicators
 13 | from app.db import (
 14 |     compute_diff_hash,
 15 |     get_cached_analysis,
 16 |     save_cached_analysis,
 17 |     DEFAULT_DB_PATH
 18 | )
 19 | 
 20 | # Global baseline cache
 21 | _baseline_cache: Optional[Dict] = None
 22 | 
 23 | 
 24 | def set_baseline(repo_path: str) -> None:
 25 |     """Load and cache baseline profile for the repository.
 26 |     
 27 |     Args:
 28 |         repo_path: path to repository root
 29 |     """
 30 |     global _baseline_cache
 31 |     _baseline_cache = load_baseline(repo_path)
 32 |     
 33 |     if _baseline_cache:
 34 |         print(f"\n[BASELINE] Loaded baseline profile:")
 35 |         print(format_baseline_summary(_baseline_cache))
 36 |     else:
 37 |         print("\n[BASELINE] No baseline profile found. Scores will use default thresholds.")
 38 | 
 39 | 
 40 | def get_baseline() -> Optional[Dict]:
 41 |     """Get cached baseline profile."""
 42 |     return _baseline_cache
 43 | 
 44 | 
 45 | def analyze_file_decay(file_data: Dict, use_cache: bool = True,
 46 |                        db_path: str = DEFAULT_DB_PATH) -> Dict:
 47 |     """
 48 |     Analyze a single file's decay using rule-based heuristics.
 49 |     
 50 |     Args:
 51 |         file_data: Dict with keys: file_path, diff_text, total_commits, language
 52 |         use_cache: whether to use cache (default: True, respects Config.CACHE_ENABLED)
 53 |         db_path: path to SQLite database file
 54 |         
 55 |     Returns:
 56 |         Dict with decay scores and analysis (AnalysisResult schema)
 57 |     """
 58 |     diff_text = file_data.get('diff_text', '')
 59 |     file_path = file_data.get('file_path', '')
 60 |     language = file_data.get('language', 'unknown')
 61 |     
 62 |     # Check cache if enabled
 63 |     if use_cache and Config.CACHE_ENABLED and diff_text:
 64 |         diff_hash = compute_diff_hash(diff_text)
 65 |         ttl = Config.CACHE_TTL_HOURS if Config.CACHE_TTL_HOURS > 0 else None
 66 |         
 67 |         cached_result = get_cached_analysis(file_path, diff_hash, ttl, db_path)
 68 |         if cached_result:
 69 |             # Cache hit - return cached result
 70 |             return cached_result
 71 |     
 72 |     # Cache miss or cache disabled - perform analysis
 73 |     # Get baseline for context-aware scoring
 74 |     baseline = get_baseline()
 75 |     
 76 |     # Calculate individual dimension scores
 77 |     doc_score = _calculate_documentation_drift_score(diff_text, language)
 78 |     test_score = _calculate_test_drift_score(file_path, diff_text)
 79 |     complexity_score = _calculate_complexity_growth_score(diff_text, language)
 80 |     naming_score = _calculate_naming_consistency_score(diff_text, language)
 81 |     
 82 |     # Determine top risk and recommendation
 83 |     scores = {
 84 |         'documentation': doc_score,
 85 |         'test_coverage': test_score,
 86 |         'complexity': complexity_score,
 87 |         'naming': naming_score
 88 |     }
 89 |     
 90 |     lowest_dimension = min(scores.keys(), key=lambda k: scores[k])
 91 |     lowest_score = scores[lowest_dimension]
 92 |     
 93 |     top_risk, recommendation = _generate_risk_and_recommendation(
 94 |         lowest_dimension, lowest_score, file_path, language
 95 |     )
 96 |     
 97 |     # Generate decay summary
 98 |     decay_summary = _generate_decay_summary(scores, file_path)
 99 |     
100 |     # Build result dict matching AnalysisResult schema
101 |     result: AnalysisResult = {
102 |         'file_path': file_data.get('file_path', ''),
103 |         'language': file_data.get('language', 'unknown'),
104 |         'total_commits': file_data.get('total_commits', 0),
105 |         'diff_text': diff_text,
106 |         'last_modified': file_data.get('last_modified', ''),
107 |         'commit_hashes': file_data.get('commit_hashes', []),
108 |         'documentation_drift_score': doc_score,
109 |         'test_drift_score': test_score,
110 |         'complexity_growth_score': complexity_score,
111 |         'naming_consistency_score': naming_score,
112 |         'decay_summary': decay_summary,
113 |         'top_risk': top_risk,
114 |         'recommendation': recommendation,
115 |     }
116 |     
117 |     # Save to cache if enabled
118 |     if use_cache and Config.CACHE_ENABLED and diff_text:
119 |         diff_hash = compute_diff_hash(diff_text)
120 |         save_cached_analysis(file_path, diff_hash, language, result, db_path)
121 |     
122 |     return result
123 | 
124 | 
125 | def batch_analyze(file_diffs: List[Dict]) -> List[Dict]:
126 |     """
127 |     Analyze multiple files with progress reporting.
128 |     
129 |     Args:
130 |         file_diffs: List of file_data dicts from git_parser
131 |         
132 |     Returns:
133 |         List of AnalysisResult dicts
134 |     """
135 |     results = []
136 |     total = len(file_diffs)
137 |     
138 |     print(f"\n[ANALYZER] Analyzing {total} files...")
139 |     print("-" * 60)
140 |     
141 |     for i, file_data in enumerate(file_diffs, 1):
142 |         file_path = file_data.get('file_path', 'unknown')
143 |         print(f"[{i}/{total}] Analyzing: {file_path}")
144 |         
145 |         try:
146 |             result = analyze_file_decay(file_data)
147 |             results.append(result)
148 |             
149 |             # Show quick score summary
150 |             avg_score = (
151 |                 result['documentation_drift_score'] +
152 |                 result['test_drift_score'] +
153 |                 result['complexity_growth_score'] +
154 |                 result['naming_consistency_score']
155 |             ) / 4
156 |             print(f"         Average score: {avg_score:.1f}/100")
157 |             
158 |         except Exception as e:
159 |             print(f"         [ERROR] Failed to analyze: {e}")
160 |             continue
161 |     
162 |     print("-" * 60)
163 |     print(f"[ANALYZER] Completed: {len(results)}/{total} files analyzed\n")
164 |     
165 |     return results
166 | 
167 | 
168 | # ============================================================================
169 | # DIMENSION SCORING FUNCTIONS
170 | # ============================================================================
171 | 
172 | def _calculate_documentation_drift_score(diff_text: str, language: str) -> int:
173 |     """
174 |     Score: 0-100 (higher = better documentation practices)
175 |     
176 |     Rule: If added 50+ lines with 0 comments/docstrings → 20, else 70+
177 |     Uses baseline docstring coverage to adjust expectations.
178 |     Language-specific patterns applied based on language_prompts.
179 |     """
180 |     lines = diff_text.split('\n')
181 |     added_lines = [line for line in lines if line.startswith('+') and not line.startswith('+++')]
182 |     
183 |     # Count added code lines (exclude empty lines)
184 |     added_code_lines = [line for line in added_lines if line.strip() and len(line.strip()) > 1]
185 |     added_count = len(added_code_lines)
186 |     
187 |     if added_count == 0:
188 |         return 100  # No changes, perfect score
189 |     
190 |     # Get baseline for context
191 |     baseline = get_baseline()
192 |     baseline_doc_coverage = baseline.get('docstring_coverage_pct', 50.0) if baseline else 50.0
193 |     
194 |     # Count added comments/docstrings with language-specific patterns
195 |     comment_patterns = {
196 |         'python': [r'^\+\s*#', r'^\+\s*"""', r"^\+\s*'''"],
197 |         'javascript': [r'^\+\s*//', r'^\+\s*/\*', r'^\+\s*\*'],
198 |         'typescript': [r'^\+\s*//', r'^\+\s*/\*', r'^\+\s*\*'],
199 |         'java': [r'^\+\s*//', r'^\+\s*/\*', r'^\+\s*\*'],
200 |         'go': [r'^\+\s*//', r'^\+\s*/\*', r'^\+\s*\*'],
201 |         'ruby': [r'^\+\s*#', r'^\+\s*=begin'],
202 |     }
203 |     
204 |     patterns = comment_patterns.get(language, [r'^\+\s*#', r'^\+\s*//'])
205 |     comment_count = 0
206 |     
207 |     for line in added_lines:
208 |         for pattern in patterns:
209 |             if re.search(pattern, line):
210 |                 comment_count += 1
211 |                 break
212 |     
213 |     # Calculate documentation ratio
214 |     doc_ratio = comment_count / added_count if added_count > 0 else 0
215 |     
216 |     # Apply scoring rules with baseline adjustment
217 |     threshold = Config.RULE_DOC_DRIFT_THRESHOLD_ADDED_LINES
218 |     
219 |     # Adjust expectations based on baseline
220 |     # If repo has low baseline coverage, be more lenient
221 |     if baseline_doc_coverage < 30:
222 |         leniency = 10
223 |     elif baseline_doc_coverage < 50:
224 |         leniency = 5
225 |     else:
226 |         leniency = 0
227 |     
228 |     if added_count >= threshold and comment_count == 0:
229 |         return max(20, 20 + leniency)  # Large change with no documentation
230 |     elif added_count >= threshold and doc_ratio < 0.05:
231 |         return max(40, 40 + leniency)  # Large change with minimal documentation
232 |     elif doc_ratio < 0.1:
233 |         return max(60, 60 + leniency)  # Some documentation but below 10%
234 |     elif doc_ratio < 0.2:
235 |         return 75  # Decent documentation (10-20%)
236 |     else:
237 |         return 90  # Good documentation (20%+)
238 | 
239 | 
240 | def _calculate_test_drift_score(file_path: str, diff_text: str) -> int:
241 |     """
242 |     Score: 0-100 (higher = better test coverage)
243 |     
244 |     Rule: If implementation changed but no test touched → 30, else 60+
245 |     """
246 |     is_test_file = _is_test_file(file_path)
247 |     
248 |     # If this is a test file, give high score
249 |     if is_test_file:
250 |         return 85
251 |     
252 |     # Check if diff mentions test-related changes
253 |     test_keywords = ['test', 'spec', 'mock', 'assert', 'expect', 'describe', 'it(']
254 |     has_test_mentions = any(keyword in diff_text.lower() for keyword in test_keywords)
255 |     
256 |     # Count lines changed
257 |     lines = diff_text.split('\n')
258 |     added_lines = len([l for l in lines if l.startswith('+') and not l.startswith('+++')])
259 |     deleted_lines = len([l for l in lines if l.startswith('-') and not l.startswith('---')])
260 |     total_changes = added_lines + deleted_lines
261 |     
262 |     # Scoring logic
263 |     if total_changes == 0:
264 |         return 100  # No changes
265 |     
266 |     if total_changes > 50 and not has_test_mentions:
267 |         return 30  # Large implementation change with no test mentions
268 |     elif total_changes > 20 and not has_test_mentions:
269 |         return 50  # Medium change with no test mentions
270 |     elif has_test_mentions:
271 |         return 75  # Test-related changes detected
272 |     else:
273 |         return 65  # Small change, acceptable
274 | 
275 | 
276 | def _calculate_complexity_growth_score(diff_text: str, language: str) -> int:
277 |     """
278 |     Score: 0-100 (higher = better complexity management)
279 |     
280 |     Rule: Count indentation/nesting increases. High increase → 40, else 70+
281 |     Uses language-specific thresholds from Config.LANGUAGE_THRESHOLDS.
282 |     """
283 |     lines = diff_text.split('\n')
284 |     added_lines = [line for line in lines if line.startswith('+') and not line.startswith('+++')]
285 |     
286 |     if not added_lines:
287 |         return 100  # No changes
288 |     
289 |     # Get language-specific thresholds
290 |     lang_thresholds = Config.LANGUAGE_THRESHOLDS.get(language, Config.LANGUAGE_THRESHOLDS.get('python', {}))
291 |     max_function_lines = lang_thresholds.get('max_function_lines', 50)
292 |     max_nesting_depth = lang_thresholds.get('max_nesting_depth', 4)
293 |     complexity_threshold = lang_thresholds.get('complexity_threshold', 150)
294 |     
295 |     # Measure nesting depth increases
296 |     max_nesting = 0
297 |     avg_nesting = 0
298 |     nesting_samples = []
299 |     
300 |     for line in added_lines:
301 |         if not line.strip():
302 |             continue
303 |         
304 |         # Count leading whitespace (indentation)
305 |         stripped = line.lstrip('+')
306 |         if not stripped.strip():
307 |             continue
308 |             
309 |         indent = len(stripped) - len(stripped.lstrip())
310 |         
311 |         # Estimate nesting level (4 spaces or 1 tab = 1 level)
312 |         if '\t' in stripped[:indent]:
313 |             nesting_level = stripped[:indent].count('\t')
314 |         else:
315 |             nesting_level = indent // 4
316 |         
317 |         nesting_samples.append(nesting_level)
318 |         max_nesting = max(max_nesting, nesting_level)
319 |     
320 |     if nesting_samples:
321 |         avg_nesting = sum(nesting_samples) / len(nesting_samples)
322 |     
323 |     # Check for long functions (heuristic: many consecutive added lines)
324 |     consecutive_adds = 0
325 |     max_consecutive = 0
326 |     
327 |     for line in lines:
328 |         if line.startswith('+') and not line.startswith('+++'):
329 |             consecutive_adds += 1
330 |             max_consecutive = max(max_consecutive, consecutive_adds)
331 |         else:
332 |             consecutive_adds = 0
333 |     
334 |     # Scoring based on language-specific complexity indicators
335 |     if max_nesting > max_nesting_depth + 2:  # Very deep nesting
336 |         return 30
337 |     elif max_nesting > max_nesting_depth:  # Deep nesting
338 |         return 50
339 |     elif max_consecutive > max_function_lines * 2:  # Very long function addition
340 |         return 45
341 |     elif max_consecutive > max_function_lines:  # Long function addition
342 |         return 60
343 |     elif avg_nesting > max_nesting_depth - 1:  # Moderate average nesting
344 |         return 70
345 |     else:
346 |         return 85  # Good complexity management
347 | 
348 | 
349 | def _calculate_naming_consistency_score(diff_text: str, language: str) -> int:
350 |     """
351 |     Score: 0-100 (higher = better naming consistency)
352 |     
353 |     Rule: Look for snake_case vs camelCase inconsistencies → 50-80 based on violations
354 |     Uses language-specific naming conventions from language_prompts.
355 |     """
356 |     lines = diff_text.split('\n')
357 |     added_lines = [line for line in lines if line.startswith('+') and not line.startswith('+++')]
358 |     
359 |     if not added_lines:
360 |         return 100  # No changes
361 |     
362 |     # Extract identifiers from added lines
363 |     # Pattern: variable/function names (alphanumeric + underscore)
364 |     identifier_pattern = r'\b([a-z_][a-z0-9_]*)\b'
365 |     identifiers = []
366 |     
367 |     for line in added_lines:
368 |         # Skip comments and strings
369 |         if '#' in line or '//' in line or '/*' in line or '"' in line or "'" in line:
370 |             continue
371 |         
372 |         matches = re.findall(identifier_pattern, line.lower())
373 |         identifiers.extend(matches)
374 |     
375 |     if not identifiers:
376 |         return 100  # No identifiers found
377 |     
378 |     # Analyze naming patterns
379 |     snake_case_count = sum(1 for name in identifiers if '_' in name and name.islower())
380 |     camel_case_count = sum(1 for name in identifiers if '_' not in name and any(c.isupper() for c in name))
381 |     
382 |     # Get expected style from baseline or language defaults
383 |     baseline = get_baseline()
384 |     if baseline and baseline.get('dominant_naming_style'):
385 |         style = baseline['dominant_naming_style']
386 |     else:
387 |         # Language-specific conventions from language_prompts
388 |         expected_style = {
389 |             'python': 'snake_case',
390 |             'javascript': 'camelCase',
391 |             'typescript': 'camelCase',
392 |             'java': 'camelCase',
393 |             'go': 'camelCase',
394 |             'ruby': 'snake_case',
395 |         }
396 |         style = expected_style.get(language, 'snake_case')
397 |     
398 |     # Calculate consistency
399 |     total_styled = snake_case_count + camel_case_count
400 |     if total_styled == 0:
401 |         return 80  # No clear style detected
402 |     
403 |     if style == 'snake_case':
404 |         consistency_ratio = snake_case_count / total_styled
405 |     else:
406 |         consistency_ratio = camel_case_count / total_styled
407 |     
408 |     # Check for magic numbers (numbers in code that should be constants)
409 |     magic_number_pattern = r'\b\d{2,}\b'  # Numbers with 2+ digits
410 |     magic_numbers = re.findall(magic_number_pattern, '\n'.join(added_lines))
411 |     magic_count = len([n for n in magic_numbers if int(n) not in [0, 1, 10, 100, 1000]])
412 |     
413 |     # Scoring
414 |     if consistency_ratio < 0.5:
415 |         score = 50  # Highly inconsistent
416 |     elif consistency_ratio < 0.7:
417 |         score = 65  # Somewhat inconsistent
418 |     elif consistency_ratio < 0.85:
419 |         score = 75  # Mostly consistent
420 |     else:
421 |         score = 85  # Very consistent
422 |     
423 |     # Penalize for magic numbers
424 |     if magic_count > 5:
425 |         score -= 15
426 |     elif magic_count > 2:
427 |         score -= 10
428 |     
429 |     return max(50, min(100, score))
430 | 
431 | 
432 | # ============================================================================
433 | # HELPER FUNCTIONS
434 | # ============================================================================
435 | 
436 | def _is_test_file(file_path: str) -> bool:
437 |     """Check if file is a test file based on path/name."""
438 |     test_indicators = ['test', 'spec', '__tests__', 'tests/']
439 |     return any(indicator in file_path.lower() for indicator in test_indicators)
440 | 
441 | 
442 | def _generate_risk_and_recommendation(dimension: str, score: int, file_path: str, language: str = 'unknown') -> tuple:
443 |     """Generate top risk and recommendation based on lowest scoring dimension.
444 |     
445 |     Args:
446 |         dimension: The dimension with the lowest score
447 |         score: The score value
448 |         file_path: Path to the file
449 |         language: Programming language for context-specific recommendations
450 |     """
451 |     # Get language-specific focus areas for better recommendations
452 |     focus_areas = get_focus_areas(language)
453 |     
454 |     risk_templates = {
455 |         'documentation': (
456 |             f"Documentation drift detected in {file_path}",
457 |             "Add inline comments and docstrings to explain complex logic"
458 |         ),
459 |         'test_coverage': (
460 |             f"Test coverage gap in {file_path}",
461 |             "Write unit tests for new functionality or update existing tests"
462 |         ),
463 |         'complexity': (
464 |             f"Complexity growth in {file_path}",
465 |             "Refactor deeply nested code and break down long functions"
466 |         ),
467 |         'naming': (
468 |             f"Naming inconsistency in {file_path}",
469 |             "Standardize variable/function names to match project conventions"
470 |         ),
471 |     }
472 |     
473 |     if score < 40:
474 |         severity = "CRITICAL"
475 |     elif score < 60:
476 |         severity = "HIGH"
477 |     else:
478 |         severity = "MODERATE"
479 |     
480 |     risk, rec = risk_templates.get(dimension, ("Unknown risk", "Review code changes"))
481 |     return f"[{severity}] {risk}", rec
482 | 
483 | 
484 | def _generate_decay_summary(scores: Dict[str, int], file_path: str) -> str:
485 |     """Generate 2-3 sentence summary of decay analysis."""
486 |     avg_score = sum(scores.values()) / len(scores)
487 |     lowest_dim = min(scores.keys(), key=lambda k: scores[k])
488 |     lowest_score = scores[lowest_dim]
489 |     
490 |     if avg_score >= 75:
491 |         health = "healthy"
492 |     elif avg_score >= 60:
493 |         health = "showing minor decay"
494 |     elif avg_score >= 40:
495 |         health = "showing significant decay"
496 |     else:
497 |         health = "in critical condition"
498 |     
499 |     summary = f"File {file_path} is {health} with an average decay score of {avg_score:.1f}/100. "
500 |     summary += f"The weakest dimension is {lowest_dim.replace('_', ' ')} (score: {lowest_score}/100). "
501 |     
502 |     if lowest_score < 50:
503 |         summary += "Immediate attention required to prevent further degradation."
504 |     elif lowest_score < 70:
505 |         summary += "Consider addressing this area in the next refactoring cycle."
506 |     else:
507 |         summary += "Continue monitoring for future changes."
508 |     
509 |     return summary
510 | 
511 | 
512 | # ============================================================================
513 | # TEST FUNCTION
514 | # ============================================================================
515 | 
516 | def test_bob_analyzer():
517 |     """Test the analyzer with sample data."""
518 |     print("\n[TEST] Testing bob_analyzer with sample data...")
519 |     print("-" * 60)
520 |     
521 |     # Sample file data
522 |     sample_diff = """
523 | @@ -10,5 +10,25 @@ def calculate_total(items):
524 | -def old_function():
525 | -    pass
526 | +def new_complex_function(data):
527 | +    result = []
528 | +    for item in data:
529 | +        if item > 0:
530 | +            for subitem in item.values():
531 | +                if subitem:
532 | +                    result.append(subitem * 100)
533 | +    return result
534 | +
535 | +def anotherFunction(x):
536 | +    return x * 42
537 | """
538 |     
539 |     sample_file = {
540 |         'file_path': 'app/sample.py',
541 |         'language': 'python',
542 |         'total_commits': 3,
543 |         'diff_text': sample_diff,
544 |         'last_modified': '2026-05-02T10:00:00Z',
545 |         'commit_hashes': ['abc123', 'def456', 'ghi789']
546 |     }
547 |     
548 |     # Analyze single file
549 |     result = analyze_file_decay(sample_file)
550 |     
551 |     print(f"\nFile: {result['file_path']}")
552 |     print(f"Language: {result['language']}")
553 |     print(f"Total commits: {result['total_commits']}")
554 |     print(f"\nDecay Scores:")
555 |     print(f"  Documentation drift: {result['documentation_drift_score']}/100")
556 |     print(f"  Test drift: {result['test_drift_score']}/100")
557 |     print(f"  Complexity growth: {result['complexity_growth_score']}/100")
558 |     print(f"  Naming consistency: {result['naming_consistency_score']}/100")
559 |     print(f"\nTop Risk: {result['top_risk']}")
560 |     print(f"Recommendation: {result['recommendation']}")
561 |     print(f"\nSummary: {result['decay_summary']}")
562 |     
563 |     print("\n" + "-" * 60)
564 |     print("[TEST] Analyzer test complete!")
565 | 
566 | 
567 | if __name__ == '__main__':
568 |     test_bob_analyzer()
569 | 
570 | # Made with Bob
</content>
</file>
<file><path>app/config.py</path>
<content lines="1-176">
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
129 | 
130 | def get_output_report_path(timestamp: Optional[str] = None) -> Path:
131 |     """Generate output report file path with timestamp."""
132 |     from datetime import datetime
133 |     if timestamp is None:
134 |         timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
135 |     return Config.OUTPUT_DIR / f"report_{timestamp}.json"
136 | 
137 | 
138 | def get_latest_report() -> Optional[Path]:
139 |     """Find the most recent report JSON file in output directory."""
140 |     if not Config.OUTPUT_DIR.exists():
141 |         return None
142 |     reports = list(Config.OUTPUT_DIR.glob("report_*.json"))
143 |     if not reports:
144 |         return None
145 |     return max(reports, key=lambda p: p.stat().st_mtime)
146 | 
147 | 
148 | 
149 | def load_repos_config() -> List[Dict]:
150 |     """Load repository configuration from repos.json.
151 |     
152 |     Returns:
153 |         List of repository configurations with name, path, days, and enabled status.
154 |     """
155 |     if not Config.REPOS_JSON_PATH.exists():
156 |         # Return default config if file doesn't exist
157 |         return [{
158 |             "name": "default",
159 |             "path": Config.DEFAULT_REPO_PATH,
160 |             "days": Config.DEFAULT_DAYS,
161 |             "enabled": True
162 |         }]
163 |     
164 |     try:
165 |         with open(Config.REPOS_JSON_PATH, 'r') as f:
166 |             repos = json.load(f)
167 |             # Filter only enabled repos
168 |             return [repo for repo in repos if repo.get('enabled', True)]
169 |     except (json.JSONDecodeError, IOError) as e:
170 |         print(f"Warning: Failed to load repos.json: {e}")
171 |         return [{
172 |             "name": "default",
173 |             "path": Config.DEFAULT_REPO_PATH,
174 |             "days": Config.DEFAULT_DAYS,
175 |             "enabled": True
176 |         }]
</content>
</file>
<file><path>driftguard.py</path>
<content lines="1-437">
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
 26 | 
 27 | 
 28 | # Global flag for graceful shutdown
 29 | shutdown_requested = False
 30 | 
 31 | 
 32 | def setup_logging(log_file: str = "logs/driftguard.log") -> logging.Logger:
 33 |     """Set up logging with rotating file handler and console output.
 34 |     
 35 |     Args:
 36 |         log_file: Path to log file (default: logs/driftguard.log)
 37 |         
 38 |     Returns:
 39 |         Configured logger instance
 40 |     """
 41 |     # Create logs directory if it doesn't exist
 42 |     log_path = Path(log_file)
 43 |     log_path.parent.mkdir(parents=True, exist_ok=True)
 44 |     
 45 |     # Create logger
 46 |     logger = logging.getLogger("driftguard")
 47 |     logger.setLevel(logging.INFO)
 48 |     
 49 |     # Remove existing handlers to avoid duplicates
 50 |     logger.handlers.clear()
 51 |     
 52 |     # File handler with rotation (10MB max, keep 5 backups)
 53 |     file_handler = RotatingFileHandler(
 54 |         log_file,
 55 |         maxBytes=10 * 1024 * 1024,  # 10MB
 56 |         backupCount=5,
 57 |         encoding='utf-8'
 58 |     )
 59 |     file_handler.setLevel(logging.INFO)
 60 |     file_formatter = logging.Formatter(
 61 |         '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
 62 |         datefmt='%Y-%m-%d %H:%M:%S'
 63 |     )
 64 |     file_handler.setFormatter(file_formatter)
 65 |     
 66 |     # Console handler
 67 |     console_handler = logging.StreamHandler(sys.stdout)
 68 |     console_handler.setLevel(logging.INFO)
 69 |     console_formatter = logging.Formatter('%(levelname)s: %(message)s')
 70 |     console_handler.setFormatter(console_formatter)
 71 |     
 72 |     # Add handlers
 73 |     logger.addHandler(file_handler)
 74 |     logger.addHandler(console_handler)
 75 |     
 76 |     return logger
 77 | 
 78 | 
 79 | def signal_handler(signum, frame):
 80 |     """Handle SIGINT (Ctrl+C) for graceful shutdown."""
 81 |     global shutdown_requested
 82 |     print("\n⚠️  Shutdown requested. Finishing current run...")
 83 |     shutdown_requested = True
 84 | 
 85 | 
 86 | def parse_interval(interval_str: str) -> int:
 87 |     """Parse interval string to seconds.
 88 |     
 89 |     Supports formats:
 90 |     - "24h" -> 86400 seconds
 91 |     - "30m" -> 1800 seconds
 92 |     - "3600" -> 3600 seconds (plain number)
 93 |     
 94 |     Args:
 95 |         interval_str: Interval string (e.g., "24h", "30m", "3600")
 96 |         
 97 |     Returns:
 98 |         Interval in seconds
 99 |         
100 |     Raises:
101 |         ValueError: If interval format is invalid
102 |     """
103 |     # Try plain number first
104 |     try:
105 |         return int(interval_str)
106 |     except ValueError:
107 |         pass
108 |     
109 |     # Parse with unit suffix
110 |     match = re.match(r'^(\d+)([hms])$', interval_str.lower())
111 |     if not match:
112 |         raise ValueError(
113 |             f"Invalid interval format: {interval_str}. "
114 |             "Use format like '24h', '30m', '3600s', or plain seconds."
115 |         )
116 |     
117 |     value, unit = match.groups()
118 |     value = int(value)
119 |     
120 |     if unit == 'h':
121 |         return value * 3600
122 |     elif unit == 'm':
123 |         return value * 60
124 |     elif unit == 's':
125 |         return value
126 |     
127 |     raise ValueError(f"Invalid time unit: {unit}")
128 | 
129 | 
130 | def run_analysis(repo: str, days: int, max_files: int, output: str = None,
131 |                  logger: logging.Logger = None, github_token: str = None) -> dict:
132 |     """Run a single analysis cycle.
133 |     
134 |     Args:
135 |         repo: Path to git repository or GitHub URL
136 |         days: Days of history to analyze
137 |         max_files: Maximum files to analyze
138 |         output: Optional output file path
139 |         logger: Optional logger instance
140 |         github_token: Optional GitHub token for API access
141 |         
142 |     Returns:
143 |         Generated report dict
144 |     """
145 |     if logger is None:
146 |         logger = logging.getLogger("driftguard")
147 |     
148 |     logger.info(f"Starting analysis: repo={repo}, days={days}, max_files={max_files}")
149 |     
150 |     # Step 1: Resolve repository (local, GitHub, or other remote)
151 |     try:
152 |         repo_data, is_remote = resolve_repo(repo, github_token)
153 |         
154 |         # If it's a GitHub repo, fetch diffs via API
155 |         if is_remote:
156 |             owner, repo_name, token = repo_data
157 |             logger.info(f"Fetching data from GitHub API: {owner}/{repo_name}")
158 |             file_diffs = _fetch_github_repo_diffs(owner, repo_name, days, token)
159 |         else:
160 |             # Local repo or cloned repo
161 |             file_diffs = get_file_diffs(repo_data, days)
162 |     except Exception as e:
163 |         logger.error(f"Error reading repository: {e}")
164 |         raise
165 |     
166 |     if not file_diffs:
167 |         logger.warning("No modified files found in the analysis window")
168 |         return None
169 |     
170 |     logger.info(f"Found {len(file_diffs)} modified files")
171 |     
172 |     # Limit to max_files
173 |     if len(file_diffs) > max_files:
174 |         logger.info(f"Limiting to top {max_files} most-changed files")
175 |         file_diffs = file_diffs[:max_files]
176 |     
177 |     # Step 2: Analyze with bob_analyzer
178 |     logger.info(f"Analyzing {len(file_diffs)} files for decay signals")
179 |     try:
180 |         analyses = batch_analyze(file_diffs)
181 |     except Exception as e:
182 |         logger.error(f"Error during analysis: {e}")
183 |         raise
184 |     
185 |     # Step 3: Score files
186 |     logger.info("Calculating health scores")
187 |     try:
188 |         scored_files = score_all_files(analyses)
189 |     except Exception as e:
190 |         logger.error(f"Error during scoring: {e}")
191 |         raise
192 |     
193 |     # Step 4: Generate report
194 |     logger.info("Generating report")
195 |     try:
196 |         report = generate_report(repo, days, scored_files)
197 |     except Exception as e:
198 |         logger.error(f"Error generating report: {e}")
199 |         raise
200 |     
201 |     # Step 5: Save report
202 |     try:
203 |         report_path = save_report(report, output)
204 |         logger.info(f"Report saved to {report_path}")
205 |     except Exception as e:
206 |         logger.error(f"Error saving report: {e}")
207 |         raise
208 |     
209 |     return report
210 | 
211 | 
212 | def watcher(repo: str, days: int, max_files: int, interval_seconds: int,
213 |             alert_config: dict = None, github_token: str = None):
214 |     """Run continuous analysis with scheduled intervals.
215 |     
216 |     Args:
217 |         repo: Path to git repository or GitHub URL
218 |         days: Days of history to analyze
219 |         max_files: Maximum files to analyze
220 |         interval_seconds: Seconds between analysis runs
221 |         alert_config: Optional alert configuration dict
222 |         github_token: Optional GitHub token for API access
223 |     """
224 |     global shutdown_requested
225 |     
226 |     # Set up logging
227 |     logger = setup_logging()
228 |     logger.info("=" * 70)
229 |     logger.info("DriftGuard Watch Mode Started")
230 |     logger.info("=" * 70)
231 |     logger.info(f"Repository: {repo}")
232 |     logger.info(f"Analysis window: {days} days")
233 |     logger.info(f"Max files: {max_files}")
234 |     logger.info(f"Interval: {interval_seconds} seconds ({interval_seconds/3600:.1f} hours)")
235 |     logger.info("=" * 70)
236 |     
237 |     # Initialize database
238 |     initialize_db()
239 |     logger.info("Database initialized")
240 |     
241 |     # Initialize alert manager
242 |     alert_manager = AlertManager(alert_config)
243 |     
244 |     # Register signal handler for graceful shutdown
245 |     signal.signal(signal.SIGINT, signal_handler)
246 |     signal.signal(signal.SIGTERM, signal_handler)
247 |     
248 |     run_count = 0
249 |     
250 |     while not shutdown_requested:
251 |         run_count += 1
252 |         logger.info(f"\n{'=' * 70}")
253 |         logger.info(f"Starting analysis run #{run_count}")
254 |         logger.info(f"{'=' * 70}")
255 |         
256 |         try:
257 |             # Run analysis
258 |             report = run_analysis(repo, days, max_files, logger=logger, github_token=github_token)
259 |             
260 |             if report:
261 |                 # Save to database
262 |                 run_id = save_run(report)
263 |                 logger.info(f"Run saved to database: {run_id}")
264 |                 
265 |                 # Check for alerts
266 |                 alert_manager.check_and_alert(report)
267 |                 
268 |                 # Print summary
269 |                 print_report_summary(report)
270 |             else:
271 |                 logger.info("No changes detected, skipping database save")
272 |             
273 |             logger.info(f"Analysis run #{run_count} completed successfully")
274 |             
275 |         except Exception as e:
276 |             logger.error(f"Error during analysis run #{run_count}: {e}", exc_info=True)
277 |         
278 |         if shutdown_requested:
279 |             break
280 |         
281 |         # Wait for next interval
282 |         logger.info(f"Next run in {interval_seconds} seconds ({interval_seconds/3600:.1f} hours)")
283 |         logger.info(f"Press Ctrl+C to stop gracefully")
284 |         
285 |         # Sleep in small increments to allow for responsive shutdown
286 |         sleep_interval = 1  # Check every second
287 |         for _ in range(interval_seconds):
288 |             if shutdown_requested:
289 |                 break
290 |             time.sleep(sleep_interval)
291 |     
292 |     logger.info("\n" + "=" * 70)
293 |     logger.info("DriftGuard Watch Mode Stopped")
294 |     logger.info(f"Total runs completed: {run_count}")
295 |     logger.info("=" * 70)
296 | 
297 | 
298 | def main():
299 |     parser = argparse.ArgumentParser(description="DriftGuard - Codebase Decay Monitor")
300 |     parser.add_argument("--repo", default=".", help="Path to git repository or GitHub URL (default: .)")
301 |     parser.add_argument("--days", type=int, default=30, help="Days of history to analyze (default: 30)")
302 |     parser.add_argument("--output", default=None, help="Output JSON file path (auto-generated if not provided)")
303 |     parser.add_argument("--max-files", type=int, default=20, help="Max files to analyze (default: 20)")
304 |     parser.add_argument("--verbose", action="store_true", help="Print raw analysis details")
305 |     parser.add_argument("--watch", action="store_true", help="Run in watch mode with scheduled intervals")
306 |     parser.add_argument("--interval", default="24h", help="Watch mode interval (e.g., '24h', '30m', '3600')")
307 |     parser.add_argument("--github-token", default=None, help="GitHub token for API access (overrides GITHUB_TOKEN env var)")
308 |     parser.add_argument("--export", default="json", choices=["json", "markdown", "pdf", "all"],
309 |                         help="Export format: json, markdown, pdf, or all (default: json)")
310 |     parser.add_argument("--remediate", action="store_true",
311 |                         help="Generate remediation files for CRITICAL and AT_RISK files")
312 |     
313 |     args = parser.parse_args()
314 |     
315 |     # Watch mode
316 |     if args.watch:
317 |         try:
318 |             interval_seconds = parse_interval(args.interval)
319 |         except ValueError as e:
320 |             print(f"❌ {e}")
321 |             sys.exit(1)
322 |         
323 |         # Run watcher
324 |         watcher(args.repo, args.days, args.max_files, interval_seconds, github_token=args.github_token)
325 |         sys.exit(0)
326 |     
327 |     print("\n" + "=" * 70)
328 |     print("🔍 DriftGuard — Codebase Decay Monitor")
329 |     print("=" * 70)
330 |     
331 |     # Step 1: Resolve repository and extract git diffs
332 |     print(f"\n📂 Scanning {args.repo} for last {args.days} days of changes...")
333 |     try:
334 |         repo_data, is_remote = resolve_repo(args.repo, args.github_token)
335 |         
336 |         # If it's a GitHub repo, fetch diffs via API
337 |         if is_remote:
338 |             owner, repo_name, token = repo_data
339 |             print(f"Using GitHub API for {owner}/{repo_name}")
340 |             file_diffs = _fetch_github_repo_diffs(owner, repo_name, args.days, token)
341 |         else:
342 |             # Local repo or cloned repo
343 |             file_diffs = get_file_diffs(repo_data, args.days)
344 |     except Exception as e:
345 |         print(f"❌ Error reading repository: {e}")
346 |         sys.exit(1)
347 |     
348 |     if not file_diffs:
349 |         print("⚠️  No modified files found in the analysis window.")
350 |         sys.exit(0)
351 |     
352 |     print(f"✅ Found {len(file_diffs)} modified files")
353 |     
354 |     # Limit to max_files
355 |     if len(file_diffs) > args.max_files:
356 |         print(f"⚠️  Limiting to top {args.max_files} most-changed files (by commit count)")
357 |         file_diffs = file_diffs[:args.max_files]
358 |     
359 |     # Step 2: Analyze with bob_analyzer
360 |     print(f"\n🤖 Analyzing {len(file_diffs)} files for decay signals...")
361 |     try:
362 |         analyses = batch_analyze(file_diffs)
363 |     except Exception as e:
364 |         print(f"❌ Error during analysis: {e}")
365 |         sys.exit(1)
366 |     
367 |     print(f"✅ Analysis complete")
368 |     
369 |     # Step 3: Score files
370 |     print("\n⚖️  Calculating health scores...")
371 |     try:
372 |         scored_files = score_all_files(analyses)
373 |     except Exception as e:
374 |         print(f"❌ Error during scoring: {e}")
375 |         sys.exit(1)
376 |     
377 |     print(f"✅ Scoring complete")
378 |     
379 |     # Step 4: Generate report
380 |     print("\n📊 Generating report...")
381 |     try:
382 |         report = generate_report(args.repo, args.days, scored_files)
383 |     except Exception as e:
384 |         print(f"❌ Error generating report: {e}")
385 |         sys.exit(1)
386 |     
387 |     # Step 5: Save report (JSON by default)
388 |     try:
389 |         report_path = save_report(report, args.output)
390 |     except Exception as e:
391 |         print(f"❌ Error saving report: {e}")
392 |         sys.exit(1)
393 |     
394 |     print(f"✅ Report saved to {report_path}")
395 |     
396 |     # Step 6: Export to additional formats if requested
397 |     if args.export != "json":
398 |         print(f"\n📄 Exporting report in {args.export} format...")
399 |         try:
400 |             export_result = export_report(report, args.export, output_dir="output")
401 |             print(f"✅ {export_result}")
402 |         except ImportError as e:
403 |             print(f"⚠️  Export failed: {e}")
404 |             print("   Install weasyprint for PDF export: pip install weasyprint")
405 |         except Exception as e:
406 |             print(f"❌ Error exporting report: {e}")
407 |     
408 |     # Step 7: Generate remediation files if requested
409 |     if args.remediate:
410 |         print("\n🔧 Generating remediation files...")
411 |         try:
412 |             # Initialize database connection
413 |             initialize_db()
414 |             import sqlite3
415 |             db_conn = sqlite3.connect("data/driftguard.db")
416 |             
417 |             try:
418 |                 remediation_count = generate_remediations_for_files(
419 |                     scored_files,
420 |                     args.repo,
421 |                     db_conn
422 |                 )
423 |                 print(f"✅ Generated {remediation_count} remediation files in remediation/")
424 |             finally:
425 |                 db_conn.close()
426 |         except Exception as e:
427 |             print(f"❌ Error generating remediation files: {e}")
428 |     
429 |     # Print summary
430 |     print_report_summary(report)
431 |     
432 |     print("\n🚀 Start dashboard: uvicorn app.main:app --reload")
433 |     print("=" * 70 + "\n")
434 | 
435 | 
436 | if __name__ == '__main__':
437 |     main()
</content>
</file>
</files>
<environment_details>
# VSCode Visible Files
demo_cache.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,app/git_parser.py,test_language_support.py,data/repos.json,app/templates/dashboard.html

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T14:58:56.090Z
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

I'll implement rate limiting around Bob analysis calls in DriftGuard. Let me create a comprehensive plan and execute it step by step.

<update_todo_list>
<todos>
[ ] Create token-bucket rate limiter class (thread-safe)
[ ] Add rate limit configuration to config.py
[ ] Integrate rate limiter into batch_analyze function
[ ] Add logging for rate limit waits
[ ] Create comprehensive tests for rate limiter
</todos>
</update_todo_list>

---

**User:**

[update_todo_list] Result:
Todo list updated successfully.
<environment_details>
# VSCode Visible Files
demo_cache.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,app/git_parser.py,test_language_support.py,data/repos.json,app/templates/dashboard.html

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T14:59:01.739Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$0.06

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
| 1 | Create token-bucket rate limiter class (thread-safe) | Pending |
| 2 | Add rate limit configuration to config.py | Pending |
| 3 | Integrate rate limiter into batch_analyze function | Pending |
| 4 | Add logging for rate limit waits | Pending |
| 5 | Create comprehensive tests for rate limiter | Pending |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

Now let me start implementing the rate limiter. First, I'll create the token-bucket rate limiter class.

<write_to_file>
<path>app/rate_limiter.py</path>
<content>"""rate_limiter.py

Token-bucket rate limiter for controlling Bob analysis call frequency.
Thread-safe implementation with configurable tokens per minute and burst capacity.
"""
import time
import threading
from typing import Optional


class TokenBucketRateLimiter:
    """Thread-safe token bucket rate limiter.
    
    Implements the token bucket algorithm to control the rate of operations.
    Tokens are added at a constant rate (tokens_per_minute) and operations
    consume tokens. If no tokens are available, the operation waits.
    
    Attributes:
        tokens_per_minute: Rate at which tokens are added (operations per minute)
        burst_capacity: Maximum tokens that can accumulate (burst size)
    """
    
    def __init__(self, tokens_per_minute: int = 30, burst_capacity: int = 5):
        """Initialize the rate limiter.
        
        Args:
            tokens_per_minute: Number of tokens added per minute (default: 30)
            burst_capacity: Maximum tokens that can be stored (default: 5)
        """
        if tokens_per_minute <= 0:
            raise ValueError("tokens_per_minute must be positive")
        if burst_capacity <= 0:
            raise ValueError("burst_capacity must be positive")
        
        self.tokens_per_minute = tokens_per_minute
        self.burst_capacity = burst_capacity
        
        # Calculate token refill rate in tokens per second
        self.refill_rate = tokens_per_minute / 60.0
        
        # Current number of tokens (start with full burst capacity)
        self._tokens = float(burst_capacity)
        
        # Last time tokens were added
        self._last_refill = time.time()
        
        # Lock for thread safety
        self._lock = threading.Lock()
    
    def _refill_tokens(self) -> None:
        """Refill tokens based on elapsed time since last refill.
        
        This method should be called while holding the lock.
        """
        now = time.time()
        elapsed = now - self._last_refill
        
        # Calculate tokens to add based on elapsed time
        tokens_to_add = elapsed * self.refill_rate
        
        # Add tokens but don't exceed burst capacity
        self._tokens = min(self.burst_capacity, self._tokens + tokens_to_add)
        
        # Update last refill time
        self._last_refill = now
    
    def acquire(self, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """Acquire tokens from the bucket.
        
        Blocks until tokens are available or timeout is reached.
        
        Args:
            tokens: Number of tokens to acquire (default: 1)
            timeout: Maximum time to wait in seconds (None = wait forever)
            
        Returns:
            True if tokens were acquired, False if timeout was reached
            
        Raises:
            ValueError: If tokens is not positive
        """
        if tokens <= 0:
            raise ValueError("tokens must be positive")
        
        start_time = time.time()
        
        while True:
            with self._lock:
                # Refill tokens based on elapsed time
                self._refill_tokens()
                
                # Check if we have enough tokens
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return True
                
                # Calculate wait time until we have enough tokens
                tokens_needed = tokens - self._tokens
                wait_time = tokens_needed / self.refill_rate
            
            # Check timeout
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    return False
                # Adjust wait time to not exceed timeout
                wait_time = min(wait_time, timeout - elapsed)
            
            # Sleep for the calculated wait time
            time.sleep(wait_time)
    
    def try_acquire(self, tokens: int = 1) -> bool:
        """Try to acquire tokens without blocking.
        
        Args:
            tokens: Number of tokens to acquire (default: 1)
            
        Returns:
            True if tokens were acquired, False otherwise
            
        Raises:
            ValueError: If tokens is not positive
        """
        if tokens <= 0:
            raise ValueError("tokens must be positive")
        
        with self._lock:
            # Refill tokens based on elapsed time
            self._refill_tokens()
            
            # Check if we have enough tokens
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            
            return False
    
    def get_available_tokens(self) -> float:
        """Get the current number of available tokens.
        
        Returns:
            Current number of tokens in the bucket
        """
        with self._lock:
            self._refill_tokens()
            return self._tokens
    
    def get_wait_time(self, tokens: int = 1) -> float:
        """Calculate wait time until tokens are available.
        
        Args:
            tokens: Number of tokens needed (default: 1)
            
        Returns:
            Wait time in seconds (0 if tokens are available now)
        """
        with self._lock:
            self._refill_tokens()
            
            if self._tokens >= tokens:
                return 0.0
            
            tokens_needed = tokens - self._tokens
            return tokens_needed / self.refill_rate
    
    def reset(self) -> None:
        """Reset the rate limiter to initial state (full burst capacity)."""
        with self._lock:
            self._tokens = float(self.burst_capacity)
            self._last_refill = time.time()
</content>
<line_count>159</line_count>
</write_to_file>

---

**User:**

[write_to_file for 'app/rate_limiter.py'] Result:
<file_write_result>
<path>app/rate_limiter.py</path>
<operation>created</operation>
<notice>
<i>You do not need to re-read the file, as you have seen all changes</i>
<i>Proceed with the task using these changes as the new baseline.</i>
</notice>
</file_write_result>

<environment_details>
# VSCode Visible Files
app\rate_limiter.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,app/git_parser.py,test_language_support.py,data/repos.json,app/templates/dashboard.html

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T14:59:36.959Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$0.12

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
| 1 | Create token-bucket rate limiter class (thread-safe) | Pending |
| 2 | Add rate limit configuration to config.py | Pending |
| 3 | Integrate rate limiter into batch_analyze function | Pending |
| 4 | Add logging for rate limit waits | Pending |
| 5 | Create comprehensive tests for rate limiter | Pending |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

<update_todo_list>
<todos>
[x] Create token-bucket rate limiter class (thread-safe)
[-] Add rate limit configuration to config.py
[ ] Integrate rate limiter into batch_analyze function
[ ] Add logging for rate limit waits
[ ] Create comprehensive tests for rate limiter
</todos>
</update_todo_list>

---

**User:**

[update_todo_list] Result:
Todo list updated successfully.
<environment_details>
# VSCode Visible Files
app\rate_limiter.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,app/git_parser.py,test_language_support.py,data/repos.json,app/templates/dashboard.html

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T14:59:42.340Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$0.17

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
| 1 | Create token-bucket rate limiter class (thread-safe) | Completed |
| 2 | Add rate limit configuration to config.py | In Progress |
| 3 | Integrate rate limiter into batch_analyze function | Pending |
| 4 | Add logging for rate limit waits | Pending |
| 5 | Create comprehensive tests for rate limiter | Pending |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

Now let me add the rate limit configuration to config.py:

<apply_diff>
<path>app/config.py</path>
<diff>
<<<<<<< SEARCH
:start_line:125
-------
    # Analysis cache settings
    CACHE_ENABLED = os.getenv("DRIFTGUARD_CACHE_ENABLED", "true").lower() == "true"
    CACHE_TTL_HOURS = int(os.getenv("DRIFTGUARD_CACHE_TTL_HOURS", "0"))  # 0 = no expiry
=======
    # Analysis cache settings
    CACHE_ENABLED = os.getenv("DRIFTGUARD_CACHE_ENABLED", "true").lower() == "true"
    CACHE_TTL_HOURS = int(os.getenv("DRIFTGUARD_CACHE_TTL_HOURS", "0"))  # 0 = no expiry
    
    # Rate limiting settings for Bob analysis calls
    BOB_RATE_LIMIT_PER_MINUTE = int(os.getenv("BOB_RATE_LIMIT_PER_MINUTE", "30"))  # Max calls per minute
    BOB_RATE_LIMIT_BURST = int(os.getenv("BOB_RATE_LIMIT_BURST", "5"))  # Burst capacity
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
Current time in ISO 8601 UTC format: 2026-05-02T14:59:51.960Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$0.23

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
| 1 | Create token-bucket rate limiter class (thread-safe) | Completed |
| 2 | Add rate limit configuration to config.py | In Progress |
| 3 | Integrate rate limiter into batch_analyze function | Pending |
| 4 | Add logging for rate limit waits | Pending |
| 5 | Create comprehensive tests for rate limiter | Pending |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

<update_todo_list>
<todos>
[x] Create token-bucket rate limiter class (thread-safe)
[x] Add rate limit configuration to config.py
[-] Integrate rate limiter into batch_analyze function
[ ] Add logging for rate limit waits
[ ] Create comprehensive tests for rate limiter
</todos>
</update_todo_list>

---

**User:**

[update_todo_list] Result:
Todo list updated successfully.
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
Current time in ISO 8601 UTC format: 2026-05-02T14:59:56.760Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$0.29

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
| 1 | Create token-bucket rate limiter class (thread-safe) | Completed |
| 2 | Add rate limit configuration to config.py | Completed |
| 3 | Integrate rate limiter into batch_analyze function | In Progress |
| 4 | Add logging for rate limit waits | Pending |
| 5 | Create comprehensive tests for rate limiter | Pending |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

Now let me integrate the rate limiter into the batch_analyze function in bob_analyzer.py:

<apply_diff>
<path>app/bob_analyzer.py</path>
<diff>
<<<<<<< SEARCH
:start_line:1
-------
"""bob_analyzer.py

Rule-based code decay analyzer for DriftGuard.
Analyzes file diffs using heuristics (no external APIs/LLMs).
"""

import re
from typing import List, Dict, Optional
from app.models import FileDiff, AnalysisResult
from app.config import Config
from app.baseline_profile import load_baseline, format_baseline_summary
from app.language_prompts import get_language_prompt, get_focus_areas, get_complexity_indicators
from app.db import (
    compute_diff_hash,
    get_cached_analysis,
    save_cached_analysis,
    DEFAULT_DB_PATH
)
=======
"""bob_analyzer.py

Rule-based code decay analyzer for DriftGuard.
Analyzes file diffs using heuristics (no external APIs/LLMs).
"""

import re
import logging
from typing import List, Dict, Optional
from app.models import FileDiff, AnalysisResult
from app.config import Config
from app.baseline_profile import load_baseline, format_baseline_summary
from app.language_prompts import get_language_prompt, get_focus_areas, get_complexity_indicators
from app.db import (
    compute_diff_hash,
    get_cached_analysis,
    save_cached_analysis,
    DEFAULT_DB_PATH
)
from app.rate_limiter import TokenBucketRateLimiter

# Initialize logger
logger = logging.getLogger("driftguard")
>>>>>>> REPLACE
</diff>
</apply_diff>

---

**User:**

[apply_diff for 'app/bob_analyzer.py'] Result:
<file_write_result>
<path>app/bob_analyzer.py</path>
<operation>modified</operation>
<problems>

New problems detected after saving the file:
app/bob_analyzer.py
- [basedpyright Error] 125 |         save_cached_analysis(file_path, diff_hash, language, result, db_path) : Argument of type "AnalysisResult" cannot be assigned to parameter "analysis_result" of type "Dict[Unknown, Unknown]" in function "save_cached_analysis"
  "AnalysisResult" is not assignable to "Dict[Unknown, Unknown]"
- [basedpyright Error] 127 |     return result : Type "AnalysisResult" is not assignable to return type "Dict[Unknown, Unknown]"
  "AnalysisResult" is not assignable to "Dict[Unknown, Unknown]"</problems>
<notice>
<i>You do not need to re-read the file, as you have seen all changes</i>
<i>Proceed with the task using these changes as the new baseline.</i>
</notice>
</file_write_result>

<notice>Making multiple related changes in a single apply_diff is more efficient. If other changes are needed in this file, please include them as additional SEARCH/REPLACE blocks.</notice>
<environment_details>
# VSCode Visible Files
app\bob_analyzer.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,app/git_parser.py,test_language_support.py,data/repos.json,app/templates/dashboard.html

# Recently Modified Files
These files have been modified since you last accessed them (file was just edited so you may need to re-read it before editing):
app/bob_analyzer.py

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:00:09.926Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$0.36

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
| 1 | Create token-bucket rate limiter class (thread-safe) | Completed |
| 2 | Add rate limit configuration to config.py | Completed |
| 3 | Integrate rate limiter into batch_analyze function | In Progress |
| 4 | Add logging for rate limit waits | Pending |
| 5 | Create comprehensive tests for rate limiter | Pending |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

Now let me update the batch_analyze function to integrate the rate limiter:

<apply_diff>
<path>app/bob_analyzer.py</path>
<diff>
<<<<<<< SEARCH
:start_line:20
-------
# Initialize logger
logger = logging.getLogger("driftguard")

# Global baseline cache
_baseline_cache: Optional[Dict] = None
=======
# Initialize logger
logger = logging.getLogger("driftguard")

# Global baseline cache
_baseline_cache: Optional[Dict] = None

# Global rate limiter instance
_rate_limiter: Optional[TokenBucketRateLimiter] = None


def get_rate_limiter() -> TokenBucketRateLimiter:
    """Get or create the global rate limiter instance.
    
    Returns:
        TokenBucketRateLimiter instance configured from Config
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = TokenBucketRateLimiter(
            tokens_per_minute=Config.BOB_RATE_LIMIT_PER_MINUTE,
            burst_capacity=Config.BOB_RATE_LIMIT_BURST
        )
    return _rate_limiter
>>>>>>> REPLACE
</diff>
</apply_diff>

---

**User:**

[apply_diff for 'app/bob_analyzer.py'] Result:
<file_write_result>
<path>app/bob_analyzer.py</path>
<operation>modified</operation>
<problems>

New problems detected after saving the file:
app/bob_analyzer.py
- [basedpyright Error] 143 |         save_cached_analysis(file_path, diff_hash, language, result, db_path) : Argument of type "AnalysisResult" cannot be assigned to parameter "analysis_result" of type "Dict[Unknown, Unknown]" in function "save_cached_analysis"
  "AnalysisResult" is not assignable to "Dict[Unknown, Unknown]"
- [basedpyright Error] 145 |     return result : Type "AnalysisResult" is not assignable to return type "Dict[Unknown, Unknown]"
  "AnalysisResult" is not assignable to "Dict[Unknown, Unknown]"</problems>
<notice>
<i>You do not need to re-read the file, as you have seen all changes</i>
<i>Proceed with the task using these changes as the new baseline.</i>
</notice>
</file_write_result>

<notice>Making multiple related changes in a single apply_diff is more efficient. If other changes are needed in this file, please include them as additional SEARCH/REPLACE blocks.</notice>
<environment_details>
# VSCode Visible Files
app\bob_analyzer.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,app/git_parser.py,test_language_support.py,data/repos.json,app/templates/dashboard.html

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:00:36.645Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$0.43

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
| 1 | Create token-bucket rate limiter class (thread-safe) | Completed |
| 2 | Add rate limit configuration to config.py | Completed |
| 3 | Integrate rate limiter into batch_analyze function | In Progress |
| 4 | Add logging for rate limit waits | Pending |
| 5 | Create comprehensive tests for rate limiter | Pending |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

Now let me update the batch_analyze function to use the rate limiter:

<apply_diff>
<path>app/bob_analyzer.py</path>
<diff>
<<<<<<< SEARCH
:start_line:147
-------
def batch_analyze(file_diffs: List[Dict]) -> List[Dict]:
    """
    Analyze multiple files with progress reporting.
    
    Args:
        file_diffs: List of file_data dicts from git_parser
        
    Returns:
        List of AnalysisResult dicts
    """
    results = []
    total = len(file_diffs)
    
    print(f"\n[ANALYZER] Analyzing {total} files...")
    print("-" * 60)
    
    for i, file_data in enumerate(file_diffs, 1):
        file_path = file_data.get('file_path', 'unknown')
        print(f"[{i}/{total}] Analyzing: {file_path}")
        
        try:
            result = analyze_file_decay(file_data)
            results.append(result)
            
            # Show quick score summary
            avg_score = (
                result['documentation_drift_score'] +
                result['test_drift_score'] +
                result['complexity_growth_score'] +
                result['naming_consistency_score']
            ) / 4
            print(f"         Average score: {avg_score:.1f}/100")
            
        except Exception as e:
            print(f"         [ERROR] Failed to analyze: {e}")
            continue
    
    print("-" * 60)
    print(f"[ANALYZER] Completed: {len(results)}/{total} files analyzed\n")
    
    return results
=======
def batch_analyze(file_diffs: List[Dict]) -> List[Dict]:
    """
    Analyze multiple files with progress reporting and rate limiting.
    
    Args:
        file_diffs: List of file_data dicts from git_parser
        
    Returns:
        List of AnalysisResult dicts
    """
    results = []
    total = len(file_diffs)
    
    # Get rate limiter instance
    rate_limiter = get_rate_limiter()
    
    print(f"\n[ANALYZER] Analyzing {total} files...")
    print(f"[ANALYZER] Rate limit: {Config.BOB_RATE_LIMIT_PER_MINUTE} calls/min, burst: {Config.BOB_RATE_LIMIT_BURST}")
    print("-" * 60)
    
    for i, file_data in enumerate(file_diffs, 1):
        file_path = file_data.get('file_path', 'unknown')
        print(f"[{i}/{total}] Analyzing: {file_path}")
        
        try:
            # Check if we need to wait for rate limit
            wait_time = rate_limiter.get_wait_time(tokens=1)
            if wait_time > 0:
                logger.info(f"Rate limiter waiting {wait_time:.1f}s before next Bob request")
                print(f"         [RATE LIMIT] Waiting {wait_time:.1f}s before next Bob request")
            
            # Acquire token (blocks if necessary)
            rate_limiter.acquire(tokens=1)
            
            # Perform analysis
            result = analyze_file_decay(file_data)
            results.append(result)
            
            # Show quick score summary
            avg_score = (
                result['documentation_drift_score'] +
                result['test_drift_score'] +
                result['complexity_growth_score'] +
                result['naming_consistency_score']
            ) / 4
            print(f"         Average score: {avg_score:.1f}/100")
            
        except Exception as e:
            print(f"         [ERROR] Failed to analyze: {e}")
            logger.error(f"Analysis failed for {file_path}: {e}")
            continue
    
    print("-" * 60)
    print(f"[ANALYZER] Completed: {len(results)}/{total} files analyzed\n")
    
    return results
>>>>>>> REPLACE
</diff>
</apply_diff>

---

**User:**

[apply_diff for 'app/bob_analyzer.py'] Result:
<file_write_result>
<path>app/bob_analyzer.py</path>
<operation>modified</operation>
<notice>
<i>You do not need to re-read the file, as you have seen all changes</i>
<i>Proceed with the task using these changes as the new baseline.</i>
</notice>
</file_write_result>

<notice>Making multiple related changes in a single apply_diff is more efficient. If other changes are needed in this file, please include them as additional SEARCH/REPLACE blocks.</notice>
<environment_details>
# VSCode Visible Files
app\bob_analyzer.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,app/git_parser.py,test_language_support.py,data/repos.json,app/templates/dashboard.html

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:00:56.286Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$0.50

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
| 1 | Create token-bucket rate limiter class (thread-safe) | Completed |
| 2 | Add rate limit configuration to config.py | Completed |
| 3 | Integrate rate limiter into batch_analyze function | In Progress |
| 4 | Add logging for rate limit waits | Pending |
| 5 | Create comprehensive tests for rate limiter | Pending |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

<update_todo_list>
<todos>
[x] Create token-bucket rate limiter class (thread-safe)
[x] Add rate limit configuration to config.py
[x] Integrate rate limiter into batch_analyze function
[x] Add logging for rate limit waits
[-] Create comprehensive tests for rate limiter
</todos>
</update_todo_list>

---

**User:**

[update_todo_list] Result:
Todo list updated successfully.
<environment_details>
# VSCode Visible Files
app\bob_analyzer.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,app/git_parser.py,test_language_support.py,data/repos.json,app/templates/dashboard.html

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:01:08.224Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$0.57

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
| 1 | Create token-bucket rate limiter class (thread-safe) | Completed |
| 2 | Add rate limit configuration to config.py | Completed |
| 3 | Integrate rate limiter into batch_analyze function | Completed |
| 4 | Add logging for rate limit waits | Completed |
| 5 | Create comprehensive tests for rate limiter | In Progress |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

Now let me create comprehensive tests for the rate limiter:

<write_to_file>
<path>test_rate_limiter.py</path>
<content>"""test_rate_limiter.py

Comprehensive tests for the TokenBucketRateLimiter.
Tests burst behavior, refill behavior, thread safety, and edge cases.
"""
import time
import threading
import pytest
from app.rate_limiter import TokenBucketRateLimiter


class TestTokenBucketRateLimiter:
    """Test suite for TokenBucketRateLimiter."""
    
    def test_initialization(self):
        """Test rate limiter initialization with valid parameters."""
        limiter = TokenBucketRateLimiter(tokens_per_minute=60, burst_capacity=10)
        assert limiter.tokens_per_minute == 60
        assert limiter.burst_capacity == 10
        assert limiter.refill_rate == 1.0  # 60 tokens/min = 1 token/sec
        assert limiter.get_available_tokens() == 10.0  # Starts with full burst
    
    def test_initialization_invalid_params(self):
        """Test that invalid parameters raise ValueError."""
        with pytest.raises(ValueError, match="tokens_per_minute must be positive"):
            TokenBucketRateLimiter(tokens_per_minute=0, burst_capacity=5)
        
        with pytest.raises(ValueError, match="tokens_per_minute must be positive"):
            TokenBucketRateLimiter(tokens_per_minute=-10, burst_capacity=5)
        
        with pytest.raises(ValueError, match="burst_capacity must be positive"):
            TokenBucketRateLimiter(tokens_per_minute=30, burst_capacity=0)
        
        with pytest.raises(ValueError, match="burst_capacity must be positive"):
            TokenBucketRateLimiter(tokens_per_minute=30, burst_capacity=-5)
    
    def test_burst_behavior(self):
        """Test that burst capacity allows rapid initial requests."""
        # 60 tokens/min = 1 token/sec, burst = 5
        limiter = TokenBucketRateLimiter(tokens_per_minute=60, burst_capacity=5)
        
        # Should be able to acquire 5 tokens immediately (burst capacity)
        start_time = time.time()
        for i in range(5):
            success = limiter.try_acquire(tokens=1)
            assert success, f"Failed to acquire token {i+1} during burst"
        elapsed = time.time() - start_time
        
        # All 5 should be acquired in less than 0.5 seconds (burst behavior)
        assert elapsed < 0.5, f"Burst took too long: {elapsed}s"
        
        # 6th token should fail (burst exhausted)
        success = limiter.try_acquire(tokens=1)
        assert not success, "Should not acquire token after burst exhausted"
    
    def test_refill_behavior(self):
        """Test that tokens refill at the correct rate."""
        # 60 tokens/min = 1 token/sec
        limiter = TokenBucketRateLimiter(tokens_per_minute=60, burst_capacity=5)
        
        # Exhaust burst capacity
        for _ in range(5):
            limiter.try_acquire(tokens=1)
        
        # Wait for 2 seconds (should refill ~2 tokens)
        time.sleep(2.1)
        
        # Should be able to acquire 2 tokens
        assert limiter.try_acquire(tokens=1), "Should acquire 1st refilled token"
        assert limiter.try_acquire(tokens=1), "Should acquire 2nd refilled token"
        
        # 3rd should fail (only 2 tokens refilled)
        assert not limiter.try_acquire(tokens=1), "Should not acquire 3rd token"
    
    def test_refill_does_not_exceed_burst(self):
        """Test that refill does not exceed burst capacity."""
        # 60 tokens/min = 1 token/sec, burst = 3
        limiter = TokenBucketRateLimiter(tokens_per_minute=60, burst_capacity=3)
        
        # Wait for 10 seconds (would refill 10 tokens, but capped at burst=3)
        time.sleep(10)
        
        # Should only have 3 tokens available (burst capacity)
        assert limiter.try_acquire(tokens=1), "Should acquire 1st token"
        assert limiter.try_acquire(tokens=1), "Should acquire 2nd token"
        assert limiter.try_acquire(tokens=1), "Should acquire 3rd token"
        assert not limiter.try_acquire(tokens=1), "Should not acquire 4th token (capped at burst)"
    
    def test_acquire_blocking(self):
        """Test that acquire() blocks until tokens are available."""
        # 60 tokens/min = 1 token/sec, burst = 2
        limiter = TokenBucketRateLimiter(tokens_per_minute=60, burst_capacity=2)
        
        # Exhaust burst
        limiter.try_acquire(tokens=2)
        
        # Acquire should block for ~1 second until token refills
        start_time = time.time()
        success = limiter.acquire(tokens=1, timeout=2.0)
        elapsed = time.time() - start_time
        
        assert success, "Should successfully acquire token after waiting"
        assert 0.8 < elapsed < 1.5, f"Should wait ~1 second, waited {elapsed}s"
    
    def test_acquire_timeout(self):
        """Test that acquire() respects timeout."""
        # Very slow refill: 6 tokens/min = 0.1 token/sec
        limiter = TokenBucketRateLimiter(tokens_per_minute=6, burst_capacity=1)
        
        # Exhaust burst
        limiter.try_acquire(tokens=1)
        
        # Try to acquire with short timeout (should fail)
        start_time = time.time()
        success = limiter.acquire(tokens=1, timeout=0.5)
        elapsed = time.time() - start_time
        
        assert not success, "Should timeout before acquiring token"
        assert 0.4 < elapsed < 0.7, f"Should timeout after ~0.5s, took {elapsed}s"
    
    def test_acquire_multiple_tokens(self):
        """Test acquiring multiple tokens at once."""
        limiter = TokenBucketRateLimiter(tokens_per_minute=60, burst_capacity=10)
        
        # Acquire 5 tokens at once
        success = limiter.try_acquire(tokens=5)
        assert success, "Should acquire 5 tokens"
        assert limiter.get_available_tokens() == 5.0, "Should have 5 tokens left"
        
        # Try to acquire 6 more (should fail, only 5 available)
        success = limiter.try_acquire(tokens=6)
        assert not success, "Should not acquire 6 tokens (only 5 available)"
    
    def test_acquire_invalid_tokens(self):
        """Test that invalid token counts raise ValueError."""
        limiter = TokenBucketRateLimiter(tokens_per_minute=60, burst_capacity=5)
        
        with pytest.raises(ValueError, match="tokens must be positive"):
            limiter.acquire(tokens=0)
        
        with pytest.raises(ValueError, match="tokens must be positive"):
            limiter.try_acquire(tokens=-1)
    
    def test_get_wait_time(self):
        """Test wait time calculation."""
        # 60 tokens/min = 1 token/sec
        limiter = TokenBucketRateLimiter(tokens_per_minute=60, burst_capacity=5)
        
        # Exhaust burst
        limiter.try_acquire(tokens=5)
        
        # Wait time for 1 token should be ~1 second
        wait_time = limiter.get_wait_time(tokens=1)
        assert 0.9 < wait_time < 1.1, f"Wait time should be ~1s, got {wait_time}s"
        
        # Wait time for 3 tokens should be ~3 seconds
        wait_time = limiter.get_wait_time(tokens=3)
        assert 2.9 < wait_time < 3.1, f"Wait time should be ~3s, got {wait_time}s"
    
    def test_get_wait_time_with_available_tokens(self):
        """Test that wait time is 0 when tokens are available."""
        limiter = TokenBucketRateLimiter(tokens_per_minute=60, burst_capacity=5)
        
        # Should have 5 tokens available
        wait_time = limiter.get_wait_time(tokens=3)
        assert wait_time == 0.0, "Wait time should be 0 when tokens are available"
    
    def test_reset(self):
        """Test that reset restores full burst capacity."""
        limiter = TokenBucketRateLimiter(tokens_per_minute=60, burst_capacity=5)
        
        # Exhaust burst
        limiter.try_acquire(tokens=5)
        assert limiter.get_available_tokens() == 0.0, "Should have 0 tokens"
        
        # Reset
        limiter.reset()
        assert limiter.get_available_tokens() == 5.0, "Should have full burst after reset"
    
    def test_thread_safety(self):
        """Test that rate limiter is thread-safe."""
        limiter = TokenBucketRateLimiter(tokens_per_minute=600, burst_capacity=50)
        
        acquired_counts = []
        lock = threading.Lock()
        
        def worker():
            """Worker thread that tries to acquire tokens."""
            count = 0
            for _ in range(10):
                if limiter.try_acquire(tokens=1):
                    count += 1
                time.sleep(0.01)  # Small delay
            
            with lock:
                acquired_counts.append(count)
        
        # Start 10 threads
        threads = []
        for _ in range(10):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        # Total acquired should not exceed burst capacity + refills
        total_acquired = sum(acquired_counts)
        # With 10 threads * 10 attempts * 0.01s delay = ~1 second total
        # Burst = 50, refill = 600/60 = 10 tokens/sec
        # Max possible = 50 + 10 = 60 tokens
        assert total_acquired <= 60, f"Acquired too many tokens: {total_acquired}"
        assert total_acquired >= 50, f"Should acquire at least burst capacity: {total_acquired}"
    
    def test_concurrent_acquire_blocking(self):
        """Test that multiple threads can block and acquire tokens."""
        limiter = TokenBucketRateLimiter(tokens_per_minute=60, burst_capacity=2)
        
        results = []
        lock = threading.Lock()
        
        def worker(worker_id):
            """Worker that blocks to acquire a token."""
            start = time.time()
            success = limiter.acquire(tokens=1, timeout=5.0)
            elapsed = time.time() - start
            
            with lock:
                results.append({
                    'worker_id': worker_id,
                    'success': success,
                    'elapsed': elapsed
                })
        
        # Start 5 threads (burst=2, so 3 will need to wait)
        threads = []
        for i in range(5):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        # All should succeed
        assert all(r['success'] for r in results), "All workers should acquire tokens"
        assert len(results) == 5, "All 5 workers should complete"
        
        # First 2 should be fast (burst), next 3 should wait
        fast_workers = [r for r in results if r['elapsed'] < 0.5]
        slow_workers = [r for r in results if r['elapsed'] >= 0.5]
        
        assert len(fast_workers) == 2, f"2 workers should be fast (burst), got {len(fast_workers)}"
        assert len(slow_workers) == 3, f"3 workers should wait, got {len(slow_workers)}"
    
    def test_high_rate_limit(self):
        """Test with high rate limit (many tokens per minute)."""
        # 600 tokens/min = 10 tokens/sec
        limiter = TokenBucketRateLimiter(tokens_per_minute=600, burst_capacity=20)
        
        # Should be able to acquire 20 tokens immediately
        for i in range(20):
            success = limiter.try_acquire(tokens=1)
            assert success, f"Should acquire token {i+1}"
        
        # Wait 0.5 seconds (should refill ~5 tokens)
        time.sleep(0.5)
        
        # Should be able to acquire ~5 more tokens
        acquired = 0
        for _ in range(10):
            if limiter.try_acquire(tokens=1):
                acquired += 1
        
        assert 4 <= acquired <= 6, f"Should acquire ~5 tokens, got {acquired}"
    
    def test_low_rate_limit(self):
        """Test with low rate limit (few tokens per minute)."""
        # 6 tokens/min = 0.1 tokens/sec = 1 token per 10 seconds
        limiter = TokenBucketRateLimiter(tokens_per_minute=6, burst_capacity=2)
        
        # Exhaust burst
        limiter.try_acquire(tokens=2)
        
        # Wait time for next token should be ~10 seconds
        wait_time = limiter.get_wait_time(tokens=1)
        assert 9.5 < wait_time < 10.5, f"Wait time should be ~10s, got {wait_time}s"


def test_rate_limiter_integration():
    """Integration test simulating real usage pattern."""
    # Simulate 30 calls per minute with burst of 5
    limiter = TokenBucketRateLimiter(tokens_per_minute=30, burst_capacity=5)
    
    call_times = []
    
    # Make 10 calls
    for i in range(10):
        wait_time = limiter.get_wait_time(tokens=1)
        if wait_time > 0:
            print(f"Call {i+1}: Waiting {wait_time:.2f}s")
        
        start = time.time()
        limiter.acquire(tokens=1)
        call_times.append(time.time() - start)
    
    # First 5 calls should be fast (burst)
    assert all(t < 0.1 for t in call_times[:5]), "First 5 calls should be fast (burst)"
    
    # Remaining calls should have some delay
    assert any(t > 0.5 for t in call_times[5:]), "Later calls should have delays"
    
    print(f"\nCall times: {[f'{t:.2f}s' for t in call_times]}")


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v', '-s'])
</content>
<line_count>346</line_count>
</write_to_file>

---

**User:**

[write_to_file for 'test_rate_limiter.py'] Result:
<file_write_result>
<path>test_rate_limiter.py</path>
<operation>created</operation>
<problems>

New problems detected after saving the file:
test_rate_limiter.py
- [basedpyright Error] 8 | import pytest : Import "pytest" could not be resolved</problems>
<notice>
<i>You do not need to re-read the file, as you have seen all changes</i>
<i>Proceed with the task using these changes as the new baseline.</i>
</notice>
</file_write_result>

<environment_details>
# VSCode Visible Files
test_rate_limiter.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,app/git_parser.py,test_language_support.py,data/repos.json,app/templates/dashboard.html

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:01:59.050Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$0.66

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
| 1 | Create token-bucket rate limiter class (thread-safe) | Completed |
| 2 | Add rate limit configuration to config.py | Completed |
| 3 | Integrate rate limiter into batch_analyze function | Completed |
| 4 | Add logging for rate limit waits | Completed |
| 5 | Create comprehensive tests for rate limiter | In Progress |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

<update_todo_list>
<todos>
[x] Create token-bucket rate limiter class (thread-safe)
[x] Add rate limit configuration to config.py
[x] Integrate rate limiter into batch_analyze function
[x] Add logging for rate limit waits
[x] Create comprehensive tests for rate limiter
</todos>
</update_todo_list>

---

**User:**

[update_todo_list] Result:
Todo list updated successfully.
<environment_details>
# VSCode Visible Files
test_rate_limiter.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,app/git_parser.py,test_language_support.py,data/repos.json,app/templates/dashboard.html

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:02:20.966Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$0.74

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
| 1 | Create token-bucket rate limiter class (thread-safe) | Completed |
| 2 | Add rate limit configuration to config.py | Completed |
| 3 | Integrate rate limiter into batch_analyze function | Completed |
| 4 | Add logging for rate limit waits | Completed |
| 5 | Create comprehensive tests for rate limiter | Completed |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

Perfect! Now let me run the tests to verify everything works correctly:

<execute_command>
<command>python -m pytest test_rate_limiter.py -v</command>
</execute_command>

---

**User:**

[execute_command for 'python -m pytest test_rate_limiter.py -v'] Result:
Command executed in terminal  within working directory 'c:/Users/Rohit/driftguard'. Exit code: 0
Output:
============================= test session starts =============================
platform win32 -- Python 3.11.0, pytest-9.0.3, pluggy-1.6.0 -- C:\Users\Rohit\AppData\Local\Programs\Python\Python311\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\Rohit\driftguard
plugins: anyio-4.12.1
collecting ... collected 17 items

test_rate_limiter.py::TestTokenBucketRateLimiter::test_initialization PASSED [  5%]
test_rate_limiter.py::TestTokenBucketRateLimiter::test_initialization_invalid_params PASSED [ 11%]
test_rate_limiter.py::TestTokenBucketRateLimiter::test_burst_behavior PASSED [ 17%]
test_rate_limiter.py::TestTokenBucketRateLimiter::test_refill_behavior PASSED [ 23%]
test_rate_limiter.py::TestTokenBucketRateLimiter::test_refill_does_not_exceed_burst PASSED [ 29%]
test_rate_limiter.py::TestTokenBucketRateLimiter::test_acquire_blocking PASSED [ 35%]
test_rate_limiter.py::TestTokenBucketRateLimiter::test_acquire_timeout PASSED [ 41%]
test_rate_limiter.py::TestTokenBucketRateLimiter::test_acquire_multiple_tokens PASSED [ 47%]
test_rate_limiter.py::TestTokenBucketRateLimiter::test_acquire_invalid_tokens PASSED [ 52%]
test_rate_limiter.py::TestTokenBucketRateLimiter::test_get_wait_time PASSED [ 58%]
test_rate_limiter.py::TestTokenBucketRateLimiter::test_get_wait_time_with_available_tokens PASSED [ 64%]
test_rate_limiter.py::TestTokenBucketRateLimiter::test_reset PASSED      [ 70%]
test_rate_limiter.py::TestTokenBucketRateLimiter::test_thread_safety PASSED [ 76%]
test_rate_limiter.py::TestTokenBucketRateLimiter::test_concurrent_acquire_blocking PASSED [ 82%]
test_rate_limiter.py::TestTokenBucketRateLimiter::test_high_rate_limit PASSED [ 88%]
test_rate_limiter.py::TestTokenBucketRateLimiter::test_low_rate_limit PASSED [ 94%]
test_rate_limiter.py::test_rate_limiter_integration PASSED               [100%]

============================= 17 passed in 27.31s =============================

<environment_details>
# VSCode Visible Files
test_rate_limiter.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,app/git_parser.py,test_language_support.py,data/repos.json,app/templates/dashboard.html

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:03:07.048Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$0.83

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
| 1 | Create token-bucket rate limiter class (thread-safe) | Completed |
| 2 | Add rate limit configuration to config.py | Completed |
| 3 | Integrate rate limiter into batch_analyze function | Completed |
| 4 | Add logging for rate limit waits | Completed |
| 5 | Create comprehensive tests for rate limiter | Completed |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

Excellent! All tests pass. Now let me update the .env.example file to document the new configuration options:

<read_file>
<args>
<file>
<path>.env.example</path>
</file>
</args>
</read_file>

---

**User:**

[read_file for '.env.example'. Reading multiple files at once is more efficient for the LLM. If other files are relevant to your current task, please read them simultaneously.] Result:
<files>
<file><path>.env.example</path>
<content lines="1-49">
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
49 | # Made with Bob
</content>
</file>
</files>
<environment_details>
# VSCode Visible Files
test_rate_limiter.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,app/git_parser.py,test_language_support.py,data/repos.json,app/templates/dashboard.html

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:03:12.880Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$0.93

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
| 1 | Create token-bucket rate limiter class (thread-safe) | Completed |
| 2 | Add rate limit configuration to config.py | Completed |
| 3 | Integrate rate limiter into batch_analyze function | Completed |
| 4 | Add logging for rate limit waits | Completed |
| 5 | Create comprehensive tests for rate limiter | Completed |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

<apply_diff>
<path>.env.example</path>
<diff>
<<<<<<< SEARCH
:start_line:40
-------
# Analysis Cache Configuration
# Enable caching of analysis results to speed up repeated analyses
DRIFTGUARD_CACHE_ENABLED=true

# Cache time-to-live in hours (0 = no expiry, cache never expires)
# Set to a positive number to automatically expire old cache entries
# Example: 168 = 7 days, 720 = 30 days
DRIFTGUARD_CACHE_TTL_HOURS=0

# Made with Bob
=======
# Analysis Cache Configuration
# Enable caching of analysis results to speed up repeated analyses
DRIFTGUARD_CACHE_ENABLED=true

# Cache time-to-live in hours (0 = no expiry, cache never expires)
# Set to a positive number to automatically expire old cache entries
# Example: 168 = 7 days, 720 = 30 days
DRIFTGUARD_CACHE_TTL_HOURS=0

# Rate Limiting Configuration
# Control the rate of Bob analysis calls to prevent overwhelming the system
# BOB_RATE_LIMIT_PER_MINUTE: Maximum number of analysis calls per minute (default: 30)
BOB_RATE_LIMIT_PER_MINUTE=30

# BOB_RATE_LIMIT_BURST: Burst capacity for rapid initial requests (default: 5)
# Allows up to this many requests immediately before rate limiting kicks in
BOB_RATE_LIMIT_BURST=5

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
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,app/git_parser.py,test_language_support.py,data/repos.json,app/templates/dashboard.html

# Recently Modified Files
These files have been modified since you last accessed them (file was just edited so you may need to re-read it before editing):
.env.example

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:03:33.589Z
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
| 1 | Create token-bucket rate limiter class (thread-safe) | Completed |
| 2 | Add rate limit configuration to config.py | Completed |
| 3 | Integrate rate limiter into batch_analyze function | Completed |
| 4 | Add logging for rate limit waits | Completed |
| 5 | Create comprehensive tests for rate limiter | Completed |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

Perfect! Now let me create a quick demonstration script to show the rate limiter in action:

<write_to_file>
<path>demo_rate_limiter.py</path>
<content>"""demo_rate_limiter.py

Demonstration of the rate limiter functionality.
Shows burst behavior, refill behavior, and rate limiting in action.
"""
import time
from app.rate_limiter import TokenBucketRateLimiter


def demo_burst_behavior():
    """Demonstrate burst capacity allowing rapid initial requests."""
    print("\n" + "=" * 70)
    print("DEMO 1: Burst Behavior")
    print("=" * 70)
    print("Rate limit: 30 calls/min (1 call every 2 seconds)")
    print("Burst capacity: 5 calls")
    print()
    
    limiter = TokenBucketRateLimiter(tokens_per_minute=30, burst_capacity=5)
    
    print("Making 8 requests...")
    for i in range(8):
        wait_time = limiter.get_wait_time(tokens=1)
        if wait_time > 0:
            print(f"Request {i+1}: Rate limiter waiting {wait_time:.1f}s before next Bob request")
        else:
            print(f"Request {i+1}: Immediate (using burst capacity)")
        
        start = time.time()
        limiter.acquire(tokens=1)
        elapsed = time.time() - start
        
        if elapsed > 0.1:
            print(f"           → Waited {elapsed:.1f}s")
    
    print("\n✓ First 5 requests used burst capacity (immediate)")
    print("✓ Requests 6-8 had to wait for token refill")


def demo_refill_behavior():
    """Demonstrate token refill over time."""
    print("\n" + "=" * 70)
    print("DEMO 2: Token Refill Behavior")
    print("=" * 70)
    print("Rate limit: 60 calls/min (1 call per second)")
    print("Burst capacity: 3 calls")
    print()
    
    limiter = TokenBucketRateLimiter(tokens_per_minute=60, burst_capacity=3)
    
    # Exhaust burst
    print("Exhausting burst capacity (3 tokens)...")
    for i in range(3):
        limiter.try_acquire(tokens=1)
        print(f"  Token {i+1} acquired")
    
    print(f"\nAvailable tokens: {limiter.get_available_tokens():.1f}")
    print("\nWaiting 2 seconds for refill...")
    time.sleep(2)
    
    print(f"Available tokens after 2s: {limiter.get_available_tokens():.1f}")
    print("✓ Tokens refilled at rate of 1 token/second")


def demo_rate_limiting_in_action():
    """Demonstrate rate limiting with realistic scenario."""
    print("\n" + "=" * 70)
    print("DEMO 3: Rate Limiting in Action (Realistic Scenario)")
    print("=" * 70)
    print("Simulating batch analysis of 10 files")
    print("Rate limit: 30 calls/min, Burst: 5")
    print()
    
    limiter = TokenBucketRateLimiter(tokens_per_minute=30, burst_capacity=5)
    
    files = [f"file_{i}.py" for i in range(1, 11)]
    
    start_time = time.time()
    for i, file_path in enumerate(files, 1):
        wait_time = limiter.get_wait_time(tokens=1)
        
        if wait_time > 0:
            print(f"[{i}/10] Analyzing: {file_path}")
            print(f"        [RATE LIMIT] Waiting {wait_time:.1f}s before next Bob request")
        else:
            print(f"[{i}/10] Analyzing: {file_path}")
        
        limiter.acquire(tokens=1)
        
        # Simulate analysis work
        time.sleep(0.1)
    
    total_time = time.time() - start_time
    print(f"\n✓ Completed 10 analyses in {total_time:.1f}s")
    print(f"✓ First 5 used burst (fast), remaining 5 were rate limited")


def demo_configuration_options():
    """Show different configuration options."""
    print("\n" + "=" * 70)
    print("DEMO 4: Configuration Options")
    print("=" * 70)
    
    configs = [
        (30, 5, "Default: 30 calls/min, burst 5"),
        (60, 10, "High throughput: 60 calls/min, burst 10"),
        (10, 2, "Conservative: 10 calls/min, burst 2"),
    ]
    
    for rate, burst, description in configs:
        print(f"\n{description}")
        limiter = TokenBucketRateLimiter(tokens_per_minute=rate, burst_capacity=burst)
        
        # Show burst
        print(f"  Burst capacity: {burst} immediate calls")
        
        # Show refill rate
        refill_rate = rate / 60.0
        print(f"  Refill rate: {refill_rate:.2f} tokens/second")
        
        # Show wait time after burst
        for _ in range(burst):
            limiter.try_acquire(tokens=1)
        wait_time = limiter.get_wait_time(tokens=1)
        print(f"  Wait time after burst: {wait_time:.1f}s")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print("🚀 DriftGuard Rate Limiter Demonstration")
    print("=" * 70)
    
    demo_burst_behavior()
    demo_refill_behavior()
    demo_rate_limiting_in_action()
    demo_configuration_options()
    
    print("\n" + "=" * 70)
    print("✅ All demonstrations complete!")
    print("=" * 70)
    print("\nConfiguration via environment variables:")
    print("  BOB_RATE_LIMIT_PER_MINUTE=30  # Max calls per minute")
    print("  BOB_RATE_LIMIT_BURST=5        # Burst capacity")
    print()


if __name__ == '__main__':
    main()
</content>
<line_count>145</line_count>
</write_to_file>

---

**User:**

[write_to_file for 'demo_rate_limiter.py'] Result:
<file_write_result>
<path>demo_rate_limiter.py</path>
<operation>created</operation>
<notice>
<i>You do not need to re-read the file, as you have seen all changes</i>
<i>Proceed with the task using these changes as the new baseline.</i>
</notice>
</file_write_result>

<environment_details>
# VSCode Visible Files
demo_rate_limiter.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,app/git_parser.py,test_language_support.py,data/repos.json,app/templates/dashboard.html

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:04:13.963Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$1.12

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
| 1 | Create token-bucket rate limiter class (thread-safe) | Completed |
| 2 | Add rate limit configuration to config.py | Completed |
| 3 | Integrate rate limiter into batch_analyze function | Completed |
| 4 | Add logging for rate limit waits | Completed |
| 5 | Create comprehensive tests for rate limiter | Completed |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

Now let me run the demonstration to show the rate limiter in action:

<execute_command>
<command>python demo_rate_limiter.py</command>
</execute_command>

---

**User:**

[execute_command for 'python demo_rate_limiter.py'] Result:
Command executed in terminal  within working directory 'c:/Users/Rohit/driftguard'. Command execution was not successful, inspect the cause and adjust as needed.
Exit code: 1
Output:

======================================================================
Traceback (most recent call last):
  File "C:\Users\Rohit\driftguard\demo_rate_limiter.py", line 149, in <module>
    main()
  File "C:\Users\Rohit\driftguard\demo_rate_limiter.py", line 131, in main
    print("\U0001f680 DriftGuard Rate Limiter Demonstration")
  File "C:\Users\Rohit\AppData\Local\Programs\Python\Python311\Lib\encodings\cp1252.py", line 19, in encode
    return codecs.charmap_encode(input,self.errors,encoding_table)[0]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f680' in position 0: character maps to <undefined>

<environment_details>
# VSCode Visible Files
demo_rate_limiter.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,app/git_parser.py,test_language_support.py,data/repos.json,app/templates/dashboard.html

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:04:24.567Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$1.23

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
| 1 | Create token-bucket rate limiter class (thread-safe) | Completed |
| 2 | Add rate limit configuration to config.py | Completed |
| 3 | Integrate rate limiter into batch_analyze function | Completed |
| 4 | Add logging for rate limit waits | Completed |
| 5 | Create comprehensive tests for rate limiter | Completed |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

Let me fix the Unicode issue in the demo script:

<apply_diff>
<path>demo_rate_limiter.py</path>
<diff>
<<<<<<< SEARCH
:start_line:127
-------
def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print("🚀 DriftGuard Rate Limiter Demonstration")
    print("=" * 70)
=======
def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print("DriftGuard Rate Limiter Demonstration")
    print("=" * 70)
>>>>>>> REPLACE
</diff>
</apply_diff>

---

**User:**

[apply_diff for 'demo_rate_limiter.py'] Result:
<file_write_result>
<path>demo_rate_limiter.py</path>
<operation>modified</operation>
<notice>
<i>You do not need to re-read the file, as you have seen all changes</i>
<i>Proceed with the task using these changes as the new baseline.</i>
</notice>
</file_write_result>

<notice>Making multiple related changes in a single apply_diff is more efficient. If other changes are needed in this file, please include them as additional SEARCH/REPLACE blocks.</notice>
<environment_details>
# VSCode Visible Files
demo_rate_limiter.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,app/git_parser.py,test_language_support.py,data/repos.json,app/templates/dashboard.html

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:04:36.367Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$1.33

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
| 1 | Create token-bucket rate limiter class (thread-safe) | Completed |
| 2 | Add rate limit configuration to config.py | Completed |
| 3 | Integrate rate limiter into batch_analyze function | Completed |
| 4 | Add logging for rate limit waits | Completed |
| 5 | Create comprehensive tests for rate limiter | Completed |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

<apply_diff>
<path>demo_rate_limiter.py</path>
<diff>
<<<<<<< SEARCH
:start_line:138
-------
    print("\n" + "=" * 70)
    print("✅ All demonstrations complete!")
    print("=" * 70)
=======
    print("\n" + "=" * 70)
    print("All demonstrations complete!")
    print("=" * 70)
>>>>>>> REPLACE
</diff>
</apply_diff>

---

**User:**

[apply_diff for 'demo_rate_limiter.py'] Result:
<file_write_result>
<path>demo_rate_limiter.py</path>
<operation>modified</operation>
<notice>
<i>You do not need to re-read the file, as you have seen all changes</i>
<i>Proceed with the task using these changes as the new baseline.</i>
</notice>
</file_write_result>

<notice>Making multiple related changes in a single apply_diff is more efficient. If other changes are needed in this file, please include them as additional SEARCH/REPLACE blocks.</notice>
<environment_details>
# VSCode Visible Files
demo_rate_limiter.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,app/git_parser.py,test_language_support.py,data/repos.json,app/templates/dashboard.html

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:04:49.716Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$1.44

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
| 1 | Create token-bucket rate limiter class (thread-safe) | Completed |
| 2 | Add rate limit configuration to config.py | Completed |
| 3 | Integrate rate limiter into batch_analyze function | Completed |
| 4 | Add logging for rate limit waits | Completed |
| 5 | Create comprehensive tests for rate limiter | Completed |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

<execute_command>
<command>python demo_rate_limiter.py</command>
</execute_command>

---

**User:**

[execute_command for 'python demo_rate_limiter.py'] Result:
Command executed in terminal  within working directory 'c:/Users/Rohit/driftguard'. Command execution was not successful, inspect the cause and adjust as needed.
Exit code: 1
Output:

======================================================================
DriftGuard Rate Limiter Demonstration
======================================================================

======================================================================
DEMO 1: Burst Behavior
======================================================================
Rate limit: 30 calls/min (1 call every 2 seconds)
Burst capacity: 5 calls

Making 8 requests...
Request 1: Immediate (using burst capacity)
Request 2: Immediate (using burst capacity)
Request 3: Immediate (using burst capacity)
Request 4: Immediate (using burst capacity)
Request 5: Immediate (using burst capacity)
Request 6: Rate limiter waiting 2.0s before next Bob request
Traceback (most recent call last):
  File "C:\Users\Rohit\driftguard\demo_rate_limiter.py", line 149, in <module>
    main()
  File "C:\Users\Rohit\driftguard\demo_rate_limiter.py", line 134, in main
    demo_burst_behavior()
  File "C:\Users\Rohit\driftguard\demo_rate_limiter.py", line 34, in demo_burst_behavior
    print(f"           \u2192 Waited {elapsed:.1f}s")
  File "C:\Users\Rohit\AppData\Local\Programs\Python\Python311\Lib\encodings\cp1252.py", line 19, in encode
    return codecs.charmap_encode(input,self.errors,encoding_table)[0]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'charmap' codec can't encode character '\u2192' in position 11: character maps to <undefined>

<environment_details>
# VSCode Visible Files
demo_rate_limiter.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,app/git_parser.py,test_language_support.py,data/repos.json,app/templates/dashboard.html

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:04:57.079Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$1.55

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
| 1 | Create token-bucket rate limiter class (thread-safe) | Completed |
| 2 | Add rate limit configuration to config.py | Completed |
| 3 | Integrate rate limiter into batch_analyze function | Completed |
| 4 | Add logging for rate limit waits | Completed |
| 5 | Create comprehensive tests for rate limiter | Completed |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

<apply_diff>
<path>demo_rate_limiter.py</path>
<diff>
<<<<<<< SEARCH
:start_line:30
-------
        start = time.time()
        limiter.acquire(tokens=1)
        elapsed = time.time() - start
        
        if elapsed > 0.1:
            print(f"           → Waited {elapsed:.1f}s")
    
    print("\n✓ First 5 requests used burst capacity (immediate)")
    print("✓ Requests 6-8 had to wait for token refill")
=======
        start = time.time()
        limiter.acquire(tokens=1)
        elapsed = time.time() - start
        
        if elapsed > 0.1:
            print(f"           > Waited {elapsed:.1f}s")
    
    print("\nOK First 5 requests used burst capacity (immediate)")
    print("OK Requests 6-8 had to wait for token refill")
>>>>>>> REPLACE
</diff>
</apply_diff>

---

**User:**

[apply_diff for 'demo_rate_limiter.py'] Result:
<file_write_result>
<path>demo_rate_limiter.py</path>
<operation>modified</operation>
<notice>
<i>You do not need to re-read the file, as you have seen all changes</i>
<i>Proceed with the task using these changes as the new baseline.</i>
</notice>
</file_write_result>

<notice>Making multiple related changes in a single apply_diff is more efficient. If other changes are needed in this file, please include them as additional SEARCH/REPLACE blocks.</notice>
<environment_details>
# VSCode Visible Files
demo_rate_limiter.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,app/git_parser.py,test_language_support.py,data/repos.json,app/templates/dashboard.html

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:05:08.602Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$1.66

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
| 1 | Create token-bucket rate limiter class (thread-safe) | Completed |
| 2 | Add rate limit configuration to config.py | Completed |
| 3 | Integrate rate limiter into batch_analyze function | Completed |
| 4 | Add logging for rate limit waits | Completed |
| 5 | Create comprehensive tests for rate limiter | Completed |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

<apply_diff>
<path>demo_rate_limiter.py</path>
<diff>
<<<<<<< SEARCH
:start_line:54
-------
    print(f"\nAvailable tokens: {limiter.get_available_tokens():.1f}")
    print("\nWaiting 2 seconds for refill...")
    time.sleep(2)
    
    print(f"Available tokens after 2s: {limiter.get_available_tokens():.1f}")
    print("✓ Tokens refilled at rate of 1 token/second")
=======
    print(f"\nAvailable tokens: {limiter.get_available_tokens():.1f}")
    print("\nWaiting 2 seconds for refill...")
    time.sleep(2)
    
    print(f"Available tokens after 2s: {limiter.get_available_tokens():.1f}")
    print("OK Tokens refilled at rate of 1 token/second")
>>>>>>> REPLACE
</diff>
</apply_diff>

---

**User:**

[apply_diff for 'demo_rate_limiter.py'] Result:
<file_write_result>
<path>demo_rate_limiter.py</path>
<operation>modified</operation>
<notice>
<i>You do not need to re-read the file, as you have seen all changes</i>
<i>Proceed with the task using these changes as the new baseline.</i>
</notice>
</file_write_result>

<notice>Making multiple related changes in a single apply_diff is more efficient. If other changes are needed in this file, please include them as additional SEARCH/REPLACE blocks.</notice>
<environment_details>
# VSCode Visible Files
demo_rate_limiter.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,app/git_parser.py,test_language_support.py,data/repos.json,app/templates/dashboard.html

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:05:17.789Z
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
| 1 | Create token-bucket rate limiter class (thread-safe) | Completed |
| 2 | Add rate limit configuration to config.py | Completed |
| 3 | Integrate rate limiter into batch_analyze function | Completed |
| 4 | Add logging for rate limit waits | Completed |
| 5 | Create comprehensive tests for rate limiter | Completed |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

<apply_diff>
<path>demo_rate_limiter.py</path>
<diff>
<<<<<<< SEARCH
:start_line:82
-------
    total_time = time.time() - start_time
    print(f"\n✓ Completed 10 analyses in {total_time:.1f}s")
    print(f"✓ First 5 used burst (fast), remaining 5 were rate limited")
=======
    total_time = time.time() - start_time
    print(f"\nOK Completed 10 analyses in {total_time:.1f}s")
    print(f"OK First 5 used burst (fast), remaining 5 were rate limited")
>>>>>>> REPLACE
</diff>
</apply_diff>

---

**User:**

[apply_diff for 'demo_rate_limiter.py'] Result:
<file_write_result>
<path>demo_rate_limiter.py</path>
<operation>modified</operation>
<notice>
<i>You do not need to re-read the file, as you have seen all changes</i>
<i>Proceed with the task using these changes as the new baseline.</i>
</notice>
</file_write_result>

<notice>Making multiple related changes in a single apply_diff is more efficient. If other changes are needed in this file, please include them as additional SEARCH/REPLACE blocks.</notice>
<environment_details>
# VSCode Visible Files
demo_rate_limiter.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,app/git_parser.py,test_language_support.py,data/repos.json,app/templates/dashboard.html

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:05:25.833Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$1.90

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
| 1 | Create token-bucket rate limiter class (thread-safe) | Completed |
| 2 | Add rate limit configuration to config.py | Completed |
| 3 | Integrate rate limiter into batch_analyze function | Completed |
| 4 | Add logging for rate limit waits | Completed |
| 5 | Create comprehensive tests for rate limiter | Completed |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

Now let me run the demo again:

<execute_command>
<command>python demo_rate_limiter.py</command>
</execute_command>

---

**User:**

[execute_command for 'python demo_rate_limiter.py'] Result:
Command executed in terminal  within working directory 'c:/Users/Rohit/driftguard'. Exit code: 0
Output:

======================================================================
DriftGuard Rate Limiter Demonstration
======================================================================

======================================================================
DEMO 1: Burst Behavior
======================================================================
Rate limit: 30 calls/min (1 call every 2 seconds)
Burst capacity: 5 calls

Making 8 requests...
Request 1: Immediate (using burst capacity)
Request 2: Immediate (using burst capacity)
Request 3: Immediate (using burst capacity)
Request 4: Immediate (using burst capacity)
Request 5: Immediate (using burst capacity)
Request 6: Rate limiter waiting 2.0s before next Bob request
           > Waited 2.0s
Request 7: Rate limiter waiting 2.0s before next Bob request
           > Waited 2.0s
Request 8: Rate limiter waiting 2.0s before next Bob request
           > Waited 2.0s

OK First 5 requests used burst capacity (immediate)
OK Requests 6-8 had to wait for token refill

======================================================================
DEMO 2: Token Refill Behavior
======================================================================
Rate limit: 60 calls/min (1 call per second)
Burst capacity: 3 calls

Exhausting burst capacity (3 tokens)...
  Token 1 acquired
  Token 2 acquired
  Token 3 acquired

Available tokens: 0.0

Waiting 2 seconds for refill...
Available tokens after 2s: 2.0
OK Tokens refilled at rate of 1 token/second

======================================================================
DEMO 3: Rate Limiting in Action (Realistic Scenario)
======================================================================
Simulating batch analysis of 10 files
Rate limit: 30 calls/min, Burst: 5

[1/10] Analyzing: file_1.py
[2/10] Analyzing: file_2.py
[3/10] Analyzing: file_3.py
[4/10] Analyzing: file_4.py
[5/10] Analyzing: file_5.py
[6/10] Analyzing: file_6.py
        [RATE LIMIT] Waiting 1.5s before next Bob request
[7/10] Analyzing: file_7.py
        [RATE LIMIT] Waiting 1.9s before next Bob request
[8/10] Analyzing: file_8.py
        [RATE LIMIT] Waiting 1.9s before next Bob request
[9/10] Analyzing: file_9.py
        [RATE LIMIT] Waiting 1.9s before next Bob request
[10/10] Analyzing: file_10.py
        [RATE LIMIT] Waiting 1.9s before next Bob request

OK Completed 10 analyses in 10.1s
OK First 5 used burst (fast), remaining 5 were rate limited

======================================================================
DEMO 4: Configuration Options
======================================================================

Default: 30 calls/min, burst 5
  Burst capacity: 5 immediate calls
  Refill rate: 0.50 tokens/second
  Wait time after burst: 2.0s

High throughput: 60 calls/min, burst 10
  Burst capacity: 10 immediate calls
  Refill rate: 1.00 tokens/second
  Wait time after burst: 1.0s

Conservative: 10 calls/min, burst 2
  Burst capacity: 2 immediate calls
  Refill rate: 0.17 tokens/second
  Wait time after burst: 6.0s

======================================================================
All demonstrations complete!
======================================================================

Configuration via environment variables:
  BOB_RATE_LIMIT_PER_MINUTE=30  # Max calls per minute
  BOB_RATE_LIMIT_BURST=5        # Burst capacity


<environment_details>
# VSCode Visible Files
demo_rate_limiter.py

# VSCode Open Tabs
ARCHITECTURE_PLAN.md,test_integration.py,test_db.py,test_trends_endpoint.py,app/trends.py,app/baseline_profile.py,app/scorer.py,test_trends.py,test_integration_trends.py,app/alert_manager.py,Dockerfile,docker-compose.yml,test_watch_mode.py,app/report_generator.py,WATCH_MODE.md,app/language_prompts.py,app/git_parser.py,test_language_support.py,data/repos.json,app/templates/dashboard.html

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\Rohit\driftguard`
### Original command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

# Current Time
Current time in ISO 8601 UTC format: 2026-05-02T15:05:49.599Z
User time zone: Asia/Calcutta, UTC+5:30

# Current Cost
$2.01

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
| 1 | Create token-bucket rate limiter class (thread-safe) | Completed |
| 2 | Add rate limit configuration to config.py | Completed |
| 3 | Integrate rate limiter into batch_analyze function | Completed |
| 4 | Add logging for rate limit waits | Completed |
| 5 | Create comprehensive tests for rate limiter | Completed |


IMPORTANT: When task status changes, remember to call the `update_todo_list` tool to update your progress.

</environment_details>

---

**Assistant:**

Perfect! The demonstration works beautifully. Now let me create a summary document and complete the task:

<attempt_completion>
<result>
Successfully implemented rate limiting around Bob analysis calls in DriftGuard:

## Implementation Summary

### 1. Token-Bucket Rate Limiter Class (`app/rate_limiter.py`)
- Thread-safe implementation using threading.Lock
- Configurable tokens per minute and burst capacity
- Token refill based on elapsed time
- Methods: acquire(), try_acquire(), get_wait_time(), get_available_tokens(), reset()

### 2. Configuration (`app/config.py`)
- BOB_RATE_LIMIT_PER_MINUTE (default: 30) - Max calls per minute
- BOB_RATE_LIMIT_BURST (default: 5) - Burst capacity for rapid initial requests
- Environment variable support via .env file

### 3. Integration (`app/bob_analyzer.py`)
- Rate limiter integrated into batch_analyze() function
- Each Bob analysis call acquires a token before execution
- Automatic waiting when rate limit is reached
- Logging of wait times: "Rate limiter waiting Xs before next Bob request"

### 4. Comprehensive Tests (`test_rate_limiter.py`)
- 17 test cases covering:
  - Burst behavior (rapid initial requests)
  - Refill behavior (token regeneration over time)
  - Thread safety (concurrent access)
  - Blocking and timeout behavior
  - Edge cases and validation
- All tests passing (27.31s execution time)

### 5. Documentation
- Updated .env.example with rate limit configuration
- Created demo_rate_limiter.py showing real-world usage
- Demonstration shows burst capacity, refill rate, and rate limiting in action

## Key Features
✓ Thread-safe token bucket algorithm
✓ Configurable via environment variables
✓ Burst capacity allows rapid initial requests
✓ Smooth token refill at constant rate
✓ Informative logging when throttling occurs
✓ Comprehensive test coverage
✓ Zero breaking changes to existing code

## Usage
Set environment variables:
```
BOB_RATE_LIMIT_PER_MINUTE=30
BOB_RATE_LIMIT_BURST=5
```

The rate limiter automatically applies to all batch analysis operations.
</result>
</attempt_completion>

