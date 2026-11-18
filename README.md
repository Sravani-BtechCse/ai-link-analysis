# AI-Powered Website Link Analysis API

A FastAPI service that fetches a public website, extracts readable page content, and uses an LLM to produce structured business and marketing insights.

## Features

- `POST /link-analysis` accepts a website URL.
- Extracts title, meta description, headings, and visible text.
- Returns brand details and the five required analysis areas: competitor suggestions, five platform-specific search queries, SEO recommendations, up to five services, and target audiences.
- Supports Gemini (default), OpenAI, and Anthropic through environment configuration.
- Validates URLs and blocks localhost/private/reserved IP destinations, checks redirects, enforces fetch timeout and response-size limits.
- Pydantic validation, clear API errors, a health endpoint, and in-memory response cache.
- No fabricated search-volume or ranking data. Competitors are explicitly labelled as AI suggestions.

## Requirements

- Python 3.10+
- One API key from Gemini, OpenAI, or Anthropic

## Setup

### Windows PowerShell

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `.env` and add your Gemini API key. The default provider is Gemini.

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Run

```bash
uvicorn app.main:app --host 127.0.0.1 --port 4000 --reload
```

Open `http://127.0.0.1:4000/docs`.

## Test the endpoint

```bash
curl -X POST "http://127.0.0.1:4000/link-analysis" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.python.org"}'
```

Expected top-level response shape:

```json
{
  "success": true,
  "website": "https://www.python.org/",
  "brand": {
    "name": "Python",
    "category": "Programming language and software ecosystem",
    "summary": "..."
  },
  "analysis": {
    "competitor_analysis": {},
    "target_search_queries": [],
    "seo_improvements": {},
    "top_services": [],
    "target_audience": {}
  },
  "source": {
    "page_title": "...",
    "characters_extracted": 12000,
    "cached": false
  },
  "model": "gemini-2.5-flash"
}
```

The content above is an illustrative shape, not a promised result. Actual output depends on the target site and model.

## Switch providers

Set `LLM_PROVIDER` and the corresponding key/model in `.env`.

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4.1-mini
```

or:

```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_key
ANTHROPIC_MODEL=claude-3-5-haiku-latest
```

Never commit `.env`.

## LLM selection research

This project uses a provider adapter so the model can be switched without changing the API contract. The default is Gemini 2.5 Flash as a practical speed/cost-oriented starting point. OpenAI GPT-4.1 mini and Anthropic Claude Haiku are alternatives.

| Provider/model | Intended fit | Pricing note |
|---|---|---|
| Google Gemini 2.5 Flash | Fast multimodal/general analysis; structured JSON mode | Check current official Gemini API pricing before submission |
| OpenAI GPT-4.1 mini | Strong instruction following and structured output | Check current official API pricing before submission |
| Anthropic Claude Haiku | Fast, lower-cost text analysis | Check current official API pricing before submission |

Do not present model response times or accuracy as measured unless you benchmark them yourself. For the final submission, record the date and official per-million-token input/output prices from each provider's pricing page. A simple cost estimate is:

`(input_tokens / 1,000,000 × input_price) + (output_tokens / 1,000,000 × output_price)`

A reasonable initial planning estimate for a single-page request is 5,000 input tokens and 1,500 output tokens, but actual usage must be measured from provider usage metadata. Run the same representative URLs against each model at least 5 times; record mean latency, schema-valid response rate, and human-rated relevance. This makes the comparison defensible.

Official pricing references:
- Google: https://ai.google.dev/gemini-api/docs/pricing
- OpenAI: https://openai.com/api/pricing/
- Anthropic: https://www.anthropic.com/pricing#api

## Cost and quality improvements

- Remove scripts, navigation, styles, and duplicate content before sending text.
- Cap extracted text and use a small/fast model for the first pass.
- Cache successful analyses for a short TTL.
- Avoid re-running analysis if the page content hash has not changed.
- Use a structured output mode and validate every response.
- Log token usage and latency; do not claim benchmark numbers without tests.

## Security notes and limitations

- Only public HTTP(S) URLs are accepted. Localhost and non-public IPs are rejected, and redirects are revalidated.
- This is a practical-test starter, not a fully hardened production crawler. DNS rebinding can still require network-level egress controls in production; use an outbound proxy/firewall that blocks private address ranges.
- Some sites block automated clients, require JavaScript rendering, or return consent pages. Those sites may fail or yield incomplete extraction.
- Competitor identification is generated as a hypothesis, not verified live market research.
- No search volume, rankings, traffic, or live social data are fetched.
- The in-memory cache is per process and resets on restart.

## Tests

```bash
pytest -q
```

## Project structure

```text
ai-link-analysis/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── schemas.py
│   ├── services/
│   │   ├── website_extractor.py
│   │   ├── llm_service.py
│   │   └── analysis_service.py
│   └── utils/
│       └── validators.py
├── tests/
├── .env.example
├── .gitignore
└── requirements.txt
```


## Web interface

The project includes a simple responsive frontend at `/`. Once the API server is running, open:

`http://localhost:4000/`

Enter a public website URL and click **Analyze website**. The frontend calls the same `/link-analysis` API and displays all five analysis sections. API documentation remains available at `/docs`.

## Deploy publicly with Render

1. Push this project to a GitHub repository.
2. In Render, create a new **Blueprint** and select that repository (it detects `render.yaml`).
3. In the Render service's Environment settings, add `GEMINI_API_KEY` as a secret value.
4. Deploy. Render will provide a public HTTPS URL; use that as the website link.

Do not commit `.env` or paste API keys into source files. The public link cannot be created until you deploy it through a hosting account and configure the secret key.
