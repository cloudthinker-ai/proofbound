# Performance measurement

`@requires` validates a function's signature once for each calling pattern, then
uses cached readers for subsequent calls. A calling pattern consists only of the
number of positional arguments and the ordered keyword names. Each protected
function has a 128-entry LRU cache. Values and authority are never cache keys or
cached results: issuer, exact ordered subjects and live scopes are checked for
every invocation. Declared default values retain their original lifetime.

Cold calling patterns pay signature validation and reader construction once.
Invalid layouts are rejected by `Signature.bind`, with its existing errors.
Functions with default, positional-only, keyword-only or variadic parameters use
the same rules. Async functions check authority when awaited.

The linter constructs a parent map only for a `define_proof` call. It still parses
and visits every application source: reserved `.prove`, `.__wrapped__` and
`inspect.unwrap` forms can occur without a GDP import. Directory discovery prunes
`.git`, `.venv`, `__pycache__`, `node_modules` and `.test-*` directories before
descending. Explicit files or roots under those ancestors are still checked.
Diagnostic order and error handling remain unchanged.

## Reproduce

Use `make install` to provision dependencies, then `make bench` to build and
measure the release extension. Normal `make install` remains a development build;
package wheels are release builds. Never compare a development extension against
a release extension and attribute the difference to a source change.

Before editing, build release and snapshot the installed package:

```bash
make bench BENCH_ARGS="--output /tmp/proofbound-before.json"
.venv/bin/python - <<'PY'
import shutil
from pathlib import Path
import gdp

shutil.copytree(Path(gdp.__file__).parent, "/tmp/proofbound-baseline/gdp")
PY
```

After editing and rebuilding, compare both packages in one interpreter:

```bash
make bench BENCH_ARGS="--baseline /tmp/proofbound-baseline/gdp --output /tmp/proofbound-after.json"
```

Repeat the comparison. For Linux, `taskset -c CPU .venv/bin/python
scripts/bench_python.py ...` fixes CPU affinity after the release build. First
measure baseline against itself by setting `PYTHONPATH=/tmp/proofbound-baseline`
and passing that same package as `--baseline`; this estimates harness noise.
Do not run multiple benchmarks simultaneously.

The harness uses synthetic identities and source files, two warmups and nine
samples per case. Baseline/current order alternates. Every case checks outputs
before timing. JSON stores raw CPU/wall samples, medians, nearest-rank p95,
Python/platform, CPU affinity and host load. GC is disabled only inside timed
batches and its previous state is restored afterwards. Defaults use 10,000
iterations; use `--iterations 50000` for longer samples on a busy host. Lint
iterations are divided by 1,000 and async iterations by 100. The async case times
100 awaited calls plus an event-loop startup per batch.

These measurements isolate library overhead. They do not include policy or
database calls, network time, application concurrency, or proof adoption in the
CloudThinker backend. This shared host is oversubscribed; local CPU measurements
are useful for paired comparisons but wall times are not production latency.

## Verified comparison

On 2026-10-06, two paired comparisons against revision `95aaa9f` used CPython
3.12.3, the same release extension, CPU affinity 17, 50,000 iterations, two
warmups and nine samples. The extension binaries had identical SHA-256 hashes;
all gains come from Python argument handling and lint traversal. Both CPU and
wall medians and p95 improved for every optimized case in both comparisons.

| Case | Baseline CPU median, first run | Current CPU median, first run | CPU speedup across both runs |
| --- | ---: | ---: | ---: |
| Positional protected call | 7.045 µs | 1.861 µs | 3.79–3.95× |
| Keyword proof argument | 6.847 µs | 1.928 µs | 3.30–3.55× |
| All keyword arguments | 6.573 µs | 2.038 µs | 3.23–3.42× |
| Default arguments | 8.000 µs | 1.583 µs | 5.05–5.06× |
| Two proof requirements | 9.018 µs | 2.786 µs | 3.24–3.28× |
| Variadic call | 9.286 µs | 2.174 µs | 3.25–4.27× |
| 100 awaited calls plus loop startup | 993.544 µs | 397.304 µs | 2.39–2.50× |
| Lint 500 assignments plus two violations | 14.578 ms | 10.827 ms | 1.35–1.50× |
| Lint 16 application files plus 1,000 excluded files | 75.716 ms | 2.162 ms | 35.02–35.15× |

The baseline-against-itself comparison showed CPU median differences up to about
7%. Unchanged native/scoped controls varied within about 10% across the paired
runs; their implementations did not change. This variability is why results are
reported as ranges and are not timing thresholds in CI.

A separate diagnostic-equivalence audit checked all **8,616** Python files in
the CloudThinker backend application at revision `f87f234`. Every ordered
diagnostic sequence matched. Both versions reported the same eight GDP007
reserved unwrap-form diagnostics in this unadopted corpus. This is a lint-output
comparison; these diagnostics are not evidence of eight authorization bugs.
The single corpus audit consumed 48.63 CPU seconds for the baseline and 35.39
for the current checker, excluding directory discovery. Its primary result is
exact output parity; it is not a repeated endpoint or throughput benchmark.

[Raw measurements and build metadata](audits/2026-10-06-python-performance/)
contain the A/A run, both A/B runs, per-case samples, and corpus fingerprint.
Local `make check`, `make package-check`, the benchmark target and a fresh
release-wheel installation passed. The installed wheel passed all 46 Python
tests, the SQLite example, lint, and both static consumer checkers.
Implementation commit `13664c4` also passed all nine hosted jobs in
[CI run 37413254647](https://github.com/cloudthinker-ai/proofbound/actions/runs/37413254647),
including Python 3.11–3.14, all 16 platform/version wheel combinations and the
dependency advisory audit. No timing threshold is enforced on hosted runners.
