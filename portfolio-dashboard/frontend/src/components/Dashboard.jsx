import { useState, useEffect } from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import { TrendingUp, TrendingDown, Home, Bitcoin, Gem, Wallet, ArrowUpRight, ArrowDownRight, MoreHorizontal, Target, Shield, AlertTriangle, Lightbulb, Download, Filter } from "lucide-react";

const API = "/api";
const COLORS = { immo: "#8b5cf6", crypto: "#f59e0b", commodity: "#06b6d4", cash: "#10b981" };

export default function Dashboard({ data, onNavigate }) {
  const { net_worth, allocation, real_estate, crypto, commodities, cash, history } = data;
  const [opinion, setOpinion] = useState(null);
  const [profile, setProfile] = useState(null);

  useEffect(() => {
    fetch(`${API}/patrimoine/opinion`).then(r => r.json()).then(setOpinion).catch(() => {});
    fetch(`${API}/profile`).then(r => r.json()).then(d => { if (d.exists) setProfile(d.profile); }).catch(() => {});
  }, []);

  const pieData = [
    { name: "Immobilier", value: allocation.immo, color: COLORS.immo, pct: allocation.immo_pct },
    { name: "Crypto", value: allocation.crypto, color: COLORS.crypto, pct: allocation.crypto_pct },
    { name: "Commodities", value: allocation.commodity, color: COLORS.commodity, pct: allocation.commodity_pct },
    { name: "Cash", value: allocation.cash, color: COLORS.cash, pct: allocation.cash_pct },
  ].filter(d => d.value > 0);

  const allPositions = [
    ...real_estate.map(p => ({ ...p, type: "immo", value: p.valeur_nette, change: p.rendement_brut, label: p.nom })),
    ...crypto.map(p => ({ ...p, type: "crypto", value: p.current_value, change: p.pnl_pct, label: p.nom || p.symbol })),
    ...commodities.map(p => ({ ...p, type: "commodity", value: p.current_value, change: p.pnl_pct, label: p.nom || p.symbol })),
    ...cash.map(p => ({ ...p, type: "cash", value: p.solde, change: p.taux_interet, label: p.nom })),
  ].sort((a, b) => (b.value || 0) - (a.value || 0));

  const now = new Date();
  const dateStr = now.toLocaleDateString("fr-FR", { weekday: "short", day: "numeric", month: "long", year: "numeric" });

  // Wallet cards data
  const wallets = [
    { label: "Immobilier", value: allocation.immo, color: "#8b5cf6", active: allocation.immo > 0 },
    { label: "Crypto", value: allocation.crypto, color: "#f59e0b", active: allocation.crypto > 0 },
    { label: "Commodities", value: allocation.commodity, color: "#06b6d4", active: allocation.commodity > 0 },
    { label: "Cash", value: allocation.cash, color: "#10b981", active: allocation.cash > 0 },
  ];

  return (
    <div className="space-y-6">
      {/* ═══ WELCOME HEADER ═══ */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">
            Bonjour {profile?.prenom || "Investisseur"} <span className="text-2xl">👋</span>
          </h1>
          <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
            Suivez et pilotez votre patrimoine au quotidien.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs px-3 py-1.5 rounded-lg" style={{ background: "var(--bg-elevated)", color: "var(--text-secondary)" }}>
            {dateStr}
          </span>
          <a href={`${API}/fiscal/report`} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-violet-600 text-xs font-medium text-white hover:bg-violet-500 transition">
            <Download size={12} /> Export
          </a>
        </div>
      </div>

      {/* ═══ TOP 3 STAT CARDS (Findexa style) ═══ */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Patrimoine Net */}
        <div className="card p-5 relative overflow-hidden">
          <div className="flex items-center justify-between mb-1">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-violet-500/15 flex items-center justify-center">
                <Wallet size={16} className="text-violet-400" />
              </div>
              <span className="text-xs font-medium" style={{ color: "var(--text-secondary)" }}>Patrimoine Net</span>
            </div>
            <button className="p-1 rounded hover:opacity-70"><MoreHorizontal size={14} style={{ color: "var(--text-muted)" }} /></button>
          </div>
          <div className="text-3xl font-bold mt-2 tracking-tight">{fmtLarge(net_worth)}</div>
          {opinion?.score_sante != null && (
            <div className={`flex items-center gap-1 mt-1 text-xs font-medium ${opinion.score_sante >= 60 ? "text-emerald-400" : opinion.score_sante >= 40 ? "text-amber-400" : "text-red-400"}`}>
              {opinion.score_sante >= 60 ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
              Score: {opinion.score_sante}/100 · {opinion.score_label}
            </div>
          )}
        </div>

        {/* Investissements */}
        <div className="card p-5">
          <div className="flex items-center justify-between mb-1">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-amber-500/15 flex items-center justify-center">
                <TrendingUp size={16} className="text-amber-400" />
              </div>
              <span className="text-xs font-medium" style={{ color: "var(--text-secondary)" }}>Investissements</span>
            </div>
            <button className="p-1 rounded hover:opacity-70"><MoreHorizontal size={14} style={{ color: "var(--text-muted)" }} /></button>
          </div>
          <div className="text-3xl font-bold mt-2 tracking-tight">{fmtLarge(allocation.crypto + allocation.commodity)}</div>
          <div className="flex items-center gap-1 mt-1 text-xs font-medium" style={{ color: "var(--text-muted)" }}>
            Crypto + Commodities
          </div>
        </div>

        {/* Cash & Épargne */}
        <div className="card p-5">
          <div className="flex items-center justify-between mb-1">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-emerald-500/15 flex items-center justify-center">
                <Wallet size={16} className="text-emerald-400" />
              </div>
              <span className="text-xs font-medium" style={{ color: "var(--text-secondary)" }}>Cash & Épargne</span>
            </div>
            <button className="p-1 rounded hover:opacity-70"><MoreHorizontal size={14} style={{ color: "var(--text-muted)" }} /></button>
          </div>
          <div className="text-3xl font-bold mt-2 tracking-tight">{fmtLarge(allocation.cash)}</div>
          <div className="flex items-center gap-1 mt-1 text-xs font-medium text-emerald-400">
            <ArrowUpRight size={12} /> {cash.reduce((s, a) => s + (a.interet_annuel_estime || 0), 0).toFixed(0)}€/an d'intérêts
          </div>
        </div>
      </div>

      {/* ═══ MAIN GRID (2 cols: left wallet/savings + right chart/transactions) ═══ */}
      <div className="grid lg:grid-cols-5 gap-4">

        {/* ── LEFT COLUMN (2/5) ── */}
        <div className="lg:col-span-2 space-y-4">

          {/* My Wallet (multi-class cards) */}
          <div className="card p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold">Mon patrimoine</h3>
              <button onClick={() => onNavigate("profile")} className="text-[10px] px-2 py-1 rounded-lg font-medium" style={{ background: "var(--bg-elevated)", color: "var(--text-secondary)" }}>
                + Configurer
              </button>
            </div>
            <div className="grid grid-cols-2 gap-3">
              {wallets.map((w, i) => (
                <div key={i} className="rounded-xl p-3 cursor-pointer transition hover:scale-[1.02]"
                  style={{ background: `${w.color}10`, border: `1px solid ${w.color}30` }}
                  onClick={() => onNavigate(["immo", "crypto", "commodities", "cash"][i])}>
                  <div className="flex items-center gap-1.5 mb-2">
                    <div className="w-5 h-5 rounded-full" style={{ background: w.color }} />
                    <span className="text-[11px] font-medium" style={{ color: "var(--text-secondary)" }}>{w.label}</span>
                  </div>
                  <div className="text-sm font-bold">{fmtLarge(w.value)}</div>
                  <div className={`text-[10px] mt-0.5 font-medium ${w.active ? "text-emerald-400" : ""}`}
                    style={{ color: w.active ? undefined : "var(--text-muted)" }}>
                    {w.active ? "Actif" : "Inactif"}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Allocation donut */}
          <div className="card p-5">
            <h3 className="text-sm font-semibold mb-3">Allocation</h3>
            {pieData.length > 0 ? (
              <div className="flex items-center gap-4">
                <div className="relative w-[120px] h-[120px] shrink-0">
                  <ResponsiveContainer>
                    <PieChart>
                      <Pie data={pieData} cx="50%" cy="50%" innerRadius={38} outerRadius={55} dataKey="value" stroke="none" startAngle={90} endAngle={-270}>
                        {pieData.map((e, i) => <Cell key={i} fill={e.color} />)}
                      </Pie>
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-[9px]" style={{ color: "var(--text-muted)" }}>Total</span>
                    <span className="text-xs font-bold">{fmtShort(net_worth)}</span>
                  </div>
                </div>
                <div className="space-y-2.5 flex-1">
                  {pieData.map(d => (
                    <div key={d.name} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="w-2.5 h-2.5 rounded-full" style={{ background: d.color }} />
                        <span className="text-[11px]" style={{ color: "var(--text-secondary)" }}>{d.name}</span>
                      </div>
                      <span className="text-[11px] font-semibold">{d.pct?.toFixed(0)}%</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-center py-6 text-sm" style={{ color: "var(--text-muted)" }}>Aucun actif</div>
            )}
          </div>

          {/* Savings Plan / Objectifs */}
          {opinion?.recommandations?.length > 0 && (
            <div className="card p-5">
              <div className="flex items-center gap-2 mb-3">
                <Lightbulb size={14} className="text-amber-400" />
                <h3 className="text-sm font-semibold">Recommandations</h3>
              </div>
              {opinion.recommandations.slice(0, 3).map((r, i) => (
                <div key={i} className="flex gap-2 py-2 border-b last:border-0" style={{ borderColor: "var(--border)" }}>
                  <Target size={12} className="text-violet-400 shrink-0 mt-0.5" />
                  <span className="text-[11px]" style={{ color: "var(--text-secondary)" }}>{r}</span>
                </div>
              ))}
              <div className="text-[9px] mt-2 italic" style={{ color: "var(--text-faint)" }}>{opinion.disclaimer}</div>
            </div>
          )}
        </div>

        {/* ── RIGHT COLUMN (3/5) ── */}
        <div className="lg:col-span-3 space-y-4">

          {/* Overview Chart */}
          <div className="card p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded-lg bg-violet-500/15 flex items-center justify-center">
                  <TrendingUp size={12} className="text-violet-400" />
                </div>
                <h3 className="text-sm font-semibold">Évolution</h3>
              </div>
              <div className="flex gap-1 text-[10px]">
                {["1M", "3M", "6M", "1A", "Max"].map(p => (
                  <button key={p} className="px-2 py-1 rounded transition" style={{ background: "var(--bg-elevated)", color: "var(--text-muted)" }}>
                    {p}
                  </button>
                ))}
              </div>
            </div>
            {history?.length > 1 ? (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={history}>
                  <CartesianGrid vertical={false} stroke="var(--border)" />
                  <XAxis dataKey="date" tick={{ fill: "var(--text-muted)", fontSize: 10 }} tickLine={false} axisLine={false} tickFormatter={d => d?.slice(5, 7)} />
                  <YAxis tick={{ fill: "var(--text-muted)", fontSize: 10 }} tickLine={false} axisLine={false} tickFormatter={v => `${(v/1000).toFixed(0)}k`} width={40} />
                  <Tooltip
                    contentStyle={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12, color: "var(--text)" }}
                    formatter={v => [`${v?.toLocaleString("fr-FR")} €`, ""]}
                    cursor={{ fill: "var(--bg-elevated)", opacity: 0.5 }}
                  />
                  <Bar dataKey="net_worth" fill="#8b5cf6" radius={[4, 4, 0, 0]} name="Net Worth" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex flex-col items-center justify-center h-[220px] text-sm" style={{ color: "var(--text-muted)" }}>
                <p>Historique insuffisant</p>
                <p className="text-[10px] mt-1" style={{ color: "var(--text-faint)" }}>Les snapshots sont enregistrés quotidiennement</p>
              </div>
            )}
          </div>

          {/* Recent Positions (table Findexa style) */}
          <div className="card">
            <div className="flex items-center justify-between px-5 py-4" style={{ borderBottom: "1px solid var(--border)" }}>
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded-lg bg-blue-500/15 flex items-center justify-center">
                  <Wallet size={12} className="text-blue-400" />
                </div>
                <h3 className="text-sm font-semibold">Positions</h3>
              </div>
              <div className="flex items-center gap-2">
                <button className="flex items-center gap-1 text-[10px] px-2 py-1 rounded" style={{ background: "var(--bg-elevated)", color: "var(--text-muted)" }}>
                  <Filter size={10} /> Filtre
                </button>
                <span className="text-[10px] px-2 py-0.5 rounded-full font-medium" style={{ background: "var(--bg-elevated)", color: "var(--text-muted)" }}>
                  {allPositions.length}
                </span>
              </div>
            </div>

            {/* Table header */}
            <div className="hidden md:grid grid-cols-12 gap-2 px-5 py-2.5 text-[10px] font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)", borderBottom: "1px solid var(--border)" }}>
              <div className="col-span-4">Actif</div>
              <div className="col-span-2">Type</div>
              <div className="col-span-2 text-right">Valeur</div>
              <div className="col-span-2 text-right">Variation</div>
              <div className="col-span-2 text-right">Statut</div>
            </div>

            {allPositions.length > 0 ? (
              <div>
                {allPositions.slice(0, 10).map((p, i) => (
                  <div key={i} className="grid grid-cols-12 gap-2 px-5 py-3 items-center transition-colors hover:opacity-90"
                    style={{ borderBottom: i < allPositions.length - 1 ? "1px solid var(--border)" : "none" }}>
                    <div className="col-span-6 md:col-span-4 flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold shrink-0"
                        style={{ background: `${COLORS[p.type]}15`, color: COLORS[p.type] }}>
                        {(p.symbol || p.label || "?").slice(0, 3).toUpperCase()}
                      </div>
                      <div className="min-w-0">
                        <div className="text-sm font-medium truncate">{p.label}</div>
                        <div className="text-[10px] truncate" style={{ color: "var(--text-muted)" }}>{p.ville || p.plateforme || p.banque || ""}</div>
                      </div>
                    </div>
                    <div className="hidden md:flex col-span-2">
                      <span className="text-[10px] px-2 py-0.5 rounded-full font-medium"
                        style={{ background: `${COLORS[p.type]}12`, color: COLORS[p.type] }}>
                        {p.type === "immo" ? "Immo" : p.type === "crypto" ? "Crypto" : p.type === "commodity" ? "Commo" : "Cash"}
                      </span>
                    </div>
                    <div className="col-span-3 md:col-span-2 text-right">
                      <div className="text-sm font-semibold">{fmt(p.value)}</div>
                    </div>
                    <div className="col-span-3 md:col-span-2 text-right">
                      {p.change != null ? (
                        <span className={`inline-flex items-center gap-0.5 text-xs font-medium ${p.change >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                          {p.change >= 0 ? <ArrowUpRight size={11} /> : <ArrowDownRight size={11} />}
                          {p.change >= 0 ? "+" : ""}{p.change?.toFixed(1)}%
                        </span>
                      ) : <span style={{ color: "var(--text-faint)" }}>—</span>}
                    </div>
                    <div className="hidden md:block col-span-2 text-right">
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${p.value > 0 ? "text-emerald-400" : ""}`}
                        style={{ background: p.value > 0 ? "rgba(16,185,129,0.1)" : "var(--bg-elevated)", color: p.value > 0 ? undefined : "var(--text-muted)" }}>
                        {p.value > 0 ? "● Actif" : "● Inactif"}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 text-sm" style={{ color: "var(--text-muted)" }}>
                Ajoutez vos premiers actifs pour voir votre patrimoine ici.
              </div>
            )}
          </div>

          {/* Alertes opinion */}
          {opinion?.alertes?.length > 0 && (
            <div className="card p-5">
              <div className="flex items-center gap-2 mb-3">
                <AlertTriangle size={14} className="text-amber-400" />
                <h3 className="text-sm font-semibold">Points d'attention</h3>
              </div>
              {opinion.alertes.map((a, i) => (
                <div key={i} className={`flex items-start gap-2 text-xs mb-2 p-2.5 rounded-lg ${a.niveau === "critique" ? "bg-red-500/10 text-red-400" : a.niveau === "important" ? "bg-amber-500/10 text-amber-400" : "bg-blue-500/10 text-blue-400"}`}>
                  <AlertTriangle size={12} className="shrink-0 mt-0.5" />
                  <span>{a.message}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function fmt(n) {
  if (n == null || isNaN(n)) return "—";
  return new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(n);
}

function fmtLarge(n) {
  if (n == null || isNaN(n)) return "0 €";
  if (n >= 1000000) return `${(n / 1000000).toFixed(2).replace(".", ",")}M €`;
  return new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(n);
}

function fmtShort(n) {
  if (n == null) return "—";
  if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M€`;
  if (n >= 1000) return `${(n / 1000).toFixed(0)}k€`;
  return `${n.toFixed(0)}€`;
}
