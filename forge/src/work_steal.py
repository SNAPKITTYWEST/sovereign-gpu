# Copyright © 2026 SnapKitty Collective and contributors.
#
# This file is part of a work licensed under the
# SnapKitty Strong Network Copyleft License Version 1.0 (SSNCL-1.0).
#
# You may use, study, modify, copy, and redistribute this work
# only under the terms of SSNCL-1.0.
#
# A copy of SSNCL-1.0 must accompany this work.

"""
Deterministic work-stealing thread pool.

Each worker holds a local deque of tasks. When its deque is empty,
it steals from the victim with the lowest index (round-robin).
No random/secrets calls — only the ANU QRNG (already logged) supplies
nondeterminism, and that nondeterminism is captured in the audit log.
"""
from __future__ import annotations
import threading
import collections
import json
import time
from typing import Callable, List, Any, Tuple

TaskFn = Callable[[Any], Tuple[Any, Any]]  # returns (result, audit_data)


class Worker(threading.Thread):
    def __init__(
        self,
        wid: int,
        task_queues: List[collections.deque],
        result_lock: threading.Lock,
        results: List[Any],
        result_idx: List[int],
        audit_lock: threading.Lock,
        audit_file: str,
        fn: TaskFn,
    ):
        super().__init__(daemon=True)
        self.wid = wid
        self.queues = task_queues
        self.result_lock = result_lock
        self.results = results
        self.result_idx = result_idx
        self.audit_lock = audit_lock
        self.audit_file = audit_file
        self.fn = fn
        self.local_queue: collections.deque = collections.deque()

    def run(self) -> None:
        while True:
            task = self._pop_local()
            if task is not None:
                self._execute_task(task)
                continue

            stolen = self._steal()
            if stolen is not None:
                self._execute_task(stolen)
                continue

            break

    def _pop_local(self):
        if self.local_queue:
            return self.local_queue.pop()
        return None

    def _steal(self):
        """
        Deterministic steal: scan workers in increasing order of index,
        skip self, take the front (FIFO) task from first non-empty victim.
        """
        n = len(self.queues)
        for offset in range(1, n):
            victim = (self.wid + offset) % n
            victim_q = self.queues[victim]
            if victim_q:
                return victim_q.popleft()
        return None

    def _execute_task(self, task):
        task_id, payload = task
        start = time.perf_counter()
        result, audit_data = self.fn(payload)
        elapsed = (time.perf_counter() - start) * 1e3

        with self.result_lock:
            self.results[task_id] = result
            self.result_idx.append(task_id)

        audit_obj = {
            "task_id": task_id,
            "worker": self.wid,
            "audit_data": audit_data,
            "elapsed_ms": round(elapsed, 3),
        }
        with self.audit_lock:
            with open(self.audit_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(audit_obj) + "\n")


def deterministic_work_steal(
    tasks: List[Any],
    fn: TaskFn,
    num_workers: int = 4,
    audit_path: str = "work_steal_audit.jsonl",
) -> List[Any]:
    """
    Execute `tasks` in parallel using a deterministic work-stealing pool.

    Each task is processed by fn(task) -> (result, audit_data).
    Returns a list of results in the *original* task order.
    """
    num_workers = min(num_workers, len(tasks))

    # Distribute tasks round-robin into per-worker deques
    queues: List[collections.deque] = [collections.deque() for _ in range(num_workers)]
    for i, t in enumerate(tasks):
        queues[i % num_workers].append((i, t))

    # Shared state
    results: List[Any] = [None] * len(tasks)
    result_idx: List[int] = []
    result_lock = threading.Lock()
    audit_lock = threading.Lock()

    # Clear audit file
    with open(audit_path, "w", encoding="utf-8") as f:
        pass

    workers = [
        Worker(wid, queues, result_lock, results, result_idx, audit_lock, audit_path, fn)
        for wid in range(num_workers)
    ]
    for w in workers:
        w.start()
    for w in workers:
        w.join()

    return results
