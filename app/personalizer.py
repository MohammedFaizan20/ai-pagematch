import google.generativeai as genai
import json
import re
from bs4 import BeautifulSoup

model = genai.GenerativeModel("gemini-2.5-flash")


def generate_personalized_copy(ad_analysis: dict, page_sections: dict) -> dict:
    prompt = f"""
You are a CRO (Conversion Rate Optimization) expert. Your job is to personalize 
landing page copy to match an ad creative the user just clicked.

The goal is message match: the landing page should feel like a natural continuation 
of the ad. Same offer, same tone, same energy.

AD CREATIVE ANALYSIS:
- Main offer: {ad_analysis.get('main_offer', 'Not detected')}
- CTA in ad: {ad_analysis.get('cta_text', 'Not detected')}
- Tone: {ad_analysis.get('tone', 'Not detected')}
- Target audience: {ad_analysis.get('target_audience', 'Not detected')}
- Key message: {ad_analysis.get('key_message', 'Not detected')}
- Pain point addressed: {ad_analysis.get('pain_point', 'Not detected')}

CURRENT LANDING PAGE SECTIONS:
- Headline: {page_sections.get('headline', 'Not found')}
- Subheadline: {page_sections.get('subheadline', 'Not found')}
- CTA text: {page_sections.get('cta_text', 'Not found')}

YOUR TASK:
Rewrite only the headline, subheadline and cta_text to align with the ad's message.

STRICT RULES:
1. Do not introduce any claims, features or offers not present in either the ad or the original page
2. Keep the rewritten headline under 12 words
3. Keep the rewritten subheadline under 30 words
4. Keep the rewritten cta_text under 6 words
5. Match the tone of the ad exactly
6. The rewritten copy must feel like a continuation of the ad, not a completely new message
7. If a field was null or not found, keep the original value or return null

Return ONLY a valid JSON object with exactly these keys, no explanation, no markdown:
{{
    "headline": "rewritten headline here",
    "subheadline": "rewritten subheadline here",
    "cta_text": "rewritten cta text here",
    "personalization_reasoning": "one sentence explaining what was changed and why"
}}
"""

    response = model.generate_content(prompt)
    raw = response.text.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    return json.loads(raw)


def inject_copy_into_html(html: str, personalized_copy: dict) -> str:
    soup = BeautifulSoup(html, "html.parser")

    new_headline = personalized_copy.get("headline")
    if new_headline:
        h1_tags = soup.find_all("h1")
        for h1 in h1_tags:
            if h1.get_text(strip=True):
                h1.string = new_headline
                break

    new_subheadline = personalized_copy.get("subheadline")
    if new_subheadline:
        h2_tags = soup.find_all("h2")
        for h2 in h2_tags:
            if h2.get_text(strip=True):
                h2.string = new_subheadline
                break

    new_cta = personalized_copy.get("cta_text")
    if new_cta:
        for a_tag in soup.find_all("a", class_=True):
            classes = " ".join(a_tag.get("class", []))
            if any(word in classes.lower() for word in ["btn", "button", "cta"]):
                a_tag.string = new_cta
                break

        for button in soup.find_all("button"):
            text = button.get_text(strip=True)
            if text and len(text) < 50:
                button.string = new_cta
                break

    return str(soup)


def build_preview_html(
    original_sections: dict,
    personalized_copy: dict,
    page_url: str,
    modified_html: str
) -> str:
    reasoning = personalized_copy.get(
        "personalization_reasoning", "No reasoning provided"
    )

    preview = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Personalized Landing Page Preview</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f5; }}
        .top-bar {{
            background: #1a1a2e;
            color: white;
            padding: 12px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 1000;
        }}
        .top-bar h1 {{ font-size: 14px; font-weight: 600; }}
        .badge {{
            background: #4ade80;
            color: #14532d;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }}
        .diff-panel {{
            background: white;
            border-bottom: 1px solid #e5e7eb;
            padding: 20px 24px;
        }}
        .diff-panel h2 {{
            font-size: 13px;
            font-weight: 600;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 16px;
        }}
        .diff-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-bottom: 12px;
        }}
        .diff-col {{ }}
        .diff-col h3 {{
            font-size: 11px;
            font-weight: 600;
            margin-bottom: 8px;
            padding: 4px 8px;
            border-radius: 4px;
            display: inline-block;
        }}
        .original h3 {{ background: #fee2e2; color: #991b1b; }}
        .personalized h3 {{ background: #dcfce7; color: #166534; }}
        .diff-item {{
            margin-bottom: 10px;
        }}
        .diff-label {{
            font-size: 11px;
            color: #9ca3af;
            margin-bottom: 2px;
        }}
        .diff-value {{
            font-size: 13px;
            color: #111827;
            padding: 6px 10px;
            border-radius: 6px;
            background: #f9fafb;
            border: 1px solid #e5e7eb;
        }}
        .personalized .diff-value {{
            background: #f0fdf4;
            border-color: #bbf7d0;
            color: #166534;
        }}
        .reasoning {{
            background: #fffbeb;
            border: 1px solid #fde68a;
            border-radius: 8px;
            padding: 10px 14px;
            font-size: 13px;
            color: #92400e;
            margin-top: 4px;
        }}
        .reasoning strong {{ font-weight: 600; }}
        .page-frame {{
            width: 100%;
            height: calc(100vh - 200px);
            border: none;
            display: block;
        }}
    </style>
</head>
<body>
    <div class="top-bar">
        <h1>Troopod — Personalized Landing Page</h1>
        <span class="badge">AI Personalized</span>
    </div>

    <div class="diff-panel">
        <h2>What changed</h2>
        <div class="diff-grid">
            <div class="diff-col original">
                <h3>Original</h3>
                <div class="diff-item">
                    <div class="diff-label">Headline</div>
                    <div class="diff-value">{original_sections.get('headline', 'N/A')}</div>
                </div>
                <div class="diff-item">
                    <div class="diff-label">Subheadline</div>
                    <div class="diff-value">{original_sections.get('subheadline', 'N/A')}</div>
                </div>
                <div class="diff-item">
                    <div class="diff-label">CTA</div>
                    <div class="diff-value">{original_sections.get('cta_text', 'N/A')}</div>
                </div>
            </div>
            <div class="diff-col personalized">
                <h3>Personalized</h3>
                <div class="diff-item">
                    <div class="diff-label">Headline</div>
                    <div class="diff-value">{personalized_copy.get('headline', 'N/A')}</div>
                </div>
                <div class="diff-item">
                    <div class="diff-label">Subheadline</div>
                    <div class="diff-value">{personalized_copy.get('subheadline', 'N/A')}</div>
                </div>
                <div class="diff-item">
                    <div class="diff-label">CTA</div>
                    <div class="diff-value">{personalized_copy.get('cta_text', 'N/A')}</div>
                </div>
            </div>
        </div>
        <div class="reasoning">
            <strong>Why these changes:</strong> {reasoning}
        </div>
    </div>

    <iframe
        class="page-frame"
        srcdoc="{modified_html.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')}"
    ></iframe>
</body>
</html>
"""
    return preview