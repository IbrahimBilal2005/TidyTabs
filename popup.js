const BACKEND_URL = "https://tidytabs-ai.onrender.com/categorize";

function setStatus(message, isLoading = false) {
  const statusDiv = document.getElementById("status");
  statusDiv.textContent = message;
  statusDiv.className = isLoading ? "loading" : "";
}

document.getElementById("organizeButton").addEventListener("click", async () => {
  setStatus("Scanning tabs");

  chrome.tabs.query({ currentWindow: true }, async (tabs) => {
    const titles = tabs.map(tab => tab.title);
    setStatus("Organizing tabs", true);

    try {
      const response = await fetch(BACKEND_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ titles }),
      });

      const data = await response.json();

      let parsed;
      try {
        parsed = JSON.parse(data.categories);
      } catch (e) {
        console.error("❌ Failed to parse GPT response:\n", data.categories);
        setStatus("❌ GPT returned invalid format. Try again.");
        return;
      }

      await organizeTabs(tabs, parsed);
      setStatus("✅ Tabs organized successfully!");
    } catch (err) {
      console.error(err);
      setStatus("❌ Failed to organize tabs.");
    }
  });
});

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

function getGroupColor(name) {
  const colors = ["blue", "red", "yellow", "green", "pink", "purple", "cyan", "orange"];
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colors[Math.abs(hash) % colors.length];
}
