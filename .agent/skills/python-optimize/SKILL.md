---
name: python-optimize
description: Performance profiling, memory management, and algorithmic optimization.
---

# Python Optimization Skill
This skill provides a toolkit for diagnosing and resolving performance bottlenecks in Python applications.

## Instructions
- Use `cProfile` and `memory-profiler` patterns to identify bottlenecks before optimizing.
- Apply algorithmic improvements: choose the right data structures (e.g., `set` for membership tests, `deque` for queues).
- Use NumPy vectorization for data-heavy operations where applicable.
- Implement caching strategies (e.g., `functools.lru_cache`, `functools.cache`) to avoid redundant calculations.
- Address memory leaks by analyzing object lifecycles and using `weakref` if necessary.
- Prioritize correctness and readability; only optimize after measuring a significant impact.
