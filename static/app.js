const messagesEl = document.getElementById("messages");
const productGridEl = document.getElementById("productGrid");
const sourcesEl = document.getElementById("sources");
const resultCountEl = document.getElementById("resultCount");
const statusBadgeEl = document.getElementById("statusBadge");
const chatFormEl = document.getElementById("chatForm");
const messageInputEl = document.getElementById("messageInput");
const imageInputEl = document.getElementById("imageInput");
const catalogSelectEl = document.getElementById("catalogSelect");
const catalogCsvInputEl = document.getElementById("catalogCsvInput");
const imagePreviewEl = document.getElementById("imagePreview");
const previewImgEl = document.getElementById("previewImg");
const clearImageBtnEl = document.getElementById("clearImageBtn");
const promptChipEls = document.querySelectorAll(".prompt-chip");
const sendButtonEl = document.getElementById("sendButton");

let conversationId = self.crypto?.randomUUID?.()
  ?? (Date.now().toString(36) + Math.random().toString(36).slice(2));
let selectedImageB64 = null;
let selectedCatalog = "all";
let isSubmitting = false;
let autoScrollFrameId = null;
let autoScrollStoppedByUser = false;
let isProgrammaticScroll = false;

promptChipEls.forEach((button) => {
  button.addEventListener("click", () => {
    messageInputEl.value = button.dataset.prompt || "";
    messageInputEl.focus();
  });
});

messageInputEl.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    chatFormEl.requestSubmit();
  }
});

imageInputEl.addEventListener("change", async (event) => {
  const [file] = event.target.files || [];
  if (!file) {
    return;
  }

  selectedImageB64 = await fileToBase64(file);
  previewImgEl.src = URL.createObjectURL(file);
  imagePreviewEl.classList.remove("hidden");
});

clearImageBtnEl.addEventListener("click", () => {
  selectedImageB64 = null;
  imageInputEl.value = "";
  previewImgEl.src = "";
  imagePreviewEl.classList.add("hidden");
});

if (catalogSelectEl) {
  catalogSelectEl.addEventListener("change", () => {
    const value = catalogSelectEl.value;
    if (value === "__upload_csv__") {
      catalogSelectEl.value = selectedCatalog;
      catalogCsvInputEl?.click();
      return;
    }
    selectedCatalog = value || "all";
  });
}

if (catalogCsvInputEl) {
  catalogCsvInputEl.addEventListener("change", async (event) => {
    const [file] = event.target.files || [];
    if (!file) return;

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("name", file.name.replace(/\.csv$/i, ""));
      const response = await fetch("/api/catalogs/upload", {
        method: "POST",
        body: formData,
      });
      if (!response.ok) {
        throw new Error(`Upload failed: ${response.status}`);
      }
      const data = await response.json();
      await loadCatalogs(data.catalog?.slug || "all");
      appendMessage("assistant", `Uploaded catalog "${data.catalog?.name || "Imported Catalog"}" with ${data.count || 0} items.`, { useMarkdown: false });
    } catch (error) {
      console.error(error);
      appendMessage("assistant", "CSV upload failed. Make sure the file is valid and try again.", { useMarkdown: false });
    } finally {
      catalogCsvInputEl.value = "";
    }
  });
}

chatFormEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (isSubmitting) {
    return;
  }

  const message = messageInputEl.value.trim();
  if (!message && !selectedImageB64) {
    return;
  }

  isSubmitting = true;
  sendButtonEl.disabled = true;
  appendMessage("user", message || "Find products that match this image.");
  const assistantMessage = appendThinkingMessage();
  setStatus("Thinking...");
  messageInputEl.value = "";

  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 45000);

    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        image_b64: selectedImageB64,
        conversation_id: conversationId,
        catalog: selectedCatalog,
      }),
      signal: controller.signal,
    });
    clearTimeout(timeout);

    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }

    const data = await response.json();
    conversationId = data.conversation_id;
    renderSources(data.sources || []);
    const newProducts = data.products || [];
    if (newProducts.length > 0) {
      renderProducts(newProducts);
    }
    await streamAssistantReply(assistantMessage.bubbleEl, data.reply || "");
    selectedImageB64 = null;
    imageInputEl.value = "";
    previewImgEl.src = "";
    imagePreviewEl.classList.add("hidden");
    setStatus("Ready");
  } catch (error) {
    assistantMessage.bubbleEl.classList.remove("thinking-bubble");
    assistantMessage.bubbleEl.innerHTML = "";
    assistantMessage.bubbleEl.textContent =
      "I hit an error while reaching the backend. Check that the API is running and your OpenAI key is configured.";
    setStatus("Error");
    console.error(error);
  } finally {
    isSubmitting = false;
    sendButtonEl.disabled = false;
  }
});

function appendThinkingMessage() {
  const article = document.createElement("article");
  article.className = "message assistant";
  article.innerHTML = `<div class="avatar">AI</div><div class="bubble thinking-bubble"><span class="thinking-dot"></span><span class="thinking-dot"></span><span class="thinking-dot"></span></div>`;
  messagesEl.appendChild(article);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return { articleEl: article, bubbleEl: article.querySelector(".bubble") };
}

async function loadCatalogs(preferred = "all") {
  if (!catalogSelectEl) return;
  try {
    const response = await fetch("/api/catalogs");
    if (!response.ok) {
      return;
    }
    const data = await response.json();
    const catalogs = Array.isArray(data.catalogs) ? data.catalogs : [];
    catalogSelectEl.innerHTML = "";
    for (const catalog of catalogs) {
      const option = document.createElement("option");
      option.value = catalog.slug;
      option.textContent = catalog.name;
      catalogSelectEl.appendChild(option);
    }

    const uploadOption = document.createElement("option");
    uploadOption.value = "__upload_csv__";
    uploadOption.textContent = "Upload CSV...";
    catalogSelectEl.appendChild(uploadOption);

    const available = catalogs.map((item) => item.slug);
    selectedCatalog = available.includes(preferred) ? preferred : (available.includes(selectedCatalog) ? selectedCatalog : "all");
    catalogSelectEl.value = selectedCatalog;
  } catch (error) {
    console.warn("Failed to load catalogs:", error);
  }
}

function appendMessage(role, text, options = {}) {
  const { isThinking = false, useMarkdown = true } = options;
  const article = document.createElement("article");
  article.className = `message ${role}`;
  article.innerHTML = `
    <div class="avatar">${role === "assistant" ? "AI" : "You"}</div>
    <div class="bubble"></div>
  `;

  const bubble = article.querySelector(".bubble");
  if (isThinking) {
    bubble.classList.add("thinking-bubble");
  }
  if (useMarkdown) {
    bubble.innerHTML = renderMarkdown(text);
  } else {
    bubble.textContent = text;
  }
  messagesEl.appendChild(article);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return { articleEl: article, bubbleEl: bubble };
}

async function streamAssistantReply(bubbleEl, text) {
  bubbleEl.classList.remove("thinking-bubble");
  bubbleEl.innerHTML = "";
  bubbleEl.textContent = "";
  const normalized = cleanAgentText(String(text || ""));
  const chunkSize = 3;

  for (let i = 0; i < normalized.length; i += chunkSize) {
    bubbleEl.textContent += normalized.slice(i, i + chunkSize);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    await sleep(12);
  }
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function sleep(ms) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

function renderSources(_sources) {
  sourcesEl.innerHTML = "";
}

function renderProducts(products) {
  stopProductsAutoScroll();
  autoScrollStoppedByUser = false;
  resultCountEl.textContent = `${products.length} item${products.length === 1 ? "" : "s"}`;

  if (!products.length) {
    productGridEl.className = "product-grid";
    productGridEl.innerHTML = "";
    return;
  }

  productGridEl.className = "product-grid";
  productGridEl.innerHTML = "";

  for (const product of products) {
    const card = document.createElement("article");
    card.className = "product-card";
    const tags = [product.category, ...(product.activity || []).slice(0, 2)];
    card.innerHTML = `
      <img src="${product.image_path}" alt="${product.name}" />
      <div>
        <h3>${product.name}</h3>
        <p class="product-meta">${product.brand} · ${product.color} · ${product.fit}</p>
        <p class="product-description">${product.description}</p>
        <p class="product-price">$${Number(product.price).toFixed(2)}</p>
        <div class="tag-row">
          ${tags.map((tag) => `<span class="tag">${tag}</span>`).join("")}
        </div>
      </div>
    `;
    productGridEl.appendChild(card);
  }

  // Defer so the browser has time to lay out the cards before measuring overflow.
  requestAnimationFrame(() => requestAnimationFrame(startProductsAutoScroll));
}

function setStatus(text) {
  if (statusBadgeEl) statusBadgeEl.textContent = text;
}

function startProductsAutoScroll() {
  autoScrollStoppedByUser = false;
  isProgrammaticScroll = true;

  const hasOverflow = productGridEl.scrollWidth > productGridEl.clientWidth + 2;
  if (!hasOverflow) {
    isProgrammaticScroll = false;
    return;
  }

  if (!productGridEl.dataset.autoScrollListenersBound) {
    productGridEl.addEventListener("wheel", () => { autoScrollStoppedByUser = true; stopProductsAutoScroll(); }, { passive: true });
    productGridEl.addEventListener("touchstart", () => { autoScrollStoppedByUser = true; stopProductsAutoScroll(); }, { passive: true });
    productGridEl.addEventListener("pointerdown", () => { autoScrollStoppedByUser = true; stopProductsAutoScroll(); }, { passive: true });
    productGridEl.dataset.autoScrollListenersBound = "true";
  }

  const speed = 0.4;
  const step = () => {
    if (autoScrollStoppedByUser) {
      isProgrammaticScroll = false;
      stopProductsAutoScroll();
      return;
    }

    const maxLeft = Math.max(0, productGridEl.scrollWidth - productGridEl.clientWidth);
    if (maxLeft <= 1) {
      isProgrammaticScroll = false;
      stopProductsAutoScroll();
      return;
    }

    if (productGridEl.scrollLeft >= maxLeft - 1) {
      productGridEl.scrollLeft = 0;
    } else {
      productGridEl.scrollLeft += speed;
    }
    autoScrollFrameId = requestAnimationFrame(step);
  };

  autoScrollFrameId = requestAnimationFrame(step);
}

function stopProductsAutoScroll() {
  if (autoScrollFrameId) {
    cancelAnimationFrame(autoScrollFrameId);
    autoScrollFrameId = null;
  }
  isProgrammaticScroll = false;
}

function renderMarkdown(text) {
  return text
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*([^*]+?)\*/g, "<em>$1</em>")
    .replace(/^#{1,3} (.+)$/gm, "<strong>$1</strong>")
    .replace(/\n/g, "<br>");
}

function cleanAgentText(text) {
  return text
    .replace(/^#{1,6}\s*/gm, "")
    .replace(/\*\*(.+?)\*\*/g, "$1")
    .replace(/\*([^*]+?)\*/g, "$1")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result || "");
      resolve(result.split(",")[1] || "");
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

// Typewriter header effect
(function startTypewriter() {
  const el = document.querySelector(".panel-header h2");
  if (!el) return;

  const phrases = [
    "Palona",
    "Shop smarter.",
    "Find your fit.",
    "Ask anything.",
    "Your style guide.",
    "Palona",
  ];

  let phraseIdx = 0;
  let charIdx = 0;
  let deleting = false;
  const TYPE_SPEED = 60;
  const DELETE_SPEED = 30;
  const PAUSE = 1800;

  function tick() {
    const current = phrases[phraseIdx];
    if (!deleting) {
      charIdx += 1;
      el.textContent = current.slice(0, charIdx);
      if (charIdx === current.length) {
        deleting = true;
        setTimeout(tick, PAUSE);
        return;
      }
    } else {
      charIdx -= 1;
      el.textContent = current.slice(0, charIdx);
      if (charIdx === 0) {
        deleting = false;
        phraseIdx = (phraseIdx + 1) % phrases.length;
      }
    }
    setTimeout(tick, deleting ? DELETE_SPEED : TYPE_SPEED);
  }

  tick();
})();

const particleOptions = {
  background: { color: "transparent" },
  // Keep particles in the dedicated #particles layer.
  fullScreen: { enable: false },
  fpsLimit: 60,
  interactivity: {
    events: {
      onClick: { enable: true, mode: "push" },
      onHover: { enable: true, mode: "repulse" },
      resize: { enable: true }
    },
    modes: {
      push: { quantity: 5 },
      repulse: { distance: 110, duration: 0.25 }
    }
  },
  particles: {
    color: { value: ["#7c9cff", "#9e7bff", "#53d6b8"] },
    links: {
      color: "#7c9cff",
      distance: 120,
      enable: true,
      opacity: 0.18,
      width: 1
    },
    move: {
      direction: "none",
      enable: true,
      outModes: { default: "bounce" },
      random: false,
      speed: 1.1,
      straight: false
    },
    number: {
      density: { enable: true, area: 900 },
      value: 60
    },
    opacity: { value: 0.35 },
    shape: { type: "circle" },
    size: { value: { min: 1, max: 4 } }
  },
  detectRetina: true
};

function startCanvasParticlesFallback() {
  const host = document.getElementById("particles");
  if (!host) return;
  if (host.querySelector("canvas")) return;

  const canvas = document.createElement("canvas");
  canvas.style.width = "100%";
  canvas.style.height = "100%";
  canvas.style.display = "block";
  canvas.style.pointerEvents = "none";
  host.appendChild(canvas);

  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const colors = ["#7c9cff", "#9e7bff", "#53d6b8"];
  const particles = [];
  const baseCount = 70;
  const maxLinkDistance = 130;

  const resize = () => {
    const dpr = Math.max(1, window.devicePixelRatio || 1);
    const w = host.clientWidth || window.innerWidth;
    const h = host.clientHeight || window.innerHeight;
    canvas.width = Math.floor(w * dpr);
    canvas.height = Math.floor(h * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  };

  const spawn = (x = Math.random() * (host.clientWidth || window.innerWidth), y = Math.random() * (host.clientHeight || window.innerHeight)) => ({
    x,
    y,
    vx: (Math.random() - 0.5) * 1.2,
    vy: (Math.random() - 0.5) * 1.2,
    r: 1 + Math.random() * 3,
    color: colors[Math.floor(Math.random() * colors.length)],
    alpha: 0.35 + Math.random() * 0.45
  });

  for (let i = 0; i < baseCount; i += 1) particles.push(spawn());

  const tick = () => {
    const w = host.clientWidth || window.innerWidth;
    const h = host.clientHeight || window.innerHeight;
    ctx.clearRect(0, 0, w, h);

    for (const p of particles) {
      p.x += p.vx;
      p.y += p.vy;

      if (p.x < 0 || p.x > w) p.vx *= -1;
      if (p.y < 0 || p.y > h) p.vy *= -1;

      ctx.globalAlpha = p.alpha;
      ctx.fillStyle = p.color;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fill();
    }

    // Draw subtle geometric links between nearby particles.
    for (let i = 0; i < particles.length; i += 1) {
      for (let j = i + 1; j < particles.length; j += 1) {
        const a = particles[i];
        const b = particles[j];
        const dx = a.x - b.x;
        const dy = a.y - b.y;
        const distance = Math.hypot(dx, dy);

        if (distance > maxLinkDistance) continue;
        const alpha = (1 - distance / maxLinkDistance) * 0.18;
        if (alpha <= 0) continue;

        ctx.globalAlpha = alpha;
        ctx.strokeStyle = "#7c9cff";
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.stroke();
      }
    }

    ctx.globalAlpha = 1;
    requestAnimationFrame(tick);
  };

  window.addEventListener("resize", resize);
  window.addEventListener("click", (event) => {
    for (let i = 0; i < 8; i += 1) {
      particles.push(spawn(event.clientX, event.clientY));
    }
    if (particles.length > 200) particles.splice(0, particles.length - 200);
  });

  resize();
  requestAnimationFrame(tick);
}

if (typeof tsParticles !== "undefined") {
  tsParticles
    .load("particles", particleOptions)
    .then(() => {
      const host = document.getElementById("particles");
      if (!host?.querySelector("canvas")) {
        console.warn("tsParticles loaded but no canvas mounted; using fallback.");
        startCanvasParticlesFallback();
      }
    })
    .catch((error) => {
      console.warn("tsParticles failed to load:", error);
      startCanvasParticlesFallback();
    });
} else {
  console.warn("tsParticles global is missing.");
  startCanvasParticlesFallback();
}

loadCatalogs();
