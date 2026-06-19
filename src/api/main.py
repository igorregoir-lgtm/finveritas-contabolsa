"""
FastAPI Backend for FinVeritas Contabolsa
Real endpoints using the domain service.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from decimal import Decimal
from typing import List, Optional
import os

from ..application.finveritas_service import FinVeritasService
from ..domain.journal import JournalLine
from ..infrastructure.database import init_db, get_db_session
from ..infrastructure.event_repository import SQLAlchemyEventRepository

app = FastAPI(
    title="FinVeritas Contabolsa API",
    description="Sistema de contabilidade padrão B3 com anti-fraude ironclad",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production restrict
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency for service
def get_service():
    # Use persistent service if DB available, else in-memory
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        session = next(get_db_session())
        repo = SQLAlchemyEventRepository(session)
        return FinVeritasService(journal_repo=repo)
    return FinVeritasService()  # falls back to in-memory

# Pydantic models
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

class SolvencyOverride(BaseModel):
    current_assets: Optional[float] = None
    # ... add more if needed for demo

@app.on_event("startup")
def on_startup():
    init_db()  # create tables if using DB

@app.get("/health")
def health():
    return {"status": "ok", "service": "finveritas-contabolsa"}

@app.post("/journal/entry")
def post_journal_entry(req: JournalEntryRequest, service: FinVeritasService = Depends(get_service)):
    try:
        lines = [
            JournalLine(
                account=l.account,
                debit=Decimal(str(l.debit)),
                credit=Decimal(str(l.credit)),
                description=l.description
            )
            for l in req.lines
        ]
        event = service.post_journal_entry(req.description, lines, actor=req.actor)
        return {
            "id": event.id,
            "hash": event.current_hash,
            "description": req.description
        }
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/fiscal/import")
def import_fiscal(req: FiscalImportRequest, service: FinVeritasService = Depends(get_service)):
    try:
        result = service.import_fiscal(req.pix, req.nfe, actor=req.actor)
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
        "status": card.overall_status,
        "ratios": [
            {
                "name": r.name,
                "value": float(r.value),
                "status": r.status,
                "explanation": r.explanation
            } for r in card.ratios
        ],
        "flags": card.flags
    }

@app.post("/export")
def export_to_bank(service: FinVeritasService = Depends(get_service)):
    try:
        pkg = service.export_to_bank()
        return pkg
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/fraud-log")
def get_fraud_log(service: FinVeritasService = Depends(get_service)):
    attempts = service.get_fraud_log()
    return [
        {
            "timestamp": a.timestamp,
            "action": a.action,
            "amount": float(a.amount) if a.amount else None,
            "decision": a.decision.value,
            "reason": a.reason
        }
        for a in attempts
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
