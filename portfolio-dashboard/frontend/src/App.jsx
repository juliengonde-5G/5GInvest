import { useState, useEffect } from "react";
import Dashboard from "./components/Dashboard";
import AIInsights from "./components/AIInsights";
import PropertiesView from "./components/PropertiesView";
import CryptoView from "./components/CryptoView";
import CommoditiesView from "./components/CommoditiesView";
import CashView from "./components/CashView";
import {
  LayoutDashboard, Home, Bitcoin, Gem, Wallet, Brain, RefreshCw,
  ChevronLeft, ChevronRight, Bell, Settings, LogOut, Search, Menu, X,
} from "lucide-react";

const API = "/api";

const NAV_ITEMS = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "immo", label: "Immobilier", icon: Home },
  { id: "crypto", label: "Crypto", icon: Bitcoin },
  { id: "commodities", label: "Commodities", icon: Gem },
  { id: "cash", label: "Cash", icon: Wallet },
  { id: "ai", label: "IA Insights", icon: Brain },
];

export default function App() {
  const [data, setData] = useState(null);
  const [aiData, setAiData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("dashboard");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  useEffect(() => { loadDashboard(); }, []);

  async function loadDashboard() {
    setLoading(true);
    try {
      const res = await fetch(`${API}/dashboard`);
      setData(await res.json());
    } catch (e) { console.error(e); }
    setLoading(false);
  }

  async function loadAI() {
    setAiData(null);
    try {
      const res = await fetch(`${API}/ai/analyze`, { method: "POST" });
      setAiData(await res.json());
    } catch (e) {
      setAiData({ error: "Analyse indisponible" });
    }
  }

  function navigate(id) {
    setActiveTab(id);
    setSidebarOpen(false);
    if (id === "ai" && !aiData) loadAI();
  }

  const sidebarW = sidebarCollapsed ? "w-16" : "w-60";

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* ═══ SIDEBAR ═══ */}
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/60 z-40 lg:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      <aside className={`
        fixed lg:relative inset-y-0 left-0 z-50 flex flex-col
        bg-sidebar border-r border-sidebar-border
        transition-all duration-200 ease-in-out
        ${sidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}
        ${sidebarW}
      `}>
        {/* Logo */}
        <div className="flex items-center gap-2 px-4 h-14 border-b border-sidebar-border shrink-0">
          {!sidebarCollapsed && (
            <>
              <div className="w-7 h-7 rounded-lg bg-emerald-500 flex items-center justify-center text-xs font-bold text-black">5G</div>
              <span className="font-semibold text-sm">Portfolio</span>
            </>
          )}
          {sidebarCollapsed && (
            <div className="w-7 h-7 rounded-lg bg-emerald-500 flex items-center justify-center text-xs font-bold text-black mx-auto">5G</div>
          )}
        </div>

        {/* Nav */}
        <nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
          {!sidebarCollapsed && (
            <div className="px-3 mb-2 text-[10px] font-semibold uppercase tracking-widest text-muted-dark">Portfolio</div>
          )}
          {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => navigate(id)}
              className={`sidebar-link w-full ${activeTab === id ? "active" : ""} ${sidebarCollapsed ? "justify-center px-0" : ""}`}
              title={sidebarCollapsed ? label : undefined}
            >
              <Icon size={18} />
              {!sidebarCollapsed && <span>{label}</span>}
            </button>
          ))}
        </nav>

        {/* Collapse toggle (desktop) */}
        <div className="hidden lg:flex border-t border-sidebar-border p-2">
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="sidebar-link w-full justify-center"
          >
            {sidebarCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          </button>
        </div>
      </aside>

      {/* ═══ MAIN ═══ */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header className="flex items-center justify-between h-14 px-4 border-b border-border shrink-0 bg-background">
          <div className="flex items-center gap-3">
            <button onClick={() => setSidebarOpen(true)} className="lg:hidden p-1.5 rounded-lg hover:bg-white/5">
              <Menu size={20} />
            </button>
            <h1 className="text-sm font-semibold">
              {NAV_ITEMS.find(n => n.id === activeTab)?.label || "Dashboard"}
            </h1>
          </div>
          <div className="flex items-center gap-1">
            <button onClick={loadDashboard} className="p-2 rounded-lg hover:bg-white/5 transition" title="Rafraîchir">
              <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
            </button>
            <button className="p-2 rounded-lg hover:bg-white/5 transition relative">
              <Bell size={16} />
              <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-emerald-500 rounded-full" />
            </button>
            <div className="w-7 h-7 rounded-full bg-gradient-to-br from-violet-500 to-blue-500 ml-2" />
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto">
          <div className="max-w-[1400px] mx-auto p-4 lg:p-6">
            {loading && !data ? (
              <div className="flex items-center justify-center py-32">
                <RefreshCw size={28} className="animate-spin text-muted" />
              </div>
            ) : data ? (
              <>
                {activeTab === "dashboard" && <Dashboard data={data} onNavigate={navigate} />}
                {activeTab === "immo" && <PropertiesView items={data.real_estate} onRefresh={loadDashboard} />}
                {activeTab === "crypto" && <CryptoView items={data.crypto} onRefresh={loadDashboard} />}
                {activeTab === "commodities" && <CommoditiesView items={data.commodities} onRefresh={loadDashboard} />}
                {activeTab === "cash" && <CashView items={data.cash} onRefresh={loadDashboard} />}
                {activeTab === "ai" && <AIInsights data={aiData} onRefresh={loadAI} />}
              </>
            ) : (
              <div className="text-center py-32 text-muted">
                Erreur de chargement. Vérifiez le backend.
              </div>
            )}
          </div>
        </main>

        {/* Footer disclaimer */}
        <footer className="text-center text-[9px] text-[#3f3f46] py-2 px-4 border-t border-border">
          Ne constitue pas un conseil en investissement. Performances passées ≠ performances futures. Risque de perte en capital.
        </footer>
      </div>
    </div>
  );
}
