# 🚀 Yutori Monitoring: Value & Usage Guide

## 💡 The Value Proposition
**"Why do I need this if I have TinyScout?"**

TinyScout is an **Active Researcher**. It's brilliant for "Tell me everything about X right now."
Yutori is a **Passive Monitor**. It solves "Tell me when X changes."

### 1. The "Time" Dimension
*   **Without Yutori:** Information is static. You get a snapshot of the world at the moment you click "Run". To see changes, you must manually run it again tomorrow.
*   **With Yutori:** Information is dynamic. The system watches 24/7. You build a historical timeline of updates, capturing the *delta* (what changed) rather than re-reading the same static "About Us" page.

### 2. Efficiency & Focus
*   **TinyScout (Deep Dive):** Uses expensive agents (Planner + Browsing + Analyzer + Synthesizer) to understand a topic deeply.
*   **Yutori (Radar):** Uses efficient scouting to scan for signals. It filters out the noise and only presents "News," "Updates," and "Announcements."

### 3. The "Intelligence Loop"
This integration creates a complete intelligence workflow:
1.  **Monitor (Yutori):** "Alert: Competitor X changed their pricing."
2.  **Research (TinyScout):** "Run deep analysis on how Competitor X's new pricing compares to ours."

---

## 📖 User Guide

### Prerequisite
Ensure your API key is set in `.env`:
```bash
YUTORI_API_KEY=yr_...
```

### Dashboard Location
**http://localhost:9998**

### Workflow

#### Phase 1: Setup (Do once)
1.  Click **"➕ Create Scout"** in the sidebar.
2.  **Query:** Be specific about *what events* you care about.
    *   *Example:* "Monitor FDA regulatory changes regarding AI in medical devices."
3.  **Frequency:** Select a schedule (e.g., Daily).
4.  **Enhance Query:** Keep enabled. We rewrite your query to specifically look for "news," "updates," and "announcements" to reduce noise.
5.  Click **Start**.

#### Phase 2: Consumption (Daily/Weekly)
1.  Click **"📋 View Scouts"**.
2.  Identify a scout with pending updates (check the "Updates" count).
3.  Click **"🔄 Fetch Updates"** to pull the latest data from the server.
4.  Click **"📊 View Updates"** to read.
    *   **Scan:** Read the AI-generated headlines.
    *   **Verify:** Click the citation links to read the source.
    *   **Deep Read:** Expand "Full Content" for the raw text.

#### Phase 3: Action
*   **Delete:** If a topic is no longer relevant, delete the scout to save resources.
*   **Refine:** If you get too much noise, delete and create a new scout with a tighter query (e.g., "Monitor ONLY press releases from Company X").

---

## 🔧 Technical Summary
*   **Persistence:** Your scouts and updates are saved in `cache/scouts.db`, so you don't lose them when you restart the app.
*   **Optimization:** We track a "cursor" for every scout, ensuring we never fetch (or pay for) the same update twice.
*   **Architecture:** This runs fully parallel to the main TinyScout agent. Monitoring will never block your main research tasks.
