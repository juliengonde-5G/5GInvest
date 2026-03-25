import { Home, MapPin, Ruler, Euro, TrendingUp, ArrowUpRight, ArrowDownRight } from "lucide-react";

export default function PropertiesView({ items, onRefresh }) {
  const total = items?.reduce((s, p) => s + (p.valeur_nette || 0), 0) || 0;
  const totalLoyers = items?.reduce((s, p) => s + (p.loyer_mensuel || 0), 0) || 0;
  const totalCashflow = items?.reduce((s, p) => s + (p.cashflow_mensuel || 0), 0) || 0;

  if (!items?.length) return <EmptyState />;

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <MiniStat label="Valeur nette" value={fmt(total)} icon={<Home size={14} />} accent="violet" />
        <MiniStat label="Biens" value={items.length} icon={<MapPin size={14} />} accent="blue" />
        <MiniStat label="Loyers / mois" value={fmt(totalLoyers)} icon={<Euro size={14} />} accent="emerald" />
        <MiniStat label="Cashflow / mois" value={fmt(totalCashflow)} accent={totalCashflow >= 0 ? "emerald" : "red"} icon={<TrendingUp size={14} />} />
      </div>

      {/* Property Cards */}
      <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
        {items.map((p, i) => (
          <div key={i} className="card p-0 overflow-hidden">
            {/* Header gradient */}
            <div className="h-20 bg-gradient-to-br from-violet-600/20 to-blue-600/10 flex items-end px-4 pb-3">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-violet-500/20 flex items-center justify-center">
                  <Home size={16} className="text-violet-400" />
                </div>
                <div>
                  <div className="text-sm font-semibold">{p.nom}</div>
                  <div className="text-[10px] text-muted flex items-center gap-1">
                    <MapPin size={10} /> {p.ville} {p.code_postal}
                  </div>
                </div>
              </div>
            </div>

            {/* Details */}
            <div className="p-4 space-y-3">
              <div className="grid grid-cols-2 gap-2 text-xs">
                <Detail label="Surface" value={`${p.surface_m2} m²`} />
                <Detail label="Type" value={p.type_bien || "—"} />
                <Detail label="Prix achat" value={fmt(p.prix_achat)} />
                <Detail label="Valeur estimée" value={fmt(p.valeur_estimee)} />
                <Detail label="Capital restant" value={fmt(p.capital_restant_du)} />
                <Detail label="Prix/m²" value={`${p.prix_m2_estime?.toLocaleString("fr-FR")} €`} />
              </div>

              <div className="border-t border-border pt-3 grid grid-cols-3 gap-2 text-center">
                <div>
                  <div className="text-[10px] text-muted">Rdt brut</div>
                  <div className={`text-sm font-bold ${p.rendement_brut > 0 ? "text-emerald-400" : "text-muted"}`}>{p.rendement_brut}%</div>
                </div>
                <div>
                  <div className="text-[10px] text-muted">Rdt net</div>
                  <div className={`text-sm font-bold ${p.rendement_net > 0 ? "text-emerald-400" : "text-muted"}`}>{p.rendement_net}%</div>
                </div>
                <div>
                  <div className="text-[10px] text-muted">Cashflow</div>
                  <div className={`text-sm font-bold ${p.cashflow_mensuel >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                    {p.cashflow_mensuel >= 0 ? "+" : ""}{p.cashflow_mensuel}€
                  </div>
                </div>
              </div>

              <div className="flex justify-between items-center pt-1">
                <span className="text-[10px] text-muted-dark">Valeur nette</span>
                <span className="text-lg font-bold">{fmt(p.valeur_nette)}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function Detail({ label, value }) {
  return (
    <div>
      <div className="text-[10px] text-muted-dark">{label}</div>
      <div className="font-medium">{value}</div>
    </div>
  );
}

function MiniStat({ label, value, icon, accent }) {
  const bg = { violet: "bg-violet-500/10 text-violet-400", blue: "bg-blue-500/10 text-blue-400",
    emerald: "bg-emerald-500/10 text-emerald-400", red: "bg-red-500/10 text-red-400" };
  return (
    <div className="card p-3">
      <div className="flex items-center gap-2 mb-2">
        <div className={`w-6 h-6 rounded-md flex items-center justify-center ${bg[accent]}`}>{icon}</div>
        <span className="text-[10px] text-muted">{label}</span>
      </div>
      <div className="text-lg font-bold">{value}</div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="text-center py-24">
      <Home size={40} className="mx-auto text-muted-dark mb-3" />
      <p className="text-muted mb-1">Aucun bien immobilier</p>
      <p className="text-[10px] text-muted-dark">POST /api/real-estate pour ajouter un bien</p>
    </div>
  );
}

function fmt(n) {
  if (n == null) return "—";
  return new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(n);
}
