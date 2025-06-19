// === Backend endpoint for categorization ===
import { BACKEND_URL } from "./config.js";

// === UI Status Message Helper ===
function setStatus(message, isLoading = false) {
  const statusDiv = document.getElementById("status");
  statusDiv.textContent = message;
  statusDiv.className = isLoading ? "loading" : "";
}

// === Main button click handler ===
document.getElementById("organizeButton").addEventListener("click", async () => {
  setStatus("Scanning tabs");

  // Get all tabs from the current Chrome window
  chrome.tabs.query({ currentWindow: true }, async (tabs) => {
    const titles = tabs.map(tab => tab.title);
    setStatus("Organizing tabs", true);

    try {
      const response = await fetch(`${BACKEND_URL}/categorize`, {
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

      // Clear previous tab groups before organizing
      await ungroupAllTabs();

      // Group the browser tabs based on GPT's parsed result
      await organizeTabs(tabs, parsed);
      setStatus("✅ Tabs organized successfully!");
    } catch (err) {
      console.error("❌ Failed to organize tabs:", err);
      setStatus("❌ Failed to organize tabs.");
    }
  });
});

// === Ungroup all grouped tabs before re-grouping ===
async function ungroupAllTabs() {
  const allTabs = await chrome.tabs.query({ currentWindow: true });
  const groupIds = [...new Set(allTabs.map(tab => tab.groupId).filter(id => id !== -1))];

  for (const groupId of groupIds) {
    const groupedTabs = allTabs.filter(tab => tab.groupId === groupId).map(tab => tab.id);
    await chrome.tabs.ungroup(groupedTabs);
  }
}

// === Group the browser tabs using GPT categories ===
async function organizeTabs(tabs, groups) {
  for (const [groupName, titles] of Object.entries(groups)) {
    const tabIds = tabs
      .filter(tab => titles.includes(tab.title))
      .map(tab => tab.id);

    if (tabIds.length > 0) {
      const groupId = await chrome.tabs.group({ tabIds });
      await chrome.tabGroups.update(groupId, {
        title: groupName,
        color: getGroupColor(groupName),
        collapsed: true,
      });
    }
  }
}

// === Assign consistent colors to categories ===
function getGroupColor(name) {
  const colors = ["blue", "red", "yellow", "green", "pink", "purple", "cyan", "orange"];
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colors[Math.abs(hash) % colors.length];
}
