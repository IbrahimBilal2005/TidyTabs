// === Imports & Config ===
import { OPENAI_API_KEY } from './config.js';

// === Global Constants ===
const CHROME_TAB_COLORS = ["grey", "blue", "red", "yellow", "green", "pink", "purple", "cyan", "orange"];
const LOADING_MESSAGES = [
  "Waking up the AI...",
  "Reading your tabs 📚",
  "Analyzing topics 🔍",
  "Classifying categories 🧠",
  "Color coding like a pro 🎨"
];

// === DOM Helpers ===
function setStatus(message, isLoading = false) {
  const statusDiv = document.getElementById("status");
  statusDiv.textContent = message;
  statusDiv.className = isLoading ? "loading" : "";
}

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
        resolve();
      }
    }
    type();
  });
}

async function animateLoadingMessages(messages, cancelRef) {
  const element = document.getElementById("status");
  for (let i = 0; i < messages.length; i++) {
    if (cancelRef.cancelled) return;
    await typeWriterEffect(messages[i], "status", 40);
    await new Promise(res => setTimeout(res, 600));
  }
  if (!cancelRef.cancelled) {
    element.className = "loading";
    element.textContent = "Almost done";
  }
}

// === Prompt & AI ===
function buildPrompt(titles) {
  return `
You are given a list of browser tab titles.

Your job is to group them into **high-level categories** based on the **intent or purpose behind each tab**, not just the literal text.

### Rules:

1. Group tab titles into clear, general categories such as:
    - "Work", "Research", "Entertainment", "Education", "Shopping", "Social Media", "News", "Email", "Documentation", "Productivity", "Finance", "Travel", "Technology", "Weather", "Health", etc.
    - Do not create overly specific or uncommon category names.

2. **NEVER** create a category named "Search" or any variation like "Google Search", "Search Results", etc. Infer the **actual topic being searched** and group accordingly.
    - Example: "netflix release dates - Google Search" → "Entertainment"
    - Example: "weather in Toronto - Google Search" → "Weather"
    - Example: "best food near me - Google Search" → "Food"
    - Example: "Burger King - Google Search" → "Food" (not "Entertainment" or "Other")

4. If the title is exactly "New Tab", assign it to the category "New Tabs".

5. Assign **every tab** to a category. Before creating new categories, check if an existing one fits.

6. If a title could fit **multiple categories**, choose the one most directly related to its primary purpose.  
    - Example, "YouTube" may sometimes be used for education, but unless the video title is educational, categorize it as "Entertainment".
    - Example: "Health risks of fast food - Google Search" → "Health" (not "Food" or "Other")

Return your response as a **valid JSON object only** (no explanation or text before or after).  
- Keys: category names (strings)  
- Values: arrays of tab titles (strings, exactly as provided)

Here’s the list of tab titles:

${JSON.stringify(titles, null, 2)}

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
      model: "gpt-3.5-turbo",
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

// === Tab Grouping ===
function groupTabsByGPT(parsedGroups, tabs) {
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

// === Main Entry ===
document.getElementById("organizeButton").addEventListener("click", async () => {
  setStatus("Scanning tabs");

  chrome.tabs.query({ currentWindow: true }, async (tabs) => {
    const titles = tabs.map(tab => tab.title);
    const cancelRef = { cancelled: false };

    animateLoadingMessages(LOADING_MESSAGES, cancelRef);

    try {
      const prompt = buildPrompt(titles);
      const gptResponse = await callGPT(prompt);

      cancelRef.cancelled = true;

      let parsed;
      try {
        parsed = JSON.parse(gptResponse);
        console.log("Parsed GPT Categories:\n", parsed);
      } catch (e) {
        console.error("Could not parse GPT response as JSON:\n", gptResponse);
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