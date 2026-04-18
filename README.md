# PageMatch — AI Landing Page Personalizer

> Automatically personalize landing page copy to match your ad creative using Gemini 2.5 Flash Vision and CRO principles.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?style=flat-square)
![Gemini](https://img.shields.io/badge/Gemini-2.5%20Flash-orange?style=flat-square)
![Playwright](https://img.shields.io/badge/Playwright-Chromium-purple?style=flat-square)


---

## What It Does

When a user clicks an ad, there is an implicit promise in that click. If the landing page does not reflect the ad's offer, tone, or message, the user leaves. This is called **ad scent loss** and it is one of the biggest reasons ad spend gets wasted.

PageMatch solves this automatically. Upload an ad creative and paste a landing page URL. The system reads the ad, scrapes the page, and rewrites the headline, subheadline, and CTA to create message match — without rebuilding the page from scratch.

---

## Live Demo

**[https://ai-pagematch.onrender.com](https://ai-pagematch.onrender.com)**

> Note: Hosted on Render free tier. First request after inactivity may take 30 to 60 seconds to cold start.

---

## How It Works

```
Ad Image Upload
      │
      ▼
Gemini 2.5 Flash Vision
→ Extracts: offer, CTA, tone, audience, pain point
      │
      ▼
Playwright Headless Browser
→ Scrapes: headline, subheadline, CTA from landing page
      │
      ▼
Gemini 2.5 Flash Text
→ Rewrites: 3 page sections to match ad messaging
      │
      ▼
BeautifulSoup HTML Injection
→ Surgically replaces text, preserves all CSS and layout
      │
      ▼
Preview Output
→ Diff panel (original vs personalized) + modified page iframe
```

---

## Tech Stack

| Layer              | Tool                                |
| ------------------ | ----------------------------------- |
| Backend            | FastAPI + uvicorn                   |
| AI Vision and Text | Gemini 2.5 Flash (Google AI Studio) |
| Page Rendering     | Playwright (headless Chromium)      |
| HTML Parsing       | BeautifulSoup4                      |
| Frontend           | Vanilla HTML, CSS, JavaScript       |
| Deployment         | Render                              |

---

## Project Structure

```
ai-pagematch/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI entry point, static serving, CORS
│   ├── routes.py         # API route definitions and request handling
│   ├── gemini_client.py  # Gemini SDK configuration and vision analysis
│   ├── scraper.py        # Two-layer page scraping and text extraction
│   └── personalizer.py   # Copy generation and HTML injection
├── static/
│   └── index.html        # Single-page frontend UI
├── .env                  # API keys (never committed)
├── .gitignore
├── Procfile              # Render deployment config
└── requirements.txt
```

---

## Getting Started

### Prerequisites

- Python 3.10 or higher
- A Google AI Studio API key (free at [aistudio.google.com](https://aistudio.google.com))

### Installation

**1. Clone the repository**

```bash
git clone https://github.com/YOUR_USERNAME/ai-pagematch.git
cd ai-pagematch
```

**2. Create and activate a virtual environment**

```bash
python -m venv venv
source venv/bin/activate       # Mac and Linux
venv\Scripts\activate          # Windows
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Install Playwright browser**

```bash
playwright install chromium
```

**5. Set up your environment variables**

Create a `.env` file in the root directory:

```
GOOGLE_API_KEY=your_gemini_api_key_here
```

**6. Run the development server**

```bash
uvicorn app.main:app --reload
```

Open `http://localhost:8000` in your browser.

---

## Usage

1. Open the app in your browser
2. Upload an ad creative image (JPEG, PNG, WEBP or GIF, max 10MB)
3. Paste a publicly accessible landing page URL
4. Click **Personalize Landing Page**
5. Wait 15 to 30 seconds for the pipeline to complete
6. View the diff panel showing original vs personalized copy and the modified page below

---

## API Reference

All routes are documented interactively at `/docs` when running locally.

| Route                    | Method | Description                 |
| ------------------------ | ------ | --------------------------- |
| `GET /`                  | GET    | Serves the frontend         |
| `GET /health`            | GET    | Health check                |
| `POST /analyze-ad`       | POST   | Ad image analysis only      |
| `POST /scrape-page`      | POST   | Landing page scraping only  |
| `POST /personalize-json` | POST   | Full pipeline, returns JSON |
| `POST /personalize`      | POST   | Full pipeline, returns HTML |

### Example: Scrape a page

```bash
curl -X POST http://localhost:8000/scrape-page \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

### Example: Full personalization

```bash
curl -X POST http://localhost:8000/personalize-json \
  -F "file=@ad_creative.png" \
  -F "url=https://example.com"
```

---

## Edge Case Handling

**Random changes:** Only three fields are ever modified: headline, subheadline, and CTA text. All other page elements are completely untouched. The Gemini prompt explicitly forbids changes outside these three fields and output is validated against a strict JSON schema.

**Broken UI:** A two-layer scraping strategy is used. Playwright is attempted first for JavaScript-rendered pages, with a requests and BeautifulSoup fallback for static pages. If both fail, a clean error is returned. HTML injection silently skips any field it cannot find rather than crashing.

**Hallucinations:** The model is grounded with an explicit instruction that it must not introduce any claims, features, or offers not already present in the ad or the original page. A `personalization_reasoning` field is returned and displayed in the UI for full transparency.

**Inconsistent outputs:** Output is enforced as strict JSON with a fixed schema. Word limits are specified per field. A cleanup step strips markdown wrappers before parsing. Failed parses raise clean 500 errors with the raw output for debugging.

---

## Assumptions

- Ad creative is provided as an image upload. This covers all major ad formats including Facebook, Instagram, and Google Display.
- Personalization targets the hero section only (headline, subheadline, CTA) as it is the highest-impact area for CRO.
- Landing pages must be publicly accessible without authentication.
- English language output is assumed.

---

## Known Limitations

- Pages protected by Cloudflare or similar bot protection may fail to scrape
- Iframe preview may appear unstyled on pages with strict Content Security Policy headers
- Gemini free tier has a rate limit of 15 requests per minute
- Render free tier cold starts take 30 to 60 seconds after inactivity

---

## Local Development Notes

On Windows, the following event loop policy is set automatically in `main.py` to enable Playwright subprocess support:

```python
asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
```

This is not required on Mac or Linux.

---

## Deployment

The app is configured for Render deployment via `Procfile`:

```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Build command on Render:

```
pip install -r requirements.txt && playwright install chromium
```

Set `GOOGLE_API_KEY` as an environment variable in the Render dashboard.

---
