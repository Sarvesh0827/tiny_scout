# Ops Console - Retool Integration Guide

## Overview

The Ops Console provides full observability into TinyScout's research pipeline through structured logging and a Retool dashboard.

## Architecture

```
Streamlit UI → RunLogger → SQLite Database → FastAPI → Retool Dashboard
                    ↓
              Console Output
```

## Components

### 1. Database (SQLite)

**Location**: `cache/ops_console.db`

**Tables**:
- `runs` - Research run metadata
- `run_events` - Structured event logs
- `documents` - Fetched and processed documents

### 2. RunLogger

Dual-output logging:
- **Console**: Real-time terminal output (for dev)
- **Database**: Structured data (for Retool)

### 3. FastAPI Backend

**Port**: 8000  
**Base URL**: `http://localhost:8000`

**Endpoints**:
```
GET /api/runs?limit=50&status=success
GET /api/runs/{run_id}
GET /api/runs/{run_id}/events?stage=planner&level=error
GET /api/runs/{run_id}/documents?selected_only=true
GET /health
```

### 4. Retool Dashboard

Three screens for complete observability.

## Setup Instructions

### Step 1: Install Dependencies

```bash
./venv/bin/pip install sqlalchemy
```

### Step 2: Start FastAPI Backend

```bash
./venv/bin/python3 ops_api.py
```

Or with uvicorn:
```bash
./venv/bin/uvicorn ops_api:app --reload --port 8000
```

### Step 3: Verify API

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/runs
```

### Step 4: Configure Retool

1. **Create New Retool App**: "TinyScout Ops Console"

2. **Add REST API Resource**:
   - Name: `TinyScoutAPI`
   - Base URL: `http://localhost:8000`
   - Headers: None needed

3. **Create 3 Pages**:

## Retool Screen Designs

### Screen A: Runs List

**Components**:
- **Table**: `runsTable`
  - Data Source: `GET /api/runs?limit=50`
  - Columns:
    - `created_at` (DateTime)
    - `research_goal` (Text, 300px wide)
    - `status` (Badge: green=success, red=failed, yellow=insufficient_evidence)
    - `topic` (Text)
    - `retriever_backend` (Badge)
    - `planner_model` (Text, small)
    - `doc_count` (Number)
    - `selected_count` (Number)
  - Row Click: Set `selectedRunId` state variable
  - Refresh: Every 30s

- **Filter Dropdown**: Status filter
  - Options: All, Success, Failed, Insufficient Evidence
  - On Change: Reload table with `?status={{filter.value}}`

### Screen B: Run Detail

**Left Panel** (60% width):
- **Text Area**: Final Report
  - Data: `{{runDetail.data.final_report}}`
  - Read-only
  - Markdown rendering

**Right Panel** (40% width):
- **Timeline Component**: Run Events
  - Data Source: `GET /api/runs/{{selectedRunId}}/events`
  - Group by: `stage`
  - Color by: `level` (info=blue, warn=yellow, error=red)
  - Show: `ts`, `message`, `payload` (expandable)

- **Filters**:
  - Stage dropdown (planner, retriever, web_agent, analyzer, synthesizer)
  - Level dropdown (info, warn, error, debug)

### Screen C: Documents Extracted

**Components**:
- **Table**: `documentsTable`
  - Data Source: `GET /api/runs/{{selectedRunId}}/documents`
  - Columns:
    - `task` (Text, 200px)
    - `url` (Link)
    - `tier` (Badge: A=green, B=yellow, C=gray)
    - `retrieval_method` (Badge)
    - `http_status` (Number, highlight 403/404 in red)
    - `content_len` (Number)
    - `relevance_score` (Number, 2 decimals)
    - `selected` (Checkbox, read-only)
  - Row Click: Show `snippet` in modal
  - Conditional Formatting:
    - `http_status >= 400`: Red background
    - `content_len < 200`: Yellow background
    - `selected == true`: Bold text

- **Filter Toggle**: "Show Selected Only"
  - On: `?selected_only=true`

- **Stats Cards** (top):
  - Total Documents
  - Selected Documents
  - Avg Relevance Score
  - Failed Fetches (4xx/5xx)

## What Gets Logged

### Planner Stage
```python
logger.log('planner', 'Planning started', payload={'query': query})
logger.log('planner', 'Raw LLM response', payload={'raw': response, 'parse_ok': True})
logger.log('planner', 'JSON parse failed', level='warn', payload={'error': str(e)})
logger.log('planner', 'Tasks generated', payload={'tasks': [...]})
```

### Retriever Stage
```python
logger.log('retriever', 'Search started', payload={'query': query, 'backend': 'tinyfish'})
logger.log('retriever', 'TinyFish returned 0 results, using HTTP fallback', level='warn')
logger.log('retriever', 'Seed fallback used', payload={'topic': topic, 'urls': urls})
logger.log('retriever', 'URLs found', payload={'count': len(urls), 'urls': urls})
```

### Web Agent Stage
```python
logger.log('web_agent', 'Fetching documents', payload={'url_count': len(urls)})
logger.log_document(
    task=task.description,
    url=url,
    retrieval_method='tinyfish',
    content_len=len(content),
    http_status=200,
    title=title,
    relevance_score=0.85,
    tier='A',
    selected=True,
    snippet=content[:500]
)
logger.log('web_agent', 'Fetch failed', level='error', payload={'url': url, 'error': '403 Forbidden'})
```

### Synthesizer Stage
```python
logger.log('synthesizer', 'Synthesis started')
logger.log('synthesizer', 'Insufficient evidence', level='warn', payload={'reason': 'no_sources_found'})
logger.log('synthesizer', 'Report generated', payload={'length': len(report)})
```

## Example Queries

### Get Failed Runs
```
GET /api/runs?status=failed&limit=20
```

### Get Error Events for a Run
```
GET /api/runs/{run_id}/events?level=error
```

### Get Only Selected Documents
```
GET /api/runs/{run_id}/documents?selected_only=true
```

## Debugging Workflow

1. **Run fails in Streamlit** → Note the run_id from console
2. **Open Retool** → Find run in Runs List
3. **Click run** → View Run Detail
4. **Check Events** → Filter by level=error
5. **Check Documents** → See which URLs failed (403/404)
6. **Identify Issue**:
   - "topic unknown" → Check planner events
   - "no_sources_found" → Check retriever events
   - "seed_fallback" → Search is failing, using seeds
   - 403/404 → URL is blocked or dead

## Acceptance Test

Run this query:
```
"Research medical imaging AI for cancer detection"
```

In Retool, you should see:
1. **Run created** with topic classification
2. **Planner events** showing task breakdown
3. **Retriever events** showing:
   - TinyFish search attempt
   - HTTP fallback (if TinyFish fails)
   - URLs returned
4. **Documents table** showing:
   - Which URLs were fetched
   - HTTP status codes
   - Content lengths
   - Relevance scores
   - Which were selected
5. **Final report** or "insufficient evidence" reason

## Tips

- **Auto-refresh**: Set Runs List to refresh every 30s to see live runs
- **Bookmarks**: Create Retool bookmarks for common filters (e.g., "Failed Runs Today")
- **Alerts**: Set up Retool alerts for runs with status=failed
- **Export**: Use Retool's CSV export to analyze patterns

## Files

- `app/ops/models.py` - SQLAlchemy models
- `app/ops/logger.py` - RunLogger class
- `ops_api.py` - FastAPI backend
- `cache/ops_console.db` - SQLite database

## Next Steps

1. Instrument all agents with RunLogger
2. Test with sample queries
3. Build Retool dashboard
4. Add human-in-loop features (mark tier, add notes)
