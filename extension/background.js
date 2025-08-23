// background.js
let uiWindowId = null;

async function openOrFocusUI() {
    if (uiWindowId !== null) {
        try {
            const win = await chrome.windows.get(uiWindowId);
            // If we got here, the window still exists -> focus it.
            await chrome.windows.update(uiWindowId, { focused: true, drawAttention: true });
            return;
        } catch {
            uiWindowId = null;
        }
    }

    const [wind] = await chrome.windows.getAll({ windowTypes: ["normal"], populate: false });
    focusListenerAttached = false;

    // Create a fresh popup window with your extension page
    const win = await chrome.windows.create({
        url: chrome.runtime.getURL("popup.html"), // rename if you like
        type: "popup",
        width: 420,
        height: 180,
        focused: true,
        left: wind.left + wind.width - 420 - 16,
        top: wind.top + 75
    });

    uiWindowId = win.id;
    panelWindowId = win.id;

    if (!focusListenerAttached) {
        chrome.windows.onFocusChanged.addListener(async (focusedId) => {
            // Ignore transient "no window" state
            if (focusedId === chrome.windows.WINDOW_ID_NONE) return;
            // If our panel is open and some other window gained focus -> close panel
            if (panelWindowId !== null && focusedId !== panelWindowId) {
                try { await chrome.windows.remove(panelWindowId); } catch { }
                panelWindowId = null;
            }
        });
        focusListenerAttached = true;
    }


    chrome.runtime.onMessage.addListener((msg) => {
        if (!panelWindowId) return;

        if (msg?.type === "EXPAND" && msg?.expand === true) {
            const height = 180; // clamp a bit
            chrome.windows.update(panelWindowId, { height }).catch(() => { });
        }

        if (msg?.type === "EXPAND" && msg?.expand === false) {
            const height = 240; // clamp a bit
            chrome.windows.update(panelWindowId, { height }).catch(() => { });
        }
    });
}


// Reset the cached window id if the user closes it
chrome.windows.onRemoved.addListener((closedId) => {
    if (closedId === uiWindowId) {
        uiWindowId = null;
    }
});

// Click on toolbar icon -> open/focus window
chrome.action.onClicked.addListener(async () => {
    await openOrFocusUI();
});
