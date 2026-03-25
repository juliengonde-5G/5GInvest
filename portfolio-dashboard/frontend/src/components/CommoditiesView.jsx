import { Gem, ArrowUpRight, ArrowDownRight } from "lucide-react";

export default function CommoditiesView({ items, onRefresh }) {
  if (!items?.length) return (
    <div className="text-center py-24">
      <Gem size={40} className="mx-auto text-muted-dark mb-3" />
      <p className="text-muted">Aucune position matières premières</p>
      <p className="text-[10px] text-muted-dark mt-1">POST /api/commodities</p>
    </div>
  );

  const total = items.reduce((s, p) => s + (p.current_value || 0), 0);

  return (
    <div className="space-y-4">
      <div className="card p-4 flex items-center justify-between">
        <div>
          <div className="text-[10px] text-muted">Valeur totale</div>
          <div className="text-xl font-bold">{fmt(total)}</div>
        </div>
        <div className="w-10 h-10 rounded-xl bg-cyan-500/10 flex items-center justify-center">
          <Gem size={20} className="text-cyan-400" />
        </div>
      </div>

      <div className="card divide-y divide-border">
        {items.map((p, i) => (
          <div key={i} className="flex items-center justify-between px-5 py-4 hover:bg-white/[0.02]">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-cyan-500/10 flex items-center justify-center text-cyan-400 text-xs font-bold">
                {p.symbol?.slice(0, 3)}
              </div>
              <div>
                <div className="text-sm font-semibold">{p.nom || p.symbol}</div>
                <div className="text-[10px] text-muted-dark">{p.quantite} · {p.type_produit} · {p.plateforme || ""}</div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm font-semibold">{fmt(p.current_value)}</div>
              {p.pnl_pct != null && (
                <div className={`text-[11px] font-medium inline-flex items-center gap-0.5 ${p.pnl_eur >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                  {p.pnl_eur >= 0 ? <ArrowUpRight size={11} /> : <ArrowDownRight size={11} />}
                  {p.pnl_pct >= 0 ? "+" : ""}{p.pnl_pct}%
                </div>
              )}
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
