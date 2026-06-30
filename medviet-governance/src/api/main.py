from pathlib import Path

import pandas as pd
from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse

from src.access.rbac import get_current_user, require_permission
from src.pii.anonymizer import MedVietAnonymizer

RAW_DATA_PATH = Path("data/raw/patients_raw.csv")
ANON_DATA_PATH = Path("data/processed/patients_anonymized.csv")

app = FastAPI(title="MedViet Data API", version="1.0.0")
anonymizer = MedVietAnonymizer()


def _load_raw_patients() -> pd.DataFrame:
    return pd.read_csv(RAW_DATA_PATH)


@app.get("/api/patients/raw")
@require_permission(resource="patient_data", action="read")
async def get_raw_patients(current_user: dict = Depends(get_current_user)):
    df = _load_raw_patients()
    return JSONResponse(content=df.head(10).to_dict(orient="records"))


@app.get("/api/patients/anonymized")
@require_permission(resource="training_data", action="read")
async def get_anonymized_patients(current_user: dict = Depends(get_current_user)):
    df = _load_raw_patients()
    df_anon = anonymizer.anonymize_dataframe(df)

    ANON_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_anon.to_csv(ANON_DATA_PATH, index=False)

    return JSONResponse(content=df_anon.head(10).to_dict(orient="records"))


@app.get("/api/metrics/aggregated")
@require_permission(resource="aggregated_metrics", action="read")
async def get_aggregated_metrics(current_user: dict = Depends(get_current_user)):
    df = _load_raw_patients()
    metrics = {
        "total_patients": int(len(df)),
        "by_condition": df["benh"].value_counts().to_dict(),
        "avg_lab_result": float(df["ket_qua_xet_nghiem"].mean()),
    }
    return metrics


@app.delete("/api/patients/{patient_id}")
@require_permission(resource="patient_data", action="delete")
async def delete_patient(
    patient_id: str,
    current_user: dict = Depends(get_current_user),
):
    return {
        "status": "deleted",
        "patient_id": patient_id,
        "message": "Simulated delete. Production should use soft delete and audit logs.",
    }


@app.get("/health")
async def health():
    return {"status": "ok", "service": "MedViet Data API"}
