import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from concurrent.futures import ThreadPoolExecutor
import asyncio
import re


def _playwright_sync(url: str) -> dict:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        })

        page.goto(url, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2000)

        html = page.content()
        browser.close()

        return extract_sections_from_html(html)


async def scrape_with_playwright(url: str) -> dict:
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, _playwright_sync, url)
    return result


def scrape_with_requests(url: str) -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    return extract_sections_from_html(response.text)


def deduplicate_text(text: str) -> str:
    if not text:
        return text
    parts = re.split(r'(?<=[a-z])(?=[A-Z])', text)
    if len(parts) > 1:
        return parts[-1].strip()
    words = text.split()
    half = len(words) // 2
    for size in range(half, 0, -1):
        chunk = " ".join(words[:size])
        remainder = " ".join(words[size:])
        if remainder.startswith(chunk):
            return chunk
    return text


def extract_sections_from_html(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    headline = None
    h1_tags = soup.find_all("h1")
    for h1 in h1_tags:
        text = h1.get_text(strip=True)
        if len(text) > 5:
            headline = text
            break

    if not headline:
        for div in soup.find_all("div", class_=True):
            classes = " ".join(div.get("class", []))
            if "heading" in classes.lower() or "hero" in classes.lower():
                text = div.get_text(strip=True)
                if len(text) > 5 and len(text) < 200:
                    headline = text
                    break

    headline = deduplicate_text(headline)

    subheadline = None
    h2_tags = soup.find_all("h2")
    for h2 in h2_tags:
        text = h2.get_text(strip=True)
        if len(text) > 5:
            subheadline = text
            break

    if not subheadline:
        for tag in ["h3", "p"]:
            candidates = soup.find_all(tag)
            for candidate in candidates:
                text = candidate.get_text(strip=True)
                if len(text) > 20 and len(text) < 300:
                    subheadline = text
                    break
            if subheadline:
                break

    subheadline = deduplicate_text(subheadline)

    cta_text = None
    for a_tag in soup.find_all("a", class_=True):
        classes = " ".join(a_tag.get("class", []))
        if any(word in classes.lower() for word in ["btn", "button", "cta"]):
            text = a_tag.get_text(strip=True)
            if text:
                cta_text = text
                break

    if not cta_text:
        for button in soup.find_all("button"):
            text = button.get_text(strip=True)
            if text and len(text) < 50:
                cta_text = text
                break

    if not cta_text:
        cta_keywords = ["get started", "try free", "sign up", "buy now",
                        "shop now", "book", "learn more", "start", "join"]
        for a_tag in soup.find_all("a"):
            text = a_tag.get_text(strip=True).lower()
            if any(keyword in text for keyword in cta_keywords):
                cta_text = a_tag.get_text(strip=True)
                break

    page_title = None
    title_tag = soup.find("title")
    if title_tag:
        page_title = title_tag.get_text(strip=True)

    return {
        "headline": headline,
        "subheadline": subheadline,
        "cta_text": cta_text,
        "page_title": page_title,
        "scrape_method": None
    }

async def scrape_landing_page(url: str) -> dict:
    try:
        result = await scrape_with_playwright(url)
        result["scrape_method"] = "playwright"
        if result["headline"]:
            return result
    except Exception as e:
        print(f"Playwright scraping failed: {e}")

    try:
        result = scrape_with_requests(url)
        result["scrape_method"] = "requests"
        if result["headline"]:
            return result
    except Exception as e:
        print(f"Requests scraping failed: {e}")

    return {
        "headline": None,
        "subheadline": None,
        "cta_text": None,
        "page_title": None,
        "scrape_method": "failed",
        "error": "Could not extract content from this page. The page may be behind authentication or block automated access."
    }