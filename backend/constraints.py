from __future__ import annotations

from typing import Dict, List, Tuple


COMPONENT_ORDER = ["cpu", "motherboard", "ram", "storage", "gpu", "psu"]

KEY_TO_DATASET = {
    "cpu": "cpus",
    "motherboard": "motherboards",
    "ram": "rams",
    "storage": "storage",
    "gpu": "gpus",
    "psu": "psus",
}


def initial_state() -> Dict:
    return {
        "cpu": None,
        "motherboard": None,
        "ram": None,
        "storage": None,
        "gpu": None,
        "psu": None,
        "total_price": 0.0,
    }


def _price(item: Dict | None) -> float:
    return float((item or {}).get("price_usd", 0) or 0)


def _cpu_tdp(state: Dict) -> int:
    return int((state.get("cpu") or {}).get("tdp_watts", 0) or 0)


def _gpu_tdp(state: Dict) -> int:
    return int((state.get("gpu") or {}).get("tdp_watts", 0) or 0)


def required_wattage(state: Dict) -> int:
    return _cpu_tdp(state) + _gpu_tdp(state) + 20


def _as_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    return text in {"1", "true", "yes", "y"}


def next_component_key(state: Dict) -> str | None:
    for key in COMPONENT_ORDER:
        if state.get(key) is None:
            return key
    return None


def component_required(purpose: str, key: str) -> bool:
    if key != "gpu":
        return True
    return purpose in {"gaming", "ai/ml", "high-end"}


def purpose_component_allowed(purpose: str, key: str, item: Dict) -> bool:
    if key == "gpu":
        vram = int(item.get("vram_gb", 0) or 0)
        if purpose == "gaming":
            return vram >= 8
        if purpose == "ai/ml":
            return vram >= 12
        if purpose == "high-end":
            return vram >= 12
    if key == "cpu":
        cores = int(item.get("cores", 0) or 0)
        if purpose == "content creation":
            return cores >= 8
        if purpose == "high-end":
            return cores >= 12
    if key == "ram":
        cap = int(item.get("capacity_gb", 0) or 0)
        if purpose == "content creation":
            return cap >= 16
        if purpose == "high-end":
            return cap >= 32
    if key == "psu":
        watt = int(item.get("wattage", 0) or 0)
        if purpose == "ai/ml":
            return watt >= 650
        if purpose == "high-end":
            return watt >= 750
    return True


def compatibility_check(state: Dict) -> Tuple[bool, List[str]]:
    checks: List[str] = []

    cpu = state.get("cpu")
    mb = state.get("motherboard")
    ram = state.get("ram")
    storage = state.get("storage")
    psu = state.get("psu")

    if cpu and mb:
        ok = str(cpu.get("socket", "")).strip().lower() == str(mb.get("socket", "")).strip().lower()
        checks.append(f"CPU socket matches motherboard socket: {'PASS' if ok else 'FAIL'}")
        if not ok:
            return False, checks

    if ram and mb:
        ok = str(ram.get("type", "")).strip().lower() == str(mb.get("ram_type", "")).strip().lower()
        checks.append(f"RAM type matches motherboard RAM support: {'PASS' if ok else 'FAIL'}")
        if not ok:
            return False, checks

    if storage and mb:
        interface = str(storage.get("interface", "")).strip().lower()
        supports_nvme = _as_bool(mb.get("nvme_support", False))
        m2_slots = int(mb.get("m2_slots", 0) or 0)
        sata_ports = int(mb.get("sata_ports", 0) or 0)

        if "nvme" in interface or "m.2" in interface:
            ok = supports_nvme and m2_slots > 0
            checks.append(f"NVMe storage supported by motherboard: {'PASS' if ok else 'FAIL'}")
            if not ok:
                return False, checks
        elif "sata" in interface:
            ok = sata_ports > 0
            checks.append(f"SATA storage supported by motherboard: {'PASS' if ok else 'FAIL'}")
            if not ok:
                return False, checks

    if psu:
        need = required_wattage(state)
        have = int(psu.get("wattage", 0) or 0)
        ok = have >= need
        checks.append(f"PSU wattage covers CPU+GPU+20W ({need}W): {'PASS' if ok else 'FAIL'}")
        if not ok:
            return False, checks

    checks.append("Partial build compatibility checks: PASS")
    return True, checks


def _purpose_score(purpose: str, state: Dict) -> float:
    cpu = state.get("cpu") or {}
    ram = state.get("ram") or {}
    gpu = state.get("gpu") or {}
    psu = state.get("psu") or {}

    cpu_cores = float(cpu.get("cores", 0) or 0)
    ram_gb = float(ram.get("capacity_gb", 0) or 0)
    gpu_vram = float(gpu.get("vram_gb", 0) or 0)
    gpu_tdp = float(gpu.get("tdp_watts", 0) or 0)
    psu_watt = float(psu.get("wattage", 0) or 0)
    total = float(state.get("total_price", 0) or 0)

    if purpose == "gaming":
        return gpu_vram * 8 + gpu_tdp * 0.05 + cpu_cores
    if purpose == "office":
        return -total
    if purpose == "content creation":
        return cpu_cores * 3 + ram_gb * 2 + gpu_vram
    if purpose == "ai/ml":
        return gpu_vram * 10 + psu_watt * 0.04 + cpu_cores * 1.5
    if purpose == "budget":
        return -total
    if purpose == "high-end":
        return cpu_cores * 4 + ram_gb * 2 + gpu_vram * 6 + psu_watt * 0.02
    return 0.0


def candidate_sort_key(purpose: str, key: str, item: Dict):
    price = _price(item)
    if purpose in {"budget", "office"}:
        return (price,)

    if key == "gpu":
        vram = int(item.get("vram_gb", 0) or 0)
        return (-vram, price)
    if key == "cpu":
        cores = int(item.get("cores", 0) or 0)
        return (-cores, price)
    if key == "ram":
        cap = int(item.get("capacity_gb", 0) or 0)
        speed = int(item.get("speed_mhz", 0) or 0)
        return (-cap, -speed, price)
    if key == "psu":
        watt = int(item.get("wattage", 0) or 0)
        return (-watt, price)

    return (price,)


def is_goal_state(state: Dict, budget: float, purpose: str) -> bool:
    for key in COMPONENT_ORDER:
        if component_required(purpose, key) and state.get(key) is None:
            return False

    if state.get("total_price", 0) > budget:
        return False

    ok, _ = compatibility_check(state)
    if not ok:
        return False

    # Goal-level quality gate by purpose.
    if purpose == "gaming":
        if not state.get("gpu"):
            return False
    if purpose == "ai/ml":
        gpu = state.get("gpu")
        if not gpu or int(gpu.get("vram_gb", 0) or 0) < 12:
            return False
    if purpose == "content creation":
        if int((state.get("cpu") or {}).get("cores", 0) or 0) < 8:
            return False
        if int((state.get("ram") or {}).get("capacity_gb", 0) or 0) < 16:
            return False
    if purpose == "high-end":
        if int((state.get("cpu") or {}).get("cores", 0) or 0) < 12:
            return False
        if int((state.get("ram") or {}).get("capacity_gb", 0) or 0) < 32:
            return False
        gpu = state.get("gpu")
        if not gpu or int(gpu.get("vram_gb", 0) or 0) < 12:
            return False
    return True


def expand_state(state: Dict, components: Dict, budget: float, purpose: str) -> List[Dict]:
    key = next_component_key(state)
    if key is None:
        return []

    states: List[Dict] = []

    # Optional GPU for office/budget: allow skipping GPU state.
    if key == "gpu" and not component_required(purpose, "gpu"):
        skip_state = dict(state)
        skip_state["gpu"] = {"name": "No dedicated GPU", "price_usd": 0, "tdp_watts": 0, "vram_gb": 0}
        states.append(skip_state)

    dataset_key = KEY_TO_DATASET[key]
    candidates = components.get(dataset_key, [])
    primary_sorted = sorted(candidates, key=lambda item: candidate_sort_key(purpose, key, item))
    price_sorted = sorted(candidates, key=_price)
    if purpose in {"budget", "office"}:
        selected = price_sorted[:6]
    else:
        selected = primary_sorted[:8] + price_sorted[:8]

    # De-duplicate while preserving order.
    seen = set()
    sorted_candidates = []
    for item in selected:
        item_id = (
            item.get("cpu_id")
            or item.get("mb_id")
            or item.get("ram_id")
            or item.get("storage_id")
            or item.get("gpu_id")
            or item.get("psu_id")
            or item.get("name")
        )
        if item_id in seen:
            continue
        seen.add(item_id)
        sorted_candidates.append(item)

    for item in sorted_candidates:
        if not purpose_component_allowed(purpose, key, item):
            continue

        new_state = dict(state)
        new_state[key] = item
        new_state["total_price"] = round(float(state.get("total_price", 0)) + _price(item), 2)

        if new_state["total_price"] > budget:
            continue

        # Lower-bound budget pruning: if even the cheapest required future parts
        # overflow budget, stop exploring this branch now.
        if new_state["total_price"] + estimate_remaining_min_cost(new_state, components, purpose) > budget:
            continue

        ok, _ = compatibility_check(new_state)
        if not ok:
            continue

        states.append(new_state)

    return states


def score_state(purpose: str, state: Dict) -> float:
    return _purpose_score(purpose, state)


def performance_score(purpose: str, state: Dict, budget: float) -> float:
    """Single ranking value used to compare multiple valid builds."""
    base = score_state(purpose, state)
    total = float(state.get("total_price", 0) or 0)
    budget = max(float(budget or 1), 1.0)
    budget_efficiency = max(0.0, (budget - total) / budget) * 20.0
    return round(base + budget_efficiency, 2)


def estimate_remaining_min_cost(state: Dict, components: Dict, purpose: str) -> float:
    """Lower-bound estimate for remaining required components cost."""
    remaining_total = 0.0
    for future_key in COMPONENT_ORDER:
        if state.get(future_key) is not None:
            continue
        if not component_required(purpose, future_key):
            continue
        future_candidates = components.get(KEY_TO_DATASET[future_key], [])
        valid_prices = [
            _price(cand)
            for cand in future_candidates
            if purpose_component_allowed(purpose, future_key, cand)
        ]
        if not valid_prices:
            return float("inf")
        remaining_total += min(valid_prices)
    return remaining_total


def format_build_response(state: Dict, budget: float, purpose: str) -> Dict:
    ok, checks = compatibility_check(state)
    return {
        "build": {
            "cpu": state.get("cpu"),
            "motherboard": state.get("motherboard"),
            "ram": state.get("ram"),
            "storage": state.get("storage"),
            "gpu": state.get("gpu"),
            "psu": state.get("psu"),
        },
        "total_price": round(float(state.get("total_price", 0) or 0), 2),
        "budget": float(budget),
        "purpose": purpose,
        "compatibility": {
            "is_compatible": ok,
            "checks": checks,
        },
        "required_wattage": required_wattage(state),
        "score": round(score_state(purpose, state), 2),
        "performance_score": performance_score(purpose, state, budget),
    }
