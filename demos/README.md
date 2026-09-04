# Runnable Demos

Two self-contained demo programs exercise the framework logic of the
SomaOS Cognitive Brain with a simulated backend. Both are pure Python
standard library (zero dependencies, Python 3.8+), fully deterministic
under a fixed seed, and print their complete run to stdout.

> **What is real vs simplified**
> Real: the scheduling framework (priority queue, deadline/aging urgency,
> preemption) and the loop architecture (fixed-rate frames, decision state
> machine, reflex override, watchdog). These are standard engineering
> patterns shown so the community can inspect and run them.
> Simplified: the scoring/fusion heuristics are stand-ins; the production
> cores ship as closed binaries inside the container and are not included
> in this repository.

## 1. Task priority scheduler (`task_priority/`)

Multi-brain-region task scheduling: staggered task arrivals with
safety/task/background classes, deadline+aging urgency, cross-task
preemption inside each region, and completion statistics.

```bash
python demos/task_priority/demo_task_priority.py --seed 7 --ticks 40
```

Example output (abridged, deterministic for seed=7):

```
t14  SUBMIT   balance_reflex -> MOTOR (SAFETY)
t14  PREEMPT  joint_command_stream <-> balance_reflex on MOTOR
summary: finished=10/10  preemptions=1  missed_deadlines=0
exit: OK
```

The safety-class reflex task preempts a running task-class job and the
scheduler still finishes all ten tasks with zero missed deadlines.

## 2. Perceive → decide loop (`perceive_decide/`)

Fixed-rate perception frames fuse into a decision state machine
(IDLE / REACH / WALK / SAFE_HOLD). A scripted IMU roll spike triggers the
reflex override; the loop shows detection and recovery.

```bash
python demos/perceive_decide/demo_perceive_decide.py --seed 11 --frames 24
```

Example output (abridged, deterministic for seed=11):

```
f12 dist=0.72m roll=+31.0deg -> SAFE_HOLD (reflex: instability) cmd=FREEZE_ALL posture=CROUCH_SAFE
f14 dist=0.55m roll=+12.0deg -> IDLE      (stabilised)            cmd=SCAN_ENV
summary: state_hist={'WALK': 12, 'SAFE_HOLD': 2, 'IDLE': 6, 'REACH': 4}
exit: OK
```

## Notes

- The same demos run inside the container in `--mode demo`
  (`docker/install.md`).
- These demos do not include the production cognitive core, model weights,
  or any private algorithms.
