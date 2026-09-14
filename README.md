# Brandhero B2B Opportunity Intelligence System

Evidence-first proof of concept for identifying Brandhero-relevant signals in B2B SaaS companies.

The system accepts a company name and domain, researches first-party website content and relevant news, classifies seven opportunity signals with local Ollama/Llama, validates every citation, and calculates a deterministic score.

## Requirements

- Python 3.10+
- Node.js and npm for the optional frontend
- Ollama running locally
- Ollama model: `llama3.1:8b`

Pull the model once:

```powershell
ollama pull llama3.1:8b
```

Python dependencies:

```powershell
pip install -r requirements.txt
```

The LLM integration uses Ollama at `http://localhost:11434`. It does not require Groq or an OpenAI API key.

## Run The CLI

From the repository root:

```powershell
python -m app.main
```

Enter the target domain and company name when prompted.

The CLI prints:

- Signal-scoped research evidence
- Model classification and validation logs
- Detected signals and source URLs
- Brandhero opportunity details
- Deterministic score and breakdown

## Run The API

Start the local API on port `8000`:

```powershell
python -m app.api
```

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Analyze a company:

```powershell
$body = @{ domain = "canva.com"; company_name = "Canva" } | ConvertTo-Json
Invoke-RestMethod -Method Post `
	-Uri http://127.0.0.1:8000/api/analyze `
	-ContentType "application/json" `
	-Body $body
```

## Run The Frontend

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

The Vite development proxy forwards `/api` requests to `http://127.0.0.1:8000`. Start the Python API before using the Analyze button.

## Signals

The analyzer evaluates:

1. `product_change`
2. `rebrand_or_positioning`
3. `website_change`
4. `market_expansion`
5. `design_product_hiring`
6. `growth_with_experience_pressure`
7. `observable_experience_problem`

Signals are evidence-first. A detected signal must have a source URL from the researcher output. Generic pages, unrelated articles, unsupported visual claims, and model-invented URLs are rejected.

## Scoring And Opportunity Tier

The numeric score is deterministic and uses the weights in `app/scoring.py`:

| Signal                                     | Weight |
| ------------------------------------------ | -----: |
| Product / Feature Change                   |     15 |
| Rebrand / Positioning Change               |     20 |
| Website / Digital Experience Change        |     20 |
| Market / Audience Expansion                |     10 |
| Design / Product Hiring                    |     10 |
| Growth with Experience Pressure            |     10 |
| Observable UX / Product Experience Problem |     15 |

Each detected signal contributes:

```text
weight * confidence * Brandhero relevance
```

The raw score tier describes the aggregate numeric score. The separate evidence-based opportunity tier describes whether the validated evidence represents a meaningful Brandhero opportunity. Therefore, one strong rebrand can produce:

- Raw score: `20/100`, score tier `Very Low`
- Evidence-based opportunity tier: `High`

This distinction is intentional and prevents a single strong trigger from being hidden by an aggregate score designed for multiple signals.

## Evidence And Entity Resolution

Research is collected per signal. The researcher:

- Restricts sources to the target company's first-party domain where applicable
- Filters unrelated news before classification
- Uses specific product announcements instead of generic changelog indexes
- Keeps the original source URL and extracted supporting claim

The model may classify supplied evidence, but it cannot create evidence. Validation removes citations that were not supplied by the researcher.

## Troubleshooting

### Frontend shows stale or different results

Make sure only one API process is running on port `8000`. An orphaned Python API process can continue serving old code after a terminal is closed. Check the listener in PowerShell:

```powershell
Get-NetTCPConnection -LocalPort 8000 -State Listen
```

Stop the reported process if necessary, then restart:

```powershell
python -m app.api
```

Refresh the frontend after restarting the API.

### Ollama connection failure

Confirm Ollama is running and the model is installed:

```powershell
ollama list
ollama run llama3.1:8b
```

### No detected signals

This can be a valid result. Inspect the `[EVIDENCE]`, `[LLAMA EVIDENCE]`, `[LLAMA CLASSIFICATION]`, and `[VALIDATION]` logs. A signal remains false when the researcher cannot supply direct, signal-specific evidence.

## Project Structure

```text
app/
	api.py          Local HTTP API
	llm.py          Ollama integration and JSON parsing
	main.py         CLI entry point
	researcher.py  Website, sitemap, release, hiring, and news research
	signals.py     Evidence preparation, classification, and validation
	scoring.py     Deterministic score calculation
frontend/         React/Vite interface
data/             Cached Brandhero profile
results/          Optional generated results
requirements.txt  Python dependencies
```

Do not commit API keys or other secrets from local environment files.
