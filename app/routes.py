from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from app.gemini_client import test_gemini_connection, analyze_ad_creative
from app.scrapper import scrape_landing_page
from app.personalizer import generate_personalized_copy, inject_copy_into_html
import requests as http_requests

router = APIRouter()


@router.get("/test-gemini")
def test_gemini():
    result = test_gemini_connection()
    return {"gemini_response": result}


@router.post("/analyze-ad")
async def analyze_ad(file: UploadFile = File(...)):
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type.")
    image_bytes = await file.read()
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Max 10MB.")
    try:
        result = analyze_ad_creative(image_bytes)
        return {"status": "success", "ad_analysis": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze ad: {str(e)}")


@router.post("/scrape-page")
async def scrape_page(payload: dict):
    url = payload.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="URL is required.")
    if not url.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid URL.")
    try:
        result = await scrape_landing_page(url)
        return {"status": "success", "page_sections": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")


@router.post("/personalize", response_class=HTMLResponse)
async def personalize(
    file: UploadFile = File(...),
    url: str = Form(...)
):
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type.")
    image_bytes = await file.read()
    try:
        ad_analysis = analyze_ad_creative(image_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ad analysis failed: {str(e)}")
    try:
        page_sections = await scrape_landing_page(url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")
    if page_sections.get("scrape_method") == "failed":
        raise HTTPException(status_code=422, detail="Could not scrape this page.")
    try:
        personalized_copy = generate_personalized_copy(ad_analysis, page_sections)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Personalization failed: {str(e)}")
    try:
        resp = http_requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        original_html = resp.text
    except Exception:
        original_html = f"<html><body><h1>{page_sections.get('headline','')}</h1></body></html>"
    from app.personalizer import build_preview_html
    modified_html = inject_copy_into_html(original_html, personalized_copy)
    preview = build_preview_html(page_sections, personalized_copy, url, modified_html)
    return HTMLResponse(content=preview)


@router.post("/personalize-json")
async def personalize_json(
    file: UploadFile = File(...),
    url: str = Form(...)
):
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type.")

    image_bytes = await file.read()

    try:
        ad_analysis = analyze_ad_creative(image_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ad analysis failed: {str(e)}")

    try:
        page_sections = await scrape_landing_page(url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

    if page_sections.get("scrape_method") == "failed":
        raise HTTPException(
            status_code=422,
            detail="Could not scrape this page. Try a different URL."
        )

    try:
        personalized_copy = generate_personalized_copy(ad_analysis, page_sections)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Personalization failed: {str(e)}")

    try:
        resp = http_requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        original_html = resp.text
    except Exception:
        original_html = f"<html><body><h1>{page_sections.get('headline','')}</h1></body></html>"

    modified_html = inject_copy_into_html(original_html, personalized_copy)

    return JSONResponse(content={
        "original": {
            "headline": page_sections.get("headline"),
            "subheadline": page_sections.get("subheadline"),
            "cta_text": page_sections.get("cta_text")
        },
        "personalized": personalized_copy,
        "modified_html": modified_html,
        "ad_analysis": ad_analysis
    })