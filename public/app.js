// Works both locally (hits localhost:8000) and on Vercel (same-origin /api/...)
const isLocal = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
const API_BASE = isLocal ? "http://localhost:8000" : "";

const form = document.getElementById("transcribe-form");
const urlInput = document.getElementById("reel-url");
const statusEl = document.getElementById("status");
const statusText = document.getElementById("status-text");
const resultBox = document.getElementById("result-box");
const transcriptEl = document.getElementById("transcript");
const resultMeta = document.getElementById("result-meta");
const errorBox = document.getElementById("error-box");
const errorText = document.getElementById("error-text");
const warningBox = document.getElementById("warning-box");
const copyBtn = document.getElementById("copy-btn");
const copyText = document.getElementById("copy-text");
const submitBtn = document.getElementById("submit-btn");
const btnText = document.getElementById("btn-text");
const btnSpinner = document.getElementById("btn-spinner");

function getProvider() {
  return document.querySelector('input[name="provider"]:checked').value;
}

function setLoading(loading) {
  submitBtn.disabled = loading;
  btnText.textContent = loading ? "Working..." : "Transcribe";
  btnSpinner.classList.toggle("hidden", !loading);
  statusEl.classList.toggle("hidden", !loading);

  const steps = ["Downloading reel...", "Extracting audio...", "Transcribing..."];
  if (loading) {
    let i = 0;
    statusText.textContent = steps[0];
    window._statusInterval = setInterval(() => {
      i = Math.min(i + 1, steps.length - 1);
      statusText.textContent = steps[i];
    }, 4000);
  } else {
    clearInterval(window._statusInterval);
  }
}

function clearState() {
  errorBox.classList.add("hidden");
  resultBox.classList.add("hidden");
  warningBox.classList.add("hidden");
  statusEl.classList.add("hidden");
}

function showError(msg) {
  errorText.textContent = msg;
  errorBox.classList.remove("hidden");
  resultBox.classList.add("hidden");
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const url = urlInput.value.trim();
  if (!url) return;

  clearState();
  setLoading(true);

  const payload = {
    url,
    provider: getProvider(),
    language: document.getElementById("language").value,
  };

  try {
    const res = await fetch(`${API_BASE}/api/transcribe`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || `Server error (HTTP ${res.status})`);
    }

    transcriptEl.textContent = data.transcript;

    resultMeta.innerHTML = "";
    const badges = [];
    if (data.provider === "openai") badges.push("OpenAI Whisper");
    if (data.provider === "gemini") badges.push("Google Gemini");
    if (data.language_detected) badges.push(`Lang: ${data.language_detected}`);
    if (data.duration_seconds != null) badges.push(`${data.duration_seconds.toFixed(1)}s`);
    badges.forEach((b) => {
      const span = document.createElement("span");
      span.textContent = b;
      resultMeta.appendChild(span);
    });

    if (data.warning) {
      warningBox.textContent = data.warning;
      warningBox.classList.remove("hidden");
    }

    resultBox.classList.remove("hidden");

  } catch (err) {
    showError(err.message);
  } finally {
    setLoading(false);
  }
});

copyBtn.addEventListener("click", async () => {
  const text = transcriptEl.textContent;
  if (!text) return;
  try {
    await navigator.clipboard.writeText(text);
    copyText.textContent = "Copied!";
    copyBtn.classList.add("copied");
    setTimeout(() => {
      copyText.textContent = "Copy";
      copyBtn.classList.remove("copied");
    }, 2000);
  } catch {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.cssText = "position:fixed;opacity:0";
    document.body.appendChild(ta);
    ta.select();
    document.execCommand("copy");
    document.body.removeChild(ta);
    copyText.textContent = "Copied!";
    setTimeout(() => { copyText.textContent = "Copy"; }, 2000);
  }
});
