# Incident Response Runbook

## Severity levels

- **SEV-1**: Production outage, data integrity risk, or active credential compromise
- **SEV-2**: Major feature unavailable or sustained high error rate
- **SEV-3**: Degraded performance with acceptable workaround

## Immediate triage checklist

1. Confirm impact scope (which endpoints/users).
2. Check `/health/live` and `/health/ready`.
3. Inspect recent deploys and CI history.
4. Review logs by `X-Request-ID`.
5. Check upstream Kaleido status and circuit-breaker behavior.

## Secret exposure response

1. Revoke/rotate exposed keys immediately.
2. Update secrets in secret manager and deployment environment.
3. Redeploy services with new credentials.
4. Review access logs for suspicious activity.
5. Record timeline and impacted resources.

## Upstream outage (Kaleido) response

1. Confirm upstream status and error classes.
2. Verify API returns sanitized upstream errors.
3. Temporarily pause non-critical write flows if needed.
4. Keep read-only paths available where possible.
5. Communicate incident status and ETA.

## Rollback procedure

1. Identify last known good commit/image.
2. Deploy rollback artifact.
3. Validate health endpoints and smoke tests.
4. Continue monitoring for 30 minutes minimum.

## Recovery verification

- Error rate returns to baseline.
- Latency within SLO thresholds.
- Write idempotency and auth behavior confirmed.
- All critical endpoints pass smoke checks.

## Postmortem template

- Timeline
- Root cause
- Detection gaps
- Corrective actions
- Preventive actions and owners
