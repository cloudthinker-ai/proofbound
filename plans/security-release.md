# Security patch 0.1.1

The owner authorized fixing all findings, hardening GitHub, and publishing.
The design gate is skipped: the two fixes use existing decorator and CLI paths.

Reject callable instances and their partials at decoration time. Support Python
functions, bound methods, and partials of those functions. Keep ordinary async
verification at await time and reject generator functions before execution.
Report source-directory traversal failures as GDP000 and fail the lint command.

Add real SQLite and filesystem permission regressions. Confirm they fail against
the installed 0.1.0 wheel before changing implementation. Test normal functions,
bound methods, partials and existing sync/async authorization behavior afterward.
Use an unprivileged process for permission tests; skip only when the OS cannot
enforce these POSIX permissions, including Windows and privileged root execution.

Update both versions to 0.1.1, public API documentation, nearest AGENTS.md,
companion skill references, wiki, release notes and publishing guidance.
Keep original MIT license bytes and upstream attribution.

Enable secret scanning, push protection, Dependabot alerts/security updates, and
weekly version updates. Give wheel jobs stable names and run CI for every PR so
required checks cannot hang on path exclusions. After the release and evidence
are published, protect main with all nine CI jobs, one approval, stale-review
dismissal, conversation resolution, administrator enforcement, and no force
push or branch deletion. Do not weaken that protection to push later evidence.

Run make check, release packaging, fresh installed-wheel tests, cargo-audit,
secret scanning and all nine cross-platform CI jobs. Publish only the four
tested CI wheels and source archive from that exact green candidate. Inject
UV_PUBLISH_TOKEN through Infisical. Verify remote artifact hashes, a fresh public
PyPI installation, public release tag, and final GitHub settings.
