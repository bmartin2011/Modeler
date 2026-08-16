# Local Docker Isolated MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Modeler start as an isolated local Docker-hosted MVP without colliding with other Docker projects, while preserving the README vision for ArchiMate visual navigation, local-first processing, and future MCP agent access.

**Architecture:** Docker Compose owns the product runtime. Services communicate on a dedicated `modeler_internal` network using Docker service names, while only human/agent entrypoints are published on namespaced host ports. The React portal uses Vite's dev server inside Docker for the MVP and proxies `/api` to the API service instead of assuming host `localhost:8000`.

**Tech Stack:** Docker Compose, FastAPI, Python 3.12, React 18, Vite 5, Vitest, ChromaDB, Apache Jena Fuseki, Postgres 16, Redis 7, SearXNG, future local OpenAI-compatible model endpoint, future MCP server.

**Spec:** `docs/superpowers/specs/2026-08-16-local-docker-isolated-mvp-design.md`

## Global Constraints

- Docker is the default host for the MVP. Opening `apps/portal/index.html` directly is not a supported product path.
- Internal traffic stays internal. Services communicate over a dedicated Docker network by service name.
- Host exposure is explicit and minimal. Only human-facing or agent-facing endpoints are published to the host.
- Host ports are namespaced away from common defaults to reduce collisions with other Docker projects.
- Local model use is explicit. LLM-backed interpretation should use Docker Desktop-provided local models or another local OpenAI-compatible endpoint by default.
- Cloud use remains opt-in. Any cloud model, hosted search, managed vector store, or external database must disclose cost, data boundary, retention policy, and reason before use.
- MCP is a product interface, not an afterthought. The MVP API should keep boundaries compatible with a future local MCP server.
- Evidence before claims applies to runtime too. The README should tell users how to verify that Docker is hosting the portal, API, and supporting services.
- Default host ports: portal `18173`, API `18100`, future MCP `18190`. Store ports are internal by default and exposed only through debug profiles or explicit overrides.

---

## File Structure

- Modify `docker-compose.yml`: define project-isolated service names, `modeler_internal` network, named volumes, namespaced host ports, local model/cloud environment variables, internal-only store access, and API health dependencies where useful.
- Modify `apps/portal/vite.config.ts`: use an environment-controlled API proxy target with a Docker-safe default of `http://api:8000`.
- Modify `apps/portal/src/api/client.ts`: add response checking so blank/error screens become visible failures instead of silent bad JSON.
- Modify `apps/portal/tests/question-panel.test.tsx`: keep interaction proof passing after client tightening.
- Create `apps/portal/tests/api-client.test.ts`: verify `/api` path use and error handling in the browser client.
- Modify `README.md`: make Docker-hosted startup the product path, document namespaced ports, explain private network/resource isolation, and include verification commands.
- Create `docs/superpowers/plans/2026-08-16-local-docker-isolated-mvp.md`: this plan.

---

### Task 1: Isolate Docker Compose Runtime

**Files:**
- Modify: `docker-compose.yml`

**Interfaces:**
- Consumes: Existing services `api`, `portal`, `fuseki`, `chroma`, `postgres`, `redis`, `searxng`.
- Produces: Docker services on `modeler_internal`, host portal at `http://localhost:18173`, host API at `http://localhost:18100`, internal API URL `http://api:8000`.

- [ ] **Step 1: Verify current Compose failure context**

Run:

```powershell
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Ports}}"
docker compose ps
```

Expected: unrelated project containers may own common ports such as `8000`. Existing `modeler-*` containers may be partially created from the failed attempt.

- [ ] **Step 2: Stop only Modeler Compose containers**

Run:

```powershell
docker compose down --remove-orphans
```

Expected: containers in the current Modeler Compose project stop. Unrelated containers such as `hearth-*` remain running.

- [ ] **Step 3: Rewrite `docker-compose.yml`**

Replace the file with:

```yaml
name: modeler-mvp

services:
  api:
    image: python:3.12-slim
    working_dir: /workspace/apps/api
    volumes:
      - .:/workspace
    command: sh -c "pip install -e .[dev] && uvicorn modeler_api.main:app --host 0.0.0.0 --port 8000 --reload"
    environment:
      API_PUBLIC_BASE_URL: http://localhost:18100
      CHROMA_URL: http://chroma:8000
      FUSEKI_URL: http://fuseki:3030
      SEARXNG_URL: http://searxng:8080
      POSTGRES_URL: postgresql://modeler:modeler@postgres:5432/modeler
      REDIS_URL: redis://redis:6379/0
      MODEL_BASE_URL: ${MODEL_BASE_URL:-}
      MODEL_NAME: ${MODEL_NAME:-}
      CLOUD_ADAPTERS_ENABLED: "false"
    ports:
      - "18100:8000"
    networks:
      - modeler_internal
    depends_on:
      - chroma
      - fuseki
      - postgres
      - redis
      - searxng

  portal:
    image: node:22-slim
    working_dir: /workspace/apps/portal
    volumes:
      - .:/workspace
    command: sh -c "corepack enable && pnpm install && pnpm run dev --host 0.0.0.0"
    environment:
      VITE_API_PROXY_TARGET: http://api:8000
      VITE_API_PUBLIC_BASE_URL: http://localhost:18100
    ports:
      - "18173:5173"
    networks:
      - modeler_internal
    depends_on:
      - api

  fuseki:
    image: stain/jena-fuseki:latest
    environment:
      ADMIN_PASSWORD: modeler
    volumes:
      - modeler_fuseki_data:/fuseki
    networks:
      - modeler_internal

  chroma:
    image: chromadb/chroma:latest
    volumes:
      - modeler_chroma_data:/chroma/chroma
    networks:
      - modeler_internal

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: modeler
      POSTGRES_PASSWORD: modeler
      POSTGRES_DB: modeler
    volumes:
      - modeler_postgres_data:/var/lib/postgresql/data
    networks:
      - modeler_internal

  redis:
    image: redis:7-alpine
    networks:
      - modeler_internal

  searxng:
    image: searxng/searxng:latest
    volumes:
      - ./docker/searxng:/etc/searxng
    networks:
      - modeler_internal

networks:
  modeler_internal:
    name: modeler_internal

volumes:
  modeler_chroma_data:
  modeler_fuseki_data:
  modeler_postgres_data:
```

- [ ] **Step 4: Check Compose syntax**

Run:

```powershell
docker compose config
```

Expected: exit code 0. The rendered config includes `name: modeler-mvp`, `modeler_internal`, `18100:8000`, and `18173:5173`.

- [ ] **Step 5: Commit**

```powershell
git add docker-compose.yml
git commit -m "fix: isolate modeler compose runtime"
```

---

### Task 2: Make Portal Proxy Docker-Safe

**Files:**
- Modify: `apps/portal/vite.config.ts`
- Create: `apps/portal/tests/api-client.test.ts`
- Modify: `apps/portal/src/api/client.ts`

**Interfaces:**
- Consumes: Environment variable `VITE_API_PROXY_TARGET`.
- Produces: Vite dev proxy to `http://api:8000` inside Docker and testable `getMilkyWay(lens)` error handling.

- [ ] **Step 1: Write the failing API client tests**

Create `apps/portal/tests/api-client.test.ts`:

```typescript
import { afterEach, describe, expect, it, vi } from "vitest";
import { getMilkyWay } from "../src/api/client";

describe("portal API client", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("requests Milky Way views through the portal API proxy", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({ lens: "value_stream", sectors: [] })
    } as Response);

    await getMilkyWay("value_stream");

    expect(fetch).toHaveBeenCalledWith("/api/views/milky-way?lens=value_stream");
  });

  it("raises a useful error when the API returns a non-OK response", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: false,
      status: 502,
      statusText: "Bad Gateway"
    } as Response);

    await expect(getMilkyWay("organization")).rejects.toThrow(
      "Modeler API request failed: 502 Bad Gateway"
    );
  });
});
```

- [ ] **Step 2: Run the new test to verify it fails**

Run:

```powershell
cd apps/portal
$env:CI='true'
pnpm test tests/api-client.test.ts
```

Expected: first test passes, second test fails because `getMilkyWay` does not check `response.ok`.

- [ ] **Step 3: Update `apps/portal/src/api/client.ts`**

Replace the file with:

```typescript
export async function getMilkyWay(lens: "value_stream" | "organization") {
  const response = await fetch(`/api/views/milky-way?lens=${lens}`);

  if (!response.ok) {
    throw new Error(`Modeler API request failed: ${response.status} ${response.statusText}`);
  }

  return response.json();
}
```

- [ ] **Step 4: Update `apps/portal/vite.config.ts`**

Replace the proxy target block with:

```typescript
const apiProxyTarget = process.env.VITE_API_PROXY_TARGET ?? "http://api:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: apiProxyTarget,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, "")
      }
    }
  },
  test: {
    environment: "jsdom"
  }
});
```

Keep the existing imports at the top of the file.

- [ ] **Step 5: Run portal tests**

Run:

```powershell
cd apps/portal
$env:CI='true'
pnpm test
```

Expected: all portal tests pass, including the new API client tests.

- [ ] **Step 6: Run portal build**

Run:

```powershell
cd apps/portal
$env:CI='true'
pnpm run build
```

Expected: TypeScript and Vite build pass.

- [ ] **Step 7: Commit**

```powershell
git add apps/portal/src/api/client.ts apps/portal/vite.config.ts apps/portal/tests/api-client.test.ts
git commit -m "fix: route portal api through docker service"
```

---

### Task 3: Update README Runtime Instructions

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: Host port policy from `docs/superpowers/specs/2026-08-16-local-docker-isolated-mvp-design.md`.
- Produces: README instructions that make Docker hosting, isolated network/resource ownership, local model defaults, and verification commands explicit.

- [ ] **Step 1: Add an isolated Docker runtime section**

In `README.md`, after the "Local-First Operating Model" section and before "MVP Verification", add this section:

````markdown
## Isolated Docker Runtime

Modeler should run as its own local Docker application stack. It should not borrow another project's Chroma, SearXNG, Redis, Postgres, network, or host ports unless a human explicitly connects those resources.

The Compose stack uses:

```text
Compose project: modeler-mvp
Network:         modeler_internal
Portal:          http://localhost:18173
API:             http://localhost:18100
```

Inside Docker, services communicate by service name on the private `modeler_internal` network. For example, the portal proxies API calls to `http://api:8000`, and the API reaches Chroma at `http://chroma:8000`.

The source file `apps/portal/index.html` is not the product entrypoint. Start Docker and open `http://localhost:18173`.
````

- [ ] **Step 2: Replace MVP Docker verification commands**

Ensure the "MVP Verification" section contains these Docker commands:

````markdown
```bash
docker compose up --build
```

In another terminal:

```bash
docker compose ps
curl http://localhost:18100/health
curl "http://localhost:18100/views/milky-way?lens=value_stream"
curl -X POST http://localhost:18100/questions \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"Who reports to John?\"}"
```

Open the portal:

```text
http://localhost:18173
```
````

- [ ] **Step 3: Scan README for obsolete ports**

Run:

```powershell
rg -n "localhost:8000|:5173|file://|apps/portal/index.html" README.md
```

Expected: `localhost:8000` does not appear. `apps/portal/index.html` appears only as a warning that it is not the product entrypoint. `:5173` does not appear as the user-facing portal URL.

- [ ] **Step 4: Commit**

```powershell
git add README.md
git commit -m "docs: document isolated docker startup"
```

---

### Task 4: Verify Docker-Hosted MVP End To End

**Files:**
- Modify only if a verification failure identifies a specific source defect.

**Interfaces:**
- Consumes: Compose stack from Task 1, portal proxy from Task 2, README commands from Task 3.
- Produces: Fresh evidence that Docker hosts the product at `http://localhost:18173` and API at `http://localhost:18100`.

- [ ] **Step 1: Start from a clean Modeler stack**

Run:

```powershell
docker compose down --remove-orphans
docker compose up -d --build
```

Expected: exit code 0. Unrelated Docker containers remain running.

- [ ] **Step 2: Check services**

Run:

```powershell
docker compose ps
```

Expected: `modeler-mvp-api-1`, `modeler-mvp-portal-1`, `modeler-mvp-chroma-1`, `modeler-mvp-fuseki-1`, `modeler-mvp-postgres-1`, `modeler-mvp-redis-1`, and `modeler-mvp-searxng-1` are running or healthy.

- [ ] **Step 3: Check API host route**

Run:

```powershell
curl.exe http://localhost:18100/health
curl.exe "http://localhost:18100/views/milky-way?lens=value_stream"
curl.exe -X POST http://localhost:18100/questions -H "Content-Type: application/json" -d "{\"question\":\"Who reports to John?\"}"
```

Expected: health returns `{"status":"ok"}`. Milky Way returns a projection with `value_stream` data. Question endpoint returns an answer containing verified reports for Maya and Luis and evidence entries.

- [ ] **Step 4: Verify rendered portal in browser**

Use the in-app browser or Playwright to open:

```text
http://localhost:18173
```

Required checks:

- Page title is `Modeler`.
- DOM contains `Modeler`, `Value Stream Lens`, `Organization Lens`, and `Who reports to John?`.
- The page is not blank.
- No Vite or React framework error overlay appears.
- Browser console has no relevant app errors.
- Switching to the organization lens updates the view.
- The Milky Way map renders sectors from API-backed seed data.

- [ ] **Step 5: Run automated tests after Docker verification**

Run:

```powershell
cd apps/api
python -m pytest -q
```

Run:

```powershell
cd apps/portal
$env:CI='true'
pnpm test
pnpm run build
```

Expected: backend tests pass, portal tests pass, portal build passes.

- [ ] **Step 6: Commit any verification fixes**

If source changes were required:

```powershell
git add <changed-files>
git commit -m "fix: complete docker hosted mvp verification"
```

If no source changes were required, do not create an empty commit.

---

### Task 5: Push Final Runtime Slice

**Files:**
- No source files unless Task 4 produced a fix.

**Interfaces:**
- Consumes: Commits from Tasks 1-4.
- Produces: Remote `main` containing the isolated Docker MVP runtime plan implementation.

- [ ] **Step 1: Check git status**

Run:

```powershell
git status --short -uall
```

Expected: no uncommitted source files. Ignored generated folders such as `apps/portal/node_modules`, `apps/portal/dist`, and `_sdd` are not listed.

- [ ] **Step 2: Review recent commits**

Run:

```powershell
git log --oneline -n 8
```

Expected: recent commits include:

```text
fix: isolate modeler compose runtime
fix: route portal api through docker service
docs: document isolated docker startup
```

- [ ] **Step 3: Push**

Run:

```powershell
git push origin main
```

Expected: push succeeds.

- [ ] **Step 4: Final report**

Report:

- Docker URL: `http://localhost:18173`
- API URL: `http://localhost:18100`
- Verification evidence from Task 4.
- Any remaining risks, especially Docker image pull time, Docker Desktop local model endpoint variability, and the fact that MCP is reserved but not implemented in this runtime slice.
