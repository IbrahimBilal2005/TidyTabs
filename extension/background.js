chrome.action.onClicked.addListener(async (tab) => {
  try {
    // Try to toggle overlay directly
    await chrome.tabs.sendMessage(tab.id, { type: "TIDYTABS_TOGGLE" });
  } catch (err) {
    console.warn("Direct inject failed, falling back:", err);

    try {
      // Try injecting content.js
      await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        files: ["content.js"]
      });

      await chrome.tabs.sendMessage(tab.id, { type: "TIDYTABS_TOGGLE" });
    } catch (injectErr) {
      console.warn("Injection also failed, opening fallback tab:", injectErr);

      // Fallback, open a safe page (can be google.com or your bundled test.html)
      chrome.tabs.create({ url: "https://google.com" }, (newTab) => {
        chrome.tabs.onUpdated.addListener(function listener(tabId, info) {
          if (tabId === newTab.id && info.status === "complete") {
            chrome.tabs.onUpdated.removeListener(listener);

            chrome.scripting.executeScript({
              target: { tabId: newTab.id },
              files: ["content.js"]
            }, () => {
              chrome.tabs.sendMessage(newTab.id, { type: "TIDYTABS_TOGGLE" });
            });
          }
        });
      });
    }
  }
});
