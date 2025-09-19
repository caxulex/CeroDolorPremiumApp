from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .flows.proyecto_a import run_checkin_flow
from .flows.proyecto_b import run_clinician_flow, run_researcher_flow
from .logging_utils import get_logger, set_trace_id
from .models import CheckinRequest, ClinicianRequest, Envelope, ResearcherRequest

logger = get_logger(__name__)

app = FastAPI(title="CeroDolor Orchestrator API")


@app.middleware("http")
async def add_trace_id(request: Request, call_next):
    set_trace_id(request.headers.get("x-trace-id"))
    return await call_next(request)


@app.get("/health", response_model=Envelope)
async def health() -> Envelope:
    return Envelope(ok=True, data={"status": "ok"})


@app.post("/proyecto-a/checkin", response_model=Envelope)
async def proyecto_a_checkin(req: CheckinRequest) -> Envelope:
    try:
        result = await run_checkin_flow(req)
        return Envelope(ok=True, data=result)
    except Exception as e:
        logger.exception("checkin failed")
        return Envelope(ok=False, error={"message": str(e)})


@app.post("/proyecto-b/clinician", response_model=Envelope)
async def proyecto_b_clinician(req: ClinicianRequest) -> Envelope:
    try:
        result = await run_clinician_flow(req)
        if "error" in result:
            return Envelope(ok=False, error=result)
        return Envelope(ok=True, data=result)
    except Exception as e:
        logger.exception("clinician flow failed")
        return Envelope(ok=False, error={"message": str(e)})


@app.post("/proyecto-b/researcher", response_model=Envelope)
async def proyecto_b_researcher(req: ResearcherRequest) -> Envelope:
    try:
        result = await run_researcher_flow(req)
        if "error" in result:
            return Envelope(ok=False, error=result)
        return Envelope(ok=True, data=result)
    except Exception as e:
        logger.exception("researcher flow failed")
        return Envelope(ok=False, error={"message": str(e)})


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception):
    logger.exception("unhandled error")
    return JSONResponse(status_code=500, content=Envelope(ok=False, error={"message": str(exc)}).dict())
