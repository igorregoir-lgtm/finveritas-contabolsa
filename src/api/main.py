"""
FastAPI Backend for FinVeritas Contabolsa
Real endpoints using the domain service.
"""

import logging
import os
import signal
import time
from contextlib import asynccontextmanager
from decimal import Decimal
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pydantic import BaseModel, Field, field_validator

from ..application.finveritas_service import FinVeritasService
from ..domain.journal import JournalLine
from ..infrastructure.database import get_db_session, init_db
from ..infrastructure.event_repository import SQLAlchemyEventRepository
from ..infrastructure.settings import Settings, get_settings


REQUEST_COUNT = Counter(
    "finveritas_api_requests_total",
    "Total API requests",
    ["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "finveritas_api_request_duration_seconds",
    "API request latency in seconds",
    ["method", "path"],
)
JOURNAL_ENTRIES = Counter(
    "finveritas_journal_entries_total",
    "Total journal entries posted",
)
FISCAL_IMPORTS = Counter(
    "finveritas_fiscal_imports_total",
    "Total fiscal imports",
)


def _configure_logging(settings: Settings) -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


logger = logging.getLogger("finveritas.api")

# ── Singleton in-memory service (avoids state loss between requests) ──────────
_in_memory_service: Optional[FinVeritasService] = None


def _get_in_memory_service() -> FinVeritasService:
    global _in_memory_service
    if _in_memory_service is None:
        _in_memory_service = FinVeritasService()
    return _in_memory_service


def get_service() -> FinVeritasService:
    settings = get_settings()
    db_url = str(settings.database_url)
    if os.getenv("DATABASE_URL") and "sqlite" not in db_url.lower():
        session = next(get_db_session())
        repo = SQLAlchemyEventRepository(session)
        return FinVeritasService(journal_repo=repo)
    return _get_in_memory_service()


APP_VERSION = "1.0.0"


# ── Lifespan (replaces deprecated @app.on_event) ─────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    _configure_logging(settings)
    init_db()
    logger.info("FinVeritas API starting (version=%s)", APP_VERSION)
    yield
    logger.info("FinVeritas API shutting down")


app = FastAPI(
    title="FinVeritas Contabolsa API",
    description="Sistema de contabilidade padrão B3 com anti-fraude ironclad",
    version=APP_VERSION,
    lifespan=lifespan,
)


def _handle_signal(signum: int, frame):
    logger.info("Received signal %s, shutting down gracefully", signal.Signals(signum).name)
    raise SystemExit(0)


signal.signal(signal.SIGTERM, _handle_signal)
signal.signal(signal.SIGINT, _handle_signal)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_and_measure(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start
    elapsed_ms = elapsed * 1000
    path = request.url.path
    status = str(response.status_code)
    REQUEST_COUNT.labels(method=request.method, path=path, status=status).inc()
    REQUEST_LATENCY.labels(method=request.method, path=path).observe(elapsed)
    logger.info(
        "%s %s - %s - %.2fms",
        request.method,
        path,
        response.status_code,
        elapsed_ms,
    )
    return response


# ── Pydantic request models ───────────────────────────────────────────────────
class PixEntry(BaseModel):
    model_config = {"strict": True, "extra": "forbid"}

    chave: str
    valor: float = Field(..., ge=0)


class JournalLineIn(BaseModel):
    model_config = {"strict": True}

    account: str
    debit: float = Field(default=0, ge=0)
    credit: float = Field(default=0, ge=0)
    description: str = ""


class JournalEntryRequest(BaseModel):
    model_config = {"strict": True, "extra": "forbid"}

    description: str
    lines: List[JournalLineIn]
    actor: str = "api-user"

    @field_validator("lines")
    @classmethod
    def _balanced(cls, lines: List[JournalLineIn]) -> List[JournalLineIn]:
        total_debit = sum(line.debit for line in lines)
        total_credit = sum(line.credit for line in lines)
        if total_debit != total_credit:
            raise ValueError("Double entry must balance: total debits equal total credits")
        return lines


class FiscalImportRequest(BaseModel):
    model_config = {"strict": True, "extra": "forbid"}

    pix: PixEntry
    nfe: Optional[dict] = None
    actor: str = "api-user"


class WhatIfRequest(BaseModel):
    model_config = {"strict": True, "extra": "forbid"}

    interco_loan_delta_m: float = 0.0
    ebitda_multiplier: float = Field(default=1.0, gt=0, le=10)


class StressRequest(BaseModel):
    model_config = {"strict": True, "extra": "forbid"}

    stress_factor: float = Field(default=0.2, ge=0, le=1)


# ── Core endpoints ────────────────────────────────────────────────────────────
@app.get("/health")
def health(service: FinVeritasService = Depends(get_service)):
    journal = service.journal
    return {
        "status": "ok",
        "service": "finveritas-contabolsa",
        "version": APP_VERSION,
        "journal": {
            "entry_count": len(journal.get_events()),
            "chain_valid": journal.verify_integrity(),
        },
    }


@app.get("/metrics")
def metrics():
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


@app.post(
    "/journal/entry",
    responses={
        400: {"description": "Business rule violation"},
        403: {"description": "Blocked by anti-fraud policy"},
    },
)
def post_journal_entry(req: JournalEntryRequest, service: FinVeritasService = Depends(get_service)):
    try:
        lines = [
            JournalLine(
                account=line.account,
                debit=Decimal(str(line.debit)),
                credit=Decimal(str(line.credit)),
                description=line.description,
            )
            for line in req.lines
        ]
        event = service.post_journal_entry(req.description, lines, actor=req.actor)
        JOURNAL_ENTRIES.inc()
        return {"id": event.id, "hash": event.current_hash, "description": req.description}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post(
    "/fiscal/import",
    responses={
        400: {"description": "Business rule violation"},
        403: {"description": "Blocked by anti-fraud policy"},
    },
)
def import_fiscal(req: FiscalImportRequest, service: FinVeritasService = Depends(get_service)):
    try:
        pix_dict = req.pix.model_dump()
        result = service.import_fiscal(pix_dict, req.nfe, actor=req.actor)
        FISCAL_IMPORTS.inc()
        return result
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/solvency")
def get_solvency(service: FinVeritasService = Depends(get_service)):
    card = service.calculate_solvency()
    return {
        "credit_score": card.credit_score,
        "overall_status": card.overall_status,
        "ratios": [
            {"name": r.name, "value": float(r.value), "status": r.status, "explanation": r.explanation}
            for r in card.ratios
        ],
        "flags": card.flags,
    }


@app.post("/export", responses={400: {"description": "Business rule violation"}})
def export_to_bank(service: FinVeritasService = Depends(get_service)):
    try:
        return service.export_to_bank()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/fraud-log")
def get_fraud_log(service: FinVeritasService = Depends(get_service)):
    return [
        {
            "timestamp": a.timestamp,
            "action": a.action,
            "amount": float(a.amount) if a.amount else None,
            "decision": a.decision.value,
            "reason": a.reason,
        }
        for a in service.get_fraud_log()
    ]


# ── Group Consolidation endpoints (main FinStatement Pro flow) ────────────────
@app.post("/consolidation/load-group")
def load_group(service: FinVeritasService = Depends(get_service)):
    return service.load_group_demo()


@app.post("/consolidation/run", responses={400: {"description": "Business rule violation"}})
def run_consolidation(service: FinVeritasService = Depends(get_service)):
    try:
        return service.run_consolidation()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/consolidation/covenants")
def get_covenants(service: FinVeritasService = Depends(get_service)):
    covs = service.get_last_covenants()
    return [
        {
            "covenant_code": c.covenant_code,
            "scope_id": c.scope_id,
            "observed_value": str(c.observed_value),
            "threshold": str(c.threshold),
            "status": c.status,
            "headroom": str(c.headroom),
        }
        for c in covs
    ]


@app.get("/consolidation/eliminations")
def get_eliminations(service: FinVeritasService = Depends(get_service)):
    elims = service.get_last_elims()
    return [
        {
            "elim_id": e.elim_id,
            "elimination_type": e.elimination_type.value,
            "rule_code": e.rule_code,
            "source_hashes": e.source_hashes,
        }
        for e in elims
    ]


@app.get("/consolidation/explanations")
def get_explanations(service: FinVeritasService = Depends(get_service)):
    return [
        {
            "explanation_id": e.explanation_id,
            "object_type": e.object_type,
            "kind": e.kind,
            "payload": e.payload,
            "source_event_hashes": e.source_event_hashes,
        }
        for e in service.get_explanations()
    ]


@app.post("/consolidation/what-if", responses={400: {"description": "Business rule violation"}})
def apply_what_if(req: WhatIfRequest, service: FinVeritasService = Depends(get_service)):
    if req.ebitda_multiplier < 0.0001:
        raise HTTPException(status_code=422, detail="ebitda_multiplier must be at least 0.0001")
    return service.apply_what_if(
        interco_loan_delta=Decimal(str(req.interco_loan_delta_m * 1_000_000)),
        ebitda_multiplier=Decimal(str(req.ebitda_multiplier)),
    )


@app.post("/consolidation/stress", responses={400: {"description": "Business rule violation"}})
def stress_test(req: StressRequest, service: FinVeritasService = Depends(get_service)):
    return service.run_stress_test(req.stress_factor)


@app.get("/consolidation/trends")
def covenant_trends(service: FinVeritasService = Depends(get_service)):
    return service.get_covenant_trends()


@app.get("/consolidation/anomalies")
def detect_anomalies(service: FinVeritasService = Depends(get_service)):
    return service.run_ai_anomaly()


@app.post("/consolidation/export-bank-pack", responses={400: {"description": "Business rule violation"}})
def export_bank_pack(service: FinVeritasService = Depends(get_service)):
    return service.export_for_bank()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",  # nosec B104: intentional container exposure
        port=8000,
        reload=True,
    )
