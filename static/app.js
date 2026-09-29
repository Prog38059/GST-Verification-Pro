// State code mapping for all 38 Indian GST jurisdictions
const GST_STATE_CODES = {
  "01": "Jammu & Kashmir",
  "02": "Himachal Pradesh",
  "03": "Punjab",
  "04": "Chandigarh",
  "05": "Uttarakhand",
  "06": "Haryana",
  "07": "Delhi",
  "08": "Rajasthan",
  "09": "Uttar Pradesh",
  "10": "Bihar",
  "11": "Sikkim",
  "12": "Arunachal Pradesh",
  "13": "Nagaland",
  "14": "Manipur",
  "15": "Mizoram",
  "16": "Tripura",
  "17": "Meghalaya",
  "18": "Assam",
  "19": "West Bengal",
  "20": "Jharkhand",
  "21": "Odisha",
  "22": "Chhattisgarh",
  "23": "Madhya Pradesh",
  "24": "Gujarat",
  "25": "Daman & Diu",
  "26": "Dadra & Nagar Haveli",
  "27": "Maharashtra",
  "28": "Andhra Pradesh (Old)",
  "29": "Karnataka",
  "30": "Goa",
  "31": "Lakshadweep",
  "32": "Kerala",
  "33": "Tamil Nadu",
  "34": "Puducherry",
  "35": "Andaman & Nicobar Islands",
  "36": "Telangana",
  "37": "Andhra Pradesh",
  "38": "Ladakh",
  "97": "Other Territory"
};

// GSTIN Regex format validator
const GSTIN_REGEX = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$/;

let currentSessionId = null;
let currentResultData = null;

// DOM Elements
const gstinInput = document.getElementById("gstinInput");
const captchaInput = document.getElementById("captchaInput");
const captchaImg = document.getElementById("captchaImg");
const captchaLoader = document.getElementById("captchaLoader");
const refreshCaptchaBtn = document.getElementById("refreshCaptchaBtn");
const verifyBtn = document.getElementById("verifyBtn");
const alertBox = document.getElementById("alertBox");
const gstinFormatBadge = document.getElementById("gstinFormatBadge");
const stateInfoBanner = document.getElementById("stateInfoBanner");
const detectedStateName = document.getElementById("detectedStateName");
const detectedPan = document.getElementById("detectedPan");
const resultsSection = document.getElementById("resultsSection");

// Buttons & Actions
const copySummaryBtn = document.getElementById("copySummaryBtn");
const printBtn = document.getElementById("printBtn");
const copyJsonBtn = document.getElementById("copyJsonBtn");
const toggleHistoryBtn = document.getElementById("toggleHistoryBtn");
const historyDrawer = document.getElementById("historyDrawer");
const drawerOverlay = document.getElementById("drawerOverlay");
const closeHistoryBtn = document.getElementById("closeHistoryBtn");
const clearHistoryBtn = document.getElementById("clearHistoryBtn");
const historyList = document.getElementById("historyList");
const historyCount = document.getElementById("historyCount");
const toast = document.getElementById("toast");

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
  loadCaptcha();
  renderHistory();
  gstinInput.focus();

  // Attach Listeners
  gstinInput.addEventListener("input", handleGstinInput);
  refreshCaptchaBtn.addEventListener("click", loadCaptcha);
  document.getElementById("gstForm").addEventListener("submit", handleVerifySubmit);

  copySummaryBtn.addEventListener("click", copySummaryToClipboard);
  printBtn.addEventListener("click", () => window.print());
  copyJsonBtn.addEventListener("click", copyJsonToClipboard);

  toggleHistoryBtn.addEventListener("click", openHistoryDrawer);
  closeHistoryBtn.addEventListener("click", closeHistoryDrawer);
  drawerOverlay.addEventListener("click", closeHistoryDrawer);
  clearHistoryBtn.addEventListener("click", clearSearchHistory);
});

// Load live captcha from backend
async function loadCaptcha() {
  try {
    captchaImg.style.display = "none";
    captchaLoader.style.display = "block";
    refreshCaptchaBtn.disabled = true;

    const res = await fetch("/api/v1/getCaptcha");
    const data = await res.json();

    if (!res.ok || !data.sessionId) {
      throw new Error(data.error || "Failed to load captcha");
    }

    currentSessionId = data.sessionId;
    captchaImg.src = data.image;
    captchaImg.onload = () => {
      captchaLoader.style.display = "none";
      captchaImg.style.display = "block";
      refreshCaptchaBtn.disabled = false;
    };
    captchaInput.value = "";
  } catch (err) {
    console.error("Captcha error:", err);
    captchaLoader.style.display = "none";
    refreshCaptchaBtn.disabled = false;
    showAlert("Failed to load captcha from GST portal. Please click the refresh button.", "danger");
  }
}

// Live GSTIN Input parsing & intelligence
function handleGstinInput(e) {
  let val = e.target.value.toUpperCase().replace(/[^0-9A-Z]/g, "");
  e.target.value = val;

  if (val.length >= 2) {
    const stateCode = val.substring(0, 2);
    const state = GST_STATE_CODES[stateCode] || "Unknown State";
    detectedStateName.textContent = `State: ${state} (${stateCode})`;
    stateInfoBanner.style.display = "inline-flex";

    if (val.length >= 12) {
      const pan = val.substring(2, 12);
      detectedPan.textContent = `PAN: ${pan}`;
    } else {
      detectedPan.textContent = "PAN: ...";
    }
  } else {
    stateInfoBanner.style.display = "none";
  }

  // Format validation indicator
  if (val.length === 15) {
    if (GSTIN_REGEX.test(val)) {
      gstinFormatBadge.textContent = "Valid Format";
      gstinFormatBadge.className = "format-badge valid";
      gstinFormatBadge.style.display = "block";
      if (!captchaInput.value) {
        captchaInput.focus();
      }
    } else {
      gstinFormatBadge.textContent = "Invalid Structure";
      gstinFormatBadge.className = "format-badge invalid";
      gstinFormatBadge.style.display = "block";
    }
  } else {
    gstinFormatBadge.style.display = "none";
  }
}

// Submit Verification
async function handleVerifySubmit(e) {
  e.preventDefault();
  hideAlert();

  const gstin = gstinInput.value.trim().toUpperCase();
  const captcha = captchaInput.value.trim();

  if (!gstin) {
    showAlert("Please enter a GSTIN number.", "danger");
    gstinInput.focus();
    return;
  }

  if (gstin.length !== 15) {
    showAlert("GSTIN must be exactly 15 characters long.", "danger");
    gstinInput.focus();
    return;
  }

  if (!captcha) {
    showAlert("Please enter the captcha code shown above.", "danger");
    captchaInput.focus();
    return;
  }

  if (!currentSessionId) {
    showAlert("Session expired. Refreshing captcha...", "danger");
    await loadCaptcha();
    return;
  }

  // Set loading state
  setLoading(true);

  try {
    const res = await fetch("/api/v1/getGSTDetails", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        sessionId: currentSessionId,
        GSTIN: gstin,
        captcha: captcha
      })
    });

    const data = await res.json();

    if (!res.ok || data.error) {
      const errorMsg = data.error || "Verification failed. Check the details and try again.";
      showAlert(errorMsg, "danger");
      // Auto refresh captcha on failure because GST portal invalidates captcha after 1 attempt
      loadCaptcha();
      captchaInput.focus();
      return;
    }

    // Success! Render results
    currentResultData = data;
    renderResults(data);
    saveSearchHistory(gstin, data);
    showAlert("GSTIN verified successfully!", "success");

    // Scroll smoothly to results
    resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });

    // Refresh captcha ready for next search
    loadCaptcha();

  } catch (err) {
    console.error("Verification error:", err);
    showAlert("Network or server connection error. Please try again.", "danger");
    loadCaptcha();
  } finally {
    setLoading(false);
  }
}

// Render Results onto the Dashboard
function renderResults(data) {
  resultsSection.style.display = "block";

  const printDateEl = document.getElementById("printDate");
  if (printDateEl) {
    const now = new Date();
    printDateEl.textContent = `Generated: ${now.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })} at ${now.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}`;
  }

  // Status
  const status = (data.sts || "UNKNOWN").toUpperCase();
  const statusBadge = document.getElementById("resStatusBadge");
  statusBadge.textContent = status;
  if (status.includes("ACT")) {
    statusBadge.className = "status-badge status-active";
  } else {
    statusBadge.className = "status-badge status-cancelled";
  }

  // Taxpayer Type
  document.getElementById("resTaxpayerType").textContent = data.dty || "Regular";

  // Trade Name and Legal Name
  document.getElementById("resTradeName").textContent = data.tradeNam || data.lgnm || "N/A";
  document.getElementById("resLegalName").textContent = `Legal Name: ${data.lgnm || "N/A"}`;

  // Registration info
  document.getElementById("resGstin").textContent = data.gstin || gstinInput.value;
  document.getElementById("resConstitution").textContent = data.ctb || "N/A";
  document.getElementById("resRegDate").textContent = data.rgdt || "N/A";

  // Cancellation Date (if cancelled)
  const cancelRow = document.getElementById("cancellationRow");
  if (data.cxdt) {
    cancelRow.style.display = "flex";
    document.getElementById("resCancelDate").textContent = data.cxdt;
  } else {
    cancelRow.style.display = "none";
  }

  // Jurisdiction & Compliance
  document.getElementById("resCentreJur").textContent = data.ctj || "N/A";
  document.getElementById("resStateJur").textContent = data.stj || "N/A";
  document.getElementById("resAadhaar").textContent = data.adhrVFlag || "N/A";
  document.getElementById("resEinvoice").textContent = data.einvoiceStatus || "N/A";

  // Address
  let addressText = "No address provided.";
  if (data.pradr && data.pradr.adr) {
    addressText = data.pradr.adr;
  }
  document.getElementById("resAddress").textContent = addressText;

  // Nature of Business Activities
  const natureTags = document.getElementById("resNatureTags");
  natureTags.innerHTML = "";
  if (Array.isArray(data.nba) && data.nba.length > 0) {
    data.nba.forEach(act => {
      const tag = document.createElement("span");
      tag.className = "tag";
      tag.textContent = act;
      natureTags.appendChild(tag);
    });
  } else {
    natureTags.innerHTML = '<span class="text-muted">Not specified</span>';
  }
}

// Copy Structured Summary
function copySummaryToClipboard() {
  if (!currentResultData) return;
  const d = currentResultData;
  const summary = `
=== GSTIN VERIFICATION REPORT ===
GSTIN: ${d.gstin || "N/A"}
Status: ${d.sts || "N/A"}
Trade Name: ${d.tradeNam || "N/A"}
Legal Name: ${d.lgnm || "N/A"}
Entity Type: ${d.ctb || "N/A"}
Taxpayer Type: ${d.dty || "N/A"}
Registration Date: ${d.rgdt || "N/A"}
${d.cxdt ? `Cancellation Date: ${d.cxdt}\n` : ""}Address: ${d.pradr?.adr || "N/A"}
State Jurisdiction: ${d.stj || "N/A"}
Centre Jurisdiction: ${d.ctj || "N/A"}
Nature of Business: ${(d.nba || []).join(", ") || "N/A"}
Aadhaar Verified: ${d.adhrVFlag || "N/A"}
e-Invoice Enabled: ${d.einvoiceStatus || "N/A"}
=================================
Verified via GST Verification Pro
`.trim();

  navigator.clipboard.writeText(summary).then(() => {
    showToast("Summary copied to clipboard!");
  }).catch(() => {
    showToast("Failed to copy to clipboard");
  });
}

// Copy Raw JSON
function copyJsonToClipboard() {
  if (!currentResultData) return;
  navigator.clipboard.writeText(JSON.stringify(currentResultData, null, 2)).then(() => {
    showToast("Raw JSON copied to clipboard!");
  });
}

// Toast notification helper
function showToast(msg) {
  toast.textContent = msg;
  toast.style.display = "block";
  setTimeout(() => {
    toast.style.display = "none";
  }, 2500);
}

// Alert Box Helpers
function showAlert(msg, type = "danger") {
  alertBox.textContent = msg;
  alertBox.className = `alert alert-${type}`;
  alertBox.style.display = "block";
}

function hideAlert() {
  alertBox.style.display = "none";
}

// Button loading state
function setLoading(isLoading) {
  const btnText = verifyBtn.querySelector(".btn-text");
  const spinner = verifyBtn.querySelector(".btn-spinner");

  if (isLoading) {
    verifyBtn.disabled = true;
    btnText.textContent = "Verifying with GST Portal...";
    spinner.style.display = "inline-block";
  } else {
    verifyBtn.disabled = false;
    btnText.textContent = "Verify Taxpayer Details";
    spinner.style.display = "none";
  }
}

// History Management (localStorage)
function getSearchHistory() {
  try {
    return JSON.parse(localStorage.getItem("gst_search_history") || "[]");
  } catch {
    return [];
  }
}

function saveSearchHistory(gstin, data) {
  let list = getSearchHistory();
  // Filter out existing duplicate of same GSTIN
  list = list.filter(item => item.gstin !== gstin);

  list.unshift({
    gstin: gstin,
    tradeNam: data.tradeNam || data.lgnm || "N/A",
    status: data.sts || "UNKNOWN",
    data: data,
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  });

  // Keep top 15 searches
  if (list.length > 15) list = list.slice(0, 15);
  localStorage.setItem("gst_search_history", JSON.stringify(list));
  renderHistory();
}

function renderHistory() {
  const list = getSearchHistory();
  historyCount.textContent = list.length;

  if (list.length === 0) {
    historyList.innerHTML = '<p class="text-muted empty-state" style="text-align:center; padding: 20px;">No recent searches yet.</p>';
    return;
  }

  historyList.innerHTML = "";
  list.forEach(item => {
    const el = document.createElement("div");
    el.className = "history-item";
    const statusClass = (item.status || "").toLowerCase().includes("act") ? "status-active" : "status-cancelled";

    el.innerHTML = `
      <div class="history-item-top">
        <span class="history-gstin">${item.gstin}</span>
        <span class="status-badge ${statusClass}" style="font-size: 0.65rem; padding: 2px 6px;">${item.status}</span>
      </div>
      <div class="history-name">${item.tradeNam}</div>
      <div class="history-time">${item.timestamp}</div>
    `;

    el.addEventListener("click", () => {
      gstinInput.value = item.gstin;
      handleGstinInput({ target: gstinInput });
      currentResultData = item.data;
      renderResults(item.data);
      closeHistoryDrawer();
      resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
    });

    historyList.appendChild(el);
  });
}

function clearSearchHistory() {
  localStorage.removeItem("gst_search_history");
  renderHistory();
  showToast("Search history cleared.");
}

function openHistoryDrawer() {
  renderHistory();
  historyDrawer.style.display = "flex";
  drawerOverlay.style.display = "block";
}

function closeHistoryDrawer() {
  historyDrawer.style.display = "none";
  drawerOverlay.style.display = "none";
}
