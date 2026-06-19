# Secrets and admin authentication

## Never commit

- `.env` with real keys
- Filled `deploy/k8s/secret.yaml` (use `secret.yaml.example` as template only)

## Admin API key

`ADMIN_API_KEY` required for audit log, debug metrics, and kill switch routes.

Send as header:

```
x-api-key: <ADMIN_API_KEY>
```

Returns 503 if key not configured; 401 if mismatch.

## Drips and signal keys

Store `DRIPS_API_KEY`, `SENTIMENT_API_KEY`, and `MARKET_DATA_API_KEY` in secret manager in production.

## Kubernetes

Create secrets out-of-band:

```bash
kubectl create secret generic swap-agrregrator-secrets --from-env-file=.env.production
```

Reference in deployments per `deploy/k8s/deployment-admin-api.yaml`.

## Mock mode

Keep `USE_MOCK_DRIPS_CLIENT=true` and `USE_MOCK_SIGNAL_PROVIDER=true` until sandbox contracts are verified.
