# Image Generation Feature

TinyScout now supports AI-generated visuals using the Freepik Image Generation API.

## Features

- **LLM-Powered Suggestions**: Claude analyzes your research report and suggests relevant visuals
- **Smart Filtering**: Only generates images when they add value (diagrams, comparisons, timelines)
- **Caching**: Prevents duplicate API calls and reduces costs
- **Rate Limiting**: Max 3 images per run, 1 retry per image
- **Async Generation**: Non-blocking image creation with status polling

## Setup

### 1. Get Freepik API Key

1. Sign up at [Freepik API](https://www.freepik.com/api)
2. Navigate to your API dashboard
3. Generate an API key for "Text-to-Image" service

### 2. Configure Environment

Add to your `.env` file:

```bash
FREEPIK_API_KEY=your_freepik_api_key_here
```

### 3. Enable in UI

In the Streamlit dashboard, check the box:
```
✨ Generate Visuals (Freepik)
```

## How It Works

1. **Report Analysis**: After synthesis, the LLM analyzes the report structure
2. **Suggestion**: Claude suggests 0-3 images with detailed prompts
3. **Generation**: Freepik API creates images asynchronously
4. **Display**: Images are embedded in the report with metadata

## When Images Are Generated

✅ **Good Candidates:**
- Market landscape maps
- System architecture diagrams
- Timeline/trend infographics
- Comparison charts (illustrated)
- Process flow diagrams

❌ **Skipped:**
- Simple factual Q&A
- Reports with < 2 sections
- Sensitive medical/political content
- Requests for real people

## Cost Control

- **Caching**: Identical prompts reuse cached images
- **Rate Limits**: Max 3 images per run
- **Retry Limits**: Max 1 retry per failed image
- **Cache Expiry**: 30 days (configurable)

## API Details

### Freepik Text-to-Image Endpoint

```
POST https://api.freepik.com/v1/ai/text-to-image
```

**Headers:**
```
x-freepik-api-key: YOUR_API_KEY
Content-Type: application/json
```

**Payload:**
```json
{
  "prompt": "Create a clean infographic...",
  "negative_prompt": "text, watermark, logo...",
  "guidance_scale": 7.5,
  "num_images": 1,
  "image": {
    "size": "landscape"
  }
}
```

**Response:**
```json
{
  "task_id": "abc123",
  "status": "processing"
}
```

### Status Polling

```
GET https://api.freepik.com/v1/ai/text-to-image/{task_id}
```

**Response (completed):**
```json
{
  "status": "success",
  "data": {
    "images": [
      {
        "url": "https://..."
      }
    ]
  }
}
```

## Troubleshooting

### "Image generation disabled"
- Check that `FREEPIK_API_KEY` is set in `.env`
- Verify API key is valid

### "No visuals suggested"
- Report may be too simple
- Try a more complex query with multiple sections

### Generation timeout
- Default timeout: 120 seconds
- Freepik typically completes in 10-30 seconds
- Check Freepik API status if persistent

## Architecture

```
┌─────────────────────────────────────────┐
│         Streamlit Dashboard             │
│  (enable_images checkbox)               │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│     ImageSuggestionAgent (LLM)          │
│  - Analyzes report                      │
│  - Returns JSON with image requests     │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│        ImageGenerator                   │
│  - Checks cache                         │
│  - Calls FreepikClient                  │
│  - Applies rate limits                  │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│        FreepikClient                    │
│  - create_task()                        │
│  - wait_for_completion()                │
│  - Returns ImageArtifact                │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│         ImageCache (SQLite)             │
│  - Stores completed images              │
│  - Prevents duplicate API calls         │
└─────────────────────────────────────────┘
```

## Files

- `app/images/models.py` - Data structures
- `app/images/freepik_client.py` - API client
- `app/images/generator.py` - Main service
- `app/images/suggestion_agent.py` - LLM suggestions
- `app/images/cache.py` - SQLite caching
- `cache/image_cache.db` - Cache database

## Future Enhancements

- [ ] Webhook support for async notifications
- [ ] Multiple image provider support (DALL-E, Midjourney)
- [ ] Image editing/refinement
- [ ] Custom style presets
- [ ] Batch generation optimization
