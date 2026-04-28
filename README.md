# AI-Based PC Builder Website

A complete Flask + vanilla JS project that builds a compatible PC using AI search algorithms: **BFS**, **DFS**, and **UCS**.

## Project Structure

```text
backend/
  app.py
  data_loader.py
  constraints.py
  search/
    __init__.py
    bfs.py
    dfs.py
    ucs.py
frontend/
  index.html
  style.css
  script.js
data/
  components.xlsx
requirements.txt
```

## Features

- User inputs: budget, purpose, algorithm
- Returns: full build, total price, compatibility status
- Uses Excel file via pandas
- Enforces compatibility:
  - CPU socket = motherboard socket
  - RAM type = motherboard supported RAM
  - Storage interface support (SATA / NVMe)
  - PSU wattage >= CPU + GPU + 20W
  - Total price <= budget
- Purpose-aware filtering and ranking:
  - Gaming, Office, Content Creation, AI/ML, Budget, High-End

## Run Locally

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Start backend server:

```bash
python backend/app.py
```

3. Open in browser:

- [http://localhost:5000](http://localhost:5000)

## Deploy Notes (Netlify + Flask)

Netlify can host the frontend static files, but it does not run this Flask app directly.

- Frontend on Netlify: publish directory is `frontend` (configured in `netlify.toml`)
- Backend (Flask API) should be hosted on a Python host such as Render/Railway/Fly.io
- Then update frontend API calls to target your backend URL

## API

### `POST /build`

Request body:

```json
{
  "budget": 1500,
  "purpose": "gaming",
  "algorithm": "ucs"
}
```

Response includes:

- Selected components
- Total price
- Compatibility report
- Purpose and algorithm metadata
