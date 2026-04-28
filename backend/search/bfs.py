from __future__ import annotations

from collections import deque
import time
from typing import Dict, Optional, Tuple

try:
    from ..constraints import expand_state, initial_state, is_goal_state, performance_score
except ImportError:
    from constraints import expand_state, initial_state, is_goal_state, performance_score


def build_with_bfs(components: Dict, budget: float, purpose: str) -> Tuple[Optional[Dict], Dict]:
    """Breadth-first search over partial PC builds."""
    start = initial_state()
    queue = deque([start])
    best_goal = None
    best_rank = float("-inf")
    max_nodes = 50000
    timeout_seconds = 4.0
    explored = 0
    started_at = time.time()

    while queue:
        if explored >= max_nodes or (time.time() - started_at) > timeout_seconds:
            return best_goal, {"explored_nodes": explored, "elapsed_ms": int((time.time() - started_at) * 1000)}
        state = queue.popleft()
        explored += 1

        if is_goal_state(state, budget, purpose):
            current_rank = performance_score(purpose, state, budget)
            if current_rank > best_rank:
                best_goal = state
                best_rank = current_rank
            continue

        for child in expand_state(state, components, budget, purpose):
            queue.append(child)

    return best_goal, {"explored_nodes": explored, "elapsed_ms": int((time.time() - started_at) * 1000)}
