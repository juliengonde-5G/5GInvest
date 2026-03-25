import { Bitcoin, ArrowUpRight, ArrowDownRight } from "lucide-react";

export default function CryptoView({ items, onRefresh }) {
  const total = items?.reduce((s, p) => s + (p.current_value || 0), 0) || 0;
  const totalPnl = items?.reduce((s, p) => s + (p.pnl_eur || 0), 0) || 0;

  if (!items?.length) return (
    <div className="text-center py-24">
      <Bitcoin size={40} className="mx-auto text-muted-dark mb-3" />
      <p className="text-muted">Aucune position crypto</p>
      <p className="text-[10px] text-muted-dark mt-1">POST /api/crypto</p>
    </div>
  );

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-3">
        <div className="card p-3">
          <div className="text-[10px] text-muted mb-1">Valeur totale</div>
          <div className="text-lg font-bold">{fmt(total)}</div>
        </div>
        <div className="card p-3">
          <div className="text-[10px] text-muted mb-1">P&L total</div>
          <div className={`text-lg font-bold ${totalPnl >= 0 ? "text-emerald-400" : "text-red-400"}`}>
            {totalPnl >= 0 ? "+" : ""}{fmt(totalPnl)}
          </div>
        </div>
        <div className="card p-3">
          <div className="text-[10px] text-muted mb-1">Positions</div>
          <div className="text-lg font-bold">{items.length}</div>
        </div>
      </div>

      <div className="card">
        <div className="divide-y divide-border">
          {items.map((p, i) => (
            <div key={i} className="flex items-center justify-between px-5 py-4 hover:bg-white/[0.02] transition-colors">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-amber-500/10 flex items-center justify-center text-amber-400 text-xs font-bold">
                  {p.symbol?.slice(0, 3)}
                </div>
                <div>
                  <div className="text-sm font-semibold">{p.nom || p.symbol}</div>
                  <div className="text-[10px] text-muted-dark">{p.quantite} {p.symbol} · {p.plateforme || ""}</div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm font-semibold">{fmt(p.current_value)}</div>
                <div className={`text-[11px] font-medium inline-flex items-center gap-0.5 ${p.pnl_eur >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                  {p.pnl_eur >= 0 ? <ArrowUpRight size={11} /> : <ArrowDownRight size={11} />}
                  {p.pnl_eur >= 0 ? "+" : ""}{fmt(p.pnl_eur)} ({p.pnl_pct >= 0 ? "+" : ""}{p.pnl_pct}%)
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function fmt(n) {
  if (n == null) return "—";
  return new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(n);
}
