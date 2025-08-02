// popup.js

import { BACKEND_URL } from "./config.js";

// === UI Status Message Helper ===
function setStatus(message, isLoading = false) {
  const statusDiv = document.getElementById("status");
  statusDiv.textContent = message;
  statusDiv.className = isLoading ? "loading" : "";
}

// === Organize Tabs Click Handler (Firefox only) ===
document.getElementById("organizeButton").addEventListener("click", async () => {
  setStatus("Scanning tabs");

  chrome.tabs.query({ currentWindow: true }, async (tabs) => {
    const titles = tabs.map(tab => tab.title);
    setStatus("Organizing tabs", true);

    try {
      const response = await fetch(`${BACKEND_URL}/categorize_local`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ titles }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error("❌ Server error:", response.status, errorText);
        setStatus("❌ Server error. Check console.");
        return;
      }

      const data = await response.json();
      const parsed = data.categories;

      await organizeTabsFirefox(tabs, parsed);
      setStatus("✅ Tabs organized successfully!");
    } catch (err) {
      console.error(err);
      setStatus("❌ Failed to organize tabs.");
    }
  });
});

// === Firefox-specific Tab Grouping ===
async function organizeTabsFirefox(tabs, groups) {
  for (const [groupName, titles] of Object.entries(groups)) {
    const tabIds = tabs
      .filter(tab => titles.includes(tab.title))
      .map(tab => tab.id);

    if (tabIds.length > 0) {
      // Firefox 138+ supports tabs.group
      await chrome.tabs.group({ tabIds });
    }
  }
}

// === Deterministic Color Assignment ===
function getGroupColor(name) {
  const colors = ["blue", "red", "yellow", "green", "pink", "purple", "cyan", "orange"];
  let hash = 0;

  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }

  return colors[Math.abs(hash) % colors.length];
}
