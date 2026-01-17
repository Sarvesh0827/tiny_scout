# Yutori Monitoring - Complete Guide

## ✅ What Was Implemented

A **complete scheduled monitoring system** using Yutori Scouting API that complements TinyScout's one-shot research mode.

## 🎯 Two Modes

### 1. Research Mode (Existing)
- **One-shot**: Run immediately
- **Flow**: Planner → TinyFish → Synthesizer
- **Output**: Single comprehensive report
- **Use case**: Deep dive into a topic right now

### 2. Monitor Mode (NEW)
- **Scheduled**: Runs on interval (30min - daily)
- **Flow**: Direct to Yutori → Periodic updates
- **Output**: Stream of updates with citations
- **Use case**: Stay informed about ongoing topics

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│  Streamlit UI (ui/monitoring.py)                │
│  - Create scouts                                │
│  - View updates                                 │
│  - Manage lifecycle                             │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│  Scout Manager (app/monitors/scout_manager.py)  │
│  - Business logic                               │
│  - Persistence                                  │
│  - Update processing                            │
└──────────────────┬──────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼────────┐   ┌────────▼────────┐
│ Yutori Client  │   │  SQLite DB      │
│ (API calls)    │   │  (persistence)  │
└────────────────┘   └─────────────────┘
```

## 📁 Files Created

```
app/monitors/
├── __init__.py              # Module exports
├── yutori_client.py         # Yutori API client
├── models.py                # SQLite models (Scout, ScoutUpdate)
└── scout_manager.py         # Business logic

ui/
└── monitoring.py            # Streamlit monitoring dashboard

cache/
└── scouts.db                # SQLite database (auto-created)
```

## 🚀 How to Use

### Step 1: Set API Key

Add to `.env`:
```bash
YUTORI_API_KEY=your_yutori_api_key_here
```

### Step 2: Start Monitoring Dashboard

```bash
./venv/bin/streamlit run ui/monitoring.py --server.port 9998
```

### Step 3: Create a Scout

1. **Click "➕ Create Scout"** in sidebar
2. **Enter monitoring query**:
   ```
   Monitor AI voice moderation industry for news, updates, and announcements
   ```
3. **Select frequency**: 30 min / 1 hour / 6 hours / 12 hours / Daily
4. **Enable "Enhance Query"** (recommended)
   - Adds monitoring-specific instructions
   - Focuses on news, announcements, policy changes, etc.
5. **Click "🚀 Start Monitoring"**

### Step 4: View Updates

1. **Switch to "📋 View Scouts"** in sidebar
2. **Click "🔄 Fetch Updates"** to check for new content
3. **Click "📊 View Updates"** to see all updates
4. **Each update shows**:
   - Headline
   - Timestamp
   - Summary
   - Citations (clickable links)
   - Full content (expandable)

## 🎨 UI Features

### Scout Card
- **Metrics**: Interval, Next Run, Update Count, Status
- **Actions**: Fetch Updates, View Updates, Delete

### Update Card
- **Headline**: Main topic
- **Timestamp**: When update was created
- **Summary**: Brief overview
- **Citations**: Source URLs with titles
- **Full Content**: Complete update text (expandable)

## 🔧 API Integration

### Create Scout
```python
from app.monitors import ScoutManager

manager = ScoutManager()

scout = await manager.create_scout(
    query="Monitor AI regulations in EU",
    interval_minutes=360,  # 6 hours
    enhance_query=True
)

print(f"Scout ID: {scout.id}")
print(f"Next run: {scout.next_run_timestamp}")
```

### Fetch Updates
```python
new_updates = await manager.fetch_updates(scout_id)

for update in new_updates:
    print(f"{update.headline}")
    print(f"  {update.summary}")
    print(f"  Citations: {update.citations}")
```

### Get All Scouts
```python
scouts = manager.get_all_scouts()

for scout in scouts:
    print(f"{scout.original_query} - {scout.output_interval}s")
```

## 📊 Database Schema

### `scouts` Table
- `id` - Yutori scout ID (primary key)
- `query` - Enhanced monitoring query
- `original_query` - User's original query
- `output_interval` - Seconds between updates
- `next_run_timestamp` - When next update is expected
- `last_cursor` - Pagination cursor
- `is_active` - Active/inactive status
- `metadata_json` - Full Yutori response

### `scout_updates` Table
- `id` - Update ID (primary key)
- `scout_id` - Foreign key to scout
- `timestamp` - When update was created
- `headline` - Update title
- `summary` - Brief summary
- `citations` - JSON array of sources
- `full_content` - Complete update text
- `metadata_json` - Full update data

## 🎯 Query Enhancement

When "Enhance Query" is enabled, the system adds monitoring-specific instructions:

**Original Query**:
```
Monitor AI voice moderation industry
```

**Enhanced Query**:
```
Monitor for: AI voice moderation industry

Focus on:
- latest news, announcements, updates
- policy changes, pricing changes
- product releases, acquisitions
- funding rounds, regulatory actions
- partnerships

Provide updates with clear citations and timestamps.
```

This improves update quality without restricting domains.

## 🔄 Update Flow

1. **User creates scout** → Yutori API creates task
2. **Yutori runs on schedule** → Generates updates
3. **User clicks "Fetch Updates"** → Pulls new updates via API
4. **Updates stored in DB** → Cursor tracks position
5. **UI displays updates** → With citations and timestamps

## 🆚 Research vs Monitor

| Feature | Research Mode | Monitor Mode |
|---------|--------------|--------------|
| **Trigger** | Manual (button click) | Scheduled (interval) |
| **Planner** | Yes (generates tasks) | No (direct query) |
| **TinyFish** | Yes (browses web) | No (Yutori handles) |
| **Output** | Single report | Stream of updates |
| **Citations** | Embedded in report | Per-update links |
| **Persistence** | Run logs only | Scouts + updates |
| **Best for** | Deep analysis | Ongoing monitoring |

## 💡 Use Cases

### Industry Monitoring
```
Monitor semiconductor industry for supply chain news, chip shortages, and manufacturing updates
```

### Competitor Tracking
```
Monitor OpenAI, Anthropic, and Google AI for product releases, pricing changes, and announcements
```

### Regulatory Compliance
```
Monitor EU AI Act and US AI regulations for policy changes, enforcement actions, and new guidelines
```

### Market Intelligence
```
Monitor venture capital funding in AI startups for Series A/B rounds, acquisitions, and valuations
```

## 🐛 Troubleshooting

### "YUTORI_API_KEY not found"
**Solution**: Add key to `.env` file

### "interval_seconds must be >= 1800"
**Solution**: Minimum frequency is 30 minutes (1800 seconds)

### "No updates yet"
**Solution**: Wait for first scheduled run or check `next_run_timestamp`

### Database locked error
**Solution**: Close other connections to `cache/scouts.db`

## 🚀 Next Steps

1. **Create your first scout** with a topic you want to monitor
2. **Wait for first update** (check `next_run_timestamp`)
3. **Fetch updates** to see what Yutori found
4. **Review citations** to verify sources
5. **Adjust frequency** based on update volume

## 🎉 You're Ready!

The Yutori monitoring system is **fully functional** and ready to use. Start monitoring any topic with scheduled updates and automatic citations!
