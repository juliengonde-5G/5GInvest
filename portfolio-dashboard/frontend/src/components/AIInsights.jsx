import { RefreshCw, Brain, AlertTriangle, Lightbulb, Shield } from "lucide-react";

export default function AIInsights({ data, onRefresh }) {
  if (!data) {
    return (
      <div className="text-center py-16">
        <Brain size={48} className="mx-auto text-accent-purple mb-4 opacity-50" />
        <p className="text-gray-400 mb-4">Analyse IA en cours...</p>
        <button onClick={onRefresh} className="px-4 py-2 bg-accent-blue rounded-lg text-sm font-medium hover:bg-indigo-600 transition">
          <RefreshCw size={14} className="inline mr-2 animate-spin" />
          Analyser
        </button>
      </div>
    );
  }

  if (data.error) {
    return (
      <div className="text-center py-16">
        <AlertTriangle size={48} className="mx-auto text-accent-orange mb-4" />
        <p className="text-gray-400">{data.error}</p>
        <button onClick={onRefresh} className="mt-4 px-4 py-2 bg-dark-600 rounded-lg text-sm hover:bg-dark-500 transition">
          Réessayer
        </button>
      </div>
    );
  }

  const riskColor = data.risk_score <= 3 ? "text-green-400"
    : data.risk_score <= 6 ? "text-amber-400"
    : "text-red-400";

  const riskBg = data.risk_score <= 3 ? "bg-green-500/10 border-green-500/30"
    : data.risk_score <= 6 ? "bg-amber-500/10 border-amber-500/30"
    : "bg-red-500/10 border-red-500/30";

  return (
    <div className="space-y-4">
      {/* Risk Score */}
      <div className={`${riskBg} rounded-xl p-6 border`}>
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Shield size={20} className={riskColor} />
              <span className="text-sm text-gray-400 uppercase tracking-wide">Score de risque</span>
            </div>
            <div className={`text-5xl font-bold ${riskColor}`}>
              {data.risk_score}<span className="text-lg text-gray-500">/10</span>
            </div>
            <div className={`text-sm mt-1 ${riskColor}`}>{data.risk_label}</div>
          </div>
          <div className="w-24 h-24">
            <svg viewBox="0 0 100 100" className="transform -rotate-90">
              <circle cx="50" cy="50" r="40" fill="none" stroke="#252540" strokeWidth="8" />
              <circle
                cx="50" cy="50" r="40" fill="none"
                stroke={data.risk_score <= 3 ? "#22c55e" : data.risk_score <= 6 ? "#f59e0b" : "#ef4444"}
                strokeWidth="8"
                strokeDasharray={`${data.risk_score * 25.13} 251.3`}
                strokeLinecap="round"
              />
            </svg>
          </div>
        </div>
      </div>

      {/* Allocation Opinion */}
      {data.allocation_opinion && (
        <div className="bg-dark-800 rounded-xl p-4 border border-dark-600">
          <div className="text-sm text-gray-400 mb-2">Avis global</div>
          <p className="text-gray-200">{data.allocation_opinion}</p>
        </div>
      )}

      {/* Insights */}
      {data.insights?.length > 0 && (
        <div className="bg-dark-800 rounded-xl p-4 border border-dark-600">
          <div className="flex items-center gap-2 mb-3">
            <Lightbulb size={16} className="text-amber-400" />
            <span className="text-sm font-semibold text-gray-400 uppercase tracking-wide">Insights</span>
          </div>
          <div className="space-y-2">
            {data.insights.map((insight, i) => (
              <div key={i} className="flex gap-3 items-start bg-dark-700 rounded-lg p-3">
                <span className="text-amber-400 text-sm font-bold mt-0.5">{i + 1}</span>
                <p className="text-sm text-gray-300">{insight}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {data.recommendations?.length > 0 && (
        <div className="bg-dark-800 rounded-xl p-4 border border-dark-600">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle size={16} className="text-accent-blue" />
            <span className="text-sm font-semibold text-gray-400 uppercase tracking-wide">Recommandations</span>
          </div>
          <div className="space-y-2">
            {data.recommendations.map((rec, i) => (
              <div key={i} className="flex gap-3 items-start bg-accent-blue/5 border border-accent-blue/20 rounded-lg p-3">
                <span className="text-accent-blue text-lg">→</span>
                <p className="text-sm text-gray-300">{rec}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Source & Disclaimer */}
      <div className="text-center space-y-2">
        <div className="text-xs text-gray-600">
          Source: {data.source || "inconnue"}
        </div>
        {data.disclaimer && (
          <div className="text-[10px] text-gray-700">{data.disclaimer}</div>
        )}
        <button onClick={onRefresh} className="text-xs text-accent-blue hover:underline">
          Relancer l'analyse
        </button>
      </div>
    </div>
  );
}
