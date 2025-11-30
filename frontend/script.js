// script.js
const API_BASE = "https://rvy389ztac.execute-api.us-east-1.amazonaws.com"; // same origin

// Example: fetch(`${API_BASE}/dashboard/summary`)


const backendStatusEl = document.getElementById("backendStatus");

// Navigation
document.querySelectorAll(".nav-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".nav-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    const target = btn.getAttribute("data-target");
    document.getElementById(target).classList.add("active");
    if (target === "dashboard") {
      loadDashboard();
    } else if (target === "products") {
      loadProducts();
    } else if (target === "batches") {
      loadProductsForBatches();
      loadBatches();
    } else if (target === "inspections") {
      loadBatchesForInspections();
    } else if (target === "alerts") {
      loadAlerts();
    }
  });
});

// Backend health
async function checkBackend() {
  try {
    const res = await fetch(API_BASE + "/health");
    if (!res.ok) throw new Error();
    backendStatusEl.textContent = "Backend: Online at " + API_BASE;
  } catch (e) {
    backendStatusEl.textContent = "Backend: Offline. Start FastAPI at " + API_BASE;
  }
}

// Dashboard
async function loadDashboard() {
  try {
    const res = await fetch(API_BASE + "/dashboard/summary");
    const data = await res.json();
    document.getElementById("totalProducts").textContent = data.total_products;
    document.getElementById("totalBatches").textContent = data.total_batches;
    document.getElementById("highRisk").textContent = data.high_risk_batches;
    document.getElementById("mediumRisk").textContent = data.medium_risk_batches;
    document.getElementById("lowRisk").textContent = data.low_risk_batches;
    document.getElementById("unknownRisk").textContent = data.unknown_risk_batches;
  } catch (e) {
    console.error("Dashboard error", e);
  }
}

// Products
const productsTableBody = document.getElementById("productsTableBody");
const productForm = document.getElementById("productForm");
const productResetBtn = document.getElementById("productResetBtn");
const productIdInput = document.getElementById("productId");
const productNameInput = document.getElementById("productName");
const productCategoryInput = document.getElementById("productCategory");
const productDescriptionInput = document.getElementById("productDescription");

async function loadProducts() {
  try {
    const res = await fetch(API_BASE + "/products");
    const data = await res.json();
    productsTableBody.innerHTML = "";
    data.forEach((p) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${p.id}</td>
        <td>${p.name}</td>
        <td>${p.category || ""}</td>
        <td>
          <button onclick="editProduct(${p.id}, '${escapeQuotes(p.name)}', '${escapeQuotes(
        p.category || ""
      )}', '${escapeQuotes(p.description || "")}')">Edit</button>
          <button class="secondary" onclick="deleteProduct(${p.id})">Delete</button>
        </td>
      `;
      productsTableBody.appendChild(tr);
    });
  } catch (e) {
    console.error("Load products error", e);
  }
}

function escapeQuotes(str) {
  return String(str).replace(/'/g, "\'").replace(/"/g, "&quot;");
}

window.editProduct = function (id, name, category, description) {
  productIdInput.value = id;
  productNameInput.value = name;
  productCategoryInput.value = category;
  productDescriptionInput.value = description.replace(/&quot;/g, '"');
};

window.deleteProduct = async function (id) {
  if (!confirm("Delete product " + id + "?")) return;
  await fetch(API_BASE + `/products/${id}`, { method: "DELETE" });
  loadProducts();
  loadProductsForBatches();
};

productForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = {
    name: productNameInput.value,
    category: productCategoryInput.value,
    description: productDescriptionInput.value,
  };
  const id = productIdInput.value;
  const method = id ? "PUT" : "POST";
  const url = id ? API_BASE + `/products/${id}` : API_BASE + "/products";
  await fetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  productForm.reset();
  productIdInput.value = "";
  loadProducts();
  loadProductsForBatches();
});

productResetBtn.addEventListener("click", () => {
  productForm.reset();
  productIdInput.value = "";
});

// Batches
const batchProductIdSelect = document.getElementById("batchProductId");
const batchesTableBody = document.getElementById("batchesTableBody");
const batchForm = document.getElementById("batchForm");

async function loadProductsForBatches() {
  try {
    const res = await fetch(API_BASE + "/products");
    const data = await res.json();
    batchProductIdSelect.innerHTML = "";
    data.forEach((p) => {
      const opt = document.createElement("option");
      opt.value = p.id;
      opt.textContent = `${p.name} (#${p.id})`;
      batchProductIdSelect.appendChild(opt);
    });
  } catch (e) {
    console.error("Load products for batches error", e);
  }
}

async function loadBatches() {
  try {
    const res = await fetch(API_BASE + "/batches");
    const data = await res.json();
    batchesTableBody.innerHTML = "";
    data.forEach((b) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${b.id}</td>
        <td>${b.code}</td>
        <td>${b.product_id}</td>
        <td>${b.status}</td>
        <td>${b.risk_level} ${b.risk_score ? "(" + b.risk_score.toFixed(1) + ")" : ""}</td>
        <td>
          <button onclick="computeRisk(${b.id})">Compute Risk</button>
          <button class="secondary" onclick="deleteBatch(${b.id})">Delete</button>
        </td>
      `;
      batchesTableBody.appendChild(tr);
    });
  } catch (e) {
    console.error("Load batches error", e);
  }
}

batchForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = {
    product_id: parseInt(batchProductIdSelect.value, 10),
    code: document.getElementById("batchCode").value,
    line_id: document.getElementById("batchLineId").value,
    status: "IN_PROGRESS",
  };
  await fetch(API_BASE + "/batches", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  batchForm.reset();
  loadBatches();
  loadBatchesForInspections();
});

window.deleteBatch = async function (id) {
  if (!confirm("Delete batch " + id + "?")) return;
  await fetch(API_BASE + `/batches/${id}`, { method: "DELETE" });
  loadBatches();
  loadBatchesForInspections();
};

window.computeRisk = async function (id) {
  await fetch(API_BASE + `/batches/${id}/compute-risk`, { method: "POST" });
  loadBatches();
  loadDashboard();
  loadAlerts();
};

// Inspections & sensor
const inspectionBatchIdSelect = document.getElementById("inspectionBatchId");
const sensorBatchIdSelect = document.getElementById("sensorBatchId");
const inspectionForm = document.getElementById("inspectionForm");
const sensorForm = document.getElementById("sensorForm");

async function loadBatchesForInspections() {
  try {
    const res = await fetch(API_BASE + "/batches");
    const data = await res.json();
    inspectionBatchIdSelect.innerHTML = "";
    sensorBatchIdSelect.innerHTML = "";
    data.forEach((b) => {
      const opt1 = document.createElement("option");
      opt1.value = b.id;
      opt1.textContent = `${b.code} (#${b.id})`;
      inspectionBatchIdSelect.appendChild(opt1);

      const opt2 = document.createElement("option");
      opt2.value = b.id;
      opt2.textContent = `${b.code} (#${b.id})`;
      sensorBatchIdSelect.appendChild(opt2);
    });
  } catch (e) {
    console.error("Load batches for inspections error", e);
  }
}

inspectionForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = {
    batch_id: parseInt(inspectionBatchIdSelect.value, 10),
    temperature: parseFloat(document.getElementById("inspectionTemp").value),
    humidity: document.getElementById("inspectionHumidity").value
      ? parseFloat(document.getElementById("inspectionHumidity").value)
      : null,
    ph: document.getElementById("inspectionPh").value
      ? parseFloat(document.getElementById("inspectionPh").value)
      : null,
    microbial_result: document.getElementById("inspectionMicrobial").value,
    notes: document.getElementById("inspectionNotes").value,
  };
  await fetch(API_BASE + "/inspections", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  inspectionForm.reset();
});

sensorForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = {
    batch_id: parseInt(sensorBatchIdSelect.value, 10),
    temperature: parseFloat(document.getElementById("sensorTemp").value),
    humidity: document.getElementById("sensorHumidity").value
      ? parseFloat(document.getElementById("sensorHumidity").value)
      : null,
  };
  await fetch(API_BASE + "/sensor-readings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  sensorForm.reset();
});

// Alerts
const alertsTableBody = document.getElementById("alertsTableBody");

async function loadAlerts() {
  try {
    const res = await fetch(API_BASE + "/alerts");
    const data = await res.json();
    alertsTableBody.innerHTML = "";
    data.forEach((a) => {
      const tr = document.createElement("tr");
      const created = new Date(a.created_at);
      tr.innerHTML = `
        <td>${created.toLocaleString()}</td>
        <td>${a.batch_id}</td>
        <td>${a.level}</td>
        <td>${a.message}</td>
      `;
      alertsTableBody.appendChild(tr);
    });
  } catch (e) {
    console.error("Load alerts error", e);
  }
}

// Initial load
checkBackend();
loadDashboard();
loadProducts();
loadProductsForBatches();
loadBatches();
loadBatchesForInspections();
loadAlerts();
// ==========================
// Sensor Anomaly Check Logic
// ==========================
const sensorAnomalyForm = document.getElementById("sensorAnomalyForm");
const sensorAnomalyResult = document.getElementById("sensorAnomalyResult");
const anomalyStatus = document.getElementById("anomalyStatus");
const anomalyLevel = document.getElementById("anomalyLevel");
const anomalyScore = document.getElementById("anomalyScore");
const anomalyMessage = document.getElementById("anomalyMessage");

if (sensorAnomalyForm) {
  sensorAnomalyForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const batchId = document.getElementById("anomalyBatchId").value;
    const temperature = parseFloat(document.getElementById("currentTemp").value);
    const humidity = parseFloat(document.getElementById("currentHumidity").value);

    if (!batchId) {
      alert("Please enter a Batch ID.");
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/sensor/analyze/batch/${batchId}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          temperature,
          humidity,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const msg = errorData.detail || "Failed to analyze sensor reading.";
        alert(msg);
        return;
      }

      const data = await response.json();

      anomalyStatus.textContent = data.is_anomaly ? "Anomaly Detected" : "Normal";
      anomalyStatus.className = data.is_anomaly ? "badge badge-high" : "badge badge-low";

      anomalyLevel.textContent = data.level;
      anomalyScore.textContent = data.score.toFixed(4);
      anomalyMessage.textContent = data.message;

      sensorAnomalyResult.classList.remove("hidden");
    } catch (err) {
      console.error(err);
      alert("Error connecting to the analysis service.");
    }
  });
}
