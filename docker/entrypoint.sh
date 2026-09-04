#!/usr/bin/env sh
# =============================================================================
# SomaOS Cognitive Brain — container entrypoint
#   --mode demo     run the self-contained demo loop (default, no weights)
#   --mode service  start the closed-source cognitive runtime (compiled core)
# =============================================================================
set -eu

MODE="demo"
for arg in "$@"; do
  case "$arg" in
    --mode) : ;;
    demo|service) MODE="$arg" ;;
  esac
done

echo "[somaos-cognitive] entrypoint: mode=${MODE}"

if [ "${MODE}" = "service" ]; then
  # Model weights are fetched at startup from a maintainer-controlled source.
  # If not configured, the runtime refuses to start the closed core and falls
  # back to the demo loop instead of failing.
  if [ -n "${SOMAOS_WEIGHT_URL:-}" ]; then
    echo "[somaos-cognitive] fetching model weights..."
    python /opt/somaos/weight_client.py \
      --url "${SOMAOS_WEIGHT_URL}" \
      --sha256 "${SOMAOS_WEIGHT_SHA256:-}" \
      --dest "${SOMAOS_WEIGHTS_DIR:-/var/lib/somaos/weights}" || {
        echo "[somaos-cognitive] weight fetch failed; falling back to demo mode"
        MODE="demo"
      }
  else
    echo "[somaos-cognitive] SOMAOS_WEIGHT_URL not configured; falling back to demo mode"
    MODE="demo"
  fi
fi

if [ "${MODE}" = "service" ]; then
  exec python /opt/somaos/service/cognitive_service.py --host 0.0.0.0 --port "${SOMAOS_PORT:-8765}"
fi

# ---- demo loop -------------------------------------------------------------
echo "============================================================"
echo " SomaOS Cognitive Brain — demo loop (simulated backend)"
echo "============================================================"
python /opt/somaos/demos/task_priority/demo_task_priority.py --seed 7 --ticks 40
echo
python /opt/somaos/demos/perceive_decide/demo_perceive_decide.py --seed 11 --frames 24
echo
echo "[somaos-cognitive] demo loop finished — exit OK"
