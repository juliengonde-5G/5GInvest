import { useState } from "react";
import { Bitcoin, ArrowUpRight, ArrowDownRight, Plus, X, Loader2, Check, Trash2 } from "lucide-react";

const API = "/api";

const POPULAR_CRYPTOS = [
  { symbol: "BTC", nom: "Bitcoin" },
  { symbol: "ETH", nom: "Ethereum" },
  { symbol: "SOL", nom: "Solana" },
  { symbol: "XRP", nom: "Ripple" },
  { symbol: "ADA", nom: "Cardano" },
  { symbol: "DOGE", nom: "Dogecoin" },
  { symbol: "DOT", nom: "Polkadot" },
  { symbol: "AVAX", nom: "Avalanche" },
  { symbol: "MATIC", nom: "Polygon" },
  { symbol: "LINK", nom: "Chainlink" },
  { symbol: "BNB", nom: "BNB" },
  { symbol: "LTC", nom: "Litecoin" },
  { symbol: "UNI", nom: "Uniswap" },
  { symbol: "ATOM", nom: "Cosmos" },
];

const PLATEFORMES = ["Revolut", "Binance", "Coinbase", "Kraken", "Trade Republic", "Ledger", "Autre"];

export default function CryptoView({ items, onRefresh }) {
  const [showAdd, setShowAdd] = useState(false);
  const total = items?.reduce((s, p) => s + (p.current_value || 0), 0) || 0;
  const totalPnl = items?.reduce((s, p) => s + (p.pnl_eur || 0), 0) || 0;

  async function deletePosition(id) {
    if (!confirm("Supprimer cette position ?")) return;
    await fetch(`${API}/crypto/${id}`, { method: "DELETE" });
    onRefresh();
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">Crypto</h2>
        <button onClick={() => setShowAdd(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-amber-600 text-sm font-medium hover:bg-amber-500 transition">
          <Plus size={16} /> Ajouter
        </button>
      </div>

      {items?.length > 0 && (
        <div className="grid grid-cols-3 gap-3">
          <div className="card p-3">
            <div className="text-[10px]" style={{ color: "var(--text-muted)" }}>Valeur totale</div>
            <div className="text-lg font-bold">{fmt(total)}</div>
          </div>
          <div className="card p-3">
            <div className="text-[10px]" style={{ color: "var(--text-muted)" }}>P&L total</div>
            <div className={`text-lg font-bold ${totalPnl >= 0 ? "text-emerald-400" : "text-red-400"}`}>
              {totalPnl >= 0 ? "+" : ""}{fmt(totalPnl)}
            </div>
          </div>
          <div className="card p-3">
            <div className="text-[10px]" style={{ color: "var(--text-muted)" }}>Positions</div>
            <div className="text-lg font-bold">{items.length}</div>
          </div>
        </div>
      )}

      {items?.length > 0 ? (
        <div className="card">
          <div className="divide-y" style={{ borderColor: "var(--border)" }}>
            {items.map((p, i) => (
              <div key={i} className="flex items-center justify-between px-5 py-4" style={{ borderColor: "var(--border)" }}>
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-amber-500/10 flex items-center justify-center text-amber-400 text-xs font-bold">
                    {p.symbol?.slice(0, 3)}
                  </div>
                  <div>
                    <div className="text-sm font-semibold">{p.nom || p.symbol}</div>
                    <div className="text-[10px]" style={{ color: "var(--text-muted)" }}>{p.quantite} {p.symbol} · {p.plateforme || ""}</div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <div className="text-sm font-semibold">{fmt(p.current_value)}</div>
                    <div className={`text-[11px] font-medium inline-flex items-center gap-0.5 ${p.pnl_eur >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                      {p.pnl_eur >= 0 ? <ArrowUpRight size={11} /> : <ArrowDownRight size={11} />}
                      {p.pnl_eur >= 0 ? "+" : ""}{fmt(p.pnl_eur)} ({p.pnl_pct >= 0 ? "+" : ""}{p.pnl_pct}%)
                    </div>
                  </div>
                  <button onClick={() => deletePosition(p.id)} className="p-1.5 rounded-lg hover:bg-red-500/10 text-red-400/50 hover:text-red-400 transition">
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : !showAdd ? (
        <div className="text-center py-20">
          <Bitcoin size={40} className="mx-auto mb-3" style={{ color: "var(--text-faint)" }} />
          <p style={{ color: "var(--text-muted)" }}>Aucune position crypto</p>
          <button onClick={() => setShowAdd(true)} className="text-amber-400 text-sm hover:underline mt-2">
            Ajouter votre première position
          </button>
        </div>
      ) : null}

      {showAdd && <AddCryptoForm onClose={() => setShowAdd(false)} onCreated={() => { setShowAdd(false); onRefresh(); }} />}
    </div>
  );
}


function AddCryptoForm({ onClose, onCreated }) {
  const [form, setForm] = useState({ symbol: "", nom: "", quantite: "", prix_achat_moyen: "", plateforme: "Revolut" });
  const [saving, setSaving] = useState(false);

  function set(k, v) { setForm(f => ({ ...f, [k]: v })); }

  function selectCrypto(c) {
    set("symbol", c.symbol);
    set("nom", c.nom);
  }

  async function save() {
    if (!form.symbol || !form.quantite) return;
    setSaving(true);
    try {
      await fetch(`${API}/crypto`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          symbol: form.symbol.toUpperCase(),
          nom: form.nom,
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
        <h3 className="font-bold">Ajouter une crypto</h3>
        <button onClick={onClose} className="p-1 rounded hover:bg-white/5"><X size={16} /></button>
      </div>

      {/* Quick select */}
      <div>
        <label className="text-[11px] font-medium mb-2 block" style={{ color: "var(--text-muted)" }}>Sélection rapide</label>
        <div className="flex flex-wrap gap-1.5">
          {POPULAR_CRYPTOS.map(c => (
            <button key={c.symbol} onClick={() => selectCrypto(c)}
              className={`px-2.5 py-1.5 rounded-lg text-[11px] border transition
                ${form.symbol === c.symbol ? "border-amber-500 bg-amber-500/10 text-white" : "text-[#71717a] hover:text-white"}`}
              style={{ borderColor: form.symbol === c.symbol ? undefined : "var(--border)" }}>
              {c.symbol}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-[10px] mb-1 block" style={{ color: "var(--text-muted)" }}>Symbole</label>
          <input value={form.symbol} onChange={e => set("symbol", e.target.value.toUpperCase())}
            className="input-field w-full" placeholder="BTC" />
        </div>
        <div>
          <label className="text-[10px] mb-1 block" style={{ color: "var(--text-muted)" }}>Nom</label>
          <input value={form.nom} onChange={e => set("nom", e.target.value)}
            className="input-field w-full" placeholder="Bitcoin" />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-[10px] mb-1 block" style={{ color: "var(--text-muted)" }}>Quantité</label>
          <input type="number" step="any" value={form.quantite} onChange={e => set("quantite", e.target.value)}
            className="input-field w-full" placeholder="0.5" />
        </div>
        <div>
          <label className="text-[10px] mb-1 block" style={{ color: "var(--text-muted)" }}>Prix d'achat moyen (€)</label>
          <input type="number" step="any" value={form.prix_achat_moyen} onChange={e => set("prix_achat_moyen", e.target.value)}
            className="input-field w-full" placeholder="45000" />
        </div>
      </div>

      <div>
        <label className="text-[10px] mb-2 block" style={{ color: "var(--text-muted)" }}>Plateforme</label>
        <div className="flex flex-wrap gap-1.5">
          {PLATEFORMES.map(p => (
            <button key={p} onClick={() => set("plateforme", p)}
              className={`px-2.5 py-1.5 rounded-lg text-[11px] border transition
                ${form.plateforme === p ? "border-amber-500 bg-amber-500/10 text-white" : "text-[#71717a] hover:text-white"}`}
              style={{ borderColor: form.plateforme === p ? undefined : "var(--border)" }}>
              {p}
            </button>
          ))}
        </div>
      </div>

      <button onClick={save} disabled={!form.symbol || !form.quantite || saving}
        className="w-full py-2.5 rounded-xl bg-amber-600 text-sm font-medium hover:bg-amber-500 transition disabled:opacity-30">
        {saving ? <Loader2 size={14} className="animate-spin inline mr-1" /> : <Check size={14} className="inline mr-1" />}
        Ajouter {form.symbol || "la position"}
      </button>
    </div>
  );
}


function fmt(n) {
  if (n == null || isNaN(n)) return "—";
  return new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(n);
}
