from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

try:
    from .constraints import format_build_response
    from .data_loader import load_components
    from .search.bfs import build_with_bfs
    from .search.dfs import build_with_dfs
    from .search.ucs import build_with_ucs
    from .search.astar import build_with_astar
except ImportError:
    from constraints import format_build_response
    from data_loader import load_components
    from search.bfs import build_with_bfs
    from search.dfs import build_with_dfs
    from search.ucs import build_with_ucs
    from search.astar import build_with_astar


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "components.xlsx"
FRONTEND_DIR = BASE_DIR / "frontend"

ALGORITHMS = {
    "bfs": build_with_bfs,
    "dfs": build_with_dfs,
    "ucs": build_with_ucs,
    "astar": build_with_astar,
}

ALLOWED_PURPOSES = {"gaming", "office", "content creation", "ai/ml", "budget", "high-end"}

app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")
CORS(app)
COMPONENTS = load_components(DATA_FILE)


@app.get("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.post("/build")
def build_pc():
    payload = request.get_json(silent=True) or {}

    budget = payload.get("budget")
    purpose = str(payload.get("purpose", "")).strip().lower()
    algorithm = str(payload.get("algorithm", "bfs")).strip().lower()

    try:
        budget = float(budget)
    except (TypeError, ValueError):
        return jsonify({"error": "Budget must be a valid number."}), 400

    if budget <= 0:
        return jsonify({"error": "Budget must be greater than 0."}), 400

    if purpose not in ALLOWED_PURPOSES:
        return jsonify({"error": f"Purpose must be one of: {sorted(ALLOWED_PURPOSES)}"}), 400

    if algorithm not in ALGORITHMS:
        return jsonify({"error": "Algorithm must be one of: bfs, dfs, ucs, astar"}), 400

    builder = ALGORITHMS[algorithm]
    result_state, search_stats = builder(COMPONENTS, budget, purpose)

    if not result_state:
        return jsonify(
            {
                "message": "No valid build found for the selected budget and purpose.",
                "budget": budget,
                "purpose": purpose,
                "algorithm": algorithm,
                "performance": {
                    "explored_nodes": search_stats.get("explored_nodes", 0),
                    "elapsed_ms": search_stats.get("elapsed_ms", 0),
                },
            }
        ), 404

    response = format_build_response(result_state, budget=budget, purpose=purpose)
    response["algorithm"] = algorithm.upper()
    response["performance"] = {
        "explored_nodes": search_stats.get("explored_nodes", 0),
        "elapsed_ms": search_stats.get("elapsed_ms", 0),
    }
    return jsonify(response)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
