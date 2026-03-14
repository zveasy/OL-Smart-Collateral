# Security Baseline

This repository must not store production secrets in git.

## Secrets policy

- Never commit `.env` or raw credentials.
- Use `.env.example` only for placeholders.
- Store real values in a secret manager (for example: GitHub Actions secrets, AWS Secrets Manager, Vault).
- Inject secrets at runtime through environment variables.

## Immediate action for previously exposed secrets

If credentials were ever committed:

1. Rotate/revoke exposed keys immediately.
2. Update downstream systems using those keys.
3. Review access logs for suspicious usage.

## API access control

- Protected routes require a bearer token.
- Tokens are mapped to roles via `API_TOKENS`.
- Use least privilege:
  - `reader` for read-only operations
  - `admin` for write operations

## Reporting vulnerabilities

Please report security vulnerabilities privately to maintainers before public disclosure.
