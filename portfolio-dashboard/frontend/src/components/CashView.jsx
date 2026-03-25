import { Wallet, Landmark, PiggyBank, ArrowUpRight } from "lucide-react";

const TYPE_LABELS = {
  ccp: "Compte courant", livret_a: "Livret A", ldds: "LDDS", lep: "LEP",
  pel: "PEL", csl: "CSL", autre: "Autre",
};

const TYPE_ICONS = {
  ccp: Wallet, livret_a: PiggyBank, ldds: PiggyBank, lep: PiggyBank,
  pel: Landmark, csl: Landmark,
};

export default function CashView({ items, onRefresh }) {
  if (!items?.length) return (
    <div className="text-center py-24">
      <Wallet size={40} className="mx-auto text-muted-dark mb-3" />
      <p className="text-muted">Aucun compte cash</p>
      <p className="text-[10px] text-muted-dark mt-1">POST /api/cash</p>
    </div>
  );

  const total = items.reduce((s, a) => s + (a.solde || 0), 0);
  const totalInteret = items.reduce((s, a) => s + (a.interet_annuel_estime || 0), 0);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <div className="card p-4">
          <div className="text-[10px] text-muted mb-1">Total cash</div>
          <div className="text-xl font-bold">{fmt(total)}</div>
        </div>
        <div className="card p-4">
          <div className="text-[10px] text-muted mb-1">Intérêts / an estimés</div>
          <div className="text-xl font-bold text-emerald-400">+{fmt(totalInteret)}</div>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-3">
        {items.map((a, i) => {
          const Icon = TYPE_ICONS[a.type_compte] || Wallet;
          const pctFull = a.plafond ? Math.min(100, (a.solde / a.plafond) * 100) : null;
          return (
            <div key={i} className="card p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                    <Icon size={16} className="text-emerald-400" />
                  </div>
                  <div>
                    <div className="text-sm font-semibold">{a.nom}</div>
                    <div className="text-[10px] text-muted-dark">{a.banque} · {TYPE_LABELS[a.type_compte] || a.type_compte}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-bold">{fmt(a.solde)}</div>
                  <div className="text-[10px] text-emerald-400 flex items-center gap-0.5 justify-end">
                    <ArrowUpRight size={10} />
                    {a.taux_interet}% / an
                  </div>
                </div>
              </div>

              {pctFull !== null && (
                <div>
                  <div className="flex justify-between text-[10px] text-muted-dark mb-1">
                    <span>Remplissage</span>
                    <span>{pctFull.toFixed(0)}% ({fmt(a.plafond)} max)</span>
                  </div>
                  <div className="h-1.5 bg-white/[0.05] rounded-full overflow-hidden">
                    <div className="h-full bg-emerald-500 rounded-full transition-all" style={{ width: `${pctFull}%` }} />
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function fmt(n) {
  if (n == null) return "—";
  return new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(n);
}
