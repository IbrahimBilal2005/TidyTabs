const OPENAI_API_KEY = "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";

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

    const prompt = `
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


    try {
      const gptResponse = await fetch("https://api.openai.com/v1/chat/completions", {
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

      const result = await gptResponse.json();
      const content = result.choices[0].message.content;
      console.log("GPT Response:\n", content);

      let parsed;
      try {
        parsed = JSON.parse(content);
      } catch (e) {
        console.error("Could not parse GPT response as JSON:", content);
        setStatus("Hmm... couldn't organize tabs this time.");
        return;
      }

      const CHROME_TAB_COLORS = [
        "grey", "blue", "red", "yellow", "green",
        "pink", "purple", "cyan", "orange"
      ];

      let tempColors = [...CHROME_TAB_COLORS];

      for (const [category, gptTitles] of Object.entries(parsed)) {
        const matchingTabIds = tabs
          .filter(tab => gptTitles.some(gptTitle =>
            tab.title.toLowerCase().includes(gptTitle.toLowerCase())
          ))
          .map(tab => tab.id);

        if (matchingTabIds.length > 0) {
          chrome.tabs.group({ tabIds: matchingTabIds }, (groupId) => {
            let randomColor = "grey";
            if (tempColors.length > 0) {
              const index = Math.floor(Math.random() * tempColors.length);
              randomColor = tempColors[index];
              tempColors.splice(index, 1);
            }

            chrome.tabGroups.update(groupId, {
              title: category,
              color: randomColor,
              collapsed: true
            });
          });
        }
      }

      setStatus("All tabs neatly grouped ✅");

    } catch (error) {
      console.error("Error during GPT tab organization:", error);
      setStatus("Something went wrong. Try again in a moment.");
    }
  });
});
