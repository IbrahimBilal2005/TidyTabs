// content.js: Injects the extension UI into the current webpage/DOM
(() => {
  if (window.__tidytabs_content_injected__) return;
  window.__tidytabs_content_injected__ = true;

  let overlayOpen = false;
  let overlayEl = null;
  let shadow = null;

  // --- expanded vs collapsed ---
  function setPopupHeight(expand = false) {
    const targetHeight = expand ? "210px" : "180px"; 
    if (overlayEl) {
      overlayEl.style.height = targetHeight;
    }
  }

  function createOverlay() {
    // Host element pinned to viewport
    overlayEl = document.createElement("div");
    overlayEl.id = "tidytabs-overlay-host";
    overlayEl.style.cssText = [
      "position: fixed",
      "top: 16px",
      "right: 16px",
      "width: 420px",
      "height: 180px", 
      "z-index: 2147483647",
      "display: flex",
      "align-items: stretch",
      "justify-content: stretch",
      "pointer-events: none"
    ].join(";");

    document.documentElement.appendChild(overlayEl);
    shadow = overlayEl.attachShadow({ mode: "open" });

    // Shadow DOM wrapper
    const wrapper = document.createElement("div");
    wrapper.style.cssText = [
      "all: initial",
      "position: relative",
      "width: 100%",
      "height: 100%",
      "pointer-events: auto",
      "border-radius: 12px",
      "overflow: hidden",
      "box-shadow: 0 12px 34px rgba(0,0,0,0.35)",
      "background: #1f2937"
    ].join(";");

    // Close button
    const header = document.createElement("div");
    header.style.cssText = [
      "position: absolute",
      "top: 6px",
      "right: 6px",
      "z-index: 2",
      "display: flex",
      "gap: 6px"
    ].join(";");

    const closeBtn = document.createElement("button");
    closeBtn.textContent = "×";
    closeBtn.title = "Close";
    closeBtn.style.cssText = [
      "all: initial",
      "cursor: pointer",
      "font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif",
      "font-size: 16px",
      "line-height: 1",
      "padding: 6px 10px",
      "color: #eee",
      "background: #2b2b2b",
      "border-radius: 10px",
      "border: 1px solid #3a3a3a",
      "box-shadow: 0 1px 2px rgba(0,0,0,0.25)"
    ].join(";");
    closeBtn.addEventListener("click", destroyOverlay);

    header.appendChild(closeBtn);
    wrapper.appendChild(header);

    // Iframe that loads extension UI
    const iframe = document.createElement("iframe");
    iframe.src = chrome.runtime.getURL("popup.html");
    iframe.title = "TidyTabs";
    iframe.style.cssText = [
      "position: absolute",
      "inset: 0",
      "width: 100%",
      "height: 100%",
      "border: 0",
      "background: transparent"
    ].join(";");

    wrapper.appendChild(iframe);
    shadow.appendChild(wrapper);

    // ESC closes overlay
    window.addEventListener("keydown", escListener, true);

    // Click outside to close
    const backdrop = document.createElement("div");
    backdrop.style.cssText = [
      "position: fixed",
      "inset: 0",
      "pointer-events: auto",
      "background: transparent"
    ].join(";");
    backdrop.addEventListener("mousedown", (e) => {
      const rect = overlayEl.getBoundingClientRect();
      if (e.clientX < rect.left || e.clientY > rect.bottom) {
        destroyOverlay();
      }
    });
    document.documentElement.insertBefore(backdrop, overlayEl);
    overlayEl.__backdrop = backdrop;

    overlayOpen = true;
  }

  function destroyOverlay() {
    if (!overlayEl) return;
    window.removeEventListener("keydown", escListener, true);
    overlayEl.__backdrop?.remove();
    overlayEl.remove();
    overlayEl = null;
    shadow = null;
    overlayOpen = false;
  }

  function escListener(e) {
    if (e.key === "Escape") {
      destroyOverlay();
      e.stopPropagation();
    }
  }

  function toggleOverlay() {
    if (overlayOpen) destroyOverlay();
    else createOverlay();
  }

  // Message from background.js to toggle
  chrome.runtime.onMessage.addListener((msg) => {
    if (msg?.type === "TIDYTABS_TOGGLE") {
      toggleOverlay();
    }
  });

  // Message from iframe (popup.js) to resize
  window.addEventListener("message", (event) => {
    if (event.data?.type === "TIDYTABS_SET_HEIGHT") {
      setPopupHeight(event.data.expand);
    }
  });

  window.__tidytabs_toggle__ = toggleOverlay;
})();
