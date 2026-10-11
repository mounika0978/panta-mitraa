"""Safe demo backend for the Rain-Fed Farming Decision Assistant.

This prototype intentionally uses transparent rules, not a generative model, for
agronomic guidance. Replace the demo rules only after approval by local KVK /
ANGRAU agricultural experts.
"""
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).parent
STATIC = ROOT / "static"
UPLOADS = ROOT / "work" / "uploads"
UPLOADS.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Rain-Fed Farming Assistant", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Lock this down to the deployed domain in production.
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=STATIC), name="static")


class AdvisoryRequest(BaseModel):
    village: str = Field(min_length=2, max_length=80)
    crop: Literal["groundnut", "red_gram", "millet"]
    stage: Literal["not_sown", "newly_sown", "vegetative", "flowering", "pod_grain", "harvest"]
    rain_last_7_days_mm: float = Field(ge=0, le=1000)
    forecast_rain_next_5_days_mm: float = Field(ge=0, le=1000)
    days_without_rain: int = Field(ge=0, le=90)


class CallbackRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    phone: str = Field(pattern=r"^[6-9][0-9]{9}$")
    village: str = Field(min_length=2, max_length=80)
    concern: str = Field(min_length=5, max_length=500)


TELUGU_CROPS = {"groundnut": "వేరుశనగ", "red_gram": "కంది", "millet": "చిరుధాన్యం"}


def advice_for(data: AdvisoryRequest) -> dict:
    """Small, auditable demo rule set—not a replacement for expert advice."""
    risk = "low"
    title = "పరిస్థితిని గమనించండి"
    message = "వాతావరణ పరిస్థితిని మరియు పంటను రోజూ గమనించండి."
    actions = ["స్థానిక వ్యవసాయ అధికారుల తాజా సూచనలు చూడండి."]

    severe_dry = data.days_without_rain >= 10 and data.forecast_rain_next_5_days_mm < 10
    low_moisture = data.rain_last_7_days_mm < 15 and data.forecast_rain_next_5_days_mm < 15

    if data.stage == "not_sown" and data.forecast_rain_next_5_days_mm < 20:
        risk, title = "medium", "విత్తనానికి ముందు జాగ్రత్త"
        message = "తగిన నేల తేమ లేకపోతే విత్తనాన్ని వెంటనే వేయడం ప్రమాదకరం కావచ్చు."
        actions = [
            "స్థానికంగా తగిన నేల తేమ ఉందో పరిశీలించండి.",
            "చిన్నకాల వాతావరణ సూచనను మరియు KVK/వ్యవసాయ అధికారిని సంప్రదించండి.",
        ]
    elif severe_dry and data.stage in {"flowering", "pod_grain"}:
        risk, title = "high", "పొడి కాలం ప్రమాదం ఎక్కువ"
        message = "పుష్పించే లేదా కాయ/గింజ దశలో పొడి కాలం పంటపై ప్రభావం చూపవచ్చు."
        actions = [
            "పొలంలో వాడిపోవడం లేదా తేమ తగ్గుదల ఉందో పరిశీలించండి.",
            "స్థానికంగా ఆమోదించిన తేమ-సంరక్షణ చర్యల కోసం వ్యవసాయ అధికారిని సంప్రదించండి.",
            "తీవ్ర లక్షణాలు ఉంటే నిపుణుడి కాల్‌బ్యాక్ కోరండి.",
        ]
    elif severe_dry or low_moisture:
        risk, title = "medium", "పొడి కాలం అవకాశం"
        message = "తక్కువ వర్షపాతం మరియు పొడి పరిస్థితులు పంటను ఒత్తిడికి గురిచేయవచ్చు."
        actions = [
            "పొలాన్ని గమనించి నేల తేమను పరిశీలించండి.",
            "అధికారిక స్థానిక సలహా ప్రకారం మాత్రమే చర్య తీసుకోండి.",
        ]

    return {
        "risk": risk,
        "title_te": title,
        "message_te": message,
        "actions_te": actions,
        "source": "Demo rule set — must be reviewed by local KVK/ANGRAU experts before field use.",
        "disclaimer_te": "ఇది సాధారణ సమాచారం మాత్రమే; వర్షం లేదా దిగుబడికి హామీ కాదు. మందులు లేదా ఎరువుల మోతాదులకు స్థానిక నిపుణుడిని సంప్రదించండి.",
        "context": {"crop_te": TELUGU_CROPS[data.crop], "village": data.village},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(STATIC / "index.html")


@app.post("/api/advisory")
def get_advisory(data: AdvisoryRequest):
    return advice_for(data)


@app.post("/api/callback")
def request_callback(data: CallbackRequest):
    # Demo only: do not persist personal data until consent, access control, and
    # a secure database are implemented.
    return {"status": "received", "message_te": "మీ కాల్‌బ్యాక్ అభ్యర్థన నమోదు అయింది. డెమోలో కాల్ చేయబడదు."}


@app.post("/api/photo")
async def upload_photo(photo: UploadFile = File(...)):
    allowed = {"image/jpeg", "image/png", "image/webp"}
    if photo.content_type not in allowed:
        raise HTTPException(400, "Upload a JPG, PNG, or WebP image.")
    content = await photo.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(400, "Image must be 5 MB or smaller.")
    filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}-{Path(photo.filename or 'leaf.jpg').name}"
    (UPLOADS / filename).write_bytes(content)
    return {
        "status": "received",
        "message_te": "ఫోటో అందింది. ఈ డెమో ఫోటో ద్వారా వ్యాధి నిర్ధారణ చేయదు.",
        "next_step_te": "లక్షణాలు తీవ్రంగా ఉంటే సమీప వ్యవసాయ అధికారి లేదా KVKని సంప్రదించండి.",
    }
