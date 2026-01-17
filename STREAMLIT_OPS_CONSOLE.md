# 🎉 Streamlit Ops Console - LIVE!

## ✅ Successfully Created

A **beautiful Streamlit dashboard** that mimics the HTML design with enhanced interactivity!

## 🚀 Access the Dashboard

**URL**: http://localhost:9999

The dashboard is **already running** and ready to use!

## 🎨 Features (Matching HTML Design)

### Visual Design
- ✨ **Gradient purple background** (matching HTML)
- 📊 **Stats cards** with metrics
- 🎨 **Color-coded events** (blue/orange/red)
- 🏷️ **Styled badges** for tiers, methods, status
- 📱 **Responsive layout** (2-column grid)

### Interactive Features (Better than HTML!)
- 🔄 **Auto-refresh toggle** (10s intervals)
- 🎯 **Live filtering** (stage & level)
- 📝 **Expandable payloads** (click to view JSON)
- 🔍 **Sidebar controls** (run ID input, filters)
- 📊 **Pandas tables** (sortable, searchable)

### Data Panels
1. **Stats Overview** (5 metric cards)
   - Run ID, Status, Topic, Documents, Selected

2. **Events Timeline** (Left panel)
   - Filterable by stage/level
   - Color-coded by severity
   - Expandable JSON payloads
   - Timestamps

3. **Run Details** (Right panel)
   - Research goal
   - Models used
   - Backend info
   - Error messages

4. **Documents Table** (Full width)
   - URLs, methods, tiers
   - Content length, scores
   - Selection status
   - Styled badges

## 🆚 Streamlit vs HTML Dashboard

| Feature | HTML | Streamlit |
|---------|------|-----------|
| **Design** | ✅ Beautiful | ✅ Beautiful (same) |
| **Interactivity** | Basic | ⭐ Advanced |
| **Auto-refresh** | JavaScript | ✅ Native toggle |
| **Filtering** | Dropdown | ✅ Sidebar + live |
| **Data tables** | Static HTML | ✅ Pandas (sortable) |
| **Deployment** | File only | ✅ Web server |
| **Best for** | Quick view | Production ops |

## 📋 How to Use

### 1. View Current Run
The dashboard loads with the test run ID by default:
```
07610c82-9e33-4d3e-a036-52cac6b91d3d
```

### 2. View Different Run
1. Copy run ID from Streamlit research dashboard
2. Paste into sidebar "Run ID" input
3. Dashboard updates automatically

### 3. Filter Events
Use sidebar dropdowns:
- **Stage**: planner, web_agent, retriever, synthesizer
- **Level**: info, warn, error, debug

### 4. Enable Auto-Refresh
Check "Auto-refresh (10s)" in sidebar to monitor live runs

### 5. Expand Event Details
Click "📝 View Payload" to see full JSON data

## 🎯 Use Cases

### Debug Failed Run
1. Enter failed run ID
2. Filter by level="error"
3. Check which stage failed
4. Expand payload for details

### Monitor Live Run
1. Enable auto-refresh
2. Watch events appear in real-time
3. See status change from "running" → "success"

### Analyze Document Selection
1. Scroll to documents table
2. Check tier distribution
3. See which URLs were selected
4. Identify low-quality sources

## 🔧 Running Multiple Dashboards

You now have **2 dashboards** running:

1. **Research Dashboard** (Port 8510)
   - Main TinyScout interface
   - Run research queries
   - Generate reports

2. **Ops Console** (Port 9999)
   - Monitor runs
   - Debug issues
   - View detailed logs

## 🎨 Customization

The design is in `ui/ops_console.py`. You can customize:

### Colors
```python
# Change gradient
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

### Auto-refresh interval
```python
time.sleep(10)  # Change to desired seconds
```

### Stats cards
```python
# Add more metrics in the columns section
col1, col2, col3, col4, col5, col6 = st.columns(6)
```

## 🚀 Next Steps

1. **Run a research query** in main dashboard (port 8510)
2. **Copy the run ID** from console output
3. **Paste into ops console** (port 9999)
4. **Watch the pipeline** in real-time!

## 📊 API Requirements

Make sure the API is running:
```bash
./venv/bin/python3 ops_api.py
```

API must be on `http://localhost:8000`

## 🎉 You're All Set!

Open **http://localhost:9999** and enjoy your beautiful ops console! 🚀
