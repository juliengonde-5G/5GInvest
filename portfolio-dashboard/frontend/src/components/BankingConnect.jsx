import { useState, useRef, useEffect } from "react";
import { Upload, FileText, CheckCircle, AlertTriangle, Loader2, X, Download, Wifi, ExternalLink } from "lucide-react";

const API = "/api";

const BANKS_LIST = [
  { id: "boursorama", label: "Boursorama / BoursoBank" },
  { id: "societe_generale", label: "Société Générale" },
  { id: "credit_agricole", label: "Crédit Agricole" },
  { id: "bnp", label: "BNP Paribas" },
  { id: "fortuneo", label: "Fortuneo" },
  { id: "revolut", label: "Revolut" },
  { id: "lcl", label: "LCL" },
  { id: "la_banque_postale", label: "La Banque Postale" },
  { id: "n26", label: "N26" },
  { id: "trade_republic", label: "Trade Republic" },
  { id: "generic", label: "Autre banque (auto-détection)" },
];

export default function BankingConnect({ accounts, onSynced }) {
  const [step, setStep] = useState("upload"); // upload, preview, importing, done
  const [bank, setBank] = useState("generic");
  const [targetAccount, setTargetAccount] = useState(null);
  const [parsed, setParsed] = useState(null);
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const fileRef = useRef();

  async function handleFile(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setError(null);
    setParsed(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API}/banking/csv/parse?bank=${bank}`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();

      if (data.error) {
        setError(data.error);
        return;
      }

      setParsed(data);
      setStep("preview");
    } catch (e) {
      setError("Erreur de lecture du fichier");
    }
  }

  async function doImport() {
    if (!targetAccount || !parsed?.transactions) return;
    setImporting(true);
    setError(null);

    try {
      const res = await fetch(`${API}/banking/csv/import/${targetAccount}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transactions: parsed.transactions }),
      });
      const data = await res.json();
      setResult(data);
      setStep("done");
      onSynced?.();
    } catch (e) {
      setError("Erreur d'import");
    }
    setImporting(false);
  }

  // ─── STEP: DONE ────────────────────────────────────────
  if (step === "done" && result) {
    return (
      <div className="card p-6 text-center">
        <CheckCircle size={40} className="mx-auto text-emerald-400 mb-3" />
        <h3 className="font-bold text-lg mb-2">Import terminé !</h3>
        <div className="text-sm text-[#a1a1aa] space-y-1">
          <div>{result.imported} transactions importées</div>
          {result.skipped > 0 && <div className="text-[#52525b]">{result.skipped} doublons ignorés</div>}
        </div>
        <button onClick={() => { setStep("upload"); setParsed(null); setResult(null); }}
          className="mt-4 px-4 py-2 rounded-lg bg-[#18181b] text-sm text-[#a1a1aa] hover:text-white transition">
          Importer un autre fichier
        </button>
      </div>
    );
  }

  // ─── STEP: PREVIEW ─────────────────────────────────────
  if (step === "preview" && parsed) {
    return (
      <div className="card p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-bold">Aperçu de l'import</h3>
          <button onClick={() => { setStep("upload"); setParsed(null); }} className="text-[#52525b] hover:text-white">
            <X size={16} />
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-[#18181b] rounded-lg p-3 text-center">
            <div className="text-[10px] text-[#52525b]">Transactions</div>
            <div className="text-lg font-bold">{parsed.nb_parsed}</div>
          </div>
          <div className="bg-[#18181b] rounded-lg p-3 text-center">
            <div className="text-[10px] text-[#52525b]">Banque détectée</div>
            <div className="text-sm font-medium">{BANKS_LIST.find(b => b.id === parsed.bank_detected)?.label || parsed.bank_detected}</div>
          </div>
          <div className="bg-[#18181b] rounded-lg p-3 text-center">
            <div className="text-[10px] text-[#52525b]">Erreurs</div>
            <div className={`text-lg font-bold ${parsed.errors?.length ? "text-amber-400" : "text-emerald-400"}`}>
              {parsed.errors?.length || 0}
            </div>
          </div>
        </div>

        {/* Erreurs */}
        {parsed.errors?.length > 0 && (
          <div className="text-xs text-amber-400 bg-amber-500/10 rounded-lg p-2 space-y-0.5">
            {parsed.errors.slice(0, 5).map((e, i) => <div key={i}>{e}</div>)}
          </div>
        )}

        {/* Aperçu des transactions */}
        <div className="max-h-[200px] overflow-y-auto">
          <div className="text-[10px] text-[#52525b] uppercase tracking-wide mb-1">Aperçu (10 premières)</div>
          {parsed.transactions.slice(0, 10).map((tx, i) => (
            <div key={i} className="flex justify-between py-1.5 border-b border-[#1c1c22] last:border-0 text-xs">
              <div className="flex gap-3">
                <span className="text-[#52525b] w-20">{tx.date}</span>
                <span className="truncate max-w-[200px]">{tx.libelle}</span>
              </div>
              <span className={`font-medium ${tx.montant >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                {tx.montant >= 0 ? "+" : ""}{tx.montant.toFixed(2)} €
              </span>
            </div>
          ))}
        </div>

        {/* Sélection du compte cible */}
        <div>
          <label className="text-[11px] text-[#71717a] font-medium mb-2 block">Importer dans quel compte ?</label>
          {accounts?.length > 0 ? (
            <div className="grid grid-cols-2 gap-2">
              {accounts.map(a => (
                <button key={a.id} onClick={() => setTargetAccount(a.id)}
                  className={`p-2.5 rounded-lg border text-left text-xs transition
                    ${targetAccount === a.id ? "border-emerald-500 bg-emerald-500/10 text-white" : "border-[#1c1c22] text-[#a1a1aa]"}`}>
                  <div className="font-medium">{a.nom}</div>
                  <div className="text-[10px] text-[#52525b]">{a.banque} · {fmt(a.solde)}</div>
                </button>
              ))}
            </div>
          ) : (
            <div className="text-xs text-[#52525b]">Créez d'abord un compte dans l'onglet Cash.</div>
          )}
        </div>

        {error && <div className="text-xs text-red-400">{error}</div>}

        <button onClick={doImport} disabled={!targetAccount || importing}
          className="w-full py-2.5 rounded-xl bg-emerald-600 text-sm font-medium hover:bg-emerald-500 transition disabled:opacity-30">
          {importing ? <><Loader2 size={14} className="animate-spin inline mr-2" /> Import en cours...</> :
            `Importer ${parsed.nb_parsed} transactions`}
        </button>
      </div>
    );
  }

  // ─── STEP: UPLOAD (CSV + Powens) ─────────────────────────
  return (
    <div className="space-y-4">
      {/* Powens auto-connect */}
      <PowensConnect accounts={accounts} onSynced={onSynced} />

      {/* CSV import */}
      <div className="card p-5 space-y-4">
      <div className="flex items-center gap-2">
        <Upload size={16} className="text-blue-400" />
        <h3 className="text-sm font-semibold">Import CSV (manuel)</h3>
      </div>

      <p className="text-xs text-[#71717a]">
        Exportez votre relevé depuis votre espace bancaire en ligne (format CSV),
        puis importez-le ici. Le format est détecté automatiquement.
      </p>

      {/* Sélection banque */}
      <div>
        <label className="text-[11px] text-[#71717a] font-medium mb-2 block">Votre banque (aide à la détection)</label>
        <div className="flex flex-wrap gap-1.5">
          {BANKS_LIST.map(b => (
            <button key={b.id} onClick={() => setBank(b.id)}
              className={`px-2.5 py-1.5 rounded-lg text-[11px] border transition
                ${bank === b.id ? "border-blue-500 bg-blue-500/10 text-white" : "border-[#1c1c22] text-[#52525b] hover:text-white"}`}>
              {b.label}
            </button>
          ))}
        </div>
      </div>

      {/* Zone d'upload */}
      <div
        onClick={() => fileRef.current?.click()}
        className="border-2 border-dashed border-[#27272a] rounded-xl p-8 text-center cursor-pointer hover:border-blue-500 transition"
      >
        <FileText size={32} className="mx-auto text-[#52525b] mb-2" />
        <div className="text-sm text-[#a1a1aa]">Cliquez pour sélectionner un fichier CSV</div>
        <div className="text-[10px] text-[#3f3f46] mt-1">ou glissez-déposez ici</div>
        <input ref={fileRef} type="file" accept=".csv,.CSV,.ofx,.OFX,.txt,.TXT" onChange={handleFile} className="hidden" />
      </div>

      {error && (
        <div className="text-xs text-red-400 bg-red-500/10 rounded-lg p-2">
          <AlertTriangle size={12} className="inline mr-1" /> {error}
        </div>
      )}

      {/* Guide export par banque */}
      <details className="text-[10px] text-[#3f3f46]">
        <summary className="cursor-pointer hover:text-[#71717a]">Comment exporter depuis ma banque ?</summary>
        <div className="mt-2 space-y-1 pl-3">
          <div><b>Boursorama:</b> Comptes → Historique → Exporter (CSV)</div>
          <div><b>SG:</b> Mes comptes → Opérations → Télécharger (CSV)</div>
          <div><b>CA:</b> Comptes → Relevé → Export tableur</div>
          <div><b>BNP:</b> Mes comptes → Opérations → Exporter</div>
          <div><b>Revolut:</b> Dashboard → Statements → Excel/CSV</div>
          <div><b>N26:</b> Mon compte → Télécharger relevé → CSV</div>
          <div><b>Fortuneo:</b> Historique → Exporter en CSV</div>
        </div>
      </details>
    </div>
    </div>
  );
}


// ─── POWENS AUTO-CONNECT ─────────────────────────────────

function PowensConnect({ accounts, onSynced }) {
  const [configured, setConfigured] = useState(null);
  const [connecting, setConnecting] = useState(false);
  const [powensData, setPowensData] = useState(null); // {token, webview_url}
  const [syncing, setSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState(null);

  useEffect(() => {
    fetch(`${API}/powens/status`).then(r => r.json()).then(d => setConfigured(d.configured)).catch(() => setConfigured(false));
  }, []);

  async function startConnect() {
    setConnecting(true);
    try {
      const res = await fetch(`${API}/powens/init`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ redirect_uri: `${window.location.origin}/powens/callback` }),
      });
      const data = await res.json();
      if (data.webview_url) {
        setPowensData(data);
        window.open(data.webview_url, "_blank");
      }
    } catch (e) {}
    setConnecting(false);
  }

  async function doSync() {
    if (!powensData?.token) return;
    setSyncing(true);
    try {
      const res = await fetch(`${API}/powens/sync`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: powensData.token }),
      });
      const data = await res.json();
      setSyncResult(data);
      if (data.status === "ok") onSynced?.();
    } catch (e) {}
    setSyncing(false);
  }

  if (configured === false || configured === null) return null;

  // Sync result
  if (syncResult?.status === "ok") {
    return (
      <div className="card p-5 border-l-4 border-l-emerald-500">
        <CheckCircle size={24} className="text-emerald-400 mb-2" />
        <h3 className="font-bold mb-2">Synchronisation Powens réussie</h3>
        {syncResult.accounts?.map((a, i) => (
          <div key={i} className="flex justify-between text-xs py-1">
            <span>{a.nom}</span>
            <span className="text-emerald-400">{a.transactions_imported} transactions</span>
          </div>
        ))}
        <button onClick={() => { setSyncResult(null); setPowensData(null); }}
          className="mt-3 text-xs text-[#52525b] hover:text-white">Reconnecter</button>
      </div>
    );
  }

  // En attente
  if (powensData) {
    return (
      <div className="card p-5 border-l-4 border-l-blue-500">
        <div className="flex items-center gap-2 mb-2">
          <Wifi size={16} className="text-blue-400 animate-pulse" />
          <h3 className="text-sm font-semibold">Connexion Powens en cours</h3>
        </div>
        <p className="text-xs text-[#71717a] mb-3">
          Authentifiez-vous dans l'onglet qui vient de s'ouvrir, puis revenez ici.
        </p>
        <button onClick={doSync} disabled={syncing}
          className="px-4 py-2 rounded-lg bg-emerald-600 text-sm font-medium hover:bg-emerald-500 transition disabled:opacity-50">
          {syncing ? <><Loader2 size={14} className="animate-spin inline mr-1" /> Synchronisation...</>
            : "J'ai terminé, synchroniser"}
        </button>
      </div>
    );
  }

  // Bouton de connexion
  return (
    <div className="card p-5 border-l-4 border-l-blue-500">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Wifi size={16} className="text-blue-400" />
            <h3 className="text-sm font-semibold">Connexion automatique (Powens)</h3>
          </div>
          <p className="text-[10px] text-[#52525b]">
            Synchronisez automatiquement vos comptes et transactions. 350+ banques françaises.
          </p>
        </div>
        <button onClick={startConnect} disabled={connecting}
          className="px-4 py-2 rounded-lg bg-blue-600 text-sm font-medium hover:bg-blue-500 transition disabled:opacity-50 shrink-0">
          {connecting ? <Loader2 size={14} className="animate-spin" /> : <><ExternalLink size={14} className="inline mr-1" /> Connecter</>}
        </button>
      </div>
    </div>
  );
}


function fmt(n) {
  if (n == null || isNaN(n)) return "—";
  return new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(n);
}
