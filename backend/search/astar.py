from __future__ import annotations

import heapq
from itertools import count
import time
from typing import Dict, Optional, Tuple

try:
    from ..constraints import (
        estimate_remaining_min_cost,
        expand_state,
        initial_state,
        is_goal_state,
        performance_score,
    )
except ImportError:
    from constraints import (
        estimate_remaining_min_cost,
        expand_state,
        initial_state,
        is_goal_state,
        performance_score,
    )


def build_with_astar(components: Dict, budget: float, purpose: str) -> Tuple[Optional[Dict], Dict]:
    """
    A* search:
    f(n) = g(n) + h(n)
    g(n): current total_price
    h(n): estimated minimum cost to complete remaining required components
    """
    start = initial_state()
    order = count()
    pq = []
    start_h = estimate_remaining_min_cost(start, components, purpose)
    heapq.heappush(pq, (start_h, 0.0, next(order), start))

    best_goal = None
    best_rank = float("-inf")
    max_nodes = 70000
    timeout_seconds = 5.0
    explored = 0
    started_at = time.time()

    while pq:
        if explored >= max_nodes or (time.time() - started_at) > timeout_seconds:
            return best_goal, {"explored_nodes": explored, "elapsed_ms": int((time.time() - started_at) * 1000)}

        _, g_cost, _, state = heapq.heappop(pq)
        explored += 1

        if is_goal_state(state, budget, purpose):
            current_rank = performance_score(purpose, state, budget)
            if current_rank > best_rank:
                best_goal = state
                best_rank = current_rank
            continue

        for child in expand_state(state, components, budget, purpose):
            child_g = float(child.get("total_price", 0))
            child_h = estimate_remaining_min_cost(child, components, purpose)
            child_f = child_g + child_h
            heapq.heappush(pq, (child_f, child_g, next(order), child))

    return best_goal, {"explored_nodes": explored, "elapsed_ms": int((time.time() - started_at) * 1000)}
