#!/usr/bin/env python3
"""
SomaOS Cognitive Brain - demo_task_priority
============================================
Runnable demonstration of the multi-brain-region task priority scheduler
of the SomaOS Cognitive Brain (bipedal humanoid target).

What is REAL in this demo:
  - The scheduling framework: priority queue, deadline/aging urgency model,
    region-capacity allocation, preemption logic, run statistics.
    These are standard, publicly known engineering patterns.

What is SIMPLIFIED (closed in production):
  - The scoring heuristic below is a stand-in for the production scorer,
    which ships as a closed binary and is NOT included in this repository.

Usage:
    python demo_task_priority.py [--seed 7] [--ticks 24]

Zero third-party dependencies. Runs on Python 3.8+.
"""

import argparse
import random
from dataclasses import dataclass, field
from enum import IntEnum

# ---------------------------------------------------------------- constants

REGION_CAPACITY = {
    "PERCEPTION": 2,
    "PLANNING": 2,
    "MOTOR": 2,
    "MEMORY": 1,
}

class Prio(IntEnum):
    SAFETY = 0      # reflex / safety-class tasks always win
    TASK = 1        # goal-directed work
    BACKGROUND = 2  # housekeeping, consolidation

CLASS_WEIGHT = {Prio.SAFETY: 10.0, Prio.TASK: 3.0, Prio.BACKGROUND: 1.0}

PREEMPT_MARGIN = 0.75  # new task must beat running task by this much

# ---------------------------------------------------------------- data model

@dataclass
class Task:
    tid: int
    name: str
    region: str
    prio: Prio
    arrival: int
    deadline: int          # absolute tick by which it should finish
    cost: int              # ticks of work required
    progress: int = 0
    preemptions: int = 0

    def remaining(self) -> int:
        return self.cost - self.progress

# Simplified heuristic stand-in for the production scorer (closed binary).
def score(task: Task, now: int) -> float:
    urgency = 1.0 - task.remaining() / max(task.deadline - task.arrival, 1)
    aging = 0.05 * (now - task.arrival)
    return CLASS_WEIGHT[task.prio] + 2.0 * urgency + aging

TASK_TEMPLATES = [
    ("visual_odometry",        "PERCEPTION", Prio.TASK),
    ("gait_planning",          "PLANNING",   Prio.TASK),
    ("reach_trajectory",       "PLANNING",   Prio.TASK),
    ("joint_command_stream",   "MOTOR",      Prio.TASK),
    ("balance_reflex",         "MOTOR",      Prio.SAFETY),
    ("obstacle_scan",          "PERCEPTION", Prio.TASK),
    ("scene_memory_write",     "MEMORY",     Prio.BACKGROUND),
    ("slip_detection",         "PERCEPTION", Prio.SAFETY),
    ("goal_replan",            "PLANNING",   Prio.TASK),
    ("log_flush",              "MEMORY",     Prio.BACKGROUND),
]

# ---------------------------------------------------------------- scheduler

class RegionScheduler:
    def __init__(self) -> None:
        self.ready: list[Task] = []
        self.running: dict[str, Task | None] = {r: None for r in REGION_CAPACITY}
        self.finished: list[Task] = []
        self.events: list[str] = []

    def submit(self, task: Task) -> None:
        self.ready.append(task)
        self.events.append(f"t{task.arrival:02d}  SUBMIT   {task.name} -> {task.region} ({task.prio.name})")

    def _pick(self, region: str, now: int) -> Task | None:
        pool = [t for t in self.ready if t.region == region and t.arrival <= now]
        if not pool:
            return None
        best = max(pool, key=lambda t: (score(t, now), -t.tid))
        self.ready.remove(best)
        return best

    def tick(self, now: int) -> None:
        # 1) try to fill idle slots
        for region, cap in REGION_CAPACITY.items():
            # single running-slot model per region keeps the demo readable
            cur = self.running[region]
            if cur is None:
                cand = self._pick(region, now)
                if cand:
                    self.running[region] = cand
                    self.events.append(f"t{now:02d}  START    {cand.name} on {region}")
            else:
                # 2) preemption check inside the same region
                cand = self._pick(region, now)
                if cand and score(cand, now) > score(cur, now) + PREEMPT_MARGIN:
                    self.ready.append(cur)
                    cand.preemptions += 1
                    self.events.append(
                        f"t{now:02d}  PREEMPT  {cur.name} <-> {cand.name} on {region}")
                    self.running[region] = cand
                elif cand:
                    self.ready.append(cand)

        # 3) advance work
        for region, task in self.running.items():
            if task is not None:
                task.progress += 1
                if task.progress >= task.cost:
                    self.finished.append(task)
                    self.events.append(f"t{now:02d}  DONE     {task.name} ({task.region})")
                    self.running[region] = None

    def missed_deadlines(self, now: int) -> list[str]:
        done_names = {t.name for t in self.finished}
        return [t.name for t in (self.ready + [r for r in self.running.values() if r])
                if now >= t.deadline and t.name not in done_names]

# ---------------------------------------------------------------- main

def main() -> None:
    ap = argparse.ArgumentParser(description="SomaOS task-priority scheduling demo")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--ticks", type=int, default=40)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    sched = RegionScheduler()

    # deterministic workload derived from the seed (staggered arrivals so
    # preemption pressure occurs while earlier tasks are still running)
    t0 = 0
    for i, (name, region, prio) in enumerate(TASK_TEMPLATES):
        cost = rng.randint(3, 8)
        deadline = t0 + cost + rng.randint(4, 14)
        sched.submit(Task(tid=i, name=name, region=region, prio=prio,
                          arrival=t0, deadline=deadline, cost=cost))
        t0 += rng.randint(2, 5)

    print("=" * 74)
    print("SomaOS Cognitive Brain -- multi-brain-region task priority demo")
    print(f"seed={args.seed}  ticks={args.ticks}  "
          f"region capacity={ {r: c for r, c in REGION_CAPACITY.items()} }")
    print("NOTE: scorer = simplified heuristic stand-in (production core is closed)")
    print("=" * 74)

    for now in range(args.ticks):
        sched.tick(now)
    for line in sched.events:
        print(line)

    print("-" * 74)
    done = sched.finished
    late = [t for t in done if t.progress > t.deadline - t.arrival]
    preempt_total = sum(t.preemptions for t in done)
    print(f"summary: finished={len(done)}/{len(TASK_TEMPLATES)}  "
          f"preemptions={preempt_total}  missed_deadlines={len(sched.missed_deadlines(args.ticks))}")
    print(f"         safety-class tasks all completed: "
          f"{all(t.progress >= t.cost for t in done if t.prio == Prio.SAFETY)}")
    if done:
        _avg_cost = sum(t.cost for t in done) / len(done)
        print(f"         avg task cost: {_avg_cost:.1f} ticks")
    print("exit: OK")

if __name__ == "__main__":
    main()
