import { useState, useEffect } from "react";
import Dashboard from "./components/Dashboard";
import AIInsights from "./components/AIInsights";
import { Moon, Sun, RefreshCw } from "lucide-react";

const API = "/api";

export default function App() {
  const [data, setData] = useState(null);
  const [aiData, setAiData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [darkMode, setDarkMode] = useState(true);
  const [activeTab, setActiveTab] = useState("dashboard");

  useEffect(() => {
    document.documentElement.classList.toggle("dark", darkMode);
  }, [darkMode]);

  useEffect(() => { loadDashboard(); }, []);

  async function loadDashboard() {
    setLoading(true);
    try {
      const res = await fetch(`${API}/dashboard`);
      const json = await res.json();
      setData(json);
    } catch (e) {
      console.error("Dashboard load error:", e);
    }
    setLoading(false);
  }

  async function loadAI() {
    setAiData(null);
    try {
      const res = await fetch(`${API}/ai/analyze`, { method: "POST" });
      const json = await res.json();
      setAiData(json);
    } catch (e) {
      console.error("AI error:", e);
      setAiData({ error: "Analyse IA indisponible." });
    }
  }

  const tabs = [
    { id: "dashboard", label: "Dashboard" },
    { id: "immo", label: "Immobilier" },
    { id: "crypto", label: "Crypto" },
    { id: "commodities", label: "Commodities" },
    { id: "cash", label: "Cash" },
    { id: "ai", label: "IA" },
  ];

  return (
    <div className="min-h-screen bg-dark-900">
      {/* Header */}
      <header className="bg-dark-800 border-b border-dark-600 px-4 py-3 flex items-center justify-between sticky top-0 z-50">
        <h1 className="text-lg font-bold tracking-tight">
          Portfolio <span className="text-accent-blue">Dashboard</span>
        </h1>
        <div className="flex items-center gap-2">
          <button onClick={loadDashboard} className="p-2 rounded-lg hover:bg-dark-600 transition" title="Rafraîchir">
            <RefreshCw size={18} className={loading ? "animate-spin" : ""} />
          </button>
          <button onClick={() => setDarkMode(!darkMode)} className="p-2 rounded-lg hover:bg-dark-600 transition">
            {darkMode ? <Sun size={18} /> : <Moon size={18} />}
          </button>
        </div>
      </header>

      {/* Tabs */}
      <nav className="bg-dark-800 border-b border-dark-600 px-4 overflow-x-auto">
        <div className="flex gap-1 min-w-max">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => { setActiveTab(t.id); if (t.id === "ai" && !aiData) loadAI(); }}
              className={`px-4 py-2.5 text-sm font-medium whitespace-nowrap transition border-b-2 ${
                activeTab === t.id
                  ? "border-accent-blue text-accent-blue"
                  : "border-transparent text-gray-400 hover:text-gray-200"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </nav>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {loading && !data ? (
          <div className="flex items-center justify-center py-20">
            <RefreshCw size={32} className="animate-spin text-accent-blue" />
          </div>
        ) : data ? (
          <>
            {activeTab === "dashboard" && <Dashboard data={data} />}
            {activeTab === "immo" && <AssetTable title="Immobilier" items={data.real_estate} type="immo" onRefresh={loadDashboard} />}
            {activeTab === "crypto" && <AssetTable title="Crypto" items={data.crypto} type="crypto" onRefresh={loadDashboard} />}
            {activeTab === "commodities" && <AssetTable title="Matières premières" items={data.commodities} type="commodity" onRefresh={loadDashboard} />}
            {activeTab === "cash" && <AssetTable title="Comptes Cash" items={data.cash} type="cash" onRefresh={loadDashboard} />}
            {activeTab === "ai" && <AIInsights data={aiData} onRefresh={loadAI} />}
          </>
        ) : (
          <div className="text-center py-20 text-gray-500">Erreur de chargement. Vérifiez le backend.</div>
        )}
      </main>

      {/* Disclaimer */}
      <footer className="text-center text-[10px] text-gray-600 py-4 px-4">
        Ne constitue pas un conseil en investissement. Performances passées ≠ futures. Risque de perte en capital.
      </footer>
    </div>
  );
}

// ─── Generic Asset Table ─────────────────────────────────

function AssetTable({ title, items, type, onRefresh }) {
  if (!items?.length) {
    return (
      <div className="text-center py-16">
        <p className="text-gray-500 mb-4">Aucun actif {title.toLowerCase()}</p>
        <p className="text-gray-600 text-sm">Ajoutez via l'API: POST /api/{type === "immo" ? "real-estate" : type}</p>
      </div>
    );
  }

  const totalValue = items.reduce((s, i) => s + (i.current_value || i.valeur_nette || i.solde || 0), 0);

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold">{title}</h2>
        <span className="text-2xl font-bold text-accent-blue">{fmt(totalValue)}</span>
      </div>

      <div className="grid gap-3">
        {items.map((item, i) => (
          <div key={i} className="bg-dark-800 rounded-xl p-4 border border-dark-600">
            <div className="flex justify-between items-start">
              <div>
                <div className="font-semibold">{item.nom || item.symbol}</div>
                <div className="text-sm text-gray-400 mt-1">
                  {type === "immo" && `${item.surface_m2}m² · ${item.ville} · Rdt: ${item.rendement_brut}%`}
                  {type === "crypto" && `${item.quantite} ${item.symbol} · PAM: ${fmt(item.prix_achat_moyen)}`}
                  {type === "commodity" && `${item.quantite} · ${item.type_produit} · ${item.plateforme || ""}`}
                  {type === "cash" && `${item.type_compte} · ${item.banque} · ${item.taux_interet}%`}
                </div>
              </div>
              <div className="text-right">
                <div className="font-bold">{fmt(item.current_value || item.valeur_nette || item.solde)}</div>
                {item.pnl_eur !== undefined && (
                  <div className={`text-sm font-medium ${item.pnl_eur >= 0 ? "text-accent-green" : "text-accent-red"}`}>
                    {item.pnl_eur >= 0 ? "+" : ""}{fmt(item.pnl_eur)} ({item.pnl_pct >= 0 ? "+" : ""}{item.pnl_pct}%)
                  </div>
                )}
                {item.cashflow_mensuel !== undefined && (
                  <div className={`text-sm ${item.cashflow_mensuel >= 0 ? "text-accent-green" : "text-accent-red"}`}>
                    {item.cashflow_mensuel >= 0 ? "+" : ""}{item.cashflow_mensuel}€/mois
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function fmt(n) {
  if (n == null) return "—";
  return new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(n);
}
