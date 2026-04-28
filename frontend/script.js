const form = document.getElementById("builder-form");
const resultBox = document.getElementById("result");
const compareBox = document.getElementById("compare-result");
const errorBox = document.getElementById("error");
const compareBtn = document.getElementById("compare-algorithms");
const exportBtn = document.getElementById("export-report");
let lastBuildResult = null;
const ALGORITHMS = ["bfs", "dfs", "ucs", "astar"];
const API_BASE_URL = (window.APP_CONFIG && window.APP_CONFIG.API_BASE_URL) || "";

function getSafe(obj, key, fallback) {
  if (!obj || obj[key] === undefined || obj[key] === null) return fallback;
  return obj[key];
}

function showError(message) {
  errorBox.textContent = message;
  errorBox.classList.remove("hidden");
  resultBox.classList.add("hidden");
  compareBox.classList.add("hidden");
  exportBtn.disabled = true;
}

function showResult(data) {
  const build = data.build || {};
  const parts = [
    ["CPU", getSafe(build.cpu, "name", "Not selected"), getSafe(build.cpu, "price_usd", 0)],
    ["Motherboard", getSafe(build.motherboard, "name", "Not selected"), getSafe(build.motherboard, "price_usd", 0)],
    ["RAM", getSafe(build.ram, "name", "Not selected"), getSafe(build.ram, "price_usd", 0)],
    ["Storage", getSafe(build.storage, "name", "Not selected"), getSafe(build.storage, "price_usd", 0)],
    ["GPU", getSafe(build.gpu, "name", "Not selected"), getSafe(build.gpu, "price_usd", 0)],
    ["PSU", getSafe(build.psu, "name", "Not selected"), getSafe(build.psu, "price_usd", 0)],
  ];

  const rows = parts
    .map(([label, name, price]) => {
      const safePrice = Number(price || 0).toFixed(2);
      return `
        <div class="build-row">
          <strong>${label}</strong>
          <span>${name} - $${safePrice}</span>
        </div>
      `;
    })
    .join("");

  const compatibility = data.compatibility || {};
  const compatible = compatibility.is_compatible ? "Compatible" : "Not compatible";
  const perf = data.performance || {};

  resultBox.innerHTML = `
    <h2>Generated Build</h2>
    ${rows}
    <p class="meta"><strong>Total Price:</strong> $${Number(data.total_price || 0).toFixed(2)}</p>
    <p class="meta"><strong>Budget:</strong> $${Number(data.budget || 0).toFixed(2)}</p>
    <p class="meta"><strong>Purpose:</strong> ${data.purpose || "-"}</p>
    <p class="meta"><strong>Algorithm:</strong> ${data.algorithm || "-"}</p>
    <p class="meta"><strong>Compatibility:</strong> ${compatible}</p>
    <p class="meta"><strong>Explored Nodes:</strong> ${Number(perf.explored_nodes || 0)}</p>
    <p class="meta"><strong>Search Time:</strong> ${Number(perf.elapsed_ms || 0)} ms</p>
  `;

  resultBox.classList.remove("hidden");
  errorBox.classList.add("hidden");
  lastBuildResult = data;
  exportBtn.disabled = false;
}

function buildReportText(data) {
  const build = data.build || {};
  const perf = data.performance || {};
  const lines = [
    "AI PC Builder Report",
    "====================",
    "",
    "Purpose: " + (data.purpose || "-"),
    "Algorithm: " + (data.algorithm || "-"),
    "Budget: $" + Number(data.budget || 0).toFixed(2),
    "Total Price: $" + Number(data.total_price || 0).toFixed(2),
    "Performance Score: " + Number(data.performance_score || 0).toFixed(2),
    "Explored Nodes: " + Number(perf.explored_nodes || 0),
    "Search Time (ms): " + Number(perf.elapsed_ms || 0),
    "",
    "Components",
    "----------",
    "CPU: " + getSafe(build.cpu, "name", "Not selected"),
    "Motherboard: " + getSafe(build.motherboard, "name", "Not selected"),
    "RAM: " + getSafe(build.ram, "name", "Not selected"),
    "Storage: " + getSafe(build.storage, "name", "Not selected"),
    "GPU: " + getSafe(build.gpu, "name", "Not selected"),
    "PSU: " + getSafe(build.psu, "name", "Not selected"),
  ];
  return lines.join("\n");
}

async function fetchBuild(payload) {
  const response = await fetch(`${API_BASE_URL}/build`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  return { response, data };
}

function renderCompareResults(items) {
  const successful = items.filter((item) => item.ok);
  if (!successful.length) {
    showError("No algorithms found a valid build for this input.");
    return;
  }

  const maxNodes = Math.max(...successful.map((item) => Number(item.nodes || 0)), 1);
  const maxTime = Math.max(...successful.map((item) => Number(item.ms || 0)), 1);

  const rows = items
    .map((item) => {
      const algoLabel = item.algorithm.toUpperCase();
      if (!item.ok) {
        return `
          <div class="compare-item">
            <div class="compare-topline">
              <strong>${algoLabel}</strong>
              <span>No valid build</span>
            </div>
          </div>
        `;
      }
      const nodePct = Math.max(3, Math.round((item.nodes / maxNodes) * 100));
      const timePct = Math.max(3, Math.round((item.ms / maxTime) * 100));
      return `
        <div class="compare-item">
          <div class="compare-topline">
            <strong>${algoLabel}</strong>
            <span>Nodes: ${item.nodes} | Time: ${item.ms} ms | Price: $${Number(item.price || 0).toFixed(2)}</span>
          </div>
          <div class="bar-wrap"><div class="bar-fill" style="width:${nodePct}%"></div></div>
          <div class="compare-note">Explored nodes bar</div>
          <div class="bar-wrap" style="margin-top:6px;"><div class="bar-fill" style="width:${timePct}%"></div></div>
          <div class="compare-note">Search time bar</div>
        </div>
      `;
    })
    .join("");

  compareBox.innerHTML = `
    <h2 class="compare-card-title">Algorithm Comparison</h2>
    ${rows}
    <p class="compare-note">Bars are normalized within this comparison (larger bar = higher value).</p>
  `;
  compareBox.classList.remove("hidden");
  errorBox.classList.add("hidden");
}

exportBtn.addEventListener("click", () => {
  if (!lastBuildResult) return;
  const report = buildReportText(lastBuildResult);
  const blob = new Blob([report], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "pc-build-report.txt";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
});

compareBtn.addEventListener("click", async () => {
  if (!form.checkValidity()) {
    form.reportValidity();
    return;
  }

  const budget = Number(document.getElementById("budget").value);
  const purpose = document.getElementById("purpose").value;
  compareBox.classList.remove("hidden");
  compareBox.innerHTML = "<p>Comparing algorithms...</p>";
  errorBox.classList.add("hidden");

  try {
    const requests = ALGORITHMS.map((algorithm) => fetchBuild({ budget, purpose, algorithm }));
    const responses = await Promise.all(requests);
    const items = responses.map(({ response, data }, idx) => ({
      algorithm: ALGORITHMS[idx],
      ok: response.ok,
      nodes: Number((data.performance || {}).explored_nodes || 0),
      ms: Number((data.performance || {}).elapsed_ms || 0),
      price: Number(data.total_price || 0),
    }));
    renderCompareResults(items);
  } catch (error) {
    showError("Could not compare algorithms. Check backend connection.");
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (!form.checkValidity()) {
    form.reportValidity();
    return;
  }

  resultBox.classList.remove("hidden");
  resultBox.innerHTML = "<p>Generating build...</p>";
  compareBox.classList.add("hidden");
  errorBox.classList.add("hidden");
  exportBtn.disabled = true;
  lastBuildResult = null;

  const payload = {
    budget: Number(document.getElementById("budget").value),
    purpose: document.getElementById("purpose").value,
    algorithm: document.getElementById("algorithm").value,
  };

  try {
    const { response, data } = await fetchBuild(payload);
    if (!response.ok) {
      showError(data.error || data.message || "Failed to generate build.");
      return;
    }
    showResult(data);
  } catch (error) {
    showError("Could not connect to backend server.");
  }
});
