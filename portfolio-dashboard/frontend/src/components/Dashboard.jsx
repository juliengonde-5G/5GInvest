import { PieChart, Pie, Cell, ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import { TrendingUp, TrendingDown, Home, Bitcoin, Gem, Wallet, ArrowUpRight, ArrowDownRight, MoreHorizontal } from "lucide-react";

const COLORS = { immo: "#8b5cf6", crypto: "#f59e0b", commodity: "#06b6d4", cash: "#10b981" };
const LABELS = { immo: "Immobilier", crypto: "Crypto", commodity: "Commodities", cash: "Cash" };

export default function Dashboard({ data, onNavigate }) {
  const { net_worth, allocation, real_estate, crypto, commodities, cash, history } = data;

  const pieData = [
    { name: "Immobilier", value: allocation.immo, color: COLORS.immo, pct: allocation.immo_pct },
    { name: "Crypto", value: allocation.crypto, color: COLORS.crypto, pct: allocation.crypto_pct },
    { name: "Commodities", value: allocation.commodity, color: COLORS.commodity, pct: allocation.commodity_pct },
    { name: "Cash", value: allocation.cash, color: COLORS.cash, pct: allocation.cash_pct },
  ].filter(d => d.value > 0);

  // All positions for the table
  const allPositions = [
    ...real_estate.map(p => ({ ...p, type: "immo", value: p.valeur_nette, change: p.rendement_brut })),
    ...crypto.map(p => ({ ...p, type: "crypto", value: p.current_value, change: p.pnl_pct })),
    ...commodities.map(p => ({ ...p, type: "commodity", value: p.current_value, change: p.pnl_pct })),
    ...cash.map(p => ({ ...p, type: "cash", value: p.solde, change: p.taux_interet })),
  ].sort((a, b) => (b.value || 0) - (a.value || 0));

  return (
    <div className="space-y-6">
      {/* ═══ STAT CARDS ═══ */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <StatCard
          label="Patrimoine Net"
          value={fmt(net_worth)}
          icon={<TrendingUp size={16} />}
          trend="+2.4%"
          trendUp={true}
          accent="emerald"
        />
        <StatCard
          label="Immobilier"
          value={fmt(allocation.immo)}
          sub={`${allocation.immo_pct?.toFixed(1)}%`}
          icon={<Home size={16} />}
          accent="violet"
          onClick={() => onNavigate("immo")}
        />
        <StatCard
          label="Crypto"
          value={fmt(allocation.crypto)}
          sub={`${allocation.crypto_pct?.toFixed(1)}%`}
          icon={<Bitcoin size={16} />}
          accent="amber"
          onClick={() => onNavigate("crypto")}
        />
        <StatCard
          label="Cash & Épargne"
          value={fmt(allocation.cash + allocation.commodity)}
          sub={`${(allocation.cash_pct + allocation.commodity_pct)?.toFixed(1)}%`}
          icon={<Wallet size={16} />}
          accent="emerald"
          onClick={() => onNavigate("cash")}
        />
      </div>

      {/* ═══ CHARTS ROW ═══ */}
      <div className="grid lg:grid-cols-5 gap-4">
        {/* Allocation Donut */}
        <div className="lg:col-span-2 card p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold">Allocation</h3>
            <button className="p-1 rounded hover:bg-white/5"><MoreHorizontal size={14} className="text-muted" /></button>
          </div>
          {pieData.length > 0 ? (
            <div className="flex items-center gap-6">
              <div className="relative w-[140px] h-[140px] shrink-0">
                <ResponsiveContainer>
                  <PieChart>
                    <Pie data={pieData} cx="50%" cy="50%" innerRadius={42} outerRadius={65} dataKey="value" stroke="none" startAngle={90} endAngle={-270}>
                      {pieData.map((e, i) => <Cell key={i} fill={e.color} />)}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-[10px] text-muted">Total</span>
                  <span className="text-sm font-bold">{fmtShort(net_worth)}</span>
                </div>
              </div>
              <div className="space-y-3 flex-1">
                {pieData.map(d => (
                  <div key={d.name} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-2.5 h-2.5 rounded-full" style={{ background: d.color }} />
                      <span className="text-xs text-muted">{d.name}</span>
                    </div>
                    <div className="text-right">
                      <span className="text-xs font-medium">{d.pct?.toFixed(1)}%</span>
                      <span className="text-[10px] text-muted-dark ml-2">{fmtShort(d.value)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="text-muted text-center py-8 text-sm">Aucun actif</div>
          )}
        </div>

        {/* Evolution Chart */}
        <div className="lg:col-span-3 card p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold">Évolution du patrimoine</h3>
            <div className="flex gap-1 text-[10px]">
              {["1M", "3M", "6M", "1A", "Max"].map(p => (
                <button key={p} className="px-2 py-1 rounded bg-white/[0.04] hover:bg-white/[0.08] text-muted transition">
                  {p}
                </button>
              ))}
            </div>
          </div>
          {history?.length > 1 ? (
            <ResponsiveContainer width="100%" height={180}>
              <AreaChart data={history}>
                <defs>
                  <linearGradient id="gradNet" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#8b5cf6" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="#8b5cf6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid vertical={false} stroke="#1c1c22" />
                <XAxis dataKey="date" tick={{ fill: "#52525b", fontSize: 10 }} tickLine={false} axisLine={false} tickFormatter={d => d.slice(5)} />
                <YAxis tick={{ fill: "#52525b", fontSize: 10 }} tickLine={false} axisLine={false} tickFormatter={v => `${(v/1000).toFixed(0)}k`} width={40} />
                <Tooltip
                  contentStyle={{ background: "#18181b", border: "1px solid #27272a", borderRadius: 8, fontSize: 12 }}
                  formatter={v => [`${v?.toLocaleString("fr-FR")} €`, ""]}
                  labelFormatter={l => l}
                />
                <Area type="monotone" dataKey="net_worth" stroke="#8b5cf6" fill="url(#gradNet)" strokeWidth={2} dot={false} name="Net Worth" />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex flex-col items-center justify-center h-[180px] text-muted text-sm">
              <p>Historique insuffisant</p>
              <p className="text-[10px] text-muted-dark mt-1">Les snapshots sont enregistrés quotidiennement</p>
            </div>
          )}
        </div>
      </div>

      {/* ═══ POSITIONS TABLE ═══ */}
      <div className="card">
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <h3 className="text-sm font-semibold">Toutes les positions</h3>
          <span className="text-[10px] text-muted bg-white/[0.04] px-2 py-0.5 rounded-full">{allPositions.length} actifs</span>
        </div>

        {/* Table header */}
        <div className="hidden md:grid grid-cols-12 gap-2 px-5 py-2.5 text-[10px] font-semibold text-muted-dark uppercase tracking-wider border-b border-border">
          <div className="col-span-4">Actif</div>
          <div className="col-span-2">Type</div>
          <div className="col-span-2 text-right">Valeur</div>
          <div className="col-span-2 text-right">Variation</div>
          <div className="col-span-2 text-right">Détail</div>
        </div>

        {/* Table rows */}
        <div className="divide-y divide-border">
          {allPositions.slice(0, 12).map((p, i) => (
            <div key={i} className="grid grid-cols-12 gap-2 px-5 py-3 items-center hover:bg-white/[0.02] transition-colors">
              {/* Name */}
              <div className="col-span-6 md:col-span-4 flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold shrink-0"
                  style={{ background: `${COLORS[p.type]}20`, color: COLORS[p.type] }}>
                  {(p.symbol || p.nom || "?").slice(0, 3).toUpperCase()}
                </div>
                <div className="min-w-0">
                  <div className="text-sm font-medium truncate">{p.nom || p.symbol}</div>
                  <div className="text-[10px] text-muted-dark truncate">{p.ville || p.plateforme || p.banque || p.type_produit || ""}</div>
                </div>
              </div>

              {/* Type badge */}
              <div className="hidden md:flex col-span-2">
                <span className="text-[10px] px-2 py-0.5 rounded-full font-medium"
                  style={{ background: `${COLORS[p.type]}15`, color: COLORS[p.type] }}>
                  {LABELS[p.type]}
                </span>
              </div>

              {/* Value */}
              <div className="col-span-3 md:col-span-2 text-right">
                <div className="text-sm font-semibold">{fmt(p.value)}</div>
              </div>

              {/* Change */}
              <div className="col-span-3 md:col-span-2 text-right">
                {p.change !== undefined && p.change !== null ? (
                  <div className={`inline-flex items-center gap-1 text-xs font-medium ${p.change >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                    {p.change >= 0 ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
                    {p.change >= 0 ? "+" : ""}{p.change?.toFixed(1)}%
                  </div>
                ) : (
                  <span className="text-xs text-muted-dark">—</span>
                )}
              </div>

              {/* Detail */}
              <div className="hidden md:block col-span-2 text-right text-[10px] text-muted-dark">
                {p.type === "immo" && `${p.surface_m2}m² · ${p.cashflow_mensuel >= 0 ? "+" : ""}${p.cashflow_mensuel}€/m`}
                {p.type === "crypto" && `${p.quantite} ${p.symbol}`}
                {p.type === "commodity" && `${p.quantite} unités`}
                {p.type === "cash" && `${p.taux_interet}% / an`}
              </div>
            </div>
          ))}
        </div>

        {allPositions.length === 0 && (
          <div className="text-center py-12 text-muted text-sm">
            Aucune position. Ajoutez des actifs via l'API.
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({ label, value, sub, icon, trend, trendUp, accent, onClick }) {
  const accentColors = {
    emerald: { bg: "bg-emerald-500/10", text: "text-emerald-400", ring: "ring-emerald-500/20" },
    violet: { bg: "bg-violet-500/10", text: "text-violet-400", ring: "ring-violet-500/20" },
    amber: { bg: "bg-amber-500/10", text: "text-amber-400", ring: "ring-amber-500/20" },
    cyan: { bg: "bg-cyan-500/10", text: "text-cyan-400", ring: "ring-cyan-500/20" },
    blue: { bg: "bg-blue-500/10", text: "text-blue-400", ring: "ring-blue-500/20" },
  };
  const c = accentColors[accent] || accentColors.emerald;

  return (
    <div className={`card p-4 ${onClick ? "cursor-pointer hover:bg-card-hover transition-colors" : ""}`} onClick={onClick}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-[11px] text-muted font-medium">{label}</span>
        <div className={`w-7 h-7 rounded-lg ${c.bg} flex items-center justify-center ${c.text}`}>{icon}</div>
      </div>
      <div className="text-xl font-bold tracking-tight">{value}</div>
      <div className="flex items-center gap-2 mt-1">
        {trend && (
          <span className={`inline-flex items-center gap-0.5 text-[10px] font-medium ${trendUp ? "text-emerald-400" : "text-red-400"}`}>
            {trendUp ? <ArrowUpRight size={10} /> : <ArrowDownRight size={10} />}
            {trend}
          </span>
        )}
        {sub && <span className="text-[10px] text-muted-dark">{sub}</span>}
      </div>
    </div>
  );
}

function fmt(n) {
  if (n == null) return "—";
  return new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(n);
}

function fmtShort(n) {
  if (n == null) return "—";
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M€`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}k€`;
  return `${n.toFixed(0)}€`;
}
