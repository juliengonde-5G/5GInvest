import { useState, useEffect, useRef } from "react";
import { MapPin, Home, Building, Car, Trees, FileText, CreditCard, Hammer, ChevronRight, ChevronLeft, Check, Loader2, X } from "lucide-react";

const API = "/api";

const TYPES_BIEN = [
  { id: "residence_principale", label: "Résidence principale", icon: Home },
  { id: "residence_secondaire", label: "Résidence secondaire", icon: Home },
  { id: "locatif_nu", label: "Locatif nu", icon: Building },
  { id: "locatif_meuble", label: "Locatif meublé", icon: Building },
  { id: "lmnp", label: "LMNP", icon: Building },
  { id: "lmp", label: "LMP", icon: Building },
  { id: "parking", label: "Parking / Garage", icon: Car },
  { id: "terrain", label: "Terrain", icon: Trees },
  { id: "scpi", label: "SCPI / Pierre-papier", icon: FileText },
  { id: "immeuble_rapport", label: "Immeuble de rapport", icon: Building },
  { id: "local_commercial", label: "Local commercial", icon: Building },
];

const MODES_DETENTION = [
  { id: "pleine_propriete", label: "Pleine propriété" },
  { id: "sci_ir", label: "SCI à l'IR" },
  { id: "sci_is", label: "SCI à l'IS" },
  { id: "indivision", label: "Indivision" },
  { id: "usufruit", label: "Usufruit" },
  { id: "nue_propriete", label: "Nue-propriété" },
  { id: "demembrement", label: "Démembrement" },
];

const DPE_OPTIONS = ["A", "B", "C", "D", "E", "F", "G"];
const DPE_COLORS = { A: "#319834", B: "#33cc31", C: "#cbfc33", D: "#fcfc33", E: "#fccc33", F: "#fc9833", G: "#fc3333" };

const TYPES_PRET = [
  { id: "classique", label: "Prêt classique" },
  { id: "ptz", label: "PTZ (Prêt à Taux Zéro)" },
  { id: "pret_relais", label: "Prêt relais" },
  { id: "in_fine", label: "Prêt in fine" },
  { id: "taux_variable", label: "Taux variable" },
  { id: "pret_employeur", label: "Prêt employeur / Action Logement" },
];

const TYPES_TRAVAUX = [
  { id: "renovation_energetique", label: "Rénovation énergétique" },
  { id: "gros_oeuvre", label: "Gros œuvre" },
  { id: "second_oeuvre", label: "Second œuvre" },
  { id: "amenagement", label: "Aménagement" },
  { id: "mise_aux_normes", label: "Mise aux normes" },
  { id: "extension", label: "Extension" },
  { id: "decoration", label: "Décoration" },
];

const STEPS = [
  { id: "type", label: "Type", icon: Home },
  { id: "adresse", label: "Adresse", icon: MapPin },
  { id: "details", label: "Détails", icon: FileText },
  { id: "detention", label: "Détention", icon: FileText },
  { id: "acquisition", label: "Acquisition", icon: CreditCard },
  { id: "financement", label: "Financement", icon: CreditCard },
  { id: "travaux", label: "Travaux", icon: Hammer },
  { id: "resume", label: "Résumé", icon: Check },
];

export default function AddPropertyForm({ onClose, onCreated }) {
  const [step, setStep] = useState(0);
  const [saving, setSaving] = useState(false);
  const [estimation, setEstimation] = useState(null);
  const [geoResult, setGeoResult] = useState(null);

  const [form, setForm] = useState({
    nom: "", type_bien: "", usage: "habitation",
    adresse: "", complement_adresse: "", code_postal: "", ville: "",
    latitude: null, longitude: null,
    surface_habitable_m2: "", surface_carrez_m2: "", surface_terrain_m2: "",
    surface_annexes_m2: "", nb_pieces: "", nb_chambres: "", nb_sdb: "",
    etage: "", annee_construction: "", dpe: "", nb_parking: 0,
    mode_detention: "pleine_propriete", quote_part_pct: 100,
    date_acquisition: "", prix_achat_net: "", frais_notaire: "", frais_agence: "",
    valeur_estimee: "",
    taxe_fonciere_annuelle: "", charges_copro_mensuelles: "",
    assurance_pno_mensuelle: "", notes: "",
  });

  const [loans, setLoans] = useState([]);
  const [works, setWorks] = useState([]);

  function set(key, value) { setForm(f => ({ ...f, [key]: value })); }

  // ── Géocodage automatique ──
  async function geocode() {
    if (!form.adresse && !form.code_postal) return;
    try {
      const q = new URLSearchParams({ adresse: form.adresse, code_postal: form.code_postal, ville: form.ville });
      const res = await fetch(`${API}/geo/geocode?${q}`);
      const data = await res.json();
      if (!data.error) {
        setGeoResult(data);
        set("latitude", data.latitude);
        set("longitude", data.longitude);
        if (data.ville && !form.ville) set("ville", data.ville);
        if (data.code_postal && !form.code_postal) set("code_postal", data.code_postal);
      }
    } catch (e) {}
  }

  // ── Estimation DVF ──
  async function fetchEstimation() {
    const surface = parseFloat(form.surface_carrez_m2) || parseFloat(form.surface_habitable_m2);
    if (!surface || !form.code_postal) return;
    try {
      const q = new URLSearchParams({
        code_postal: form.code_postal,
        type_bien: form.type_bien || "appartement",
        surface_m2: String(surface),
        ...(form.latitude ? { lat: String(form.latitude), lon: String(form.longitude) } : {}),
      });
      const res = await fetch(`${API}/geo/dvf/estimate?${q}`);
      const data = await res.json();
      if (!data.error) {
        setEstimation(data);
        if (!form.valeur_estimee && data.estimation_valeur) {
          set("valeur_estimee", data.estimation_valeur);
        }
      }
    } catch (e) {}
  }

  // ── Sauvegarde ──
  async function save() {
    setSaving(true);
    try {
      const body = { ...form };
      // Convertir les champs numériques
      for (const k of ["surface_habitable_m2", "surface_carrez_m2", "surface_terrain_m2",
        "surface_annexes_m2", "nb_pieces", "nb_chambres", "nb_sdb", "etage",
        "annee_construction", "nb_parking", "quote_part_pct",
        "prix_achat_net", "frais_notaire", "frais_agence", "valeur_estimee",
        "taxe_fonciere_annuelle", "charges_copro_mensuelles", "assurance_pno_mensuelle"]) {
        if (body[k] !== "" && body[k] !== null) body[k] = parseFloat(body[k]) || 0;
        else body[k] = 0;
      }

      const res = await fetch(`${API}/real-estate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const prop = await res.json();

      // Ajouter les prêts
      for (const loan of loans) {
        await fetch(`${API}/real-estate/${prop.id}/loans`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(loan),
        });
      }

      // Ajouter les travaux
      for (const work of works) {
        await fetch(`${API}/real-estate/${prop.id}/works`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(work),
        });
      }

      onCreated?.(prop);
    } catch (e) {
      console.error(e);
    }
    setSaving(false);
  }

  const canNext = () => {
    if (step === 0) return !!form.type_bien;
    if (step === 1) return !!form.adresse || !!form.code_postal;
    return true;
  };

  return (
    <div className="fixed inset-0 bg-black/70 z-50 flex items-start justify-center overflow-y-auto py-8 px-4">
      <div className="bg-[#0c0c0f] border border-[#1c1c22] rounded-2xl w-full max-w-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#1c1c22]">
          <h2 className="text-lg font-bold">Ajouter un bien immobilier</h2>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-white/5"><X size={18} /></button>
        </div>

        {/* Stepper */}
        <div className="flex gap-1 px-6 py-3 overflow-x-auto">
          {STEPS.map((s, i) => (
            <button key={s.id} onClick={() => i <= step && setStep(i)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[10px] font-medium whitespace-nowrap transition
                ${i === step ? "bg-violet-500/20 text-violet-400" : i < step ? "bg-emerald-500/10 text-emerald-400" : "text-[#52525b]"}`}>
              {i < step ? <Check size={12} /> : <s.icon size={12} />}
              {s.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="px-6 py-4 min-h-[300px]">
          {/* STEP 0: Type */}
          {step === 0 && (
            <div>
              <p className="text-sm text-[#a1a1aa] mb-4">Quel type de bien souhaitez-vous ajouter ?</p>
              <div className="grid grid-cols-2 gap-2">
                {TYPES_BIEN.map(t => (
                  <button key={t.id} onClick={() => { set("type_bien", t.id); set("nom", t.label); }}
                    className={`flex items-center gap-3 p-3 rounded-xl border text-left text-sm transition
                      ${form.type_bien === t.id ? "border-violet-500 bg-violet-500/10 text-white" : "border-[#1c1c22] hover:border-[#27272a] text-[#a1a1aa]"}`}>
                    <t.icon size={18} />
                    {t.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* STEP 1: Adresse */}
          {step === 1 && (
            <div className="space-y-4">
              <p className="text-sm text-[#a1a1aa]">Renseignez l'adresse pour localiser le bien et obtenir une estimation automatique.</p>
              <Input label="Adresse" value={form.adresse} onChange={v => set("adresse", v)} placeholder="12 rue de la Paix" onBlur={geocode} />
              <Input label="Complément" value={form.complement_adresse} onChange={v => set("complement_adresse", v)} placeholder="Bât. A, 3ème étage" />
              <div className="grid grid-cols-2 gap-3">
                <Input label="Code postal" value={form.code_postal} onChange={v => set("code_postal", v)} placeholder="75001" onBlur={geocode} />
                <Input label="Ville" value={form.ville} onChange={v => set("ville", v)} placeholder="Paris" />
              </div>
              {geoResult && !geoResult.error && (
                <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-3 text-xs text-emerald-400">
                  <MapPin size={14} className="inline mr-1" />
                  Localisé: {geoResult.label} (score: {(geoResult.score * 100).toFixed(0)}%)
                </div>
              )}
              {/* Carte Leaflet placeholder - sera rendue si lat/lon disponibles */}
              {form.latitude && (
                <div className="rounded-lg overflow-hidden border border-[#1c1c22] h-[200px] bg-[#18181b] flex items-center justify-center">
                  <img
                    src={`https://staticmap.openstreetmap.de/staticmap.php?center=${form.latitude},${form.longitude}&zoom=15&size=600x200&markers=${form.latitude},${form.longitude},red-pushpin`}
                    alt="Carte"
                    className="w-full h-full object-cover"
                    onError={(e) => { e.target.style.display = 'none'; }}
                  />
                </div>
              )}
            </div>
          )}

          {/* STEP 2: Détails du bien */}
          {step === 2 && (
            <div className="space-y-4">
              <p className="text-sm text-[#a1a1aa]">Caractéristiques du bien</p>
              <Input label="Nom du bien" value={form.nom} onChange={v => set("nom", v)} placeholder="Appartement Paris 1er" />
              <div className="grid grid-cols-2 gap-3">
                <Input label="Surface habitable (m²)" value={form.surface_habitable_m2} onChange={v => set("surface_habitable_m2", v)} type="number" />
                <Input label="Surface Carrez (m²)" value={form.surface_carrez_m2} onChange={v => set("surface_carrez_m2", v)} type="number" />
              </div>
              <div className="grid grid-cols-3 gap-3">
                <Input label="Pièces" value={form.nb_pieces} onChange={v => set("nb_pieces", v)} type="number" />
                <Input label="Chambres" value={form.nb_chambres} onChange={v => set("nb_chambres", v)} type="number" />
                <Input label="SdB" value={form.nb_sdb} onChange={v => set("nb_sdb", v)} type="number" />
              </div>
              <div className="grid grid-cols-3 gap-3">
                <Input label="Étage" value={form.etage} onChange={v => set("etage", v)} type="number" />
                <Input label="Année construction" value={form.annee_construction} onChange={v => set("annee_construction", v)} type="number" placeholder="1990" />
                <Input label="Parkings" value={form.nb_parking} onChange={v => set("nb_parking", v)} type="number" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <Input label="Surface terrain (m²)" value={form.surface_terrain_m2} onChange={v => set("surface_terrain_m2", v)} type="number" />
                <Input label="Surface annexes (m²)" value={form.surface_annexes_m2} onChange={v => set("surface_annexes_m2", v)} type="number" />
              </div>
              {/* DPE */}
              <div>
                <label className="text-[11px] text-[#71717a] font-medium mb-2 block">DPE</label>
                <div className="flex gap-1.5">
                  {DPE_OPTIONS.map(d => (
                    <button key={d} onClick={() => set("dpe", d)}
                      className={`w-9 h-9 rounded-lg font-bold text-sm transition ${form.dpe === d ? "ring-2 ring-white" : "opacity-60 hover:opacity-100"}`}
                      style={{ background: DPE_COLORS[d], color: d <= "C" ? "#000" : "#fff" }}>
                      {d}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* STEP 3: Détention */}
          {step === 3 && (
            <div className="space-y-4">
              <p className="text-sm text-[#a1a1aa]">Comment détenez-vous ce bien ? Cela impacte la fiscalité de la plus-value.</p>
              <div className="grid grid-cols-2 gap-2">
                {MODES_DETENTION.map(m => (
                  <button key={m.id} onClick={() => set("mode_detention", m.id)}
                    className={`p-3 rounded-xl border text-left text-sm transition
                      ${form.mode_detention === m.id ? "border-violet-500 bg-violet-500/10 text-white" : "border-[#1c1c22] text-[#a1a1aa] hover:border-[#27272a]"}`}>
                    {m.label}
                  </button>
                ))}
              </div>
              {(form.mode_detention === "indivision" || form.mode_detention.startsWith("sci")) && (
                <Input label="Quote-part de détention (%)" value={form.quote_part_pct} onChange={v => set("quote_part_pct", v)} type="number" />
              )}
              <Input label="Date d'acquisition" value={form.date_acquisition} onChange={v => set("date_acquisition", v)} type="date" />
              <div className="grid grid-cols-2 gap-3">
                <Input label="Taxe foncière annuelle (€)" value={form.taxe_fonciere_annuelle} onChange={v => set("taxe_fonciere_annuelle", v)} type="number" />
                <Input label="Charges copro / mois (€)" value={form.charges_copro_mensuelles} onChange={v => set("charges_copro_mensuelles", v)} type="number" />
              </div>
              <Input label="Assurance PNO / mois (€)" value={form.assurance_pno_mensuelle} onChange={v => set("assurance_pno_mensuelle", v)} type="number" />
            </div>
          )}

          {/* STEP 4: Acquisition */}
          {step === 4 && (
            <div className="space-y-4">
              <p className="text-sm text-[#a1a1aa]">Prix d'achat et frais. Ces données servent au calcul de la plus-value à la revente.</p>
              <Input label="Prix d'achat net vendeur (€)" value={form.prix_achat_net} onChange={v => set("prix_achat_net", v)} type="number" />
              <div className="grid grid-cols-2 gap-3">
                <Input label="Frais de notaire (€)" value={form.frais_notaire} onChange={v => set("frais_notaire", v)} type="number" />
                <Input label="Frais d'agence (€)" value={form.frais_agence} onChange={v => set("frais_agence", v)} type="number" />
              </div>
              <div className="bg-[#18181b] rounded-lg p-3 text-xs">
                <span className="text-[#71717a]">Coût total d'acquisition: </span>
                <span className="text-white font-bold">{fmt((parseFloat(form.prix_achat_net) || 0) + (parseFloat(form.frais_notaire) || 0) + (parseFloat(form.frais_agence) || 0))}</span>
              </div>

              {/* Estimation DVF */}
              <div className="border-t border-[#1c1c22] pt-4">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-[11px] text-[#71717a] font-medium">Estimation actuelle (DVF)</span>
                  <button onClick={fetchEstimation} className="text-[10px] text-violet-400 hover:underline">Estimer</button>
                </div>
                {estimation ? (
                  <div className="bg-violet-500/10 border border-violet-500/30 rounded-lg p-3 text-xs space-y-1">
                    <div className="flex justify-between"><span className="text-[#a1a1aa]">Prix/m² médian:</span><span className="font-bold">{estimation.prix_m2_median?.toLocaleString("fr-FR")} €</span></div>
                    <div className="flex justify-between"><span className="text-[#a1a1aa]">Estimation:</span><span className="font-bold text-violet-400">{estimation.estimation_valeur?.toLocaleString("fr-FR")} €</span></div>
                    <div className="flex justify-between"><span className="text-[#a1a1aa]">Fourchette:</span><span>{estimation.fourchette_basse?.toLocaleString("fr-FR")} - {estimation.fourchette_haute?.toLocaleString("fr-FR")} €</span></div>
                    <div className="text-[10px] text-[#52525b]">Basé sur {estimation.nb_transactions} transactions</div>
                  </div>
                ) : (
                  <div className="text-[10px] text-[#52525b]">Cliquez "Estimer" après avoir renseigné l'adresse et la surface.</div>
                )}
                <Input label="Valeur estimée (€)" value={form.valeur_estimee} onChange={v => set("valeur_estimee", v)} type="number" className="mt-3" />
              </div>
            </div>
          )}

          {/* STEP 5: Financement */}
          {step === 5 && (
            <div className="space-y-4">
              <p className="text-sm text-[#a1a1aa]">Ajoutez un ou plusieurs prêts (PTZ + classique, prêt relais, etc.)</p>
              {loans.map((loan, i) => (
                <div key={i} className="bg-[#18181b] rounded-xl p-4 border border-[#1c1c22] space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">{loan.nom || `Prêt ${i + 1}`}</span>
                    <button onClick={() => setLoans(l => l.filter((_, j) => j !== i))} className="text-red-400 text-[10px] hover:underline">Supprimer</button>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <LoanField label="Nom" value={loan.nom} onChange={v => updateLoan(i, "nom", v)} />
                    <Select label="Type" value={loan.type_pret} onChange={v => updateLoan(i, "type_pret", v)} options={TYPES_PRET} />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <LoanField label="Banque" value={loan.banque} onChange={v => updateLoan(i, "banque", v)} />
                    <LoanField label="Montant emprunté (€)" value={loan.montant_emprunte} onChange={v => updateLoan(i, "montant_emprunte", v)} type="number" />
                  </div>
                  <div className="grid grid-cols-3 gap-2">
                    <LoanField label="Taux (%)" value={loan.taux_nominal} onChange={v => updateLoan(i, "taux_nominal", v)} type="number" step="0.01" />
                    <LoanField label="Taux assurance (%)" value={loan.taux_assurance} onChange={v => updateLoan(i, "taux_assurance", v)} type="number" step="0.01" />
                    <LoanField label="Durée (mois)" value={loan.duree_mois} onChange={v => updateLoan(i, "duree_mois", v)} type="number" />
                  </div>
                  <div className="grid grid-cols-3 gap-2">
                    <LoanField label="Mensualité HI (€)" value={loan.mensualite_hors_assurance} onChange={v => updateLoan(i, "mensualite_hors_assurance", v)} type="number" />
                    <LoanField label="Assurance/mois (€)" value={loan.mensualite_assurance} onChange={v => updateLoan(i, "mensualite_assurance", v)} type="number" />
                    <LoanField label="Capital restant (€)" value={loan.capital_restant_du} onChange={v => updateLoan(i, "capital_restant_du", v)} type="number" />
                  </div>
                  <LoanField label="Date début" value={loan.date_debut} onChange={v => updateLoan(i, "date_debut", v)} type="date" />
                </div>
              ))}
              <button onClick={() => setLoans(l => [...l, { nom: `Prêt ${l.length + 1}`, type_pret: "classique", banque: "", montant_emprunte: 0, taux_nominal: 0, taux_assurance: 0, duree_mois: 240, date_debut: "", mensualite_hors_assurance: 0, mensualite_assurance: 0, capital_restant_du: 0, en_cours: true }])}
                className="w-full py-2.5 rounded-xl border border-dashed border-[#27272a] text-sm text-[#71717a] hover:text-white hover:border-violet-500 transition">
                + Ajouter un prêt
              </button>
            </div>
          )}

          {/* STEP 6: Travaux */}
          {step === 6 && (
            <div className="space-y-4">
              <p className="text-sm text-[#a1a1aa]">Travaux réalisés. Les travaux déductibles impactent le calcul de la plus-value.</p>
              {works.map((work, i) => (
                <div key={i} className="bg-[#18181b] rounded-xl p-4 border border-[#1c1c22] space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">{work.description || `Travaux ${i + 1}`}</span>
                    <button onClick={() => setWorks(w => w.filter((_, j) => j !== i))} className="text-red-400 text-[10px] hover:underline">Supprimer</button>
                  </div>
                  <LoanField label="Description" value={work.description} onChange={v => updateWork(i, "description", v)} />
                  <div className="grid grid-cols-2 gap-2">
                    <Select label="Type" value={work.type_travaux} onChange={v => updateWork(i, "type_travaux", v)} options={TYPES_TRAVAUX} />
                    <LoanField label="Montant (€)" value={work.montant} onChange={v => updateWork(i, "montant", v)} type="number" />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <LoanField label="Date" value={work.date_travaux} onChange={v => updateWork(i, "date_travaux", v)} type="date" />
                    <div className="flex items-center gap-2 pt-5">
                      <input type="checkbox" checked={work.deductible_fiscalement} onChange={e => updateWork(i, "deductible_fiscalement", e.target.checked)}
                        className="w-4 h-4 accent-violet-500" />
                      <span className="text-xs text-[#a1a1aa]">Déductible fiscalement</span>
                    </div>
                  </div>
                </div>
              ))}
              <button onClick={() => setWorks(w => [...w, { description: "", type_travaux: "amenagement", montant: 0, date_travaux: "", deductible_fiscalement: false }])}
                className="w-full py-2.5 rounded-xl border border-dashed border-[#27272a] text-sm text-[#71717a] hover:text-white hover:border-violet-500 transition">
                + Ajouter des travaux
              </button>
            </div>
          )}

          {/* STEP 7: Résumé */}
          {step === 7 && (
            <div className="space-y-3 text-sm">
              <h3 className="font-bold text-base">{form.nom}</h3>
              <div className="grid grid-cols-2 gap-3">
                <SummaryItem label="Type" value={TYPES_BIEN.find(t => t.id === form.type_bien)?.label} />
                <SummaryItem label="Adresse" value={`${form.adresse}, ${form.code_postal} ${form.ville}`} />
                <SummaryItem label="Surface" value={`${form.surface_habitable_m2 || form.surface_carrez_m2} m²`} />
                <SummaryItem label="Pièces" value={form.nb_pieces} />
                <SummaryItem label="DPE" value={form.dpe} />
                <SummaryItem label="Détention" value={MODES_DETENTION.find(m => m.id === form.mode_detention)?.label} />
                <SummaryItem label="Quote-part" value={`${form.quote_part_pct}%`} />
                <SummaryItem label="Date acquisition" value={form.date_acquisition} />
                <SummaryItem label="Prix achat total" value={fmt((parseFloat(form.prix_achat_net) || 0) + (parseFloat(form.frais_notaire) || 0) + (parseFloat(form.frais_agence) || 0))} />
                <SummaryItem label="Valeur estimée" value={fmt(parseFloat(form.valeur_estimee) || 0)} accent />
                <SummaryItem label="Prêts" value={`${loans.length} prêt(s)`} />
                <SummaryItem label="Travaux" value={`${works.length} poste(s) - ${fmt(works.reduce((s, w) => s + (parseFloat(w.montant) || 0), 0))}`} />
              </div>
              {estimation && (
                <div className="bg-violet-500/10 border border-violet-500/30 rounded-lg p-3 text-xs">
                  DVF: {estimation.prix_m2_median?.toLocaleString("fr-FR")} €/m² · {estimation.nb_transactions} transactions
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-[#1c1c22]">
          <button onClick={() => step > 0 ? setStep(step - 1) : onClose()}
            className="flex items-center gap-1 px-4 py-2 rounded-lg text-sm text-[#a1a1aa] hover:text-white transition">
            <ChevronLeft size={16} /> {step > 0 ? "Précédent" : "Annuler"}
          </button>
          {step < STEPS.length - 1 ? (
            <button onClick={() => { setStep(step + 1); if (step === 1) fetchEstimation(); }}
              disabled={!canNext()}
              className="flex items-center gap-1 px-5 py-2 rounded-lg bg-violet-600 text-sm font-medium hover:bg-violet-500 transition disabled:opacity-30">
              Suivant <ChevronRight size={16} />
            </button>
          ) : (
            <button onClick={save} disabled={saving}
              className="flex items-center gap-1 px-5 py-2 rounded-lg bg-emerald-600 text-sm font-medium hover:bg-emerald-500 transition disabled:opacity-50">
              {saving ? <Loader2 size={16} className="animate-spin" /> : <Check size={16} />}
              Enregistrer
            </button>
          )}
        </div>
      </div>
    </div>
  );

  function updateLoan(i, key, value) {
    setLoans(l => l.map((loan, j) => j === i ? { ...loan, [key]: value } : loan));
  }
  function updateWork(i, key, value) {
    setWorks(w => w.map((work, j) => j === i ? { ...work, [key]: value } : work));
  }
}

// ── Sub-components ──

function Input({ label, value, onChange, type = "text", placeholder = "", onBlur, className = "", step }) {
  return (
    <div className={className}>
      <label className="text-[11px] text-[#71717a] font-medium mb-1 block">{label}</label>
      <input type={type} value={value} onChange={e => onChange(e.target.value)} onBlur={onBlur}
        placeholder={placeholder} step={step}
        className="w-full px-3 py-2 bg-[#18181b] border border-[#27272a] rounded-lg text-sm text-white placeholder-[#3f3f46] focus:border-violet-500 focus:outline-none transition" />
    </div>
  );
}

function LoanField({ label, value, onChange, type = "text", step }) {
  return (
    <div>
      <label className="text-[10px] text-[#52525b] mb-0.5 block">{label}</label>
      <input type={type} value={value} onChange={e => onChange(e.target.value)} step={step}
        className="w-full px-2 py-1.5 bg-[#0c0c0f] border border-[#1c1c22] rounded-md text-xs text-white focus:border-violet-500 focus:outline-none" />
    </div>
  );
}

function Select({ label, value, onChange, options }) {
  return (
    <div>
      <label className="text-[10px] text-[#52525b] mb-0.5 block">{label}</label>
      <select value={value} onChange={e => onChange(e.target.value)}
        className="w-full px-2 py-1.5 bg-[#0c0c0f] border border-[#1c1c22] rounded-md text-xs text-white focus:border-violet-500 focus:outline-none">
        {options.map(o => <option key={o.id} value={o.id}>{o.label}</option>)}
      </select>
    </div>
  );
}

function SummaryItem({ label, value, accent }) {
  return (
    <div>
      <div className="text-[10px] text-[#52525b]">{label}</div>
      <div className={`text-sm font-medium ${accent ? "text-violet-400" : "text-white"}`}>{value || "—"}</div>
    </div>
  );
}

function fmt(n) {
  if (n == null || isNaN(n)) return "—";
  return new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(n);
}
