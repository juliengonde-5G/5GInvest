import { useState } from "react";
import { Gem, ArrowUpRight, ArrowDownRight, Plus, X, Loader2, Check, Trash2 } from "lucide-react";

const API = "/api";

const COMMODITIES = [
  { symbol: "GOLD", nom: "Or (once)", type_produit: "physique" },
  { symbol: "SILVER", nom: "Argent (once)", type_produit: "physique" },
  { symbol: "OIL", nom: "Pétrole WTI (baril)", type_produit: "etf" },
];

const TYPES = ["physique", "etf", "cfd", "certificat"];
const PLATEFORMES = ["Revolut", "Trade Republic", "DEGIRO", "Boursorama", "Or.fr", "Autre"];

export default function CommoditiesView({ items, onRefresh }) {
  const [showAdd, setShowAdd] = useState(false);
  const total = items?.reduce((s, p) => s + (p.current_value || 0), 0) || 0;

  async function deletePosition(id) {
    if (!confirm("Supprimer cette position ?")) return;
    await fetch(`${API}/commodities/${id}`, { method: "DELETE" });
    onRefresh();
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">Matières premières</h2>
        <button onClick={() => setShowAdd(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-cyan-600 text-sm font-medium hover:bg-cyan-500 transition">
          <Plus size={16} /> Ajouter
        </button>
      </div>

      {items?.length > 0 && (
        <div className="card p-4 flex items-center justify-between">
          <div>
            <div className="text-[10px]" style={{ color: "var(--text-muted)" }}>Valeur totale</div>
            <div className="text-xl font-bold">{fmt(total)}</div>
          </div>
          <div className="w-10 h-10 rounded-xl bg-cyan-500/10 flex items-center justify-center">
            <Gem size={20} className="text-cyan-400" />
          </div>
        </div>
      )}

      {items?.length > 0 ? (
        <div className="card divide-y" style={{ borderColor: "var(--border)" }}>
          {items.map((p, i) => (
            <div key={i} className="flex items-center justify-between px-5 py-4" style={{ borderColor: "var(--border)" }}>
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-cyan-500/10 flex items-center justify-center text-cyan-400 text-xs font-bold">
                  {p.symbol?.slice(0, 3)}
                </div>
                <div>
                  <div className="text-sm font-semibold">{p.nom || p.symbol}</div>
                  <div className="text-[10px]" style={{ color: "var(--text-muted)" }}>{p.quantite} · {p.type_produit} · {p.plateforme || ""}</div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="text-right">
                  <div className="text-sm font-semibold">{fmt(p.current_value)}</div>
                  {p.pnl_pct != null && (
                    <div className={`text-[11px] font-medium inline-flex items-center gap-0.5 ${p.pnl_eur >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                      {p.pnl_eur >= 0 ? <ArrowUpRight size={11} /> : <ArrowDownRight size={11} />}
                      {p.pnl_pct >= 0 ? "+" : ""}{p.pnl_pct}%
                    </div>
                  )}
                </div>
                <button onClick={() => deletePosition(p.id)} className="p-1.5 rounded-lg hover:bg-red-500/10 text-red-400/50 hover:text-red-400 transition">
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : !showAdd ? (
        <div className="text-center py-20">
          <Gem size={40} className="mx-auto mb-3" style={{ color: "var(--text-faint)" }} />
          <p style={{ color: "var(--text-muted)" }}>Aucune position matières premières</p>
          <button onClick={() => setShowAdd(true)} className="text-cyan-400 text-sm hover:underline mt-2">
            Ajouter votre première position
          </button>
        </div>
      ) : null}

      {showAdd && <AddCommodityForm onClose={() => setShowAdd(false)} onCreated={() => { setShowAdd(false); onRefresh(); }} />}
    </div>
  );
}

function AddCommodityForm({ onClose, onCreated }) {
  const [form, setForm] = useState({ symbol: "GOLD", nom: "Or (once)", type_produit: "physique", quantite: "", prix_achat_moyen: "", plateforme: "Revolut" });
  const [saving, setSaving] = useState(false);
  function set(k, v) { setForm(f => ({ ...f, [k]: v })); }

  async function save() {
    if (!form.symbol || !form.quantite) return;
    setSaving(true);
    try {
      await fetch(`${API}/commodities`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          symbol: form.symbol.toUpperCase(),
          nom: form.nom,
          type_produit: form.type_produit,
          quantite: parseFloat(form.quantite) || 0,
          prix_achat_moyen: parseFloat(form.prix_achat_moyen) || 0,
          plateforme: form.plateforme,
        }),
      });
      onCreated();
    } catch (e) {}
    setSaving(false);
  }

  return (
    <div className="card p-5 space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="font-bold">Ajouter une matière première</h3>
        <button onClick={onClose} className="p-1 rounded hover:bg-white/5"><X size={16} /></button>
      </div>

      <div>
        <label className="text-[11px] font-medium mb-2 block" style={{ color: "var(--text-muted)" }}>Produit</label>
        <div className="flex gap-2">
          {COMMODITIES.map(c => (
            <button key={c.symbol} onClick={() => { set("symbol", c.symbol); set("nom", c.nom); set("type_produit", c.type_produit); }}
              className={`flex-1 p-3 rounded-xl border text-center text-xs transition
                ${form.symbol === c.symbol ? "border-cyan-500 bg-cyan-500/10 text-white" : ""}`}
              style={{ borderColor: form.symbol === c.symbol ? undefined : "var(--border)", color: form.symbol === c.symbol ? undefined : "var(--text-secondary)" }}>
              {c.nom}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-[10px] mb-1 block" style={{ color: "var(--text-muted)" }}>Quantité (onces / barils / parts)</label>
          <input type="number" step="any" value={form.quantite} onChange={e => set("quantite", e.target.value)}
            className="input-field w-full" placeholder="1.5" />
        </div>
        <div>
          <label className="text-[10px] mb-1 block" style={{ color: "var(--text-muted)" }}>Prix d'achat moyen (€)</label>
          <input type="number" step="any" value={form.prix_achat_moyen} onChange={e => set("prix_achat_moyen", e.target.value)}
            className="input-field w-full" placeholder="1800" />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-[10px] mb-2 block" style={{ color: "var(--text-muted)" }}>Type</label>
          <div className="flex flex-wrap gap-1">
            {TYPES.map(t => (
              <button key={t} onClick={() => set("type_produit", t)}
                className={`px-2 py-1 rounded-lg text-[10px] border transition capitalize
                  ${form.type_produit === t ? "border-cyan-500 bg-cyan-500/10 text-white" : ""}`}
                style={{ borderColor: form.type_produit === t ? undefined : "var(--border)", color: form.type_produit === t ? undefined : "var(--text-muted)" }}>
                {t}
              </button>
            ))}
          </div>
        </div>
        <div>
          <label className="text-[10px] mb-2 block" style={{ color: "var(--text-muted)" }}>Plateforme</label>
          <div className="flex flex-wrap gap-1">
            {PLATEFORMES.map(p => (
              <button key={p} onClick={() => set("plateforme", p)}
                className={`px-2 py-1 rounded-lg text-[10px] border transition
                  ${form.plateforme === p ? "border-cyan-500 bg-cyan-500/10 text-white" : ""}`}
                style={{ borderColor: form.plateforme === p ? undefined : "var(--border)", color: form.plateforme === p ? undefined : "var(--text-muted)" }}>
                {p}
              </button>
            ))}
          </div>
        </div>
      </div>

      <button onClick={save} disabled={!form.symbol || !form.quantite || saving}
        className="w-full py-2.5 rounded-xl bg-cyan-600 text-sm font-medium hover:bg-cyan-500 transition disabled:opacity-30">
        {saving ? <Loader2 size={14} className="animate-spin inline mr-1" /> : <Check size={14} className="inline mr-1" />}
        Ajouter
      </button>
    </div>
  );
}

function fmt(n) {
  if (n == null || isNaN(n)) return "—";
  return new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(n);
}
