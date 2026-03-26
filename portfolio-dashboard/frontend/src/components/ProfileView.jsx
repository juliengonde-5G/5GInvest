import { useState, useEffect } from "react";
import { User, Shield, Target, Banknote, Building, Check, ChevronRight, ChevronLeft, Loader2, X } from "lucide-react";

const API = "/api";

const OBJECTIFS = [
  { id: "constitution", label: "Constituer un patrimoine", desc: "Partir de zéro, accumuler" },
  { id: "retraite", label: "Préparer la retraite", desc: "Objectif âge et montant" },
  { id: "revenus_complementaires", label: "Revenus complémentaires", desc: "Cashflow immobilier, dividendes" },
  { id: "transmission", label: "Transmission", desc: "Préparer la succession" },
  { id: "liberte_financiere", label: "Liberté financière", desc: "Ne plus dépendre d'un salaire" },
  { id: "projet", label: "Projet spécifique", desc: "Achat immobilier, voyage, études" },
];

const BANQUES_LIST = [
  "Revolut", "Boursorama", "Fortuneo", "Trade Republic", "DEGIRO",
  "Bourse Direct", "Société Générale", "BNP Paribas", "Crédit Agricole",
  "LCL", "La Banque Postale", "CIC", "Crédit Mutuel", "Caisse d'Épargne",
  "Banque Populaire", "HSBC", "ING", "N26", "Hello Bank", "Linxo",
];

export default function ProfileView() {
  const [profile, setProfile] = useState(null);
  const [editing, setEditing] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadProfile(); }, []);

  async function loadProfile() {
    setLoading(true);
    try {
      const res = await fetch(`${API}/profile`);
      const data = await res.json();
      if (data.exists) setProfile(data.profile);
      else setEditing(true);
    } catch (e) {}
    setLoading(false);
  }

  if (loading) return <div className="flex justify-center py-20"><Loader2 size={28} className="animate-spin text-[#52525b]" /></div>;

  if (editing || !profile) return <OnboardingForm initial={profile} onSaved={(p) => { setProfile(p); setEditing(false); }} />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">Mon profil patrimonial</h2>
        <button onClick={() => setEditing(true)} className="text-sm text-blue-400 hover:underline">Modifier</button>
      </div>

      <div className="card p-5">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-violet-500 to-blue-500 flex items-center justify-center text-lg font-bold">
            {profile.prenom?.[0] || "?"}
          </div>
          <div>
            <div className="font-bold text-lg">{profile.prenom}</div>
            <div className="text-xs text-[#71717a]">{profile.age} ans · {profile.situation_familiale} · {profile.nb_enfants || 0} enfant(s)</div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 text-sm">
          <Info label="Revenu net annuel" value={fmt(profile.revenu_net_annuel)} />
          <Info label="Charges mensuelles" value={fmt(profile.charges_fixes_mensuelles)} />
          <Info label="Capacité d'épargne" value={`${fmt(profile.capacite_epargne_mensuelle)} /mois`} />
          <Info label="Taux d'effort" value={`${profile.taux_effort_pct}%`} />
          <Info label="Objectif" value={OBJECTIFS.find(o => o.id === profile.objectif_principal)?.label || profile.objectif_principal} />
          <Info label="Profil risque" value={profile.profil_risque} />
          <Info label="Horizon" value={profile.horizon_global} />
          <Info label="Banques" value={(profile.banques || []).join(", ")} />
        </div>

        <div className="flex gap-2 mt-4 flex-wrap">
          {profile.has_pea && <Badge label="PEA" color="violet" />}
          {profile.has_assurance_vie && <Badge label="AV" color="blue" />}
          {profile.has_per && <Badge label="PER" color="cyan" />}
          {profile.has_cto && <Badge label="CTO" color="emerald" />}
        </div>
      </div>
    </div>
  );
}


function OnboardingForm({ initial, onSaved }) {
  const [step, setStep] = useState(0);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    prenom: "", age: 35, situation_familiale: "celibataire", nb_enfants: 0,
    nb_parts_fiscales: 1, revenu_net_annuel: 30000, charges_fixes_mensuelles: 1500,
    capacite_epargne_mensuelle: 300, epargne_precaution_mois: 3,
    tmi: 0.11, option_fiscale: "pfu",
    objectif_principal: "constitution", age_objectif: 60, montant_objectif: 500000,
    profil_risque: "equilibre", experience_investissement: "debutant", horizon_global: "moyen",
    banques: ["Revolut"], has_pea: false, has_assurance_vie: false, has_per: false, has_cto: true,
    rgpd_consent: false,
    ...initial,
  });

  function set(k, v) { setForm(f => ({ ...f, [k]: v })); }

  const STEPS = [
    { label: "Identité", icon: User },
    { label: "Revenus", icon: Banknote },
    { label: "Objectifs", icon: Target },
    { label: "Risque", icon: Shield },
    { label: "Banques", icon: Building },
  ];

  async function save() {
    if (!form.rgpd_consent) return;
    setSaving(true);
    try {
      const body = { ...form };
      for (const k of ["age", "nb_enfants", "revenu_net_annuel", "charges_fixes_mensuelles",
        "capacite_epargne_mensuelle", "age_objectif", "montant_objectif", "epargne_precaution_mois"]) {
        body[k] = parseFloat(body[k]) || 0;
      }
      body.nb_parts_fiscales = parseFloat(body.nb_parts_fiscales) || 1;
      body.tmi = parseFloat(body.tmi) || 0.11;

      const res = await fetch(`${API}/profile`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      const data = await res.json();
      if (data.status === "ok") onSaved(data.profile);
    } catch (e) {}
    setSaving(false);
  }

  return (
    <div className="max-w-lg mx-auto space-y-6">
      <h2 className="text-xl font-bold text-center">Configurez votre profil patrimonial</h2>

      {/* Stepper */}
      <div className="flex gap-1 justify-center">
        {STEPS.map((s, i) => (
          <button key={i} onClick={() => i <= step && setStep(i)}
            className={`flex items-center gap-1 px-3 py-1.5 rounded-full text-[10px] font-medium transition
              ${i === step ? "bg-violet-500/20 text-violet-400" : i < step ? "bg-emerald-500/10 text-emerald-400" : "text-[#52525b]"}`}>
            {i < step ? <Check size={12} /> : <s.icon size={12} />} {s.label}
          </button>
        ))}
      </div>

      <div className="card p-5">
        {/* Step 0: Identité */}
        {step === 0 && (
          <div className="space-y-4">
            <Input label="Prénom" value={form.prenom} onChange={v => set("prenom", v)} />
            <Input label="Âge" value={form.age} onChange={v => set("age", v)} type="number" />
            <div>
              <label className="text-[11px] text-[#71717a] font-medium mb-2 block">Situation familiale</label>
              <div className="grid grid-cols-2 gap-2">
                {["celibataire", "marie", "pacse", "divorce", "veuf"].map(s => (
                  <button key={s} onClick={() => set("situation_familiale", s)}
                    className={`p-2 rounded-lg border text-xs capitalize transition ${form.situation_familiale === s ? "border-violet-500 bg-violet-500/10 text-white" : "border-[#1c1c22] text-[#a1a1aa]"}`}>
                    {s.replace("_", " ")}
                  </button>
                ))}
              </div>
            </div>
            <Input label="Nombre d'enfants" value={form.nb_enfants} onChange={v => set("nb_enfants", v)} type="number" />
            <Input label="Parts fiscales" value={form.nb_parts_fiscales} onChange={v => set("nb_parts_fiscales", v)} type="number" step="0.5" />
          </div>
        )}

        {/* Step 1: Revenus */}
        {step === 1 && (
          <div className="space-y-4">
            <Input label="Revenu net annuel (€)" value={form.revenu_net_annuel} onChange={v => set("revenu_net_annuel", v)} type="number" />
            <Input label="Charges fixes mensuelles (€)" value={form.charges_fixes_mensuelles} onChange={v => set("charges_fixes_mensuelles", v)} type="number" />
            <Input label="Capacité d'épargne mensuelle (€)" value={form.capacite_epargne_mensuelle} onChange={v => set("capacite_epargne_mensuelle", v)} type="number" />
            <Input label="Épargne de précaution (mois de réserve)" value={form.epargne_precaution_mois} onChange={v => set("epargne_precaution_mois", v)} type="number" />
            <div>
              <label className="text-[11px] text-[#71717a] font-medium mb-1 block">Fiscalité</label>
              <div className="grid grid-cols-2 gap-2">
                <button onClick={() => set("option_fiscale", "pfu")}
                  className={`p-2 rounded-lg border text-xs transition ${form.option_fiscale === "pfu" ? "border-violet-500 bg-violet-500/10" : "border-[#1c1c22] text-[#a1a1aa]"}`}>
                  PFU (Flat Tax 30%)
                </button>
                <button onClick={() => set("option_fiscale", "bareme")}
                  className={`p-2 rounded-lg border text-xs transition ${form.option_fiscale === "bareme" ? "border-violet-500 bg-violet-500/10" : "border-[#1c1c22] text-[#a1a1aa]"}`}>
                  Barème progressif
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Step 2: Objectifs */}
        {step === 2 && (
          <div className="space-y-4">
            <div>
              <label className="text-[11px] text-[#71717a] font-medium mb-2 block">Objectif principal</label>
              <div className="grid grid-cols-2 gap-2">
                {OBJECTIFS.map(o => (
                  <button key={o.id} onClick={() => set("objectif_principal", o.id)}
                    className={`p-3 rounded-xl border text-left text-xs transition ${form.objectif_principal === o.id ? "border-violet-500 bg-violet-500/10 text-white" : "border-[#1c1c22] text-[#a1a1aa]"}`}>
                    <div className="font-medium">{o.label}</div>
                    <div className="text-[10px] text-[#52525b] mt-0.5">{o.desc}</div>
                  </button>
                ))}
              </div>
            </div>
            {(form.objectif_principal === "retraite" || form.objectif_principal === "liberte_financiere") && (
              <Input label="Âge cible" value={form.age_objectif} onChange={v => set("age_objectif", v)} type="number" />
            )}
            <Input label="Montant objectif (€)" value={form.montant_objectif} onChange={v => set("montant_objectif", v)} type="number" />
          </div>
        )}

        {/* Step 3: Risque */}
        {step === 3 && (
          <div className="space-y-4">
            <div>
              <label className="text-[11px] text-[#71717a] font-medium mb-2 block">Profil de risque</label>
              <div className="space-y-2">
                {[
                  { id: "prudent", label: "Prudent", desc: "Capital garanti, 2-4%/an", color: "emerald" },
                  { id: "equilibre", label: "Équilibré", desc: "Mix sécurité/rendement, 4-7%/an", color: "blue" },
                  { id: "dynamique", label: "Dynamique", desc: "Volatilité acceptée, 7-12%/an", color: "amber" },
                  { id: "agressif", label: "Agressif", desc: "Rendement max, >12%/an", color: "red" },
                ].map(p => (
                  <button key={p.id} onClick={() => set("profil_risque", p.id)}
                    className={`w-full p-3 rounded-xl border text-left text-sm transition ${form.profil_risque === p.id ? `border-${p.color}-500 bg-${p.color}-500/10 text-white` : "border-[#1c1c22] text-[#a1a1aa]"}`}>
                    <span className="font-medium">{p.label}</span>
                    <span className="text-[10px] text-[#52525b] ml-2">{p.desc}</span>
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="text-[11px] text-[#71717a] font-medium mb-2 block">Expérience</label>
              <div className="grid grid-cols-3 gap-2">
                {["debutant", "intermediaire", "avance"].map(e => (
                  <button key={e} onClick={() => set("experience_investissement", e)}
                    className={`p-2 rounded-lg border text-xs capitalize transition ${form.experience_investissement === e ? "border-violet-500 bg-violet-500/10" : "border-[#1c1c22] text-[#a1a1aa]"}`}>
                    {e.replace("_", " ")}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="text-[11px] text-[#71717a] font-medium mb-2 block">Horizon global</label>
              <div className="grid grid-cols-3 gap-2">
                {[{id:"court", label:"Court (<1 an)"}, {id:"moyen", label:"Moyen (1-5 ans)"}, {id:"long", label:"Long (>5 ans)"}].map(h => (
                  <button key={h.id} onClick={() => set("horizon_global", h.id)}
                    className={`p-2 rounded-lg border text-xs transition ${form.horizon_global === h.id ? "border-violet-500 bg-violet-500/10" : "border-[#1c1c22] text-[#a1a1aa]"}`}>
                    {h.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Step 4: Banques + RGPD */}
        {step === 4 && (
          <div className="space-y-4">
            <div>
              <label className="text-[11px] text-[#71717a] font-medium mb-2 block">Vos banques (cliquez pour sélectionner)</label>
              <div className="flex flex-wrap gap-1.5">
                {BANQUES_LIST.map(b => (
                  <button key={b} onClick={() => {
                    const list = form.banques || [];
                    set("banques", list.includes(b) ? list.filter(x => x !== b) : [...list, b]);
                  }}
                    className={`px-2.5 py-1.5 rounded-lg text-[11px] border transition ${(form.banques || []).includes(b) ? "border-violet-500 bg-violet-500/10 text-white" : "border-[#1c1c22] text-[#52525b] hover:text-white"}`}>
                    {b}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex flex-wrap gap-3">
              <label className="flex items-center gap-2 text-xs"><input type="checkbox" checked={form.has_pea} onChange={e => set("has_pea", e.target.checked)} className="accent-violet-500" /> PEA</label>
              <label className="flex items-center gap-2 text-xs"><input type="checkbox" checked={form.has_assurance_vie} onChange={e => set("has_assurance_vie", e.target.checked)} className="accent-violet-500" /> Assurance-vie</label>
              <label className="flex items-center gap-2 text-xs"><input type="checkbox" checked={form.has_per} onChange={e => set("has_per", e.target.checked)} className="accent-violet-500" /> PER</label>
              <label className="flex items-center gap-2 text-xs"><input type="checkbox" checked={form.has_cto} onChange={e => set("has_cto", e.target.checked)} className="accent-violet-500" /> CTO</label>
            </div>
            <div className="bg-[#18181b] rounded-lg p-3">
              <label className="flex items-start gap-2 text-xs text-[#a1a1aa] cursor-pointer">
                <input type="checkbox" checked={form.rgpd_consent} onChange={e => set("rgpd_consent", e.target.checked)} className="accent-violet-500 mt-0.5" />
                <span>J'accepte le traitement de mes données personnelles conformément à la politique de confidentialité (RGPD). Mes données sont stockées localement sur mon serveur.</span>
              </label>
            </div>
          </div>
        )}
      </div>

      {/* Navigation */}
      <div className="flex justify-between">
        <button onClick={() => step > 0 ? setStep(step - 1) : null}
          className={`flex items-center gap-1 text-sm ${step > 0 ? "text-[#a1a1aa] hover:text-white" : "invisible"}`}>
          <ChevronLeft size={14} /> Précédent
        </button>
        {step < STEPS.length - 1 ? (
          <button onClick={() => setStep(step + 1)}
            className="flex items-center gap-1 px-5 py-2 rounded-xl bg-violet-600 text-sm font-medium hover:bg-violet-500 transition">
            Suivant <ChevronRight size={14} />
          </button>
        ) : (
          <button onClick={save} disabled={!form.rgpd_consent || saving}
            className="flex items-center gap-1 px-5 py-2 rounded-xl bg-emerald-600 text-sm font-medium hover:bg-emerald-500 transition disabled:opacity-30">
            {saving ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />} Enregistrer
          </button>
        )}
      </div>
    </div>
  );
}

function Info({ label, value }) {
  return (
    <div>
      <div className="text-[10px] text-[#52525b]">{label}</div>
      <div className="text-sm font-medium">{value || "—"}</div>
    </div>
  );
}

function Badge({ label, color }) {
  return <span className={`text-[10px] px-2 py-0.5 rounded-full bg-${color}-500/10 text-${color}-400 font-medium`}>{label}</span>;
}

function Input({ label, value, onChange, type = "text", placeholder = "", step }) {
  return (
    <div>
      <label className="text-[11px] text-[#71717a] font-medium mb-1 block">{label}</label>
      <input type={type} value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder} step={step}
        className="w-full px-3 py-2 bg-[#18181b] border border-[#27272a] rounded-lg text-sm text-white placeholder-[#3f3f46] focus:border-violet-500 focus:outline-none transition" />
    </div>
  );
}

function fmt(n) {
  if (n == null || isNaN(n)) return "—";
  return new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(n);
}
