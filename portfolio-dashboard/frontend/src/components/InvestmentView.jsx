import { useState, useEffect } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { TrendingUp, TrendingDown, ArrowUpRight, ArrowDownRight, Plus, Target, Clock, Zap, Shield, AlertTriangle, Check, X, ChevronRight, Loader2 } from "lucide-react";

const API = "/api";

const PROFILS = [
  { id: "prudent", label: "Prudent", desc: "2-4% visé, capital préservé", color: "emerald", icon: Shield },
  { id: "equilibre", label: "Équilibré", desc: "4-7% visé, mix sécurité/rendement", color: "blue", icon: Target },
  { id: "dynamique", label: "Dynamique", desc: "7-12% visé, volatilité acceptée", color: "amber", icon: Zap },
  { id: "agressif", label: "Agressif", desc: ">12% visé, risque élevé", color: "red", icon: AlertTriangle },
  { id: "sur_mesure", label: "Sur-mesure", desc: "Adapté à votre profil temps/renta", color: "violet", icon: Target },
];

const REACTIVITES = [
  { id: "passive", label: "Passive", desc: "Buy & hold, peu d'interventions" },
  { id: "moderee", label: "Modérée", desc: "Arbitrages trimestriels" },
  { id: "active", label: "Active", desc: "Suivi hebdomadaire, arbitrages fréquents" },
  { id: "tres_active", label: "Très active", desc: "Trading quotidien, swing" },
];

export default function InvestmentView({ onRefresh }) {
  const [paths, setPaths] = useState([]);
  const [selectedPath, setSelectedPath] = useState(null);
  const [showCreate, setShowCreate] = useState(false);
  const [opinions, setOpinions] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadPaths(); }, []);

  async function loadPaths() {
    setLoading(true);
    try {
      const res = await fetch(`${API}/paths`);
      const data = await res.json();
      setPaths(data);
      // Charger les opinions pour chaque parcours actif
      for (const p of data.filter(p => p.statut === "actif")) {
        loadOpinion(p.id);
      }
    } catch (e) {}
    setLoading(false);
  }

  async function loadOpinion(pathId) {
    try {
      const res = await fetch(`${API}/paths/${pathId}/opinion`);
      const data = await res.json();
      setOpinions(prev => ({ ...prev, [pathId]: data }));
    } catch (e) {}
  }

  if (loading) return <div className="flex justify-center py-20"><Loader2 size={28} className="animate-spin text-[#52525b]" /></div>;

  if (selectedPath) {
    return <PathDetail path={selectedPath} opinion={opinions[selectedPath.id]} onBack={() => { setSelectedPath(null); loadPaths(); }} />;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">Parcours d'investissement</h2>
        <button onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 text-sm font-medium hover:bg-blue-500 transition">
          <Plus size={16} /> Nouveau parcours
        </button>
      </div>

      {/* Opinions du jour */}
      {Object.values(opinions).some(o => o.alertes?.length > 0) && (
        <div className="space-y-2">
          {Object.values(opinions).flatMap(o => o.alertes || []).map((a, i) => (
            <div key={i} className={`card p-3 border-l-4 ${a.urgence === "critique" ? "border-l-red-500 bg-red-500/5" : "border-l-amber-500 bg-amber-500/5"}`}>
              <div className="flex items-center gap-2">
                <AlertTriangle size={14} className={a.urgence === "critique" ? "text-red-400" : "text-amber-400"} />
                <span className="text-sm font-medium">{a.message}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Parcours cards */}
      {paths.length > 0 ? (
        <div className="grid md:grid-cols-2 gap-4">
          {paths.map(p => {
            const profil = PROFILS.find(pr => pr.id === p.profil_risque) || PROFILS[1];
            const opinion = opinions[p.id];
            return (
              <div key={p.id} className="card p-0 overflow-hidden cursor-pointer hover:bg-[#131316] transition" onClick={() => setSelectedPath(p)}>
                <div className={`h-1.5 bg-${profil.color}-500`} />
                <div className="p-4">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <div className="font-bold">{p.nom}</div>
                      <div className="text-[10px] text-[#71717a] mt-0.5">{profil.label} · {p.maturite_mois} mois · {p.enveloppe?.toUpperCase()}</div>
                    </div>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${p.statut === "actif" ? "bg-emerald-500/10 text-emerald-400" : "bg-[#27272a] text-[#71717a]"}`}>
                      {p.statut}
                    </span>
                  </div>

                  <div className="grid grid-cols-3 gap-3 mb-3">
                    <div>
                      <div className="text-[10px] text-[#52525b]">Investi</div>
                      <div className="text-sm font-bold">{fmt(p.mise_depart)}</div>
                    </div>
                    <div>
                      <div className="text-[10px] text-[#52525b]">Valeur</div>
                      <div className="text-sm font-bold">{fmt(p.valeur_actuelle)}</div>
                    </div>
                    <div>
                      <div className="text-[10px] text-[#52525b]">P&L</div>
                      <div className={`text-sm font-bold ${p.pnl_eur >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                        {p.pnl_eur >= 0 ? "+" : ""}{fmt(p.pnl_eur)}
                      </div>
                    </div>
                  </div>

                  {/* Barre de progression */}
                  <div>
                    <div className="flex justify-between text-[10px] text-[#52525b] mb-1">
                      <span>Progression vers objectif</span>
                      <span>{p.progression_objectif_pct?.toFixed(0)}%</span>
                    </div>
                    <div className="h-1.5 bg-[#1c1c22] rounded-full overflow-hidden">
                      <div className={`h-full bg-${profil.color}-500 rounded-full transition-all`}
                        style={{ width: `${Math.min(100, p.progression_objectif_pct || 0)}%` }} />
                    </div>
                  </div>

                  {/* Opinion mini */}
                  {opinion?.opinions?.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-[#1c1c22] text-[11px] text-[#a1a1aa] line-clamp-2">
                      {opinion.opinions[0]}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="text-center py-20">
          <Target size={40} className="mx-auto text-[#27272a] mb-3" />
          <p className="text-[#71717a] mb-2">Aucun parcours d'investissement</p>
          <button onClick={() => setShowCreate(true)} className="text-blue-400 text-sm hover:underline">
            Créer votre premier parcours
          </button>
        </div>
      )}

      {showCreate && <CreatePathModal onClose={() => setShowCreate(false)} onCreated={() => { setShowCreate(false); loadPaths(); }} />}
    </div>
  );
}


// ─── PATH DETAIL ─────────────────────────────────────────

function PathDetail({ path, opinion, onBack }) {
  const [detail, setDetail] = useState(path);
  const [arbs, setArbs] = useState(path.arbitrages || []);

  async function refresh() {
    const res = await fetch(`${API}/paths/${path.id}`);
    const d = await res.json();
    setDetail(d);
    setArbs(d.arbitrages || []);
  }

  async function handleArbitrage(arbId, statut) {
    await fetch(`${API}/paths/${path.id}/arbitrages/${arbId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ statut }),
    });
    refresh();
  }

  const positions = detail.positions?.filter(p => !p.date_sortie) || [];
  const closed = detail.positions?.filter(p => p.date_sortie) || [];

  return (
    <div className="space-y-6">
      <button onClick={onBack} className="text-sm text-[#71717a] hover:text-white transition">&larr; Retour aux parcours</button>

      {/* Header */}
      <div className="card p-5">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-xl font-bold">{detail.nom}</h2>
            <div className="text-xs text-[#71717a] mt-1">{detail.profil_risque} · {detail.reactivite} · {detail.maturite_mois} mois · {detail.banque} ({detail.enveloppe})</div>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold">{fmt(detail.valeur_actuelle)}</div>
            <div className={`text-sm font-medium ${detail.pnl_eur >= 0 ? "text-emerald-400" : "text-red-400"}`}>
              {detail.pnl_eur >= 0 ? "+" : ""}{fmt(detail.pnl_eur)} ({detail.rendement_actuel_pct}%)
            </div>
          </div>
        </div>
        <div className="mt-3">
          <div className="flex justify-between text-[10px] text-[#52525b] mb-1">
            <span>Objectif: {fmt(detail.objectif_sortie)}</span>
            <span>{detail.progression_objectif_pct?.toFixed(0)}%</span>
          </div>
          <div className="h-2 bg-[#1c1c22] rounded-full overflow-hidden">
            <div className="h-full bg-blue-500 rounded-full" style={{ width: `${Math.min(100, detail.progression_objectif_pct || 0)}%` }} />
          </div>
        </div>
      </div>

      {/* Opinion */}
      {opinion && (opinion.opinions?.length > 0 || opinion.alertes?.length > 0) && (
        <div className="card p-4 border-l-4 border-l-blue-500">
          <div className="text-xs text-[#71717a] uppercase tracking-wide mb-2">Opinion du jour</div>
          {opinion.alertes?.map((a, i) => (
            <div key={i} className={`text-sm mb-2 font-medium ${a.urgence === "critique" ? "text-red-400" : "text-amber-400"}`}>
              <AlertTriangle size={14} className="inline mr-1" /> {a.message}
            </div>
          ))}
          {opinion.opinions?.map((o, i) => (
            <div key={i} className="text-sm text-[#a1a1aa] mb-1">{o}</div>
          ))}
          <div className="text-[9px] text-[#3f3f46] mt-2 italic">{opinion.disclaimer}</div>
        </div>
      )}

      {/* Positions ouvertes */}
      <div className="card">
        <div className="flex justify-between items-center px-5 py-3 border-b border-[#1c1c22]">
          <span className="text-sm font-semibold">Positions ouvertes ({positions.length})</span>
        </div>
        {positions.length > 0 ? (
          <div className="divide-y divide-[#1c1c22]">
            {positions.map(p => (
              <div key={p.id} className="flex items-center justify-between px-5 py-3">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-blue-500/10 text-blue-400 flex items-center justify-center text-[10px] font-bold">
                    {p.symbol?.slice(0, 3)}
                  </div>
                  <div>
                    <div className="text-sm font-medium">{p.nom || p.symbol}</div>
                    <div className="text-[10px] text-[#52525b]">{p.quantite} × {p.prix_entree}€ · {p.type_produit}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-semibold">{fmt(p.valeur_actuelle)}</div>
                  <div className={`text-[11px] font-medium inline-flex items-center gap-0.5 ${p.pnl_eur >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                    {p.pnl_eur >= 0 ? <ArrowUpRight size={11} /> : <ArrowDownRight size={11} />}
                    {p.pnl_eur >= 0 ? "+" : ""}{fmt(p.pnl_eur)} ({p.pnl_pct}%)
                  </div>
                  {p.objectif_atteint && (
                    <div className={`text-[10px] mt-0.5 ${p.objectif_atteint === "take_profit" ? "text-emerald-400" : "text-red-400"}`}>
                      {p.objectif_atteint === "take_profit" ? "TAKE PROFIT" : "STOP LOSS"}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-[#52525b] text-sm">Aucune position ouverte</div>
        )}
      </div>

      {/* Arbitrages proposés */}
      {arbs.filter(a => a.statut === "propose").length > 0 && (
        <div className="card">
          <div className="px-5 py-3 border-b border-[#1c1c22]">
            <span className="text-sm font-semibold">Arbitrages proposés</span>
          </div>
          {arbs.filter(a => a.statut === "propose").map(a => (
            <div key={a.id} className="px-5 py-4 border-b border-[#1c1c22] last:border-0">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${a.type_action === "buy" ? "bg-emerald-500/10 text-emerald-400" : a.type_action === "sell" ? "bg-red-500/10 text-red-400" : "bg-amber-500/10 text-amber-400"}`}>
                    {a.type_action}
                  </span>
                  <span className="text-sm font-medium ml-2">{a.nom_produit || a.symbol}</span>
                  {a.montant_suggere > 0 && <span className="text-xs text-[#71717a] ml-2">{fmt(a.montant_suggere)}</span>}
                </div>
                <div className="flex gap-1">
                  <button onClick={() => handleArbitrage(a.id, "accepte")}
                    className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20"><Check size={14} /></button>
                  <button onClick={() => handleArbitrage(a.id, "refuse")}
                    className="p-1.5 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20"><X size={14} /></button>
                </div>
              </div>
              <div className="text-xs text-[#a1a1aa]">{a.raison}</div>
              {a.symbol_remplacement && (
                <div className="text-[10px] text-[#71717a] mt-1">Remplacement suggéré: {a.nom_remplacement || a.symbol_remplacement}</div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}


// ─── CREATE PATH MODAL ───────────────────────────────────

function CreatePathModal({ onClose, onCreated }) {
  const [step, setStep] = useState(0);
  const [form, setForm] = useState({
    nom: "", profil_risque: "equilibre", reactivite: "moderee",
    maturite_mois: 12, mise_depart: 100, objectif_sortie: 0,
    objectif_rendement_pct: 6, banque: "Revolut", enveloppe: "cto",
    date_ouverture_enveloppe: "",
  });
  const [saving, setSaving] = useState(false);

  function set(k, v) { setForm(f => ({ ...f, [k]: v })); }

  // Auto-calcul objectif de sortie
  useEffect(() => {
    const mise = parseFloat(form.mise_depart) || 0;
    const rdt = parseFloat(form.objectif_rendement_pct) || 0;
    const mois = parseInt(form.maturite_mois) || 12;
    set("objectif_sortie", Math.round(mise * (1 + rdt / 100 * mois / 12)));
  }, [form.mise_depart, form.objectif_rendement_pct, form.maturite_mois]);

  async function save() {
    setSaving(true);
    try {
      const body = { ...form, mise_depart: parseFloat(form.mise_depart), objectif_sortie: parseFloat(form.objectif_sortie), maturite_mois: parseInt(form.maturite_mois), objectif_rendement_pct: parseFloat(form.objectif_rendement_pct) };
      const res = await fetch(`${API}/paths`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      if (res.ok) onCreated();
    } catch (e) {}
    setSaving(false);
  }

  return (
    <div className="fixed inset-0 bg-black/70 z-50 flex items-start justify-center overflow-y-auto py-8 px-4">
      <div className="bg-[#0c0c0f] border border-[#1c1c22] rounded-2xl w-full max-w-lg">
        <div className="flex justify-between items-center px-6 py-4 border-b border-[#1c1c22]">
          <h3 className="font-bold">Nouveau parcours d'investissement</h3>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-white/5"><X size={16} /></button>
        </div>

        <div className="px-6 py-4 space-y-4">
          {step === 0 && (
            <>
              <Input label="Nom du parcours" value={form.nom} onChange={v => set("nom", v)} placeholder="Mon parcours crypto" />
              <div>
                <label className="text-[11px] text-[#71717a] font-medium mb-2 block">Profil de risque</label>
                <div className="grid grid-cols-2 gap-2">
                  {PROFILS.map(p => (
                    <button key={p.id} onClick={() => set("profil_risque", p.id)}
                      className={`p-3 rounded-xl border text-left text-xs transition ${form.profil_risque === p.id ? `border-${p.color}-500 bg-${p.color}-500/10` : "border-[#1c1c22] text-[#a1a1aa]"}`}>
                      <div className="font-medium text-white">{p.label}</div>
                      <div className="text-[10px] text-[#71717a] mt-0.5">{p.desc}</div>
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="text-[11px] text-[#71717a] font-medium mb-2 block">Réactivité</label>
                <div className="grid grid-cols-2 gap-2">
                  {REACTIVITES.map(r => (
                    <button key={r.id} onClick={() => set("reactivite", r.id)}
                      className={`p-2.5 rounded-xl border text-left text-xs transition ${form.reactivite === r.id ? "border-blue-500 bg-blue-500/10" : "border-[#1c1c22] text-[#a1a1aa]"}`}>
                      <div className="font-medium text-white">{r.label}</div>
                      <div className="text-[10px] text-[#71717a]">{r.desc}</div>
                    </button>
                  ))}
                </div>
              </div>
            </>
          )}

          {step === 1 && (
            <>
              <div className="grid grid-cols-2 gap-3">
                <Input label="Mise de départ (€)" value={form.mise_depart} onChange={v => set("mise_depart", v)} type="number" />
                <Input label="Horizon (mois)" value={form.maturite_mois} onChange={v => set("maturite_mois", v)} type="number" />
              </div>
              <Input label="Rendement annuel visé (%)" value={form.objectif_rendement_pct} onChange={v => set("objectif_rendement_pct", v)} type="number" step="0.5" />
              <div className="bg-[#18181b] rounded-lg p-3 text-xs">
                <span className="text-[#71717a]">Objectif de sortie calculé: </span>
                <span className="text-white font-bold">{fmt(form.objectif_sortie)}</span>
                <span className="text-[#52525b] ml-2">(+{fmt(form.objectif_sortie - form.mise_depart)})</span>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <Input label="Banque / Courtier" value={form.banque} onChange={v => set("banque", v)} />
                <div>
                  <label className="text-[11px] text-[#71717a] font-medium mb-1 block">Enveloppe</label>
                  <select value={form.enveloppe} onChange={e => set("enveloppe", e.target.value)}
                    className="w-full px-3 py-2 bg-[#18181b] border border-[#27272a] rounded-lg text-sm text-white focus:border-blue-500 focus:outline-none">
                    <option value="cto">CTO</option>
                    <option value="pea">PEA</option>
                    <option value="assurance_vie">Assurance-vie</option>
                    <option value="per">PER</option>
                  </select>
                </div>
              </div>
              <Input label="Date ouverture enveloppe" value={form.date_ouverture_enveloppe} onChange={v => set("date_ouverture_enveloppe", v)} type="date" />
            </>
          )}
        </div>

        <div className="flex justify-between px-6 py-4 border-t border-[#1c1c22]">
          <button onClick={() => step > 0 ? setStep(0) : onClose()} className="text-sm text-[#a1a1aa] hover:text-white">
            {step > 0 ? "Précédent" : "Annuler"}
          </button>
          {step === 0 ? (
            <button onClick={() => setStep(1)} disabled={!form.nom}
              className="px-5 py-2 rounded-lg bg-blue-600 text-sm font-medium hover:bg-blue-500 transition disabled:opacity-30">
              Suivant <ChevronRight size={14} className="inline ml-1" />
            </button>
          ) : (
            <button onClick={save} disabled={saving}
              className="px-5 py-2 rounded-lg bg-emerald-600 text-sm font-medium hover:bg-emerald-500 transition disabled:opacity-50">
              {saving ? <Loader2 size={14} className="animate-spin inline mr-1" /> : <Check size={14} className="inline mr-1" />}
              Créer le parcours
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function Input({ label, value, onChange, type = "text", placeholder = "", step }) {
  return (
    <div>
      <label className="text-[11px] text-[#71717a] font-medium mb-1 block">{label}</label>
      <input type={type} value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder} step={step}
        className="w-full px-3 py-2 bg-[#18181b] border border-[#27272a] rounded-lg text-sm text-white placeholder-[#3f3f46] focus:border-blue-500 focus:outline-none transition" />
    </div>
  );
}

function fmt(n) {
  if (n == null || isNaN(n)) return "—";
  return new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(n);
}
