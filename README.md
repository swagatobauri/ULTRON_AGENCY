# ULTRON — AI-Powered Digital Agency

**ULTRON** is a multi-agent AI system that generates, reviews, schedules, and posts content to Telegram channels — fully automated, with human-in-the-loop approval.

Built with **LangGraph** for agent orchestration and **Groq's Llama 3.3 70B** for blazing-fast inference, it runs an entire content agency pipeline in seconds.

---

## What It Does

Give ULTRON a simple prompt like:

```
Create 3 posts about our AI startup that helps small businesses
```

And it will:

1. **Analyze** your task and extract brand context
2. **Research** the web for relevant trends and insights
3. **Write** Telegram-optimized messages with proper formatting
4. **Review** content quality and request revisions if needed
5. **Schedule** posts at optimal engagement times
6. **Post** to your Telegram channel — after you approve

---

## How Is This Different From Just Using an LLM?

A fair question. If you just send a prompt to ChatGPT or Llama, you get text back. ULTRON does something fundamentally different — **the agents actually talk to each other through shared state, use external tools, and make decisions that affect the pipeline flow.**

Here's what happens under the hood when you run a task:

```
You: "Create 3 posts for a fitness brand"
                    │
                    ▼
    ┌─── Manager Agent ───┐
    │ Calls Llama 3.3 70B │  ← LLM call #1
    │ Extracts:            │
    │  • company = fitness │
    │  • tone = motivating │
    │  • count = 3 posts   │
    └──────────┬───────────┘
               │ writes company_info to state
               ▼
    ┌─── Researcher Agent ──┐
    │ Runs 3 Google searches │  ← NOT an LLM — real web search
    │ Feeds results + task   │
    │ into Llama 3.3 70B     │  ← LLM call #2
    │ Outputs: research brief│
    └──────────┬─────────────┘
               │ writes research_results to state
               ▼
    ┌─── Content Creator ────────┐
    │ Reads: task + company_info │  ← uses data from Manager
    │      + research_results    │  ← uses data from Researcher
    │ Calls Llama 3.3 70B       │  ← LLM call #3
    │ Outputs: 3 messages        │
    └──────────┬─────────────────┘
               │ writes messages to state
               ▼
    ┌─── Critic Agent ─────────────────┐
    │ Reads the 3 messages              │
    │ Scores each on 6 criteria         │  ← LLM call #4
    │ Score < 7.5?                      │
    │   YES → writes feedback to state  │
    │         sets current_agent =      │
    │         "content_creator"         │  ← LOOPS BACK
    │   NO  → approved = true           │
    └──────────┬────────────────────────┘
               │ (after approval)
               ▼
    ┌─── Scheduler Agent ───┐
    │ Calls Llama 3.1 8B    │  ← LLM call #5 (smaller model)
    │ Creates JSON schedule  │
    │ Registers jobs with    │
    │ APScheduler            │  ← NOT an LLM — real job scheduling
    └──────────┬─────────────┘
               ▼
    ┌─── Human Approval ────┐
    │ You review the content │  ← NOT automated — you decide
    │ Approve / Reject /     │
    │ Regenerate             │
    └──────────┬─────────────┘
               ▼
    ┌─── Poster Agent ──────┐
    │ Calls Telegram Bot API │  ← NOT an LLM — real API call
    │ Posts to your channel   │
    └────────────────────────┘
```

**The key differences from a plain LLM:**

| | Plain LLM | ULTRON |
|---|-----------|--------|
| **Communication** | One prompt → one response | Agents pass structured data to each other through `AgentState` |
| **Self-correction** | None — you get what you get | Critic reviews output, sends specific feedback back to Content Creator for revision (up to 2 cycles) |
| **External tools** | Can't search the web or call APIs | Researcher runs real Google searches; Poster calls Telegram API; Scheduler uses APScheduler |
| **Decision making** | No branching logic | LangGraph routes between agents based on state — Critic can loop back or approve forward |
| **Human control** | Copy-paste manually | Built-in approval flow — nothing posts without your OK |
| **Multiple models** | One model, one call | Uses 70B for heavy tasks and 8B for simple ones — optimized per agent |

Each agent **reads what previous agents wrote** and **writes its own output** for the next agent. The Content Creator doesn't just get your prompt — it gets the Manager's brand analysis AND the Researcher's web findings. The Critic doesn't just say "looks good" — it scores on 6 criteria and writes specific feedback that the Content Creator uses word-for-word in its revision.

This is orchestration, not just prompting.

**Don't take our word for it** — the dashboard includes a **Live Agent Activity Feed** that streams every action in real-time: Google searches, LLM calls, scoring decisions, feedback loops, and handoffs. You can literally watch the agents work.

---

## The Agent Pipeline

ULTRON uses **6 specialized AI agents**, each with a clear role, connected through a LangGraph state machine:

```
┌──────────┐     ┌────────────┐     ┌─────────────────┐
│ Manager  │────▶│ Researcher │────▶│ Content Creator  │
└──────────┘     └────────────┘     └────────┬────────┘
                                             │
                                             ▼
┌──────────┐     ┌────────────┐     ┌────────────────┐
│  Poster  │◀────│ Scheduler  │◀────│     Critic     │
└──────────┘     └────────────┘     └────────┬───────┘
                                             │
                                    ┌────────▼───────┐
                                    │  Needs work?   │
                                    │  Loop back to  │
                                    │ Content Creator│
                                    └────────────────┘
```

| Agent | What It Does |
|-------|-------------|
| **Manager** | Analyzes the task, extracts company info, creates a content brief |
| **Researcher** | Searches the web (Google) for trends, strategies, and audience insights |
| **Content Creator** | Writes Telegram messages with Markdown formatting, emojis, and CTAs |
| **Critic** | Scores messages (1-10) on hooks, clarity, engagement, brand fit. Sends back for revision if < 7.5 |
| **Scheduler** | Picks optimal posting times using Telegram engagement patterns |
| **Poster** | Posts approved messages to your Telegram channel via the Bot API |

The **Critic → Content Creator** feedback loop runs up to 2 revision cycles, ensuring quality output.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Agent Framework** | [LangGraph](https://github.com/langchain-ai/langgraph) — state machine for multi-agent orchestration |
| **LLM Provider** | [Groq](https://groq.com/) — ultra-fast inference with Llama 3.3 70B + Llama 3.1 8B |
| **LLM Integration** | [LangChain](https://www.langchain.com/) — `langchain-groq` for model abstraction |
| **Web Search** | `googlesearch-python` — real-time Google search for research agent |
| **Telegram Bot** | `python-telegram-bot` — interactive bot with inline buttons for approval flow |
| **Backend API** | Flask + Flask-CORS — REST API for the dashboard |
| **Job Scheduling** | APScheduler — background scheduling for timed posts |
| **Frontend (Landing)** | Next.js 14 + React Three Fiber + Framer Motion — 3D animated landing page |
| **Frontend (Dashboard)** | Vanilla HTML/CSS/JS served by Flask — real-time pipeline status UI |
| **Deployment** | Render + Gunicorn — production-ready hosting |
| **Language** | Python 3.10 |

---

## Project Structure

```
ULTRON/
│
├── main.py                 # CLI entry point — run the pipeline from terminal
├── bot.py                  # Telegram bot — interactive content generation via chat
├── dashboard.py            # Flask backend — REST API + dashboard server
├── config.py               # LLM setup (Groq), Telegram API config, env vars
│
├── agents/                 # The 6 AI agents
│   ├── manager.py          # Task analysis and brief creation
│   ├── researcher.py       # Web search + research brief generation
│   ├── content_creator.py  # Telegram message generation with revisions
│   ├── critic.py           # Quality review and scoring
│   ├── scheduler.py        # Optimal posting time calculation
│   └── poster.py           # Telegram channel posting
│
├── utils/
│   ├── state.py            # AgentState TypedDict — shared state across agents
│   └── helpers.py          # Logging, validation, parsing utilities
│
├── tools/                  # External tool integrations
│   ├── search_tool.py
│   ├── image_tool.py
│   └── instagram_tool.py
│
├── templates/              # Flask HTML templates
│   ├── index.html          # Dashboard UI
│   └── landing.html        # Landing page
│
├── static/                 # Static assets (CSS, JS)
│   ├── css/
│   └── js/
│
├── frontend/               # Next.js landing page (3D + animations)
│   ├── app/
│   │   ├── page.js         # Animated landing page with Three.js
│   │   └── dashboard/      # Dashboard route
│   └── components/
│
├── tests/                  # Test files
├── requirements.txt        # Python dependencies
├── Procfile                # Render deployment config
└── .env                    # API keys (not committed)
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+ (for the frontend)
- A [Groq API key](https://console.groq.com/) (free tier works)
- A [Telegram Bot Token](https://core.telegram.org/bots#how-do-i-create-a-bot) + Channel ID

### 1. Clone & Install

```bash
git clone https://github.com/swagatobauri/ULTRON_AGENCY.git
cd ULTRON_AGENCY

# Python deps
pip install -r requirements.txt

# Frontend deps (optional — for the landing page)
cd frontend
npm install
cd ..
```

### 2. Set Up Environment

Create a `.env` file in the root:

```env
GROQ_API_KEY=your_groq_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_channel_id
```

### 3. Run It

You have **3 ways** to use ULTRON:

#### Option A — CLI Mode
```bash
python main.py
# Enter a task when prompted
```

#### Option B — Telegram Bot
```bash
python bot.py
# Then open Telegram and send /start to your bot
```

#### Option C — Dashboard
```bash
python dashboard.py
# Open http://localhost:5000 in your browser
```

---

## Telegram Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and usage guide |
| `/generate <task>` | Run the full AI pipeline |
| `/status` | Check bot status and pending approvals |
| `/help` | Show all available commands |

After generating, the bot sends you message previews with **Approve**, **Reject**, and **Regenerate** buttons — nothing gets posted without your explicit approval.

---

## Dashboard API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/generate` | POST | Start a new pipeline run |
| `/api/status/<run_id>` | GET | Check pipeline progress (real-time stage tracking) |
| `/api/logs/<run_id>` | GET | Live activity feed (incremental, supports `?after=N`) |
| `/api/approve/<run_id>` | POST | Approve and post messages to Telegram |
| `/api/reject/<run_id>` | POST | Discard generated messages |
| `/api/regenerate/<run_id>` | POST | Re-run pipeline with the same task |
| `/api/history` | GET | Last 20 posted message batches |

Rate limited to **3 requests/day** and **1 request/minute** per IP.

---

## How the State Flows

Every agent reads from and writes to a shared `AgentState`:

```python
class AgentState(TypedDict):
    task: str                    # The user's original prompt
    company_info: str            # Extracted brand context
    research_results: str        # Web research brief
    messages: List[str]          # Generated Telegram messages
    feedback: str                # Critic's revision notes
    approved: bool               # Whether content passed review
    scheduled_times: List[str]   # Planned posting schedule
    posted_message_ids: List[str]# Telegram message IDs after posting
    current_agent: str           # Which agent runs next
    error: Optional[str]         # Error tracking
    revision_count: int          # Number of revision cycles
```

LangGraph handles the routing — each agent returns an updated state with `current_agent` set to the next agent in line.

---

## Two LLMs, Two Speeds

| Model | Used By | Why |
|-------|---------|-----|
| **Llama 3.3 70B** (`temperature: 0.7`) | Manager, Researcher, Content Creator, Critic | Heavy lifting — analysis, writing, and review need the big model |
| **Llama 3.1 8B** (`temperature: 0.3`) | Scheduler | Lightweight — just needs to output a JSON schedule |

Both run through Groq for near-instant inference.

---

## License

This project is open source. Feel free to fork, modify, and use it for your own AI agency experiments.

---

