import google.generativeai as genai
import os
import json
import PIL.Image
import io

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")


def test_gemini_connection():
    response = model.generate_content("Say hello in one sentence.")
    return response.text


def analyze_ad_creative(image_bytes: bytes) -> dict:
    image = PIL.Image.open(io.BytesIO(image_bytes))

    prompt = """
    You are an expert digital marketing analyst specializing in CRO (Conversion Rate Optimization).
    
    Analyze this ad creative carefully and extract the following information.
    
    Return ONLY a valid JSON object with exactly these keys, nothing else before or after:
    {
        "main_offer": "the primary offer or hook in the ad (e.g. 50% off, Free trial, Lose 10kg)",
        "cta_text": "the call to action text visible in the ad (e.g. Shop Now, Get Started, Book a Call)",
        "tone": "one of: urgent, friendly, aspirational, professional, playful, emotional",
        "target_audience": "who this ad is targeting based on visuals and copy",
        "key_message": "one sentence summarizing the core message of the ad",
        "visual_theme": "brief description of the visual style and dominant colors",
        "pain_point": "the problem or desire this ad is addressing"
    }
    
    If any field cannot be determined from the ad, use null for that field.
    Do not include any explanation, markdown formatting, or code blocks. Return raw JSON only.
    """

    response = model.generate_content([prompt, image])
    raw = response.text.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    return json.loads(raw)