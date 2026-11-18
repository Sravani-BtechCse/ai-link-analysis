import ipaddress, socket
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup
from fastapi import HTTPException
from app.config import get_settings
from app.utils.validators import validate_public_url

USER_AGENT = "LinkAnalysisBot/1.0 (+website content analysis; respectful fetcher)"

def _assert_public_host(url: str) -> None:
    validate_public_url(url)

async def fetch_website(url: str) -> dict:
    settings = get_settings()
    _assert_public_host(url)
    timeout = httpx.Timeout(settings.request_timeout_seconds)
    limits = httpx.Limits(max_connections=5, max_keepalive_connections=2)
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=False, limits=limits,
                                     headers={"User-Agent": USER_AGENT}) as client:
            current = url
            response = None
            # Manually validate every redirect to reduce SSRF risk.
            for _ in range(4):
                _assert_public_host(current)
                response = await client.get(current)
                if response.is_redirect:
                    location = response.headers.get("location")
                    if not location:
                        break
                    current = urljoin(current, location)
                    continue
                break
            if response is None:
                raise HTTPException(status_code=502, detail="Website did not return a response.")
            if response.is_redirect:
                raise HTTPException(status_code=400, detail="Too many website redirects.")
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
                raise HTTPException(status_code=415, detail="The URL did not return an HTML page.")
            raw = response.content[:settings.max_html_bytes]
    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Website request timed out.")
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Website returned HTTP {exc.response.status_code}.")
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Could not retrieve the website.")

    soup = BeautifulSoup(raw, "html.parser")
    for node in soup(["script", "style", "noscript", "svg", "nav", "footer", "header"]):
        node.decompose()
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    description_tag = soup.find("meta", attrs={"name": "description"})
    description = description_tag.get("content", "").strip() if description_tag else ""
    h1 = [x.get_text(" ", strip=True) for x in soup.find_all("h1")[:8]]
    headings = [x.get_text(" ", strip=True) for x in soup.find_all(["h2", "h3"])[:20]]
    text = " ".join(soup.stripped_strings)
    text = " ".join(text.split())[:settings.max_text_chars]
    if len(text) < 80:
        raise HTTPException(status_code=422, detail="Not enough readable page content was found.")
    return {
        "final_url": current,
        "title": title,
        "meta_description": description,
        "h1": h1,
        "headings": headings,
        "text": text,
        "characters_extracted": len(text),
        "content_truncated": len(response.content) > settings.max_html_bytes or len(text) >= settings.max_text_chars
    }
