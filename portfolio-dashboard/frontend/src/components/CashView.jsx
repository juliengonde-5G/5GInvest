import { useState, useEffect } from "react";
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { Wallet, Landmark, PiggyBank, ArrowUpRight, Plus, AlertTriangle, Lightbulb, TrendingUp, Clock, Loader2, Wifi } from "lucide-react";
import BankingConnect from "./BankingConnect";

const API = "/api";

export default function CashView({ items, onRefresh }) {
  const [summary, setSummary] = useState(null);
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [forecastHorizon, setForecastHorizon] = useState("3_mois");
  const [showAdd, setShowAdd] = useState(false);
  const [showBanking, setShowBanking] = useState(false);

  useEffect(() => { loadSummary(); }, [items]);

  async function loadSummary() {
    try {
      const res = await fetch(`${API}/cash/summary`);
      setSummary(await res.json());
    } catch (e) {}
  }

  async function loadAnalysis(accountId) {
    setAnalysis(null);
    try {
      const res = await fetch(`${API}/cash/${accountId}/analysis`);
      setAnalysis(await res.json());
    } catch (e) {}
  }

  function selectAccount(account) {
    setSelectedAccount(account);
    loadAnalysis(account.id);
  }

  const total = summary?.total_solde || 0;
  const totalInteret = summary?.total_interet_annuel || 0;
  const comptes = summary?.comptes || items || [];
  const propositions = summary?.propositions || [];

  // Si un compte est sélectionné, afficher le détail
  if (selectedAccount && analysis) return (
    <AccountDetail
      account={selectedAccount}
      analysis={analysis}
      forecastHorizon={forecastHorizon}
      setForecastHorizon={setForecastHorizon}
      onBack={() => { setSelectedAccount(null); setAnalysis(null); }}
    />
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">Cash & Épargne</h2>
        <div className="flex gap-2">
          <button onClick={() => setShowBanking(!showBanking)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 text-sm font-medium hover:bg-blue-500 transition">
            <Wifi size={16} /> Importer CSV
          </button>
          <button onClick={() => setShowAdd(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 text-sm font-medium hover:bg-emerald-500 transition">
            <Plus size={16} /> Manuel
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-3">
        <div className="card p-4">
          <div className="text-[10px] text-[#71717a] mb-1">Total cash</div>
          <div className="text-xl font-bold">{fmt(total)}</div>
        </div>
        <div className="card p-4">
          <div className="text-[10px] text-[#71717a] mb-1">Intérêts / an</div>
          <div className="text-xl font-bold text-emerald-400">+{fmt(totalInteret)}</div>
        </div>
        <div className="card p-4">
          <div className="text-[10px] text-[#71717a] mb-1">Comptes</div>
          <div className="text-xl font-bold">{comptes.length}</div>
        </div>
      </div>

      {/* Connexion bancaire */}
      {showBanking && (
        <BankingConnect accounts={comptes} onSynced={() => { setShowBanking(false); onRefresh(); loadSummary(); }} />
      )}

      {/* Propositions d'optimisation */}
      {propositions.length > 0 && (
        <div className="space-y-2">
          {propositions.map((p, i) => (
            <div key={i} className="card p-3 border-l-4 border-l-amber-500 bg-amber-500/5">
              <div className="flex items-center gap-2 text-sm">
                <Lightbulb size={14} className="text-amber-400 shrink-0" />
                <span className="text-[#a1a1aa]">{p.message}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Comptes */}
      {comptes.length > 0 ? (
        <div className="grid md:grid-cols-2 gap-3">
          {comptes.map((a, i) => (
            <div key={i} className="card p-4 cursor-pointer hover:bg-[#131316] transition" onClick={() => selectAccount(a)}>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                    {a.type_compte === "ccp" ? <Wallet size={16} className="text-emerald-400" /> : <PiggyBank size={16} className="text-emerald-400" />}
                  </div>
                  <div>
                    <div className="text-sm font-semibold">{a.nom}</div>
                    <div className="text-[10px] text-[#52525b]">{a.banque} · {a.type_label || a.type_compte}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-bold">{fmt(a.solde)}</div>
                  <div className="text-[10px] text-emerald-400 flex items-center gap-0.5 justify-end">
                    <ArrowUpRight size={10} /> {a.taux_interet}% / an
                  </div>
                </div>
              </div>

              {a.remplissage_pct !== null && a.remplissage_pct !== undefined && (
                <div>
                  <div className="flex justify-between text-[10px] text-[#52525b] mb-1">
                    <span>Remplissage</span>
                    <span>{a.remplissage_pct.toFixed(0)}% ({fmt(a.plafond)} max)</span>
                  </div>
                  <div className="h-1.5 bg-[#1c1c22] rounded-full overflow-hidden">
                    <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${Math.min(100, a.remplissage_pct)}%` }} />
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-20">
          <Wallet size={40} className="mx-auto text-[#27272a] mb-3" />
          <p className="text-[#71717a]">Aucun compte cash</p>
        </div>
      )}
    </div>
  );
}


// ─── ACCOUNT DETAIL WITH FORECAST ─────────────────────────

function AccountDetail({ account, analysis, forecastHorizon, setForecastHorizon, onBack }) {
  const forecast = analysis?.forecast?.[forecastHorizon] || [];
  const budget = analysis?.budget || {};
  const recurring = analysis?.recurring || [];

  return (
    <div className="space-y-6">
      <button onClick={onBack} className="text-sm text-[#71717a] hover:text-white">&larr; Retour</button>

      {/* Header */}
      <div className="card p-5">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-xl font-bold">{account.nom}</h2>
            <div className="text-xs text-[#71717a]">{account.banque} · {account.type_label} · {account.taux_interet}%</div>
          </div>
          <div className="text-2xl font-bold">{fmt(account.solde)}</div>
        </div>
      </div>

      {/* Budget summary */}
      {budget.total_revenus > 0 && (
        <div className="card p-5">
          <h3 className="text-sm font-semibold mb-3">Budget (3 derniers mois)</h3>
          <div className="grid grid-cols-3 gap-3 mb-4">
            <div>
              <div className="text-[10px] text-[#52525b]">Revenus / mois</div>
              <div className="text-sm font-bold text-emerald-400">+{fmt(budget.total_revenus / 3)}</div>
            </div>
            <div>
              <div className="text-[10px] text-[#52525b]">Dépenses / mois</div>
              <div className="text-sm font-bold text-red-400">-{fmt(budget.total_depenses / 3)}</div>
            </div>
            <div>
              <div className="text-[10px] text-[#52525b]">Taux épargne</div>
              <div className="text-sm font-bold text-blue-400">{budget.taux_epargne_pct}%</div>
            </div>
          </div>

          {/* Top dépenses */}
          {budget.top_depenses?.length > 0 && (
            <div>
              <div className="text-[10px] text-[#52525b] mb-2">Top dépenses</div>
              {budget.top_depenses.map(([cat, montant], i) => (
                <div key={i} className="flex justify-between text-xs py-1 border-b border-[#1c1c22] last:border-0">
                  <span className="text-[#a1a1aa] capitalize">{cat}</span>
                  <span className="font-medium text-red-400">-{fmt(montant)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Prévisionnel */}
      <div className="card p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold">Prévisionnel de solde</h3>
          <div className="flex gap-1">
            {[["3_mois", "3M"], ["6_mois", "6M"], ["12_mois", "12M"]].map(([key, label]) => (
              <button key={key} onClick={() => setForecastHorizon(key)}
                className={`px-2.5 py-1 rounded text-[10px] font-medium transition
                  ${forecastHorizon === key ? "bg-emerald-500/20 text-emerald-400" : "bg-white/[0.04] text-[#52525b] hover:text-white"}`}>
                {label}
              </button>
            ))}
          </div>
        </div>
        {forecast.length > 0 ? (
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={forecast}>
              <defs>
                <linearGradient id="gradForecast" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#10b981" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#10b981" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid vertical={false} stroke="#1c1c22" />
              <XAxis dataKey="date" tick={{ fill: "#52525b", fontSize: 10 }} tickLine={false} axisLine={false}
                tickFormatter={d => d.slice(5, 10)} />
              <YAxis tick={{ fill: "#52525b", fontSize: 10 }} tickLine={false} axisLine={false}
                tickFormatter={v => `${(v/1000).toFixed(0)}k`} width={40} />
              <Tooltip contentStyle={{ background: "#18181b", border: "1px solid #27272a", borderRadius: 8, fontSize: 12 }}
                formatter={v => [`${v?.toLocaleString("fr-FR")} €`, "Solde prévu"]} />
              <Area type="monotone" dataKey="solde_prevu" stroke="#10b981" fill="url(#gradForecast)" strokeWidth={2} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-center py-8 text-[#52525b] text-sm">
            Ajoutez des transactions pour générer le prévisionnel
          </div>
        )}
      </div>

      {/* Flux récurrents */}
      {recurring.length > 0 && (
        <div className="card">
          <div className="px-5 py-3 border-b border-[#1c1c22]">
            <span className="text-sm font-semibold">Flux récurrents détectés ({recurring.length})</span>
          </div>
          <div className="divide-y divide-[#1c1c22]">
            {recurring.map((r, i) => (
              <div key={i} className="flex items-center justify-between px-5 py-3">
                <div>
                  <div className="text-sm font-medium">{r.libelle}</div>
                  <div className="text-[10px] text-[#52525b] capitalize">{r.categorie} · {r.frequence} · {r.nb_occurrences}x</div>
                </div>
                <div className={`text-sm font-bold ${r.montant_moyen >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                  {r.montant_moyen >= 0 ? "+" : ""}{fmt(r.montant_moyen)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}


function fmt(n) {
  if (n == null || isNaN(n)) return "—";
  return new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(n);
}
