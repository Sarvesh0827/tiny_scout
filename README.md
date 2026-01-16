# TinyScout: Autonomous AI Research Agent

TinyScout is an autonomous web research agent that performs deep, multi-source research on any topic. It uses LangGraph orchestration, local LLM (Mistral via Ollama), and intelligent web scraping to deliver comprehensive, grounded research reports.

## Features

- **Autonomous Research**: Breaks down complex queries into actionable research tasks
- **Multi-Source Intelligence**: Fetches and analyzes content from curated, high-quality sources
- **Grounding Gate**: Prevents hallucinations by refusing to synthesize when evidence is insufficient
- **Relevance Scoring**: Ranks sources by keyword relevance to ensure quality
- **Smart Caching**: Caches fetched content to avoid redundant requests
- **Streamlit UI**: Interactive dashboard to monitor agent activity and view results

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐      ┌──────────────┐
│   Planner   │─────▶│  Web Agent   │─────▶│  Analyzer   │─────▶│ Synthesizer  │
│             │      │              │      │             │      │              │
│ Breaks down │      │ Fetches &    │      │ Extracts    │      │ Compiles     │
│ query into  │      │ extracts     │      │ insights    │      │ final report │
│ tasks       │      │ from sources │      │             │      │              │
└─────────────┘      └──────────────┘      └─────────────┘      └──────────────┘
```

## Tech Stack

- **LLM**: Local Mistral 7B (via Ollama)
- **Orchestration**: LangGraph + LangChain
- **Web Scraping**: Trafilatura + httpx/requests
- **UI**: Streamlit
- **Backend**: Python 3.10+

## Installation

1. **Clone the repository**:
   ```bash
   git clone git@github.com:Sarvesh0827/hack1.git
   cd hack1
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install and run Ollama** (for local LLM):
   ```bash
   # Install Ollama from https://ollama.ai
   ollama pull mistral
   ollama serve
   ```

## Usage

Run the Streamlit dashboard:

```bash
export PYTHONPATH=$PYTHONPATH:. && streamlit run ui/dashboard.py
```

Then navigate to `http://localhost:8501` and enter your research query.

### Example Query

> "Analyze the current state of AI voice moderation: key players, trends, and unmet needs."

The agent will:
1. Break this into sub-tasks (key players, trends, unmet needs)
2. Fetch relevant sources for each task
3. Score and rank sources by relevance
4. Synthesize a comprehensive report with citations

## Project Structure

```
hack1/
├── app/
│   ├── agents/           # Agent implementations
│   │   ├── planner.py
│   │   ├── web_agent.py
│   │   ├── analyzer.py
│   │   └── synthesizer.py
│   ├── models.py         # Data models
│   ├── state.py          # LangGraph state
│   ├── graph.py          # Orchestration logic
│   ├── seeds.py          # Curated source URLs
│   └── main.py           # FastAPI backend (optional)
├── ui/
│   └── dashboard.py      # Streamlit UI
├── cache/                # Cached web content
├── requirements.txt
└── README.md
```

## Configuration

### Seeded URLs

The agent uses curated, high-quality sources organized by category in `app/seeds.py`:

- **key_players**: Company/product pages
- **trends**: Recent news and blog posts
- **unmet_needs**: Research papers and critical analyses
- **default**: General reliable sources

You can customize these lists for your domain.

### Grounding Threshold

In `app/graph.py`, the grounding gate prevents synthesis when:
- Valid sources < 1
- Total extracted text < 1000 characters

Adjust these thresholds based on your needs.

## Development

### Running Tests

```bash
python verify_agents.py
```

### Adding New Agents

1. Create a new agent class in `app/agents/`
2. Add it to the graph in `app/graph.py`
3. Update the state schema in `app/state.py` if needed

## Roadmap

- [ ] Integrate TinyFish for advanced web browsing
- [ ] Add parallel task execution with Ray
- [ ] Implement embedding-based relevance scoring
- [ ] Support for PDF and document parsing
- [ ] Multi-LLM support (Claude, GPT-4, etc.)

## License

MIT

## Contributing

Contributions welcome! Please open an issue or PR.
