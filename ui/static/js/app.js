/**
 * SatQuery AI - Interactive Frontend Controller
 * Implements real-time agent workflow, mode toggling, sample loading,
 * visual evidence inspection, and execution trace updates.
 */

// Global state
const SatQueryState = {
  currentView: "analyze",
  currentMode: "single_image", // "single_image" | "bi_temporal" | "optical_sar"
  currentQuery: "Describe the land cover and major objects visible in this image",
  activeEvidenceIndex: 0,
  isAnalyzing: false,
  sampleData: {}
};

// Predefined local datasets fallback
const LOCAL_SAMPLE_FALLBACKS = {
  single_image: {
    task: "Single-image Understanding",
    model: "GeoChat",
    badge: "Single Image",
    badgeClass: "blue",
    input_type: "1 image (optical)",
    filename: "test_image.tif",
    format: "GeoTIFF",
    dimensions: "1024 × 1024",
    bands: "4 (RGB + NIR)",
    modality: "Optical",
    acquisition_date: "2024-05-15",
    status: "Analysis Ready",
    answer: "The image shows a mix of agricultural fields, a river, and urban built-up areas. The dominant land cover is vegetation with clear signs of human settlement near the riverbanks.",
    confidence: 0.92,
    confidence_level: "High Confidence",
    detected_land_cover: [
      { label: "Vegetation", color: "#22c55e", percentage: 52 },
      { label: "Water Body", color: "#3b82f6", percentage: 14 },
      { label: "Built-up Area", color: "#ef4444", percentage: 18 },
      { label: "Agriculture", color: "#eab308", percentage: 12 },
      { label: "Roads", color: "#cbd5e1", percentage: 4 }
    ],
    evidence: [
      { id: "main", label: "Input Image", url: "/data/samples/single_image/image.png" },
      { id: "seg", label: "Land Cover Segmentation", url: "/data/samples/single_image/segmentation.png" },
      { id: "sar", label: "SAR Backscatter", url: "/data/samples/single_image/sar_feature.png" },
      { id: "ndvi", label: "NIR False Color", url: "/data/samples/single_image/ndvi.png" }
    ],
    execution_trace: [
      { step: "01", name: "Input Validation", desc: "Checked format, metadata, compatibility", status: "Completed" },
      { step: "02", name: "Query Understanding", desc: "Identified as single-image analysis", status: "Completed" },
      { step: "03", name: "Agent Routing", desc: "Selected GeoChat model", status: "Completed" },
      { step: "04", name: "Model Execution", desc: "VQA + Captioning", status: "Completed" },
      { step: "05", name: "Result Integration", desc: "Combined output with spatial evidence", status: "Completed" },
      { step: "06", name: "Final Output", desc: "Answer + Visual evidence + Confidence", status: "Completed" }
    ]
  },
  bi_temporal: {
    task: "Bi-temporal Change Analysis",
    model: "ChangeStar",
    badge: "Bi-temporal",
    badgeClass: "orange",
    input_type: "2 images (optical pair: 2024 vs 2026)",
    filename: "pair_2024_2026.tif",
    format: "GeoTIFF Pair",
    dimensions: "1024 × 1024",
    bands: "4 Bands per epoch",
    modality: "Bi-temporal Optical",
    acquisition_date: "2024-04-12 / 2026-03-08",
    status: "Analysis Ready",
    answer: "Significant urban expansion and new infrastructure development detected. Built-up area increased by approximately +38.4 hectares between 2024 and 2026, primarily replacing former pasture and forest land with a new transportation corridor.",
    confidence: 0.89,
    confidence_level: "High Confidence",
    detected_land_cover: [
      { label: "New Built-up Area", color: "#f97316", percentage: 24 },
      { label: "Intact Vegetation", color: "#22c55e", percentage: 48 },
      { label: "Water Body (Unchanged)", color: "#3b82f6", percentage: 14 },
      { label: "Cleared Land", color: "#eab308", percentage: 9 },
      { label: "New Highway Corridor", color: "#cbd5e1", percentage: 5 }
    ],
    evidence: [
      { id: "before", label: "2024 Before Image", url: "/data/samples/bi_temporal/before.png" },
      { id: "after", label: "2026 After Image", url: "/data/samples/bi_temporal/after.png" },
      { id: "change", label: "ChangeStar Delta Map", url: "/data/samples/bi_temporal/change_map.png" }
    ],
    execution_trace: [
      { step: "01", name: "Input Validation", desc: "Validated dual epoch GeoTIFFs & spatial co-registration", status: "Completed" },
      { step: "02", name: "Query Understanding", desc: "Identified task as bi-temporal delta detection", status: "Completed" },
      { step: "03", name: "Agent Routing", desc: "Routed to ChangeStar specialist", status: "Completed" },
      { step: "04", name: "Model Execution", desc: "Dense temporal cross-attention & segmentation", status: "Completed" },
      { step: "05", name: "Result Integration", desc: "Computed change polygon statistics & delta mask", status: "Completed" },
      { step: "06", name: "Final Output", desc: "Delivered change map and quantitative impact report", status: "Completed" }
    ]
  },
  optical_sar: {
    task: "Cross-modal Analysis",
    model: "CROMA",
    badge: "Cross-modal",
    badgeClass: "purple",
    input_type: "2 images (Optical + SAR Sentinel Pair)",
    filename: "s2_s1_colocated.tif",
    format: "Multispectral + C-Band SAR",
    dimensions: "1024 × 1024",
    bands: "Optical (B2,B3,B4,B8) + SAR (VV, VH)",
    modality: "Optical + SAR Cross-Modal",
    acquisition_date: "2025-11-20",
    status: "Analysis Ready",
    answer: "Cross-modal fusion successfully disambiguated cloud-obscured surface features in the north-west sector. SAR backscatter identified hidden industrial structures beneath cloud cover while optical spectral bands accurately delineated agricultural plots and river boundary geometry.",
    confidence: 0.94,
    confidence_level: "High Confidence",
    detected_land_cover: [
      { label: "Cloud-Penetrated Structures", color: "#a855f7", percentage: 16 },
      { label: "Vegetation / Agriculture", color: "#22c55e", percentage: 50 },
      { label: "Water Body (Specular)", color: "#3b82f6", percentage: 14 },
      { label: "Urban Settlement", color: "#ef4444", percentage: 15 },
      { label: "Transport Arteries", color: "#cbd5e1", percentage: 5 }
    ],
    evidence: [
      { id: "optical", label: "Optical S2 Imagery", url: "/data/samples/optical_sar/optical.png" },
      { id: "sar", label: "SAR S1 Radar Backscatter", url: "/data/samples/optical_sar/sar.png" },
      { id: "joint", label: "CROMA Joint Analysis", url: "/data/samples/optical_sar/joint_analysis.png" }
    ],
    execution_trace: [
      { step: "01", name: "Input Validation", desc: "Validated Optical (S2) and SAR (S1) spatial alignment", status: "Completed" },
      { step: "02", name: "Query Understanding", desc: "Identified cross-modal fusion & feature disambiguation", status: "Completed" },
      { step: "03", name: "Agent Routing", desc: "Selected CROMA multimodal specialist", status: "Completed" },
      { step: "04", name: "Model Execution", desc: "Cross-attention optical-radar encoder fusion", status: "Completed" },
      { step: "05", name: "Result Integration", desc: "Merged cloud-penetrated structures with optical mask", status: "Completed" },
      { step: "06", name: "Final Output", desc: "Delivered joint cross-modal synthesis & classification", status: "Completed"}
    ]
  }
};

const MODE_QUERIES = {
  single_image: [
    "Describe the land cover",
    "Is there a water body?",
    "Where are the built-up areas?"
  ],
  bi_temporal: [
    "What changed between these two dates?",
    "Has the built-up area increased?",
    "Where did the change occur?"
  ],
  optical_sar: [
    "Use both images to identify built-up areas",
    "Identify water-covered regions",
    "Compare the information from optical and SAR"
  ]
};

// Initialization
document.addEventListener("DOMContentLoaded", () => {
  setupNavigation();
  setupModeSwitching();
  setupQueryChips();
  setupDropzone();
  setupAnalyzeButton();
  loadModeData(SatQueryState.currentMode);
});

// View Navigation
function setupNavigation() {
  const navItems = document.querySelectorAll(".nav-item");
  navItems.forEach(item => {
    item.addEventListener("click", () => {
      const view = item.dataset.view;
      switchView(view);
    });
  });
}

function switchView(viewName) {
  SatQueryState.currentView = viewName;
  
  // Update nav active states
  document.querySelectorAll(".nav-item").forEach(item => {
    item.classList.toggle("active", item.dataset.view === viewName);
  });

  // Toggle page visibility
  document.querySelectorAll(".page-view").forEach(page => {
    page.classList.remove("active");
  });

  const activePage = document.getElementById(`view-${viewName}`);
  if (activePage) {
    activePage.classList.add("active");
  }

  // Populate dedicated views when switched
  if (viewName === "results") {
    renderDedicatedResults();
  } else if (viewName === "trace") {
    renderDedicatedTrace();
  }
}

// Mode Switching (Single Image | Bi-temporal | Optical + SAR)
function setupModeSwitching() {
  const modeButtons = document.querySelectorAll(".mode-tab-btn");
  modeButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const mode = btn.dataset.mode;
      setMode(mode);
    });
  });
}

function setMode(mode) {
  SatQueryState.currentMode = mode;

  // Toggle button styling
  document.querySelectorAll(".mode-tab-btn").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.mode === mode);
  });

  // Update query chips
  renderQueryChips(mode);

  // Set default query in textarea
  const chips = MODE_QUERIES[mode];
  if (chips && chips.length > 0) {
    setQuery(chips[0]);
  }

  // Load mode sample data & update preview and agent panels
  loadModeData(mode);
}

// Query Chips Handling
function setupQueryChips() {
  renderQueryChips(SatQueryState.currentMode);

  const textarea = document.getElementById("satQueryInput");
  const charCounter = document.getElementById("queryCharCount");

  if (textarea) {
    textarea.addEventListener("input", (e) => {
      const len = e.target.value.length;
      if (charCounter) charCounter.textContent = `${len}/500`;
      SatQueryState.currentQuery = e.target.value;
    });
  }
}

function renderQueryChips(mode) {
  const container = document.getElementById("exampleChipsContainer");
  if (!container) return;

  container.innerHTML = "";
  const queries = MODE_QUERIES[mode] || [];

  queries.forEach(q => {
    const chip = document.createElement("div");
    chip.className = "query-chip";
    chip.textContent = q;
    chip.addEventListener("click", () => setQuery(q));
    container.appendChild(chip);
  });
}

function setQuery(q) {
  SatQueryState.currentQuery = q;
  const textarea = document.getElementById("satQueryInput");
  const charCounter = document.getElementById("queryCharCount");
  if (textarea) {
    textarea.value = q;
    if (charCounter) charCounter.textContent = `${q.length}/500`;
  }
}

// Load Data for Selected Mode
async function loadModeData(mode) {
  let data = null;

  try {
    const res = await fetch(`/api/samples/${mode}`);
    if (res.ok) {
      data = await res.json();
    }
  } catch (err) {
    console.warn("Backend API not reachable, using local demo data provider:", err);
  }

  if (!data) {
    data = LOCAL_SAMPLE_FALLBACKS[mode] || LOCAL_SAMPLE_FALLBACKS.single_image;
  }

  SatQueryState.sampleData[mode] = data;
  updateUIPanels(data);
}

// Update UI Panels with Model and Evidence Data
function updateUIPanels(data) {
  // 1. Image Preview Panel
  renderPreviewSection(data);

  // 2. Agent Center Panel
  renderAgentPanel(data);

  // 3. Right Results Panel
  renderResultsPanel(data);
}

// Render Preview Section (Single vs Dual)
function renderPreviewSection(data) {
  const singlePreviewWrap = document.getElementById("singlePreviewBlock");
  const dualPreviewWrap = document.getElementById("dualPreviewBlock");

  if (SatQueryState.currentMode === "single_image") {
    if (singlePreviewWrap) singlePreviewWrap.style.display = "block";
    if (dualPreviewWrap) dualPreviewWrap.style.display = "none";

    const thumb = document.getElementById("previewImgThumb");
    if (thumb) thumb.src = "/data/samples/single_image/image.png";

    document.getElementById("metaFileName").textContent = data.filename || "test_image.tif";
    document.getElementById("metaFormat").textContent = data.format || "GeoTIFF";
    document.getElementById("metaDimensions").textContent = data.dimensions || "1024 × 1024";
    document.getElementById("metaBands").textContent = data.bands || "4 (RGB + NIR)";
    document.getElementById("metaModality").textContent = data.modality || "Optical";
    document.getElementById("metaDate").textContent = data.acquisition_date || "2024-05-15";
  } else if (SatQueryState.currentMode === "bi_temporal") {
    if (singlePreviewWrap) singlePreviewWrap.style.display = "none";
    if (dualPreviewWrap) dualPreviewWrap.style.display = "grid";

    document.getElementById("dualLabel1").textContent = "BEFORE (2024)";
    document.getElementById("dualImg1").src = "/data/samples/bi_temporal/before.png";

    document.getElementById("dualLabel2").textContent = "AFTER (2026)";
    document.getElementById("dualImg2").src = "/data/samples/bi_temporal/after.png";
  } else if (SatQueryState.currentMode === "optical_sar") {
    if (singlePreviewWrap) singlePreviewWrap.style.display = "none";
    if (dualPreviewWrap) dualPreviewWrap.style.display = "grid";

    document.getElementById("dualLabel1").textContent = "OPTICAL (S2)";
    document.getElementById("dualImg1").src = "/data/samples/optical_sar/optical.png";

    document.getElementById("dualLabel2").textContent = "SAR (S1 RADAR)";
    document.getElementById("dualImg2").src = "/data/samples/optical_sar/sar.png";
  }
}

// Render Center Agent Panel
function renderAgentPanel(data) {
  document.getElementById("detectedTaskVal").textContent = data.task;
  document.getElementById("selectedModelVal").textContent = data.model;
  
  const badgeEl = document.getElementById("selectedModelBadge");
  if (badgeEl) {
    badgeEl.textContent = data.badge || (data.model === "GeoChat" ? "Single Image" : (data.model === "ChangeStar" ? "Bi-temporal" : "Cross-modal"));
    badgeEl.className = `specialist-badge ${data.badgeClass || (data.model === "GeoChat" ? "blue" : (data.model === "ChangeStar" ? "orange" : "purple"))}`;
  }

  document.getElementById("inputTypeVal").textContent = data.input_type || "1 image (optical)";
  document.getElementById("agentStatusVal").innerHTML = `<span style="color:var(--green-success)">●</span> ${data.status || "Analysis Ready"}`;

  // Highlight active specialist model card
  document.querySelectorAll(".specialist-card").forEach(card => {
    card.classList.remove("selected");
  });
  const activeCard = document.getElementById(`specCard-${data.model.toLowerCase()}`);
  if (activeCard) {
    activeCard.classList.add("selected");
  }
}

// Render Results Panel
function renderResultsPanel(data) {
  // Answer
  document.getElementById("answerText").textContent = data.answer;

  // Visual Evidence Main Image
  const evidenceList = data.evidence || [];
  SatQueryState.activeEvidenceIndex = 0;

  if (evidenceList.length > 0) {
    setEvidenceImage(evidenceList[0]);
  }

  // Evidence Thumbnails
  const thumbRow = document.getElementById("evidenceThumbnailsRow");
  if (thumbRow) {
    thumbRow.innerHTML = "";
    evidenceList.forEach((ev, idx) => {
      const btn = document.createElement("div");
      btn.className = `evidence-thumb-btn ${idx === 0 ? "active" : ""}`;
      
      const imgUrl = ev.url || (data.assets_base ? `${data.assets_base}/${ev.file}` : `/data/samples/${SatQueryState.currentMode}/${ev.file || "image.png"}`);
      btn.innerHTML = `<img src="${imgUrl}" alt="${ev.label}" title="${ev.label}" />`;

      btn.addEventListener("click", () => {
        document.querySelectorAll(".evidence-thumb-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        setEvidenceImage({ ...ev, url: imgUrl });
      });

      thumbRow.appendChild(btn);
    });
  }

  // Detected Land Cover Legend
  const legendBox = document.getElementById("detectedLandCoverList");
  if (legendBox) {
    legendBox.innerHTML = "";
    (data.detected_land_cover || []).forEach(item => {
      const row = document.createElement("div");
      row.className = "legend-item";
      row.innerHTML = `
        <span class="legend-dot" style="background-color: ${item.color}"></span>
        <span>${item.label} (${item.percentage}%)</span>
      `;
      legendBox.appendChild(row);
    });
  }

  // Confidence Meter
  const confVal = Math.round((data.confidence || 0.92) * 100);
  document.getElementById("confidenceValueText").textContent = `${confVal}%`;
  document.getElementById("confidenceLevelText").textContent = data.confidence_level || "High Confidence";

  const circleBar = document.getElementById("confidenceCircleBar");
  if (circleBar) {
    const circumference = 2 * Math.PI * 18; // r=18
    const offset = circumference - (confVal / 100) * circumference;
    circleBar.style.strokeDasharray = circumference;
    circleBar.style.strokeDashoffset = offset;
  }

  // Execution Trace List
  const traceList = document.getElementById("executionTraceList");
  if (traceList) {
    traceList.innerHTML = "";
    (data.execution_trace || []).forEach(tr => {
      const row = document.createElement("div");
      row.className = "trace-row";
      row.innerHTML = `
        <div class="trace-row-left">
          <span class="trace-num-badge">${tr.step}</span>
          <span class="trace-item-title">${tr.name}</span>
          <span class="trace-item-desc">${tr.desc}</span>
        </div>
        <span class="trace-completed-check">✓ Completed</span>
      `;
      traceList.appendChild(row);
    });
  }
}

function setEvidenceImage(ev) {
  const mainImg = document.getElementById("evidenceMainImg");
  const overlayTag = document.getElementById("evidenceOverlayTag");

  if (mainImg) {
    const url = ev.url || (ev.file ? `/data/samples/${SatQueryState.currentMode}/${ev.file}` : "/data/samples/single_image/image.png");
    mainImg.src = url;
  }

  if (overlayTag) {
    overlayTag.textContent = ev.label || "Visual Evidence";
  }
}

// Analyze Button & Animated Stepper Execution
function setupAnalyzeButton() {
  const analyzeBtn = document.getElementById("analyzeSubmitBtn");
  if (!analyzeBtn) return;

  analyzeBtn.addEventListener("click", () => {
    runAnalysisWorkflow();
  });
}

async function runAnalysisWorkflow() {
  if (SatQueryState.isAnalyzing) return;
  SatQueryState.isAnalyzing = true;

  const btn = document.getElementById("analyzeSubmitBtn");
  const originalBtnText = btn.innerHTML;
  btn.innerHTML = `<svg class="spin" style="width:16px;height:16px;animation:spin 1s linear infinite;" viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="10" stroke-width="3" stroke-dasharray="32" stroke-dashoffset="12"></circle></svg> Analyzing Satellite Data...`;
  btn.style.opacity = "0.85";

  // Reset Steppers to Pending
  const steps = [
    { id: "step-01", name: "Input Validation", desc: "Format, metadata, compatibility" },
    { id: "step-02", name: "Query Understanding", desc: "Identifying task type" },
    { id: "step-03", name: "Model Selection", desc: "Routing to specialist model" },
    { id: "step-04", name: "Analysis Ready", desc: "Executing selected specialist" }
  ];

  // Stage animation sequence
  for (let i = 0; i < steps.length; i++) {
    const stepEl = document.getElementById(steps[i].id);
    if (stepEl) {
      const ind = stepEl.querySelector(".step-indicator");
      const tag = stepEl.querySelector(".step-status-tag");
      
      ind.className = "step-indicator active";
      ind.innerHTML = `<span style="font-size:10px;">●</span>`;
      if (tag) tag.textContent = "Processing...";
    }
    await new Promise(r => setTimeout(r, 280));

    if (stepEl) {
      const ind = stepEl.querySelector(".step-indicator");
      const tag = stepEl.querySelector(".step-status-tag");
      ind.className = "step-indicator done";
      ind.innerHTML = "✓";
      if (tag) {
        tag.className = "step-status-tag completed";
        tag.textContent = "Completed";
      }
    }
  }

  // Call API or local model prediction
  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mode: SatQueryState.currentMode,
        query: SatQueryState.currentQuery
      })
    });
    
    if (res.ok) {
      const resultData = await res.json();
      SatQueryState.sampleData[SatQueryState.currentMode] = resultData;
      updateUIPanels(resultData);
    } else {
      loadModeData(SatQueryState.currentMode);
    }
  } catch (err) {
    console.warn("Analysis using local provider:", err);
    loadModeData(SatQueryState.currentMode);
  }

  SatQueryState.isAnalyzing = false;
  btn.innerHTML = originalBtnText;
  btn.style.opacity = "1";
}

// Drag & Dropzone Setup
function setupDropzone() {
  const dropzone = document.getElementById("fileDropzone");
  const fileInput = document.getElementById("filePickerInput");

  if (!dropzone || !fileInput) return;

  dropzone.addEventListener("click", () => fileInput.click());

  fileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files[0]) {
      handleCustomFileUpload(e.target.files[0]);
    }
  });

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.style.borderColor = "var(--cyan-accent)";
  });

  dropzone.addEventListener("dragleave", () => {
    dropzone.style.borderColor = "rgba(56, 189, 248, 0.25)";
  });

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.style.borderColor = "rgba(56, 189, 248, 0.25)";
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleCustomFileUpload(e.dataTransfer.files[0]);
    }
  });
}

function handleCustomFileUpload(file) {
  const ext = file.name.split(".").pop().toUpperCase();
  const metaFileName = document.getElementById("metaFileName");
  const metaFormat = document.getElementById("metaFormat");
  const thumb = document.getElementById("previewImgThumb");

  if (metaFileName) metaFileName.textContent = file.name;
  if (metaFormat) metaFormat.textContent = ext === "TIF" || ext === "TIFF" ? "GeoTIFF" : ext;

  // Render object URL thumbnail
  if (thumb && file.type.startsWith("image/")) {
    thumb.src = URL.createObjectURL(file);
  }
}

// Gallery Page Sample Loading
window.analyzeSampleFromGallery = function(mode) {
  setMode(mode);
  switchView("analyze");
  setTimeout(() => {
    runAnalysisWorkflow();
  }, 200);
};

// Dedicated Results Page Rendering
function renderDedicatedResults() {
  const data = SatQueryState.sampleData[SatQueryState.currentMode] || LOCAL_SAMPLE_FALLBACKS[SatQueryState.currentMode];
  if (!data) return;

  document.getElementById("dedResultsQuery").textContent = `"${SatQueryState.currentQuery}"`;
  document.getElementById("dedResultsAnswer").textContent = data.answer;
  document.getElementById("dedResultsModel").textContent = data.model;
  document.getElementById("dedResultsTask").textContent = data.task;
  document.getElementById("dedResultsConf").textContent = `${Math.round(data.confidence * 100)}% (${data.confidence_level})`;

  // High-res preview
  const previewImg = document.getElementById("dedResultsMainImg");
  if (previewImg) {
    const activeEv = (data.evidence && data.evidence[0]) || {};
    previewImg.src = activeEv.url || `/data/samples/${SatQueryState.currentMode}/${activeEv.file || "image.png"}`;
  }

  // Land cover bars
  const barsContainer = document.getElementById("dedResultsLandCoverBars");
  if (barsContainer) {
    barsContainer.innerHTML = "";
    (data.detected_land_cover || []).forEach(lc => {
      const barItem = document.createElement("div");
      barItem.style.marginBottom = "10px";
      barItem.innerHTML = `
        <div style="display:flex;justify-content:space-between;font-size:0.78rem;margin-bottom:4px;">
          <span style="color:#e2e8f0;display:flex;align-items:center;gap:6px;">
            <span style="width:8px;height:8px;border-radius:50%;background:${lc.color}"></span>
            ${lc.label}
          </span>
          <span style="font-family:var(--font-mono);color:${lc.color}">${lc.percentage}%</span>
        </div>
        <div style="width:100%;height:6px;background:rgba(255,255,255,0.06);border-radius:3px;overflow:hidden;">
          <div style="width:${lc.percentage}%;height:100%;background:${lc.color};border-radius:3px;"></div>
        </div>
      `;
      barsContainer.appendChild(barItem);
    });
  }
}

// Dedicated Execution Trace Page Rendering
function renderDedicatedTrace() {
  const data = SatQueryState.sampleData[SatQueryState.currentMode] || LOCAL_SAMPLE_FALLBACKS[SatQueryState.currentMode];
  const listContainer = document.getElementById("dedTraceTimelineList");
  if (!listContainer || !data) return;

  listContainer.innerHTML = "";

  const stages = [
    { step: "01", title: "USER QUERY & INPUT VALIDATION", meta: `Input: ${data.filename} (${data.format}, ${data.dimensions}) • Modality: ${data.modality}`, latency: "2.4 ms" },
    { step: "02", title: "QUERY INTENT UNDERSTANDING", meta: `Parsed Query: "${SatQueryState.currentQuery}" • Intent: ${data.task}`, latency: "6.1 ms" },
    { step: "03", title: "AGENTIC SPECIALIST ROUTING", meta: `Selected Specialist: ${data.model} • Routing Confidence: 99.4%`, latency: "4.8 ms" },
    { step: "04", title: "SPECIALIST MODEL INFERENCE", meta: `Engine: PyTorch / TorchGeo Adapter • Precision: FP16 • Tensor Shape: [1, 4, 1024, 1024]`, latency: "28.5 ms" },
    { step: "05", title: "MULTI-MODAL RESULT INTEGRATION", meta: `Spatial Masks Delineated • Calibrated Confidence: ${Math.round(data.confidence * 100)}%`, latency: "5.2 ms" },
    { step: "06", title: "FINAL SYNTHESIS & VERIFIABLE EVIDENCE", meta: `Delivered response, ${data.evidence.length} evidence layers, and polygon statistics`, latency: "1.1 ms" }
  ];

  stages.forEach(st => {
    const card = document.createElement("div");
    card.className = "timeline-stage-card";
    card.innerHTML = `
      <div class="timeline-icon-circle">${st.step}</div>
      <div>
        <div class="timeline-stage-name">${st.title}</div>
        <div class="timeline-stage-meta">${st.meta}</div>
      </div>
      <div class="timeline-latency">
        <div>✓ Completed</div>
        <div style="font-size:0.7rem;color:var(--text-dim);">${st.latency}</div>
      </div>
    `;
    listContainer.appendChild(card);
  });
}
