import { OPENAI_API_KEY } from './config.js';

function setStatus(message, isLoading = false) {
  const statusDiv = document.getElementById("status");
  statusDiv.textContent = message;
  statusDiv.className = isLoading ? "loading" : "";
}

function buildPrompt(titles) {
  return `
You are given a list of browser tab titles.

Your job is to group them into meaningful categories **based on what each tab is about**, not just what the title literally says.

Special rules:
- If a title includes "Google Search", classify it by the topic that was searched (e.g., "netflix - Google Search" → "Entertainment").
- If the title is exactly "New Tab", group it into a category called "New Tabs".
- Avoid a category called “Search” — do not group based on the presence of “Google Search”.

Return only a JSON object where:
- Each key is a category name (like "Entertainment", "Education", "Security", etc.)
- Each value is an array of tab titles from the list

Do not return anything else.

Here are the titles:
${titles.join('\n')}
`.trim();
}

async function callGPT(prompt) {
  const res = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${OPENAI_API_KEY}`
    },
    body: JSON.stringify({
      model: "gpt-4",
      messages: [
        { role: "system", content: "You are a helpful assistant that organizes browser tabs by purpose." },
        { role: "user", content: prompt }
      ],
      temperature: 0.4
    })
  });

  const result = await res.json();
  return result.choices[0].message.content;
}

function groupTabsByGPT(parsedGroups, tabs) {
  const CHROME_TAB_COLORS = ["grey", "blue", "red", "yellow", "green", "pink", "purple", "cyan", "orange"];
  let tempColors = [...CHROME_TAB_COLORS];

  for (const [category, gptTitles] of Object.entries(parsedGroups)) {
    const matchingTabIds = tabs
      .filter(tab => gptTitles.some(title =>
        tab.title.toLowerCase().includes(title.toLowerCase())
      ))
      .map(tab => tab.id);

    if (matchingTabIds.length > 0) {
      chrome.tabs.group({ tabIds: matchingTabIds }, (groupId) => {
        const color = tempColors.length > 0
          ? tempColors.splice(Math.floor(Math.random() * tempColors.length), 1)[0]
          : "grey";

        chrome.tabGroups.update(groupId, {
          title: category,
          color,
          collapsed: true
        });
      });
    }
  }
}

// --- Typewriter effect ---
function typeWriterEffect(message, targetId, speed = 40) {
  return new Promise((resolve) => {
    const element = document.getElementById(targetId);
    element.textContent = '';
    let i = 0;
    function type() {
      if (i < message.length) {
        element.textContent += message.charAt(i);
        i++;
        setTimeout(type, speed);
      } else {
        resolve(); // done typing
      }
    }
    type();
  });
}

// --- Loop through staged messages until cancelled ---
async function animateLoadingMessages(messages, cancelRef) {
  const element = document.getElementById("status");

  for (let i = 0; i < messages.length; i++) {
    if (cancelRef.cancelled) return;
    await typeWriterEffect(messages[i], "status", 40);
    await new Promise(res => setTimeout(res, 600));
  }

  // Final hold message with loading dots
  if (!cancelRef.cancelled) {
    element.className = "loading";
    element.textContent = "Almost done";
  }
}


document.getElementById("organizeButton").addEventListener("click", async () => {
  setStatus("Scanning tabs");

  chrome.tabs.query({ currentWindow: true }, async (tabs) => {
    const titles = tabs.map(tab => tab.title);

    const cancelRef = { cancelled: false };

    const loadingMessages = [
      "Waking up the AI...",
      "Reading your tabs 📚",
      "Analyzing topics 🔍",
      "Classifying categories 🧠",
      "Color coding like a pro 🎨"
    ];

    // Start staged animation
    animateLoadingMessages(loadingMessages, cancelRef);

    try {
      const prompt = buildPrompt(titles);
      const gptResponse = await callGPT(prompt);

      cancelRef.cancelled = true;

      let parsed;
      try {
        parsed = JSON.parse(gptResponse);
      } catch (e) {
        console.error("Could not parse GPT response as JSON:", gptResponse);
        setStatus("Hmm... couldn't organize tabs this time.");
        return;
      }

      groupTabsByGPT(parsed, tabs);
      setStatus("All tabs neatly grouped ✅");
    } catch (error) {
      cancelRef.cancelled = true;
      console.error("Error during GPT tab organization:", error);
      setStatus("Something went wrong. Try again in a moment.");
    }
  });
});
