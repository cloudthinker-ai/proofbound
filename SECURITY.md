# Security reporting

Proofbound's 0.1 series is experimental. Security fixes target the latest 0.1
release; upgrade before reporting a problem in an older version.

Use GitHub's private vulnerability reporting:
[Report a vulnerability](https://github.com/cloudthinker-ai/proofbound/security/advisories/new).

Include the affected version, Python or Rust environment, a minimal reproduction,
and the expected and actual behavior. Use synthetic identities and omit
credentials or production payloads. Keep exploit details out of public issues.

The [guarantee matrix](docs/guarantees.md) defines the supported boundary.
Application policy, permission revocation, mutable values, check/write races and
hostile code already executing in the process remain application responsibilities.
