"""
5GInvest - API FastAPI
Backend pour l'app mobile PWA + notifications push.
"""

import os
import json
import datetime
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config.settings import INITIAL_BUDGET_EUR, ASSET_CLASSES, SHORT_TERM_CONFIG
from config.user_profile import load_profile, save_profile
from market.data_fetcher import fetch_stock_data, fetch_crypto_history, fetch_current_price
from strategy.short_term import analyze_asset, scan_all_assets, get_buy_recommendations
from strategy.justifier import justifier_allocation
from alerts.alert_engine import AlertEngine
from portfolio.tracker import PortfolioTracker
from banks.catalog import BANKS, get_bank, get_user_banks
from programs.engine import ProgramManager, ALLOCATION_MODELS, INSTRUMENTS_MAP
from fiscal.engine import FiscalEngine, display_fiscal_comparison
from api.push_service import PushService


# ─── Lifespan ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Démarre le scheduler au lancement."""
    from api.scheduler import start_scheduler
    scheduler = start_scheduler()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(
    title="5GInvest",
    description="Module d'investissement guidé - API",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir les fichiers statiques PWA
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

push_service = PushService()


# ─── Pydantic Models ──────────────────────────────────────

class ProfileUpdate(BaseModel):
    prenom: str = "Investisseur"
    age: int = 30
    situation_familiale: str = "celibataire"
    nb_parts_fiscales: float = 1.0
    revenu_annuel_net: int = 30000
    option_fiscale: str = "pfu"
    has_pea: bool = False
    pea_age_ans: int = 0
    pea_montant_verse: float = 0
    has_pea_pme: bool = False
    has_assurance_vie: bool = False
    av_age_ans: int = 0
    av_encours: float = 0
    has_per: bool = False
    has_cto: bool = True
    banques: List[str] = ["Revolut"]
    profil_risque: str = "equilibre"
    objectif_principal: str = "trading"
    horizon_global: str = "court"
    experience_bourse: str = "debutant"


class ProgramCreate(BaseModel):
    nom: str
    budget_initial: float = 100.0
    horizon: str = "court"
    duree_mois: int = 6
    risque: str = "equilibre"
    objectif_rendement_pct: float = 6.0
    banques: List[str] = ["Revolut"]
    enveloppe_preferee: str = "cto"
    dca_enabled: bool = False
    dca_montant: float = 0
    dca_frequence: str = "mensuel"


class TradeRequest(BaseModel):
    symbol: str
    amount_eur: Optional[float] = None
    price: Optional[float] = None
    asset_class: str = "stocks_us"


class PushSubscription(BaseModel):
    endpoint: str
    keys: dict


# ─── HOME / MARKET ────────────────────────────────────────

@app.get("/api/home")
async def get_home():
    """Page d'accueil: note marché + résumé."""
    profile = load_profile()
    pm = ProgramManager()
    programs = pm.list_programs()

    indices = _fetch_indices_fast()
    commentary = _generate_commentary(indices)

    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "market": {
            "indices": indices,
            "commentary": commentary,
        },
        "profile": _safe_profile(profile) if profile else None,
        "programs": [{
            "id": p["id"],
            "nom": p["nom"],
            "budget_initial": p["budget_initial"],
            "risque": p["risque"],
            "horizon": p["horizon"],
            "status": p["status"],
        } for p in programs],
        "portfolio_summary": _get_portfolio_summary(),
    }


@app.get("/api/market")
async def get_market():
    """Données de marché en temps réel."""
    return {"indices": _fetch_indices_fast()}


# ─── PROFILE ──────────────────────────────────────────────

@app.get("/api/profile")
async def get_profile():
    profile = load_profile()
    if not profile:
        return {"exists": False}
    return {"exists": True, "profile": _safe_profile(profile)}


@app.post("/api/profile")
async def update_profile(data: ProfileUpdate):
    from config.user_profile import _calculer_tmi
    profile = data.model_dump()
    profile["tmi"] = _calculer_tmi(profile["revenu_annuel_net"], profile["nb_parts_fiscales"])
    if profile["option_fiscale"] == "pfu":
        profile["taux_imposition_gains"] = 0.30
    else:
        profile["taux_imposition_gains"] = profile["tmi"] + 0.172
    profile["created_at"] = datetime.datetime.now().isoformat()
    profile["updated_at"] = datetime.datetime.now().isoformat()
    save_profile(profile)
    return {"status": "ok", "profile": _safe_profile(profile)}


# ─── BANKS ────────────────────────────────────────────────

@app.get("/api/banks")
async def list_banks():
    return {"banks": [{
        "id": k,
        "nom": v["nom"],
        "type": v["type"],
        "enveloppes": v["enveloppes"],
        "produits": {k2: v2 for k2, v2 in v["produits"].items() if v2 is True},
        "frais": v["frais"],
        "avantages": v["avantages"],
        "limites": v["limites"],
        "ideal_pour": v.get("ideal_pour", []),
    } for k, v in BANKS.items()]}


@app.get("/api/banks/{bank_id}")
async def get_bank_detail(bank_id: str):
    bank = get_bank(bank_id)
    if not bank:
        raise HTTPException(404, f"Banque '{bank_id}' non trouvée")
    return bank


# ─── PROGRAMS ─────────────────────────────────────────────

@app.get("/api/programs")
async def list_programs():
    pm = ProgramManager()
    return {"programs": pm.list_programs()}


@app.get("/api/programs/{program_id}")
async def get_program(program_id: str):
    pm = ProgramManager()
    program = pm.get_program(program_id)
    if not program:
        raise HTTPException(404, "Programme non trouvé")
    return program


@app.post("/api/programs")
async def create_program(data: ProgramCreate):
    profile = load_profile()
    if not profile:
        raise HTTPException(400, "Profil requis. Configurez d'abord votre profil.")

    pm = ProgramManager()

    # Construire le programme
    import uuid
    program = data.model_dump()
    program["id"] = str(uuid.uuid4())[:8]
    program["created_at"] = datetime.datetime.now().isoformat()
    program["status"] = "active"
    program["budget_restant"] = program["budget_initial"]
    program["positions"] = {}
    program["historique"] = []

    # Générer allocation
    program["allocation"] = pm._generer_allocation(program, profile)

    # Justifier
    justified = justifier_allocation(program["allocation"], program, profile)
    program["allocation"] = justified

    if "programs" not in pm.data:
        pm.data["programs"] = []
    pm.data["programs"].append(program)
    pm._save()

    return {"status": "ok", "program": program}


@app.delete("/api/programs/{program_id}")
async def delete_program(program_id: str):
    pm = ProgramManager()
    deleted = pm.delete_program(program_id)
    if not deleted:
        raise HTTPException(404, "Programme non trouvé")
    return {"status": "ok"}


# ─── SCAN / RECOMMEND ────────────────────────────────────

@app.get("/api/scan")
async def scan_opportunities():
    """Scanner toutes les opportunités."""
    market_data = _fetch_all_data()
    results = scan_all_assets(market_data)
    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "results": results,
        "summary": {
            "buy": len([r for r in results if r["signal"] == "BUY"]),
            "sell": len([r for r in results if r["signal"] == "SELL"]),
            "hold": len([r for r in results if r["signal"] == "HOLD"]),
        },
    }


@app.get("/api/recommend")
async def recommend(budget: float = 100.0):
    """Recommandation d'allocation."""
    market_data = _fetch_all_data()
    results = scan_all_assets(market_data)
    recommendations = get_buy_recommendations(results, budget)

    for rec in recommendations:
        rec["stop_loss_price"] = round(
            rec["price"] * (1 - SHORT_TERM_CONFIG["stop_loss_pct"] / 100), 4
        )
        rec["take_profit_price"] = round(
            rec["price"] * (1 + SHORT_TERM_CONFIG["take_profit_pct"] / 100), 4
        )

    return {
        "budget": budget,
        "recommendations": recommendations,
        "cash_remaining": budget - sum(r["allocation_eur"] for r in recommendations),
    }


# ─── PORTFOLIO ────────────────────────────────────────────

@app.get("/api/portfolio")
async def get_portfolio():
    return _get_portfolio_summary()


@app.post("/api/portfolio/buy")
async def buy(trade: TradeRequest):
    portfolio = PortfolioTracker()
    price = trade.price or fetch_current_price(trade.symbol, trade.asset_class)
    if not price:
        raise HTTPException(400, f"Prix introuvable pour {trade.symbol}")
    amount = trade.amount_eur or 0
    if amount <= 0:
        raise HTTPException(400, "Montant invalide")
    result = portfolio.buy(trade.symbol, amount, price, trade.asset_class)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result


@app.post("/api/portfolio/sell")
async def sell(trade: TradeRequest):
    portfolio = PortfolioTracker()
    pos = portfolio.get_position(trade.symbol)
    if not pos:
        raise HTTPException(404, f"Pas de position sur {trade.symbol}")
    price = trade.price or fetch_current_price(trade.symbol, pos.get("asset_class", "stocks_us"))
    if not price:
        raise HTTPException(400, f"Prix introuvable pour {trade.symbol}")
    result = portfolio.sell(trade.symbol, price)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result


# ─── FISCAL ───────────────────────────────────────────────

@app.get("/api/fiscal/simulate")
async def fiscal_simulate(gain: float, enveloppe: str = "cto", duree_ans: int = 0):
    profile = load_profile()
    if not profile:
        raise HTTPException(400, "Profil requis")
    fiscal = FiscalEngine(profile)
    comparison = fiscal.comparer_enveloppes(gain, duree_ans)
    return {"gain": gain, "comparison": comparison}


# ─── PUSH NOTIFICATIONS ──────────────────────────────────

@app.post("/api/push/subscribe")
async def push_subscribe(sub: PushSubscription):
    push_service.save_subscription(sub.model_dump())
    return {"status": "ok"}


@app.post("/api/push/test")
async def push_test():
    """Envoyer une notification test."""
    count = push_service.send_notification(
        title="5GInvest - Test",
        body="Les notifications fonctionnent !",
        data={"url": "/"},
    )
    return {"status": "ok", "sent": count}


@app.get("/api/push/vapid-key")
async def get_vapid_key():
    return {"publicKey": push_service.get_public_key()}


# ─── ALERTS ───────────────────────────────────────────────

@app.get("/api/alerts")
async def get_alerts():
    alert_engine = AlertEngine()
    return alert_engine.get_summary()


# ─── PWA SERVING ──────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def serve_app():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>5GInvest</h1><p>Fichiers statiques manquants.</p>")


@app.get("/sw.js")
async def serve_sw():
    sw_path = os.path.join(STATIC_DIR, "sw.js")
    return FileResponse(sw_path, media_type="application/javascript")


@app.get("/manifest.json")
async def serve_manifest():
    manifest_path = os.path.join(STATIC_DIR, "manifest.json")
    return FileResponse(manifest_path, media_type="application/json")


# ─── HELPERS ──────────────────────────────────────────────

def _safe_profile(profile: dict) -> dict:
    """Retourne le profil sans données sensibles."""
    safe = {k: v for k, v in profile.items()}
    return safe


def _fetch_indices_fast() -> list:
    """Fetch des indices principaux."""
    indices = []
    try:
        import yfinance as yf
        symbols = {
            "^GSPC": "S&P 500", "^IXIC": "Nasdaq", "^FCHI": "CAC 40",
            "BTC-EUR": "Bitcoin", "GC=F": "Or", "EURUSD=X": "EUR/USD",
        }
        for sym, nom in symbols.items():
            try:
                t = yf.Ticker(sym)
                h = t.history(period="2d")
                if len(h) >= 2:
                    cur = h["Close"].iloc[-1]
                    prev = h["Close"].iloc[-2]
                    chg = ((cur - prev) / prev) * 100
                    indices.append({
                        "symbol": sym, "nom": nom,
                        "price": round(cur, 2), "change_pct": round(chg, 2),
                    })
            except Exception:
                pass
    except ImportError:
        pass
    return indices


def _generate_commentary(indices: list) -> list:
    """Génère des commentaires contextuels."""
    if not indices:
        return ["Données de marché indisponibles."]

    comments = []
    changes = [i["change_pct"] for i in indices if "change_pct" in i]
    avg = sum(changes) / len(changes) if changes else 0

    if avg > 1:
        comments.append("Marchés en forte hausse. Attention à ne pas acheter les sommets.")
    elif avg > 0.3:
        comments.append("Marchés en légère hausse. Tendance favorable.")
    elif avg < -1:
        comments.append("Marchés en forte baisse. Opportunités pour les profils dynamiques.")
    elif avg < -0.3:
        comments.append("Marchés en léger repli. Phase de consolidation.")
    else:
        comments.append("Marchés stables. Bon moment pour analyser.")

    now = datetime.datetime.now()
    if now.weekday() >= 5:
        comments.append("Weekend: seules les cryptos sont tradables.")
    elif now.hour >= 22 or now.hour < 7:
        comments.append("Marchés fermés. Préparez vos ordres pour demain.")

    return comments


def _fetch_all_data() -> dict:
    """Fetch toutes les données marché."""
    import time
    all_data = {}
    for asset_class, config in ASSET_CLASSES.items():
        if not config["enabled"]:
            continue
        for symbol in config["symbols"]:
            if asset_class == "crypto":
                data = fetch_crypto_history(symbol, days=30)
            else:
                data = fetch_stock_data(symbol, period="1mo", interval="1d")
            if "error" not in data:
                data["asset_class"] = asset_class
                all_data[symbol] = data
            time.sleep(0.2)
    return all_data


def _get_portfolio_summary() -> dict:
    """Résumé du portefeuille."""
    portfolio = PortfolioTracker()
    positions = portfolio.get_all_positions()
    if not positions:
        return {
            "total_value_eur": portfolio.get_cash(),
            "cash_eur": portfolio.get_cash(),
            "positions": [],
            "total_pnl_eur": 0,
            "total_pnl_pct": 0,
        }
    prices = {}
    for sym, pos in positions.items():
        p = fetch_current_price(sym, pos.get("asset_class", "stocks_us"))
        if p:
            prices[sym] = p
    return portfolio.get_portfolio_value(prices)
