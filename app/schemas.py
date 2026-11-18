from typing import Any
from pydantic import BaseModel, Field, HttpUrl, ConfigDict

class LinkAnalysisRequest(BaseModel):
    url: HttpUrl

class Competitor(BaseModel):
    name: str
    website: str | None = None
    strengths: list[str] = Field(default_factory=list)
    weaknesses_or_gaps: list[str] = Field(default_factory=list)
    comparison_note: str

class CompetitorAnalysis(BaseModel):
    brand_overview: str
    business_category: str
    main_products_services: list[str]
    competitors: list[Competitor] = Field(default_factory=list)
    brand_strengths: list[str] = Field(default_factory=list)
    competitive_advantages: list[str] = Field(default_factory=list)
    opportunities: list[str] = Field(default_factory=list)
    evidence_note: str

class SearchQuery(BaseModel):
    query: str
    platforms: list[str]
    intent: str
    business_relevance: str
    target_audience: str

class SEOImprovements(BaseModel):
    primary_keyword: str
    secondary_keywords: list[str]
    long_tail_keywords: list[str]
    recommended_title: str
    title_primary_keyword: str
    meta_description: str
    supporting_content: list[str]

class ServiceItem(BaseModel):
    service_name: str
    description: str
    target_industry: str
    target_customer: str
    main_benefit: str
    evidence: str
    inferred: bool = False

class TargetAudience(BaseModel):
    primary_audience: list[str]
    secondary_audience: list[str]
    industries: list[str]
    business_types: list[str]
    customer_profiles: list[str]
    geographic_focus: list[str]
    customer_needs: list[str]
    potential_interests: list[str]
    recommended_marketing_segments: list[str]

class Analysis(BaseModel):
    competitor_analysis: CompetitorAnalysis
    target_search_queries: list[SearchQuery]
    seo_improvements: SEOImprovements
    top_services: list[ServiceItem]
    target_audience: TargetAudience

class Brand(BaseModel):
    name: str
    category: str
    summary: str

class LinkAnalysisResponse(BaseModel):
    success: bool = True
    website: str
    brand: Brand
    analysis: Analysis
    source: dict[str, Any]
    model: str
