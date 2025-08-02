// popup.js

import { BACKEND_URL } from "./config.js";
var percent_loaded = 0;

// === UI Status Message Helper ===
function setStatus(message, isLoading = false) {
  const statusDiv = document.getElementById("status");
  statusDiv.textContent = message;
  statusDiv.className = isLoading ? "loading" : "";
}

function setStatusGenerate(message, isLoading = false) {
  const statusDiv = document.getElementById("status_generate");
  statusDiv.textContent = message;
  statusDiv.className = isLoading ? "loading" : "";
}

// === Organize Tabs Click Handler ===
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

      await organizeTabs(tabs, parsed);
      setStatus("✅ Tabs organized successfully!");
    } catch (err) {
      console.error(err);
      setStatus("❌ Failed to organize tabs.");
    }
  });
});

// === Group Tabs Based on Categories ===
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
        collapsed: true
      });
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

async function generate_tabs(){
  const prompt = document.getElementById("searchInput").value.trim();
  setStatusGenerate("Loading...")

  const response = await fetch(URL=`${BACKEND_URL}/generate_tabs`, {
    method: 'POST',
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });


  const data = JSON.parse(await response.json());
  const group_name = await data.group_name
  const parsed = await data.tabs; // List of dicts, containing dicts that have title, url, description

  var newTabIds = [];

  for (const tab of parsed) {
    if (tab.url) {
      const newTab = await chrome.tabs.create({ url: tab.url, active: false });
      newTabIds.push(newTab.id);
    }
  }


  if (newTabIds.length > 0) {
    let groupId = await chrome.tabs.group({ tabIds: newTabIds });
    await chrome.tabGroups.update(groupId, {
      title: group_name,
      color: getGroupColor(group_name),
      collapsed: true
    });
  }

  setStatusGenerate(`✅ Your tabs are saved in the tab group: ${group_name}`)

}


document.getElementById("searchBtn").addEventListener("click", generate_tabs);

document.getElementById("searchInput").addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    generate_tabs(event);
  }
});



