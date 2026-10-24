""" Slow image work done ahead of time: RotSprite rotations and generated effects

Jobs are queued while loading and done a little each frame on the main menu
(`work`), or all at once when a round starts (`finish`). A job is a function, or a
generator: a generator is resumed until it ends, so a long job can be split into
small steps (each `yield` is a point where the work can stop until the next frame).
"""
import time
from collections import deque

_jobs = deque()


def add(job) -> None:
    """ Queue `job`: a function without arguments, or a generator """
    _jobs.append(job)


def _step() -> None:
    job = _jobs[0]
    if callable(job):
        _jobs.popleft()
        job()
        return
    try:
        next(job)
    except StopIteration:
        _jobs.popleft()


def work(budget_ms) -> None:
    """ Do queued work for at most about `budget_ms` milliseconds """
    end = time.perf_counter() + budget_ms / 1000
    while _jobs and time.perf_counter() < end:
        _step()


def finish() -> None:
    """ Do all the queued work now """
    while _jobs:
        _step()


def pending() -> int:
    return len(_jobs)
