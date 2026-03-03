import os
import json
import pathlib
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import anthropic

app = FastAPI(title="Dropshipping Product Finder")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = pathlib.Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

client = anthropic.Anthropic()

# ---------------------------------------------------------------------------
# Trending products dataset (2025/2026 dropshipping trends)
# ---------------------------------------------------------------------------
TRENDING_PRODUCTS = [
    {
        "id": 1, "name": "Smart LED Strip Lights", "category": "Smart Home",
        "trend_score": 94, "direction": "up", "emoji": "💡",
        "price_range": "€8–€35", "tags": ["Bestseller", "Ganzjährig"],
        "description": "RGB-LEDs mit App-Steuerung und Sprachassistent-Kompatibilität"
    },
    {
        "id": 2, "name": "Tragbarer Mini-Beamer", "category": "Elektronik",
        "trend_score": 88, "direction": "up", "emoji": "📽️",
        "price_range": "€30–€120", "tags": ["Trending", "Hohe Marge"],
        "description": "Kompakter Projektor für Heimkino-Erlebnisse unterwegs"
    },
    {
        "id": 3, "name": "Hunde-Autositzabdeckung", "category": "Haustier",
        "trend_score": 85, "direction": "stable", "emoji": "🐾",
        "price_range": "€12–€45", "tags": ["Ganzjährig", "Niedrige Konkurrenz"],
        "description": "Wasserdichte Sitzschoner für Hunde im Auto"
    },
    {
        "id": 4, "name": "Elektrischer Nagelschneider", "category": "Beauty",
        "trend_score": 91, "direction": "up", "emoji": "💅",
        "price_range": "€5–€25", "tags": ["Viral", "Hohe Nachfrage"],
        "description": "Automatischer Nagelschneider für Babys und Senioren"
    },
    {
        "id": 5, "name": "Magnetisches Ladekabel", "category": "Zubehör",
        "trend_score": 89, "direction": "up", "emoji": "🔌",
        "price_range": "€3–€15", "tags": ["Immergrün", "Hohe Marge"],
        "description": "360° magnetische Schnellladekabel für alle Geräte"
    },
    {
        "id": 6, "name": "Stehschreibtisch-Aufsatz", "category": "Büro",
        "trend_score": 86, "direction": "up", "emoji": "🖥️",
        "price_range": "€20–€80", "tags": ["Home Office", "Ganzjährig"],
        "description": "Höhenverstellbarer Schreibtischaufsatz für gesundes Arbeiten"
    },
    {
        "id": 7, "name": "Schlaf-Kopfhörer Stirnband", "category": "Health",
        "trend_score": 83, "direction": "up", "emoji": "😴",
        "price_range": "€8–€30", "tags": ["Nische", "Geringe Konkurrenz"],
        "description": "Flache Bluetooth-Kopfhörer im Stirnband-Design zum Schlafen"
    },
    {
        "id": 8, "name": "Wasserflaschen-Reiniger", "category": "Küche",
        "trend_score": 80, "direction": "stable", "emoji": "🧴",
        "price_range": "€4–€18", "tags": ["Eco", "Ganzjährig"],
        "description": "UV-Sterilisator und Reiniger für Trinkflaschen"
    },
    {
        "id": 9, "name": "Kinder-Lernuhr", "category": "Spielzeug",
        "trend_score": 78, "direction": "up", "emoji": "⏰",
        "price_range": "€8–€35", "tags": ["Saisonal", "Geschenk-Idee"],
        "description": "Lehrreiche Wanduhr für Kinder zum Uhrenlernen"
    },
    {
        "id": 10, "name": "Silikon-Sportarmband", "category": "Sport",
        "trend_score": 76, "direction": "stable", "emoji": "🏃",
        "price_range": "€2–€12", "tags": ["Massenmarkt", "Hohe Menge"],
        "description": "Schweißfeste Ersatzbänder für Smartwatches und Fitnesstracker"
    },
    {
        "id": 11, "name": "Portable Neck Fan", "category": "Lifestyle",
        "trend_score": 87, "direction": "up", "emoji": "🌬️",
        "price_range": "€10–€40", "tags": ["Saisonal", "Viral"],
        "description": "Freihändiger USB-Nackenlüfter für heiße Sommertage"
    },
    {
        "id": 12, "name": "Posture Corrector", "category": "Health",
        "trend_score": 82, "direction": "up", "emoji": "🦴",
        "price_range": "€5–€20", "tags": ["Ganzjährig", "Gesundheitstrend"],
        "description": "Ergonomischer Haltungskorrektur-Gürtel für den Rücken"
    },
]

CATEGORIES = list({p["category"] for p in TRENDING_PRODUCTS})


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------
class AnalyzeRequest(BaseModel):
    product_name: str


class CompareRequest(BaseModel):
    product_name: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/")
async def index():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/api/trending")
async def get_trending():
    return {"products": TRENDING_PRODUCTS, "categories": sorted(CATEGORIES)}


@app.post("/api/analyze")
async def analyze_product(request: AnalyzeRequest):
    product = request.product_name.strip()
    if not product:
        raise HTTPException(400, "Produktname darf nicht leer sein")

    prompt = f"""Du bist ein erfahrener Dropshipping-Experte und Marktanalyst für den deutschsprachigen E-Commerce-Markt (Deutschland, Österreich, Schweiz).

Analysiere das folgende Produkt für ein Dropshipping-Business im Jahr 2026:

Produkt: "{product}"

Erstelle eine detaillierte JSON-Analyse mit GENAU dieser Struktur (keine zusätzlichen Felder, keine Markdown-Formatierung, nur reines JSON):

{{
  "product_name": "<Name>",
  "overall_score": <0-10 float>,
  "recommendation": "KAUFEN" | "PRÜFEN" | "MEIDEN",
  "recommendation_text": "<2-3 Sätze Begründung>",
  "market_demand": {{
    "score": <0-10>,
    "level": "Sehr Hoch" | "Hoch" | "Mittel" | "Niedrig",
    "description": "<2 Sätze>",
    "monthly_searches_estimate": "<z.B. 10.000–50.000>"
  }},
  "competition": {{
    "score": <0-10, wobei 10 = wenig Konkurrenz = gut>,
    "level": "Sehr Hoch" | "Hoch" | "Mittel" | "Niedrig",
    "description": "<2 Sätze>",
    "main_competitors": ["<Plattform1>", "<Plattform2>"]
  }},
  "profitability": {{
    "score": <0-10>,
    "purchase_price_estimate": "<z.B. 3–8 €>",
    "selling_price_estimate": "<z.B. 15–30 €>",
    "margin_estimate": "<z.B. 45–65%>",
    "description": "<2 Sätze>"
  }},
  "trend": {{
    "direction": "Stark steigend" | "Steigend" | "Stabil" | "Fallend",
    "seasonality": "Ganzjährig" | "Saisonal" | "Sommer" | "Winter" | "Q4",
    "peak_months": "<z.B. November–Januar>",
    "description": "<1-2 Sätze>"
  }},
  "target_audience": "<Beschreibung der Zielgruppe>",
  "best_platforms": ["<Plattform1>", "<Plattform2>", "<Plattform3>"],
  "advantages": ["<Vorteil1>", "<Vorteil2>", "<Vorteil3>", "<Vorteil4>"],
  "risks": ["<Risiko1>", "<Risiko2>", "<Risiko3>"],
  "marketing_tips": ["<Tipp1>", "<Tipp2>", "<Tipp3>"],
  "legal_notes": "<Wichtige rechtliche Hinweise für DE/AT/CH falls relevant, sonst leer>"
}}

Wichtig: Antworte NUR mit dem JSON-Objekt. Keine Erklärungen, kein Markdown."""

    try:
        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text.strip()
        # Strip possible markdown code fences
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise HTTPException(500, f"Ungültige JSON-Antwort von KI: {e}")
    except Exception as e:
        raise HTTPException(500, f"Analysefehler: {e}")


@app.post("/api/compare")
async def compare_suppliers(request: CompareRequest):
    product = request.product_name.strip()
    if not product:
        raise HTTPException(400, "Produktname darf nicht leer sein")

    prompt = f"""Du bist ein erfahrener Dropshipping-Einkaufsberater für den deutschsprachigen Markt.

Vergleiche die wichtigsten Lieferanten und Einkaufsquellen für das folgende Produkt im Jahr 2026:

Produkt: "{product}"

Erstelle eine detaillierte JSON-Analyse mit GENAU dieser Struktur (nur reines JSON, kein Markdown):

{{
  "product_name": "<Name>",
  "best_choice": "<Name des empfohlenen Lieferanten>",
  "summary": "<2-3 Sätze Gesamtempfehlung>",
  "suppliers": [
    {{
      "name": "AliExpress",
      "price_range": "<z.B. 3–8 €>",
      "shipping_time_de": "<z.B. 10–25 Tage>",
      "min_order_qty": <Zahl>,
      "quality_rating": <1-5>,
      "reliability_rating": <1-5>,
      "pros": ["<Pro1>", "<Pro2>", "<Pro3>"],
      "cons": ["<Con1>", "<Con2>"],
      "url_hint": "aliexpress.com",
      "recommended": <true|false>
    }},
    {{
      "name": "Alibaba",
      "price_range": "<z.B. 1–5 €>",
      "shipping_time_de": "<z.B. 15–30 Tage>",
      "min_order_qty": <Zahl>,
      "quality_rating": <1-5>,
      "reliability_rating": <1-5>,
      "pros": ["<Pro1>", "<Pro2>", "<Pro3>"],
      "cons": ["<Con1>", "<Con2>"],
      "url_hint": "alibaba.com",
      "recommended": <true|false>
    }},
    {{
      "name": "CJ Dropshipping",
      "price_range": "<z.B. 4–10 €>",
      "shipping_time_de": "<z.B. 7–15 Tage>",
      "min_order_qty": <Zahl>,
      "quality_rating": <1-5>,
      "reliability_rating": <1-5>,
      "pros": ["<Pro1>", "<Pro2>", "<Pro3>"],
      "cons": ["<Con1>", "<Con2>"],
      "url_hint": "cjdropshipping.com",
      "recommended": <true|false>
    }},
    {{
      "name": "Spocket (EU)",
      "price_range": "<z.B. 8–20 €>",
      "shipping_time_de": "<z.B. 3–7 Tage>",
      "min_order_qty": <Zahl>,
      "quality_rating": <1-5>,
      "reliability_rating": <1-5>,
      "pros": ["<Pro1>", "<Pro2>", "<Pro3>"],
      "cons": ["<Con1>", "<Con2>"],
      "url_hint": "spocket.co",
      "recommended": <true|false>
    }}
  ],
  "negotiation_tips": ["<Tipp1>", "<Tipp2>", "<Tipp3>"],
  "quality_checklist": ["<Check1>", "<Check2>", "<Check3>", "<Check4>"]
}}

Antworte NUR mit dem JSON-Objekt."""

    try:
        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise HTTPException(500, f"Ungültige JSON-Antwort von KI: {e}")
    except Exception as e:
        raise HTTPException(500, f"Vergleichsfehler: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
