import json
from pydantic import ValidationError
from app.config import get_settings
from app.schemas import Analysis, Brand

SYSTEM_PROMPT = """You are a careful digital marketing analyst. Use only the supplied website evidence
for claims about the submitted brand and its services. Clearly mark inferences. Competitor names may be
suggested from general knowledge, but say they are AI-generated suggestions and do not imply live research.
Never invent search volumes, rankings, traffic, or measured performance. Return valid JSON matching the
requested schema. Provide exactly five target search queries across Google, Facebook, Instagram, LinkedIn,
and X (Twitter), and up to five services supported by evidence. If evidence is insufficient, say so."""

def _prompt(site: dict) -> str:
    return f"""Analyze this website and return one JSON object with keys:
brand: {{name, category, summary}}
analysis: {{
 competitor_analysis: {{brand_overview, business_category, main_products_services,
   competitors:[{{name, website, strengths:[], weaknesses_or_gaps:[], comparison_note}}],
   brand_strengths:[], competitive_advantages:[], opportunities:[], evidence_note}},
 target_search_queries:[{{query, platforms:[], intent, business_relevance, target_audience}}],
 seo_improvements:{{primary_keyword, secondary_keywords:[], long_tail_keywords:[],
   recommended_title, title_primary_keyword, meta_description, supporting_content:[]}},
 top_services:[{{service_name, description, target_industry, target_customer, main_benefit, evidence, inferred}}],
 target_audience:{{primary_audience:[], secondary_audience:[], industries:[], business_types:[],
   customer_profiles:[], geographic_focus:[], customer_needs:[], potential_interests:[],
   recommended_marketing_segments:[]}}
}}
Rules: use the actual page content; do not fabricate facts; competitors should be suggestions and labelled as such;
include five queries and no search-volume claims; provide up to five services, distinguishing inferred items.
Website URL: {site['final_url']}
Page title: {site['title']}
Meta description: {site['meta_description']}
H1 headings: {site['h1']}
Other headings: {site['headings']}
Extracted page text:
{site['text']}
"""
async def analyze_with_llm(site: dict) -> tuple[Brand, Analysis, str]:
    settings = get_settings()
    provider = settings.llm_provider.lower()
    prompt = _prompt(site)
    try:
        if provider == "gemini":
            if not settings.gemini_api_key:
                raise RuntimeError("GEMINI_API_KEY is missing. Add it to .env.")
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=settings.gemini_api_key)
            response = await client.aio.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    temperature=settings.model_temperature,
                ),
            )
            raw, model_name = response.text, settings.gemini_model
        elif provider == "openai":
            if not settings.openai_api_key:
                raise RuntimeError("OPENAI_API_KEY is missing. Add it to .env.")
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.openai_api_key)
            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role":"system","content":SYSTEM_PROMPT},
                          {"role":"user","content":prompt}],
                response_format={"type":"json_object"},
                temperature=settings.model_temperature,
            )
            raw, model_name = response.choices[0].message.content, settings.openai_model
        elif provider == "anthropic":
            if not settings.anthropic_api_key:
                raise RuntimeError("ANTHROPIC_API_KEY is missing. Add it to .env.")
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic(api_key=settings.anthropic_api_key)
            response = await client.messages.create(
                model=settings.anthropic_model, max_tokens=5000,
                system=SYSTEM_PROMPT + " Return only valid JSON.",
                messages=[{"role":"user","content":prompt}],
            )
            raw, model_name = response.content[0].text, settings.anthropic_model
        else:
            raise RuntimeError("Unsupported LLM_PROVIDER. Choose gemini, openai, or anthropic.")
        data = json.loads(raw)
        brand = Brand.model_validate(data["brand"])
        analysis = Analysis.model_validate(data["analysis"])
        if len(analysis.target_search_queries) != 5:
            raise ValueError("The model did not return exactly five search queries.")
        return brand, analysis, model_name
    except (ValidationError, KeyError, json.JSONDecodeError, ValueError) as exc:
        raise RuntimeError(f"LLM returned an invalid analysis structure: {exc}") from exc
    except Exception as exc:
        if isinstance(exc, RuntimeError):
            raise
        raise RuntimeError(f"LLM provider request failed: {type(exc).__name__}: {exc}") from exc
