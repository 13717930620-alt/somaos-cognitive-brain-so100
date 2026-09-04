# SomaOS Cognitive Brain — Container Install & Run

This project is distributed as a **closed-source container**. Sources and
model weights are not published. Two ways to verify it runs:

---

## A. Pull the prebuilt image (community / reviewers)

```bash
docker pull ghcr.io/13717930620-alt/somaos-cognitive-brain:latest

# Demo mode — self-contained, no weights needed, prints the full
# task-priority scheduling and perceive-decide loops to stdout:
docker run --rm ghcr.io/13717930620-alt/somaos-cognitive-brain:latest

# Service mode — starts the closed cognitive runtime (weights are fetched
# at startup from a maintainer-controlled source, see "Weights" below):
docker run --rm \
  -e SOMAOS_WEIGHT_URL="https://<maintainer-controlled>/cognitive-weights.zip" \
  -e SOMAOS_WEIGHT_SHA256="<sha256>" \
  -p 8765:8765 \
  ghcr.io/13717930620-alt/somaos-cognitive-brain:latest --mode service

curl http://localhost:8765/health
# {"service": "somaos-cognitive", "core_loaded": true, "mode": "closed-core"}
```

## B. Build locally (maintainer)

The image is built on a machine that holds the private sources. `./src`
(never committed here) must exist next to this repository checkout:

```bash
# layout expected at build time:
#   somaos-cognitive-brain/   <- this repository (public files)
#   src/core/*.py             <- private cognitive core (NOT published)

docker build -t ghcr.io/13717930620-alt/somaos-cognitive-brain:latest .
docker push ghcr.io/13717930620-alt/somaos-cognitive-brain:latest
```

Build guarantees:

- The builder stage compiles `src/core/*.py` to binary extensions (`.so`).
- The runtime stage receives only the compiled artifacts — no core source
  file survives into the image.
- Model weights are never baked into the image; they are fetched at
  startup from a maintainer-controlled URL (see below).

## Weights

Weights are intentionally not part of the repository or the image. The
container fetches them at startup:

- `SOMAOS_WEIGHT_URL` — direct HTTPS download of the weights archive (zip)
- `SOMAOS_WEIGHT_SHA256` — expected digest, verified before extraction
- `SOMAOS_WEIGHTS_DIR` — target directory inside the container
  (default `/var/lib/somaos/weights`)

If the source is not configured, the entrypoint falls back to demo mode
instead of failing.

## Demo mode

The default `CMD` runs the included demo loop (also available in this
repository under `demos/`): a deterministic multi-brain-region task
priority scheduling run followed by a perceive → decide → command loop
with a scripted instability reflex. These demos exercise the real
framework logic (scheduling, state machine, reflex override) with a
simulated backend; the production core itself is closed.
