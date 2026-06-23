"""
FastAPI Backend for FinVeritas Contabolsa
Real endpoints using the domain service.
"""

import os
from contextlib import asynccontextmanager
from decimal import Decimal
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ..application.finveritas_service import FinVeritasService
from ..domain.journal import JournalLine
from ..infrastructure.database import get_db_session, init_db
from ..infrastructure.event_repository import SQLAlchemyEventRepository

# ── Singleton in-memory service (avoids state loss between requests) ──────────
_in_memory_service: Optional[FinVeritasService] = None


def _get_in_memory_service() -> FinVeritasService:
    global _in_memory_service
    if _in_memory_service is None:
        _in_memory_service = FinVeritasService()
    return _in_memory_service


def get_service() -> FinVeritasService:
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        session = next(get_db_session())
        repo = SQLAlchemyEventRepository(session)
        return FinVeritasService(journal_repo=repo)
    return _get_in_memory_service()


# ── Lifespan (replaces deprecated @app.on_event) ─────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


APP_VERSION = "1.0.0"

app = FastAPI(
    title="FinVeritas Contabolsa API",
    description="Sistema de contabilidade padrão B3 com anti-fraude ironclad",
    version=APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production restrict
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic request models ───────────────────────────────────────────────────
class JournalLineIn(BaseModel):
    account: str
    debit: float = 0
    credit: float = 0
    description: str = ""


class JournalEntryRequest(BaseModel):
    description: str
    lines: List[JournalLineIn]
    actor: str = "api-user"


class FiscalImportRequest(BaseModel):
    pix: dict
    nfe: Optional[dict] = None
    actor: str = "api-user"


class WhatIfRequest(BaseModel):
    interco_loan_delta_m: float = 0.0
    ebitda_multiplier: float = 1.0


class StressRequest(BaseModel):
    stress_factor: float = 0.2


# ── Core endpoints ────────────────────────────────────────────────────────────
@app.get("/health")
def health(service: FinVeritasService = Depends(get_service)):
    journal = service.get_journal()
    return {
        "status": "ok",
        "service": "finveritas-contabolsa",
        "version": APP_VERSION,
        "journal": {
            "entry_count": journal.entry_count,
            "chain_valid": journal.verify_integrity(),
        },
    }


@app.post("/journal/entry")
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
        return {"id": event.id, "hash": event.current_hash, "description": req.description}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/fiscal/import")
def import_fiscal(req: FiscalImportRequest, service: FinVeritasService = Depends(get_service)):
    try:
        return service.import_fiscal(req.pix, req.nfe, actor=req.actor)
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


@app.post("/export")
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


@app.post("/consolidation/run")
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


@app.post("/consolidation/what-if")
def apply_what_if(req: WhatIfRequest, service: FinVeritasService = Depends(get_service)):
    return service.apply_what_if(
        interco_loan_delta=Decimal(str(req.interco_loan_delta_m * 1_000_000)),
        ebitda_multiplier=Decimal(str(req.ebitda_multiplier)),
    )


@app.post("/consolidation/stress")
def stress_test(req: StressRequest, service: FinVeritasService = Depends(get_service)):
    return service.run_stress_test(req.stress_factor)


@app.get("/consolidation/trends")
def covenant_trends(service: FinVeritasService = Depends(get_service)):
    return service.get_covenant_trends()


@app.get("/consolidation/anomalies")
def detect_anomalies(service: FinVeritasService = Depends(get_service)):
    return service.run_ai_anomaly()


@app.post("/consolidation/export-bank-pack")
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
