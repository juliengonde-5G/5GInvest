import { useState, useEffect } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { Home, MapPin, Euro, TrendingUp, Plus, RefreshCw, ArrowUpRight, CreditCard, Hammer } from "lucide-react";
import AddPropertyForm from "./AddPropertyForm";

const API = "/api";

export default function PropertiesView({ items, onRefresh }) {
  const [showForm, setShowForm] = useState(false);
  const [summary, setSummary] = useState(null);

  useEffect(() => { loadSummary(); }, [items]);

  async function loadSummary() {
    try {
      const res = await fetch(`${API}/real-estate/summary`);
      setSummary(await res.json());
    } catch (e) {}
  }

  const dvfHistory = summary?.dvf_history || [];
  const total = summary?.total_valeur_estimee || 0;
  const totalNette = summary?.total_valeur_nette || 0;
  const totalCredit = summary?.total_credit_restant || 0;
  const totalCashflow = summary?.total_cashflow_mensuel || 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">Patrimoine immobilier</h2>
        <button onClick={() => setShowForm(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-violet-600 text-sm font-medium hover:bg-violet-500 transition">
          <Plus size={16} /> Ajouter un bien
        </button>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <StatCard label="Valeur brute" value={fmt(total)} icon={<Home size={14} />} accent="violet" />
        <StatCard label="Valeur nette" value={fmt(totalNette)} icon={<TrendingUp size={14} />} accent="emerald"
          sub={totalCredit > 0 ? `Crédit: ${fmt(totalCredit)}` : undefined} />
        <StatCard label="Biens" value={summary?.nb_biens || 0} icon={<MapPin size={14} />} accent="blue" />
        <StatCard label="Cashflow / mois" value={fmt(totalCashflow)}
          icon={<Euro size={14} />}
          accent={totalCashflow >= 0 ? "emerald" : "red"} />
      </div>

      {/* DVF Historique 10 ans */}
      {dvfHistory.length > 0 && (
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold">Évolution prix/m² (DVF 10 ans)</h3>
            <span className="text-[10px] text-[#52525b]">{dvfHistory.length} années · Source: DVF notaires</span>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={dvfHistory}>
              <CartesianGrid vertical={false} stroke="#1c1c22" />
              <XAxis dataKey="year" tick={{ fill: "#52525b", fontSize: 11 }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fill: "#52525b", fontSize: 10 }} tickLine={false} axisLine={false}
                tickFormatter={v => `${v.toLocaleString("fr-FR")}€`} width={60} />
              <Tooltip
                contentStyle={{ background: "#18181b", border: "1px solid #27272a", borderRadius: 8, fontSize: 12 }}
                formatter={v => [`${v?.toLocaleString("fr-FR")} €/m²`, "Prix médian"]}
              />
              <Bar dataKey="prix_m2_median" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Property Cards */}
      {(summary?.biens || items || []).length > 0 ? (
        <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
          {(summary?.biens || items).map((p, i) => (
            <PropertyCard key={i} p={p} />
          ))}
        </div>
      ) : (
        <div className="text-center py-24">
          <Home size={40} className="mx-auto text-[#27272a] mb-3" />
          <p className="text-[#71717a] mb-2">Aucun bien immobilier</p>
          <button onClick={() => setShowForm(true)} className="text-violet-400 text-sm hover:underline">
            Ajouter votre premier bien
          </button>
        </div>
      )}

      {/* Form Modal */}
      {showForm && (
        <AddPropertyForm
          onClose={() => setShowForm(false)}
          onCreated={() => { setShowForm(false); onRefresh(); loadSummary(); }}
        />
      )}
    </div>
  );
}

function PropertyCard({ p }) {
  const pvInfo = p.impot_pv_estime || {};
  const nbLoans = p.loans?.length || 0;
  const nbWorks = p.works?.length || 0;

  return (
    <div className="card p-0 overflow-hidden">
      {/* Header gradient */}
      <div className="h-24 bg-gradient-to-br from-violet-600/20 to-blue-600/10 px-4 pb-3 flex items-end">
        <div className="flex items-center gap-3 w-full">
          <div className="w-10 h-10 rounded-xl bg-violet-500/20 flex items-center justify-center shrink-0">
            <Home size={20} className="text-violet-400" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="text-sm font-bold truncate">{p.nom}</div>
            <div className="text-[10px] text-[#a1a1aa] flex items-center gap-1 truncate">
              <MapPin size={10} /> {p.adresse ? `${p.adresse}, ` : ""}{p.code_postal} {p.ville}
            </div>
          </div>
          {p.dpe && (
            <span className="text-xs font-bold px-2 py-0.5 rounded"
              style={{ background: DPE_COLORS[p.dpe], color: p.dpe <= "C" ? "#000" : "#fff" }}>
              {p.dpe}
            </span>
          )}
        </div>
      </div>

      <div className="p-4 space-y-3">
        {/* Surfaces & type */}
        <div className="grid grid-cols-3 gap-2 text-xs">
          <Detail label="Surface" value={`${p.surface_habitable_m2 || p.surface_carrez_m2 || 0} m²`} />
          <Detail label="Pièces" value={p.nb_pieces || "—"} />
          <Detail label="Détention" value={`${p.duree_detention_ans || 0} ans`} />
        </div>

        {/* Financier */}
        <div className="border-t border-[#1c1c22] pt-3 grid grid-cols-2 gap-2 text-xs">
          <Detail label="Prix achat total" value={fmt(p.prix_achat_total)} />
          <Detail label="Valeur estimée" value={fmt(p.valeur_estimee)} accent />
          <Detail label="DVF prix/m²" value={`${p.prix_m2_dvf?.toLocaleString("fr-FR") || "—"} €`} />
          <Detail label="Capital restant" value={fmt(p.capital_restant_du_total)} />
        </div>

        {/* Rendements */}
        {p.loyer_mensuel_hc > 0 && (
          <div className="border-t border-[#1c1c22] pt-3 grid grid-cols-3 gap-2 text-center">
            <div>
              <div className="text-[10px] text-[#52525b]">Rdt brut</div>
              <div className={`text-sm font-bold ${p.rendement_brut > 0 ? "text-emerald-400" : "text-[#52525b]"}`}>{p.rendement_brut}%</div>
            </div>
            <div>
              <div className="text-[10px] text-[#52525b]">Rdt net</div>
              <div className={`text-sm font-bold ${p.rendement_net > 0 ? "text-emerald-400" : "text-[#52525b]"}`}>{p.rendement_net}%</div>
            </div>
            <div>
              <div className="text-[10px] text-[#52525b]">Cashflow</div>
              <div className={`text-sm font-bold ${p.cashflow_mensuel >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                {p.cashflow_mensuel >= 0 ? "+" : ""}{p.cashflow_mensuel}€
              </div>
            </div>
          </div>
        )}

        {/* Plus-value */}
        <div className="border-t border-[#1c1c22] pt-3 space-y-1">
          <div className="flex justify-between text-xs">
            <span className="text-[#71717a]">Plus-value brute</span>
            <span className={p.plus_value_brute >= 0 ? "text-emerald-400 font-medium" : "text-red-400 font-medium"}>
              {p.plus_value_brute >= 0 ? "+" : ""}{fmt(p.plus_value_brute)}
            </span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-[#71717a]">Impôt PV estimé</span>
            <span className="font-medium">{pvInfo.exonere ? <span className="text-emerald-400">Exonéré</span> : fmt(pvInfo.total)}</span>
          </div>
          <div className="text-[10px] text-[#3f3f46]">{pvInfo.raison}</div>
        </div>

        {/* Valeur nette */}
        <div className="flex justify-between items-center border-t border-[#1c1c22] pt-3">
          <span className="text-xs text-[#71717a]">Valeur nette</span>
          <span className="text-lg font-bold">{fmt(p.valeur_nette)}</span>
        </div>

        {/* Badges prêts/travaux */}
        <div className="flex gap-2">
          {nbLoans > 0 && (
            <span className="text-[10px] bg-blue-500/10 text-blue-400 px-2 py-0.5 rounded-full flex items-center gap-1">
              <CreditCard size={10} /> {nbLoans} prêt(s)
            </span>
          )}
          {nbWorks > 0 && (
            <span className="text-[10px] bg-amber-500/10 text-amber-400 px-2 py-0.5 rounded-full flex items-center gap-1">
              <Hammer size={10} /> {nbWorks} travaux
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

const DPE_COLORS = { A: "#319834", B: "#33cc31", C: "#cbfc33", D: "#fcfc33", E: "#fccc33", F: "#fc9833", G: "#fc3333" };

function Detail({ label, value, accent }) {
  return (
    <div>
      <div className="text-[10px] text-[#52525b]">{label}</div>
      <div className={`font-medium ${accent ? "text-violet-400" : "text-white"}`}>{value}</div>
    </div>
  );
}

function StatCard({ label, value, sub, icon, accent }) {
  const colors = {
    violet: "bg-violet-500/10 text-violet-400",
    emerald: "bg-emerald-500/10 text-emerald-400",
    blue: "bg-blue-500/10 text-blue-400",
    red: "bg-red-500/10 text-red-400",
  };
  return (
    <div className="card p-4">
      <div className="flex items-center gap-2 mb-2">
        <div className={`w-7 h-7 rounded-lg flex items-center justify-center ${colors[accent]}`}>{icon}</div>
        <span className="text-[11px] text-[#71717a]">{label}</span>
      </div>
      <div className="text-lg font-bold">{typeof value === "number" ? value : value}</div>
      {sub && <div className="text-[10px] text-[#52525b] mt-0.5">{sub}</div>}
    </div>
  );
}

function fmt(n) {
  if (n == null || isNaN(n)) return "—";
  return new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(n);
}
