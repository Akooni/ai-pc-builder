from __future__ import annotations

import heapq
from itertools import count
import time
from typing import Dict, Optional, Tuple

try:
    from ..constraints import expand_state, initial_state, is_goal_state, performance_score, score_state
except ImportError:
    from constraints import expand_state, initial_state, is_goal_state, performance_score, score_state


def build_with_ucs(components: Dict, budget: float, purpose: str) -> Tuple[Optional[Dict], Dict]:
    """
    Uniform Cost Search:
    - primary cost: total build price (lower is better)
    - tie-breaker: higher purpose score
    """
    start = initial_state()
    pq = []
    order = count()
    heapq.heappush(pq, (0.0, 0.0, next(order), start))
    best_goal = None
    best_rank = float("-inf")
    max_nodes = 60000
    timeout_seconds = 5.0
    explored = 0
    started_at = time.time()

    while pq:
        if explored >= max_nodes or (time.time() - started_at) > timeout_seconds:
            return best_goal, {"explored_nodes": explored, "elapsed_ms": int((time.time() - started_at) * 1000)}
        cost, neg_score, _, state = heapq.heappop(pq)
        explored += 1

        if is_goal_state(state, budget, purpose):
            current_rank = performance_score(purpose, state, budget)
            if current_rank > best_rank:
                best_goal = state
                best_rank = current_rank
            continue

        for child in expand_state(state, components, budget, purpose):
            child_cost = float(child.get("total_price", 0))
            child_score = score_state(purpose, child)
            heapq.heappush(pq, (child_cost, -child_score, next(order), child))

    return best_goal, {"explored_nodes": explored, "elapsed_ms": int((time.time() - started_at) * 1000)}
