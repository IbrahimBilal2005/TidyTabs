const input = document.getElementById('main-input');
const results = document.getElementById('results');
const organize_btn = document.getElementById("organize-btn");
const search_btn = document.getElementById("search-btn")
let search_suggestion;

const menuTrigger = document.querySelector(".menu .link");
const submenuLinks = document.querySelectorAll(".submenu-link");

submenuLinks.forEach(link => {
  link.addEventListener("click", (e) => {
    e.preventDefault();
    menuTrigger.childNodes[0].nodeValue = link.textContent.trim(); 
  });
});

import { BACKEND_URL } from "./config.js";

function setStatus(message, isLoading = false, isError = false) {
  const statusDiv = results;
  statusDiv.style.display = "flex";
  statusDiv.style.justifyContent = "center";
  statusDiv.style.alignItems = "center";

  if (isLoading) {
    setPopupHeight(true);
    chrome.runtime.sendMessage({ type: 'EXPAND', expand: true });
    statusDiv.innerHTML = `
      <div style="display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 4px;">
        <span style="color: #cbd5e1; font-size: 0.75rem; border:none">${message}</span>
        <div class="progress">
          <div class="progress-value"></div>
        </div>
      </div>
    `;
  } else {
    statusDiv.innerHTML = `
    <div style="
      font-size: 0.8rem;
      color: ${isError ? '#f87171' : '#86efac'};
      text-align: center;
      padding: 6px 0;">
      ${message}
    </div>
  `;

  }

  setPopupHeight(false);
  chrome.runtime.sendMessage({ type: 'EXPAND', expand: false });
}


function setStatusGenerate(message, isLoading = false, isError = false) {
  setStatus(message, isLoading, isError);
}


// === Auto-Organize Tabs ===
organize_btn.addEventListener("click", async () => {
 
  console.log("Reached event handler for organize")
  setStatus("Scanning tabs…", true);

  // Get the last focused *normal* browser window
  const focusedWin = await chrome.windows.getLastFocused();
  let targetWin = focusedWin;

  if (focusedWin.type !== 'normal') {
    // Fallback: pick any normal window
    const normals = await chrome.windows.getAll({ windowTypes: ['normal'] });
    targetWin = normals.find(w => w.focused) || normals[0];
  }

  if (!targetWin) {
    setStatus("No normal browser window found.", false, true);
    return;
  }

  chrome.tabs.query({ windowId: targetWin.id }, async (tabs) => {
    const titles = tabs.map(tab => tab.title);
    setStatus("Organizing tabs…", true);

    try {
      const response = await fetch(`${BACKEND_URL}/categorize_local`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ titles }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error("Server error:", response.status, errorText);
        setStatus("Server error. Check console.", true);
        return;
      }

      const data = await response.json();
      const parsed = data.categories;

      await organizeTabs(tabs, parsed);
      setStatus("Tabs organized successfully!");
    } catch (err) {
      console.error(err);
      setStatus("Failed to organize tabs.", true);
    }
  });
});

// === Group Tabs Based on Categories ===
async function organizeTabs(tabs, groups) {

  const focusedWin = await chrome.windows.getLastFocused();
  let targetWin = focusedWin;

  if (focusedWin.type !== 'normal') {
    // Fallback: pick any normal window
    const normals = await chrome.windows.getAll({ windowTypes: ['normal'] });
    targetWin = normals.find(w => w.focused) || normals[0];
  }

  if (!targetWin) {
    setStatus("No normal browser window found.", false, true);
    return;
  }

  // chrome.tabs.query({ windowId: targetWin.id }, async (tabs) => {



  for (const [groupName, titles] of Object.entries(groups)) {
    const tabIds = tabs
      .filter(tab => titles.includes(tab.title))
      .map(tab => tab.id);

    if (tabIds.length > 0) {
      const groupId = await chrome.tabs.group({
      tabIds,
      createProperties: { windowId: targetWin.id }
    });
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
  const prompt = input.value.trim();
  setStatusGenerate("Generating tabs…", true);

  const response = await fetch(URL=`${BACKEND_URL}/generate_tabs`, {
    method: 'POST',
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });

  const focusedWin = await chrome.windows.getLastFocused();
  let targetWin = focusedWin;

  if (focusedWin.type !== 'normal') {
    // Fallback: pick any normal window
    const normals = await chrome.windows.getAll({ windowTypes: ['normal'] });
    targetWin = normals.find(w => w.focused) || normals[0];
  }

  if (!targetWin) {
    setStatus("No normal browser window found.", false, true);
    return;
  }


  const data = JSON.parse(await response.json());
  console.log(data)
  const group_name = await data.group_name
  console.log(group_name)
  const parsed = await data.tabs; // List of dicts, containing dicts that have title, url, description

  var newTabIds = [];

  for (const tab of parsed) {
    if (tab.url) {
      const newTab = await chrome.tabs.create({ url: tab.url, active: false});
      newTabIds.push(newTab.id);
    }
  }


  if (newTabIds.length > 0) {
    let groupId = await chrome.tabs.group({ tabIds: newTabIds, createProperties: { windowId: targetWin.id } });
    await chrome.tabGroups.update(groupId, {
      title: group_name,
      color: getGroupColor(group_name),
      collapsed: true
    });
  }

  setStatusGenerate(`Your tabs are saved in: ${group_name}`)
}

// === Bind Events ===
search_btn.addEventListener("click", generate_tabs);
input.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    generate_tabs();
  }
});


function cycle_suggestions() {
  const suggestions_lst = [
    "Help me plan a trip to NYC...",
    "Create a study guide for Calculus...",
    "Setup tabs for buying a new PC...",
    "Find ideas for a React project...",
    "Setup my research paper on LLMs..."
  ];

  const index = Math.floor(Math.random() * suggestions_lst.length);
  return suggestions_lst[index];
}

// Run once when the popup/extension DOM is ready
document.addEventListener("DOMContentLoaded", () => {
  if (!input) return;
  search_suggestion = cycle_suggestions();
  input.placeholder = search_suggestion;
});


// Expand popup when loading dialog pops up, keep it smaller otherwise
function setPopupHeight(expand = false) {
  const targetHeight = expand ? "300px" : "210px";
  document.documentElement.style.height = targetHeight;
  document.body.style.height = targetHeight;
}

