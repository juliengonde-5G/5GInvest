import { PieChart, Pie, Cell, ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import { TrendingUp, TrendingDown, Home, Bitcoin, Gem, Wallet } from "lucide-react";

const COLORS = {
  immo: "#6366f1",
  crypto: "#f59e0b",
  commodity: "#06b6d4",
  cash: "#22c55e",
};

export default function Dashboard({ data }) {
  const { net_worth, allocation, real_estate, crypto, commodities, cash, history } = data;

  const pieData = [
    { name: "Immobilier", value: allocation.immo, color: COLORS.immo },
    { name: "Crypto", value: allocation.crypto, color: COLORS.crypto },
    { name: "Commodities", value: allocation.commodity, color: COLORS.commodity },
    { name: "Cash", value: allocation.cash, color: COLORS.cash },
  ].filter((d) => d.value > 0);

  return (
    <div className="space-y-6">
      {/* Net Worth */}
      <div className="bg-gradient-to-r from-dark-800 to-dark-700 rounded-2xl p-6 border border-dark-600">
        <div className="text-sm text-gray-400 mb-1">Patrimoine net total</div>
        <div className="text-4xl font-bold tracking-tight">{fmt(net_worth)}</div>
      </div>

      {/* 4 Asset Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <AssetCard icon={<Home size={20} />} label="Immobilier" value={allocation.immo} pct={allocation.immo_pct} color="text-indigo-400" bg="bg-indigo-500/10" />
        <AssetCard icon={<Bitcoin size={20} />} label="Crypto" value={allocation.crypto} pct={allocation.crypto_pct} color="text-amber-400" bg="bg-amber-500/10" />
        <AssetCard icon={<Gem size={20} />} label="Commodities" value={allocation.commodity} pct={allocation.commodity_pct} color="text-cyan-400" bg="bg-cyan-500/10" />
        <AssetCard icon={<Wallet size={20} />} label="Cash" value={allocation.cash} pct={allocation.cash_pct} color="text-green-400" bg="bg-green-500/10" />
      </div>

      {/* Charts Row */}
      <div className="grid lg:grid-cols-2 gap-4">
        {/* Pie Chart */}
        <div className="bg-dark-800 rounded-xl p-4 border border-dark-600">
          <h3 className="text-sm font-semibold text-gray-400 mb-3 uppercase tracking-wide">Allocation</h3>
          {pieData.length > 0 ? (
            <div className="flex items-center gap-4">
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="value" stroke="none">
                    {pieData.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-2 text-sm min-w-[120px]">
                {pieData.map((d) => (
                  <div key={d.name} className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ background: d.color }} />
                    <span className="text-gray-400">{d.name}</span>
                    <span className="ml-auto font-medium">{((d.value / net_worth) * 100).toFixed(0)}%</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="text-gray-500 text-center py-8">Aucun actif</div>
          )}
        </div>

        {/* Line Chart - Evolution */}
        <div className="bg-dark-800 rounded-xl p-4 border border-dark-600">
          <h3 className="text-sm font-semibold text-gray-400 mb-3 uppercase tracking-wide">Évolution</h3>
          {history?.length > 1 ? (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={history}>
                <CartesianGrid strokeDasharray="3 3" stroke="#252540" />
                <XAxis dataKey="date" tick={{ fill: "#64748b", fontSize: 11 }} tickFormatter={(d) => d.slice(5)} />
                <YAxis tick={{ fill: "#64748b", fontSize: 11 }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                <Tooltip
                  contentStyle={{ background: "#1a1a2e", border: "1px solid #252540", borderRadius: "8px" }}
                  formatter={(v) => [`${v.toLocaleString("fr-FR")}€`, ""]}
                />
                <Line type="monotone" dataKey="net_worth" stroke="#6366f1" strokeWidth={2} dot={false} name="Net Worth" />
                <Line type="monotone" dataKey="immo" stroke={COLORS.immo} strokeWidth={1} dot={false} opacity={0.5} name="Immo" />
                <Line type="monotone" dataKey="crypto" stroke={COLORS.crypto} strokeWidth={1} dot={false} opacity={0.5} name="Crypto" />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-gray-500 text-center py-8">
              Historique insuffisant.<br />
              <span className="text-xs">Les snapshots sont pris quotidiennement.</span>
            </div>
          )}
        </div>
      </div>

      {/* Top Positions */}
      <div className="bg-dark-800 rounded-xl p-4 border border-dark-600">
        <h3 className="text-sm font-semibold text-gray-400 mb-3 uppercase tracking-wide">Positions principales</h3>
        <div className="space-y-2">
          {[...real_estate.map((p) => ({ ...p, type: "immo", value: p.valeur_nette })),
            ...crypto.map((p) => ({ ...p, type: "crypto", value: p.current_value })),
            ...commodities.map((p) => ({ ...p, type: "commodity", value: p.current_value })),
          ]
            .sort((a, b) => (b.value || 0) - (a.value || 0))
            .slice(0, 8)
            .map((p, i) => (
              <div key={i} className="flex items-center justify-between py-2 border-b border-dark-600 last:border-0">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full`} style={{ background: COLORS[p.type] }} />
                  <div>
                    <div className="font-medium text-sm">{p.nom || p.symbol}</div>
                    <div className="text-xs text-gray-500">{p.type === "immo" ? p.ville : p.plateforme || p.symbol}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-semibold text-sm">{fmt(p.value)}</div>
                  {p.pnl_pct !== undefined && (
                    <div className={`text-xs font-medium ${p.pnl_pct >= 0 ? "text-green-400" : "text-red-400"}`}>
                      {p.pnl_pct >= 0 ? <TrendingUp size={12} className="inline mr-1" /> : <TrendingDown size={12} className="inline mr-1" />}
                      {p.pnl_pct >= 0 ? "+" : ""}{p.pnl_pct}%
                    </div>
                  )}
                  {p.rendement_brut !== undefined && (
                    <div className="text-xs text-indigo-400">Rdt {p.rendement_brut}%</div>
                  )}
                </div>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
}

function AssetCard({ icon, label, value, pct, color, bg }) {
  return (
    <div className={`${bg} rounded-xl p-4 border border-dark-600`}>
      <div className={`${color} mb-2`}>{icon}</div>
      <div className="text-xs text-gray-400">{label}</div>
      <div className="text-lg font-bold mt-1">{fmt(value)}</div>
      <div className="text-xs text-gray-500">{pct?.toFixed(1)}%</div>
    </div>
  );
}

function fmt(n) {
  if (n == null || n === 0) return "0 €";
  return new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(n);
}
