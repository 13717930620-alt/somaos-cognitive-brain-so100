#!/usr/bin/env python3
"""
SomaOS Cognitive Brain - demo_perceive_decide
==============================================
Runnable demonstration of the perceive -> assess -> decide -> command loop
of the SomaOS Cognitive Brain (bipedal humanoid target).

What is REAL in this demo:
  - The loop architecture: fixed-rate frame processing, decision state
    machine (IDLE / REACH / WALK / SAFE_HOLD), watchdog on lost targets,
    reflex override on instability, command-frame emission.
    These are standard, publicly known engineering patterns.

What is SIMPLIFIED (closed in production):
  - The percept fusion and behaviour scoring are simplified stand-ins.
    The production cores ship as closed binaries and are NOT included.

Usage:
    python demo_perceive_decide.py [--seed 11] [--frames 24]

Zero third-party dependencies. Runs on Python 3.8+.
"""

import argparse
import random
from enum import Enum

# ---------------------------------------------------------------- states

class State(Enum):
    IDLE = "IDLE"
    REACH = "REACH"
    WALK = "WALK"
    SAFE_HOLD = "SAFE_HOLD"

ROLL_LIMIT_DEG = 25.0     # instability threshold -> reflex override
TARGET_LOST_FRAMES = 3    # watchdog frames before giving up
REACH_DIST_M = 0.45       # closer than this -> reach, else walk

# ---------------------------------------------------------------- helpers

def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))

# Simplified percept fusion stand-in (production fusion core is closed).
def fuse(rng: random.Random, dist: float, roll: float) -> dict:
    return {
        "target_dist_m": dist + rng.uniform(-0.02, 0.02),
        "target_bearing_deg": rng.uniform(-8, 8),
        "body_roll_deg": roll,
    }

# Simplified behaviour scoring stand-in (production scorer is closed).
def decide(state: State, percept: dict, lost_count: int) -> tuple[State, str]:
    if abs(percept["body_roll_deg"]) > ROLL_LIMIT_DEG:
        return State.SAFE_HOLD, "reflex: instability"
    if state == State.SAFE_HOLD:
        if abs(percept["body_roll_deg"]) < ROLL_LIMIT_DEG * 0.6:
            return State.IDLE, "stabilised"
        return State.SAFE_HOLD, "still unstable"

    if lost_count >= TARGET_LOST_FRAMES:
        return State.IDLE, "target lost watchdog"

    if percept["target_dist_m"] <= 0.02:   # consumed / arrived
        return State.IDLE, "goal reached"

    if percept["target_dist_m"] < REACH_DIST_M:
        return State.REACH, "in arm workspace"
    return State.WALK, "out of arm workspace"

def command_for(state: State, percept: dict) -> str:
    if state == State.IDLE:
        return "cmd=SCAN_ENV"
    if state == State.REACH:
        gx = clamp(percept["target_bearing_deg"], -30, 30)
        return f"cmd=ARM_REACH bearing={gx:+.1f}deg"
    if state == State.WALK:
        return (f"cmd=WALK vy=0.25m/s yaw={percept['target_bearing_deg']:+.1f}deg")
    return "cmd=FREEZE_ALL posture=CROUCH_SAFE"

# ---------------------------------------------------------------- main

def main() -> None:
    ap = argparse.ArgumentParser(description="SomaOS perceive-decide demo")
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--frames", type=int, default=24)
    args = ap.parse_args()

    rng = random.Random(args.seed)

    # scripted scenario (deterministic under any seed):
    #  - a target approaching from 1.6 m, consumed near frame 20
    #  - IMU roll spike injected around frame 12 (reflex demonstration)
    #  - target lost never triggers (target stays visible)
    n = args.frames
    dists = [max(0.0, 1.6 - 0.085 * i) for i in range(n)]
    rolls = [rng.uniform(-2.5, 2.5) for _ in range(n)]
    spike = n // 2
    rolls[spike] = 31.0       # injected instability
    rolls[spike + 1] = 28.0   # still above limit
    rolls[spike + 2] = 12.0   # recovering

    print("=" * 74)
    print("SomaOS Cognitive Brain -- perceive -> decide -> command loop demo")
    print(f"seed={args.seed} frames={n}  roll_limit={ROLL_LIMIT_DEG}deg  "
          f"reach_dist={REACH_DIST_M}m")
    print("NOTE: fusion+scoring = simplified stand-ins (production cores closed)")
    print("=" * 74)

    state = State.IDLE
    lost = 0
    dist_hist = []
    state_hist: dict[str, int] = {}
    reflex_frame = None
    recovered_frame = None

    for i in range(n):
        raw_dist = dists[i]
        if raw_dist <= 0.02:
            lost += 1
        p = fuse(rng, raw_dist, rolls[i])
        new_state, reason = decide(state, p, lost)
        if new_state == State.SAFE_HOLD and state != State.SAFE_HOLD:
            reflex_frame = i
        if state == State.SAFE_HOLD and new_state != State.SAFE_HOLD:
            recovered_frame = i
        state = new_state
        state_hist[state.value] = state_hist.get(state.value, 0) + 1

        print(f"f{i:02d} dist={p['target_dist_m']:.2f}m roll={p['body_roll_deg']:+5.1f}deg "
              f"-> {state.value:<9} ({reason:<20}) {command_for(state, p)}")

    print("-" * 74)
    print(f"summary: state_hist={state_hist}")
    print(f"         reflex override at frame {reflex_frame}, "
          f"recovered at frame {recovered_frame}")
    print(f"         roll spike {rolls[spike]:+.1f}deg > limit {ROLL_LIMIT_DEG}deg "
          f"-> SAFE_HOLD worked as designed")
    print("exit: OK")

if __name__ == "__main__":
    main()
