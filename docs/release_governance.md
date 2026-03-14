# Release Governance

This document defines minimum controls before production deployment.

## Required branch protections

Enable these rules on `main`:

- Require pull request before merge
- Require status checks to pass:
  - CI (python-tests, solidity-tests)
  - Security (python-audit, npm-audit-prod, slither, secret-scan)
- Require up-to-date branches before merge
- Require review from code owners
- Restrict force pushes and branch deletion

## Required artifacts before release

- Container image built successfully
- Test evidence for:
  - `python3 -m pytest`
  - `npm run test:solidity`
- Security scan results archived in CI
- Deployment change notes (what changed, rollback plan)

## Production deployment gates

1. All required checks green.
2. No open critical incidents.
3. Secrets rotated if key material changed.
4. On-call owner assigned for deployment window.

## Post-deploy validation

- Health checks: `/health/live`, `/health/ready`
- Functional smoke calls to read and write APIs
- Verify metrics/alerts for error rate and latency
