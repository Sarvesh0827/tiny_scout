# Ops Console Dashboard - Quick Start Guide

## ✅ What Was Created

A **standalone HTML dashboard** that provides full observability into TinyScout's research pipeline.

## 🚀 How to Use

### Option 1: Open Directly in Browser

```bash
# From the project directory
open ops_dashboard.html
```

Or simply double-click `ops_dashboard.html` in Finder.

### Option 2: Serve via Python HTTP Server

```bash
# Start a simple HTTP server
python3 -m http.server 8080

# Then open in browser:
# http://localhost:8080/ops_dashboard.html
```

### Option 3: View Specific Run

Add `?run_id=YOUR_RUN_ID` to the URL:

```
file:///path/to/ops_dashboard.html?run_id=07610c82-9e33-4d3e-a036-52cac6b91d3d
```

## 📊 Dashboard Features

### 1. **Stats Overview** (Top Cards)
- Run ID (first 8 chars)
- Status (success/failed/insufficient_evidence)
- Topic classification
- Total documents fetched
- Selected documents count

### 2. **Events Timeline** (Left Panel)
- Real-time event stream
- Filter by stage (planner/web_agent/retriever/synthesizer)
- Filter by level (info/warn/error/debug)
- Expandable payload for each event
- Color-coded by severity:
  - Blue: Info
  - Orange: Warning
  - Red: Error

### 3. **Run Details** (Right Panel)
- Research goal
- Models used (planner, analyzer, synthesizer)
- Retriever backend
- Error messages (if any)

### 4. **Documents Table** (Bottom Panel)
- All fetched documents
- Columns:
  - URL (clickable)
  - Retrieval method (tinyfish/http/cache)
  - Tier (A/B/C/unknown)
  - Content length
  - Relevance score
  - Selected status (✅/❌)

## 🎨 Visual Features

- **Gradient purple theme** (modern, professional)
- **Auto-refresh** every 10 seconds
- **Responsive design** (works on desktop/tablet)
- **Color-coded badges** for status/tier/method
- **Hover effects** on tables
- **Smooth scrolling** for long content

## 🔧 Prerequisites

1. **API Server Running**:
   ```bash
   ./venv/bin/python3 ops_api.py
   ```
   API must be running on `http://localhost:8000`

2. **CORS Enabled**: Already configured in `ops_api.py`

## 📝 Example Usage

### View Latest Run

1. Run a research query in Streamlit
2. Copy the Run ID from the console (e.g., `07610c82...`)
3. Open `ops_dashboard.html?run_id=07610c82-9e33-4d3e-a036-52cac6b91d3d`
4. Dashboard loads automatically

### Debug Failed Run

1. Filter events by level="error"
2. Check which stage failed
3. Expand payload to see details
4. Check documents table for 403/404 errors

### Monitor Live Run

1. Open dashboard
2. Auto-refresh shows new events every 10s
3. Watch status change from "running" → "success"

## 🆚 Dashboard vs Retool

| Feature | HTML Dashboard | Retool |
|---------|---------------|--------|
| **Setup Time** | Instant (just open file) | 30-60 min |
| **Cost** | Free | $10-50/month |
| **Customization** | Edit HTML/CSS/JS | Drag-and-drop UI |
| **Hosting** | Local file | Cloud-hosted |
| **Best For** | Quick debugging | Production ops |

## 🎯 When to Use Each

**Use HTML Dashboard** when:
- ✅ Quick local debugging
- ✅ Demo/presentation
- ✅ No internet connection
- ✅ Rapid iteration

**Use Retool** when:
- ✅ Team collaboration
- ✅ Production monitoring
- ✅ Advanced filtering/alerts
- ✅ Integration with other tools

## 🔗 API Endpoints Used

```javascript
GET /api/runs/{run_id}           // Run details + stats
GET /api/runs/{run_id}/events    // Event timeline
GET /api/runs/{run_id}/documents // Document table
```

## 🎨 Customization

### Change Theme Colors

Edit the CSS gradient in `ops_dashboard.html`:

```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

### Change Auto-Refresh Interval

Edit the JavaScript at the bottom:

```javascript
setInterval(loadData, 10000); // 10 seconds
```

### Add More Filters

Add new `<select>` elements in the filter bar:

```html
<select id="customFilter">
    <option value="">All</option>
    <option value="value1">Option 1</option>
</select>
```

## 🐛 Troubleshooting

### "Failed to load" errors

**Problem**: API not reachable  
**Solution**: Ensure `ops_api.py` is running on port 8000

```bash
./venv/bin/python3 ops_api.py
```

### CORS errors in console

**Problem**: Browser blocking cross-origin requests  
**Solution**: Already fixed in `ops_api.py` with CORS middleware

### No data showing

**Problem**: Invalid run_id  
**Solution**: Check run_id in URL matches a real run

```bash
curl http://localhost:8000/api/runs | jq
```

## 📱 Mobile Support

The dashboard is responsive and works on tablets, but for best experience use desktop (1280px+ width).

## 🚀 Next Steps

1. **Open the dashboard**: `open ops_dashboard.html`
2. **Run a test query** in Streamlit
3. **Copy the run_id** from the console
4. **View in dashboard**: Add `?run_id=YOUR_ID` to URL
5. **Debug issues** using events/documents panels

## 🎉 You're Ready!

The Ops Console is now fully functional. Use it to debug failed runs, monitor live research, and understand exactly what TinyScout is doing at every step.
