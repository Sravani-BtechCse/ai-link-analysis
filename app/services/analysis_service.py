import hashlib, time
from app.services.website_extractor import fetch_website
from app.services.llm_service import analyze_with_llm

_CACHE: dict[str, tuple[float, dict]] = {}

async def run_analysis(url: str) -> dict:
    key = hashlib.sha256(url.encode()).hexdigest()
    now = time.time()
    cached = _CACHE.get(key)
    if cached and cached[0] > now:
        result = dict(cached[1])
        result["source"] = {**result["source"], "cached": True}
        return result
    site = await fetch_website(url)
    brand, analysis, model_name = await analyze_with_llm(site)
    result = {
        "success": True,
        "website": site["final_url"],
        "brand": brand.model_dump(),
        "analysis": analysis.model_dump(),
        "source": {
            "page_title": site["title"],
            "meta_description": site["meta_description"],
            "characters_extracted": site["characters_extracted"],
            "content_truncated": site["content_truncated"],
            "cached": False,
            "competitor_research_note": "Competitors are AI-generated suggestions unless independently verified."
        },
        "model": model_name
    }
    from app.config import get_settings
    _CACHE[key] = (now + get_settings().cache_ttl_seconds, result)
    return result
