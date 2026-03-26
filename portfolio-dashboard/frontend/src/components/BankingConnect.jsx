import { useState, useEffect } from "react";
import { Building, Link, CheckCircle, XCircle, RefreshCw, ExternalLink, Loader2, AlertTriangle, Wifi, WifiOff } from "lucide-react";

const API = "/api";

export default function BankingConnect({ onSynced }) {
  const [configured, setConfigured] = useState(null);
  const [institutions, setInstitutions] = useState([]);
  const [search, setSearch] = useState("");
  const [connecting, setConnecting] = useState(null);  // institution_id en cours
  const [requisition, setRequisition] = useState(null);
  const [syncing, setSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { checkStatus(); }, []);

  async function checkStatus() {
    setLoading(true);
    try {
      const res = await fetch(`${API}/banking/status`);
      const data = await res.json();
      setConfigured(data.configured);
      if (data.configured) loadInstitutions();
    } catch (e) {}
    setLoading(false);
  }

  async function loadInstitutions() {
    try {
      const res = await fetch(`${API}/banking/institutions?country=FR`);
      setInstitutions(await res.json());
    } catch (e) {}
  }

  async function connectBank(institutionId) {
    setConnecting(institutionId);
    try {
      const res = await fetch(`${API}/banking/connect`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          institution_id: institutionId,
          redirect_url: `${window.location.origin}/banking/callback`,
        }),
      });
      const data = await res.json();
      if (data.link) {
        setRequisition(data);
        // Ouvrir le lien dans un nouvel onglet
        window.open(data.link, "_blank");
      } else {
        setRequisition({ error: data.error || "Erreur de connexion" });
      }
    } catch (e) {
      setRequisition({ error: "Erreur réseau" });
    }
    setConnecting(null);
  }

  async function checkAndSync() {
    if (!requisition?.requisition_id) return;
    setSyncing(true);
    setSyncResult(null);
    try {
      // Vérifier le statut
      const statusRes = await fetch(`${API}/banking/requisition/${requisition.requisition_id}/status`);
      const status = await statusRes.json();

      if (status.status === "LN") {
        // Lié ! Synchroniser
        const syncRes = await fetch(`${API}/banking/requisition/${requisition.requisition_id}/sync`, { method: "POST" });
        const result = await syncRes.json();
        setSyncResult(result);
        if (result.status === "ok") {
          onSynced?.();
        }
      } else {
        setSyncResult({ error: `Connexion pas encore active. Statut: ${status.status}. Authentifiez-vous sur le site de votre banque.` });
      }
    } catch (e) {
      setSyncResult({ error: "Erreur de synchronisation" });
    }
    setSyncing(false);
  }

  if (loading) return <div className="flex justify-center py-12"><Loader2 size={24} className="animate-spin text-[#52525b]" /></div>;

  // API non configurée
  if (configured === false) {
    return (
      <div className="card p-6 text-center">
        <WifiOff size={32} className="mx-auto text-[#52525b] mb-3" />
        <h3 className="font-bold mb-2">Connexion bancaire non configurée</h3>
        <p className="text-xs text-[#71717a] mb-4 max-w-md mx-auto">
          Pour synchroniser automatiquement vos comptes, créez un compte gratuit sur
          GoCardless Bank Account Data et ajoutez vos clés API dans le fichier .env
        </p>
        <div className="bg-[#18181b] rounded-lg p-3 text-[10px] text-left text-[#52525b] max-w-sm mx-auto font-mono">
          GOCARDLESS_SECRET_ID=votre_id<br />
          GOCARDLESS_SECRET_KEY=votre_key
        </div>
        <p className="text-[10px] text-[#3f3f46] mt-3">
          En attendant, vous pouvez ajouter vos comptes manuellement dans l'onglet Cash.
        </p>
      </div>
    );
  }

  // Résultat de synchronisation
  if (syncResult?.status === "ok") {
    return (
      <div className="card p-6">
        <div className="text-center mb-4">
          <CheckCircle size={40} className="mx-auto text-emerald-400 mb-2" />
          <h3 className="font-bold text-lg">Synchronisation réussie !</h3>
        </div>
        <div className="space-y-2">
          {syncResult.accounts?.map((acc, i) => (
            <div key={i} className="flex justify-between items-center bg-[#18181b] rounded-lg p-3">
              <div>
                <div className="text-sm font-medium">{acc.nom}</div>
                <div className="text-[10px] text-[#52525b]">{acc.transactions_imported} transactions importées</div>
              </div>
              <div className="text-sm font-bold">{fmt(acc.solde)}</div>
            </div>
          ))}
        </div>
        <button onClick={() => { setSyncResult(null); setRequisition(null); }}
          className="w-full mt-4 py-2 rounded-lg bg-[#18181b] text-sm text-[#a1a1aa] hover:text-white transition">
          Connecter une autre banque
        </button>
      </div>
    );
  }

  // En attente de connexion
  if (requisition && !requisition.error) {
    return (
      <div className="card p-6 text-center">
        <Wifi size={32} className="mx-auto text-blue-400 mb-3 animate-pulse" />
        <h3 className="font-bold mb-2">En attente d'authentification</h3>
        <p className="text-xs text-[#71717a] mb-4">
          Authentifiez-vous sur le site de votre banque dans l'onglet qui vient de s'ouvrir.
          Revenez ici ensuite.
        </p>
        <button onClick={checkAndSync} disabled={syncing}
          className="px-6 py-2.5 rounded-xl bg-emerald-600 text-sm font-medium hover:bg-emerald-500 transition disabled:opacity-50">
          {syncing ? <><Loader2 size={14} className="animate-spin inline mr-2" /> Synchronisation...</> : <><RefreshCw size={14} className="inline mr-2" /> J'ai terminé, synchroniser</>}
        </button>
        {syncResult?.error && (
          <div className="mt-3 text-xs text-amber-400 bg-amber-500/10 rounded-lg p-2">
            <AlertTriangle size={12} className="inline mr-1" /> {syncResult.error}
          </div>
        )}
      </div>
    );
  }

  // Sélection de banque
  const filtered = institutions.filter(i =>
    (i.name || "").toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-4">
      <div className="card p-4">
        <div className="flex items-center gap-2 mb-3">
          <Wifi size={16} className="text-emerald-400" />
          <h3 className="text-sm font-semibold">Connecter une banque</h3>
        </div>
        <p className="text-xs text-[#71717a] mb-3">
          Sélectionnez votre banque pour synchroniser automatiquement vos comptes et transactions (90 jours).
        </p>
        <input
          type="text"
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Rechercher une banque..."
          className="w-full px-3 py-2 bg-[#18181b] border border-[#27272a] rounded-lg text-sm text-white placeholder-[#3f3f46] focus:border-emerald-500 focus:outline-none mb-3"
        />

        <div className="grid grid-cols-2 gap-2 max-h-[400px] overflow-y-auto">
          {filtered.slice(0, 30).map(inst => (
            <button
              key={inst.id}
              onClick={() => connectBank(inst.id)}
              disabled={connecting === inst.id}
              className="flex items-center gap-2 p-3 rounded-xl border border-[#1c1c22] text-left text-xs hover:border-emerald-500 hover:bg-emerald-500/5 transition disabled:opacity-50"
            >
              <Building size={16} className="text-[#52525b] shrink-0" />
              <div className="min-w-0">
                <div className="font-medium text-white truncate">{inst.name}</div>
                {inst.bic && <div className="text-[10px] text-[#3f3f46]">{inst.bic}</div>}
              </div>
              {connecting === inst.id && <Loader2 size={12} className="animate-spin ml-auto" />}
            </button>
          ))}
        </div>

        {requisition?.error && (
          <div className="mt-3 text-xs text-red-400 bg-red-500/10 rounded-lg p-2">
            <XCircle size={12} className="inline mr-1" /> {requisition.error}
          </div>
        )}
      </div>

      <div className="text-[9px] text-[#3f3f46] text-center px-4">
        Connexion sécurisée via GoCardless (certifié PSD2). Vos identifiants bancaires ne sont jamais stockés sur notre serveur.
      </div>
    </div>
  );
}

function fmt(n) {
  if (n == null || isNaN(n)) return "—";
  return new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: 2 }).format(n);
}
