# Optional Hearth Compose Service

Modeler can run as an optional local Docker Compose service for SmartHome/Hearth. This service shape is intentionally local-first, advisory-only, and safe to leave disabled when Hearth is not using Modeler.

The compose-ready file is `docker-compose.hearth.yml`. It is separate from the main MVP stack so Hearth can opt in without borrowing Modeler's default portal, host ports, or project network.

## Service Shape

| Setting | Default | Notes |
| --- | --- | --- |
| Compose file | `docker-compose.hearth.yml` | Optional Hearth-specific stack. |
| Compose profile | `hearth` | Omitting the profile keeps the service disabled. |
| API service | `modeler-hearth-api` | Runs the existing FastAPI app from `apps/api`. |
| Image | `${MODELER_HEARTH_IMAGE:-python:3.12-slim}` | Matches the current lightweight local development posture. |
| Build context | `.` | The service installs `apps/api` from the repository checkout at startup. |
| Local API port | `${MODELER_HEARTH_HOST_PORT:-18100}` | Published on loopback only by default. |
| Internal container port | `8000` | Uvicorn listens on `0.0.0.0:8000` inside the container. |
| Healthcheck endpoint | `/integration/hearth/status` | Hearth-facing status endpoint from the integration contract. |
| Network | `modeler_hearth_local` | Compose-owned local network, marked `internal`. |
| Artifacts volume | `modeler_hearth_artifacts` | Mounted at `/workspace/data/runtime/hearth/artifacts`. |
| State volume | `modeler_hearth_state` | Mounted at `/workspace/data/runtime/hearth/state`. |

The service does not require public cloud credentials by default. `MODEL_BASE_URL` and `MODEL_NAME` are optional and default to empty so a missing local model configuration can be represented by Modeler/Hearth as disabled or degraded rather than as a fatal compose error.

## Environment Variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `MODELER_HEARTH_IMAGE` | `python:3.12-slim` | Override the API runtime image if Hearth builds or pins one later. |
| `MODELER_HEARTH_BIND_HOST` | `127.0.0.1` | Keeps the API local to the host by default. |
| `MODELER_HEARTH_HOST_PORT` | `18100` | Host port Hearth should call. |
| `MODELER_CONTRACT_VERSION` | `2026-09-12.hearth.v1` | Expected Hearth integration contract. |
| `MODELER_HEARTH_ENABLED` | `true` | Compose-level signal that this optional service is enabled. |
| `MODELER_HEARTH_OPTIONAL` | `true` | Documents that Hearth must treat Modeler as optional. |
| `MODELER_HEARTH_MISSING_CONFIG_STATUS` | `degraded` | Preferred status when optional configuration is absent. |
| `MODEL_BASE_URL` | empty | Optional local OpenAI-compatible model endpoint. |
| `MODEL_NAME` | empty | Optional model name for the local endpoint. |
| `CLOUD_ADAPTERS_ENABLED` | `false` | Keeps the no-secret, local-first default posture explicit. |

The dependency URLs are wired inside Docker by service name: `modeler-hearth-chroma`, `modeler-hearth-fuseki`, `modeler-hearth-postgres`, `modeler-hearth-redis`, and `modeler-hearth-searxng`. Hearth should depend on the published Modeler API URL, not on these internals.

## Enable

From the Modeler repository root:

```bash
docker compose -f docker-compose.hearth.yml --profile hearth up --build -d
```

To use a different local port without changing the file:

```bash
MODELER_HEARTH_HOST_PORT=18108 docker compose -f docker-compose.hearth.yml --profile hearth up --build -d
```

Hearth should treat `http://localhost:18100` as the default local Modeler endpoint unless the operator overrides `MODELER_HEARTH_HOST_PORT`.

## Verify

Check that the service is running and that the Hearth status endpoint answers:

```bash
docker compose -f docker-compose.hearth.yml --profile hearth ps
curl http://localhost:18100/integration/hearth/status
```

A healthy or degraded status is acceptable for optional Hearth integration. Degraded means Modeler can answer with explicit missing information or optional dependency state; it should not block unrelated Hearth startup.

For contract compatibility checks, Hearth can also call:

```bash
curl http://localhost:18100/integration/hearth/contract
```

## Disable

Stop the optional Hearth service without removing persisted local state:

```bash
docker compose -f docker-compose.hearth.yml --profile hearth down
```

Disable from Hearth by omitting the `hearth` profile or by leaving Modeler's service fragment out of Hearth's compose invocation. Hearth should represent that as `disabled`, not as a startup failure.

## Roll Back

If the optional service causes local integration trouble, stop it and remove only the Hearth-specific volumes:

```bash
docker compose -f docker-compose.hearth.yml --profile hearth down
```

```bash
docker volume rm modeler-hearth_modeler_hearth_artifacts modeler-hearth_modeler_hearth_state modeler-hearth_modeler_hearth_chroma_data modeler-hearth_modeler_hearth_fuseki_data modeler-hearth_modeler_hearth_postgres_data
```

Rollback does not touch Hearth volumes or the default `modeler-mvp` compose project.

## Integration Notes

- The default bind host is loopback-only. Do not publish Modeler on a LAN or public interface unless a later, explicit trust-boundary design says to do so.
- The compose network is local to this optional stack. Hearth should communicate through the API port and should not couple to Modeler's Chroma, Fuseki, Postgres, Redis, or SearXNG containers.
- No secrets are required in the default file. The local development database and Fuseki passwords are non-production container defaults and should not be reused as real credentials.
- Missing local model configuration should surface through `/integration/hearth/status` as missing information, disabled, or degraded behavior rather than crashing Hearth.
- This file does not change visualization output formats, artifact render safety, or #6-owned tests.
