from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.config import get_settings
from app.schemas import LinkAnalysisRequest
from app.services.analysis_service import run_analysis

settings = get_settings()
app = FastAPI(title=settings.app_name, version="1.0.0",
              description="Extracts public website content and generates structured AI marketing insights.")

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", include_in_schema=False)
async def homepage():
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/link-analysis")
async def link_analysis(payload: LinkAnalysisRequest):
    try:
        return await run_analysis(str(payload.url))
    except HTTPException:
        raise
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Unexpected analysis error. Check server logs.")
