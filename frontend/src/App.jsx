import React, { useState } from 'react';
import {
  Search,
  Sparkles,
  ExternalLink,
  CheckCircle2,
  XCircle,
  Target,
  UserCheck,
  Clock,
  Send,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  Layers,
  AlertCircle,
  Loader2,
  Building2,
  ShieldCheck,
  BarChart3
} from 'lucide-react';

const SIGNAL_LABELS = {
  product_change: { title: 'Product / Feature Change', desc: 'Recent feature releases or major product changes' },
  rebrand_or_positioning: { title: 'Rebrand / Positioning Change', desc: 'Brand messaging, positioning, or identity shift' },
  website_change: { title: 'Website / Digital Experience Change', desc: 'Website redesign or digital experience update' },
  market_expansion: { title: 'Market / Audience Expansion', desc: 'Expansion into enterprise, new segments or platforms' },
  design_product_hiring: { title: 'Design / Product Hiring', desc: 'Active hiring for Product/UX/UI/Brand design roles' },
  growth_with_experience_pressure: { title: 'Growth with Experience Pressure', desc: 'Scaling challenges & coordination/notification complexity' },
  observable_experience_problem: { title: 'Observable UX / Experience Problem', desc: 'Observable product UX or digital friction' },
};

const TIER_COLORS = {
  'Very High': 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
  'High': 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
  'Medium': 'bg-amber-500/10 text-amber-400 border-amber-500/30',
  'Low': 'bg-blue-500/10 text-blue-400 border-blue-500/30',
  'Very Low': 'bg-slate-500/10 text-slate-400 border-slate-700/50',
};

export default function App() {
  const [domain, setDomain] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [copied, setCopied] = useState(false);
  const [expandedSignals, setExpandedSignals] = useState({});

  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!domain.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          domain: domain.trim(),
          company_name: companyName.trim() || undefined,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({ detail: 'Analysis failed' }));
        throw new Error(errData.detail || `Server error: ${res.status}`);
      }

      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError(err.message || 'Failed to connect to backend.');
    } finally {
      setLoading(false);
    }
  };

  const copyOutreach = (text) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const toggleSignal = (key) => {
    setExpandedSignals((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Navbar */}
      <header className="border-b border-slate-800/80 bg-slate-900/50 backdrop-blur sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/20">
              B
            </div>
            <div>
              <span className="font-semibold text-slate-100 tracking-tight">Brandhero</span>
              <span className="ml-2 text-xs uppercase px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-medium border border-slate-700">
                Opportunity Intelligence
              </span>
            </div>
          </div>
          <div className="text-xs text-slate-400 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            Deterministic Signal Engine
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 py-8 space-y-8">
        {/* Search Input Section */}
        <section className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 shadow-xl relative overflow-hidden">
          <div className="absolute top-0 right-0 -mr-16 -mt-16 w-64 h-64 rounded-full bg-indigo-500/5 blur-3xl pointer-events-none"></div>

          <h1 className="text-xl font-semibold text-slate-100 mb-1">Evaluate Target B2B Company</h1>
          <p className="text-sm text-slate-400 mb-6">
            Collects verifiable website pages & company news, evaluates 7 Brandhero design signals, and produces deterministic outreach angles.
          </p>

          <form onSubmit={handleAnalyze} className="grid grid-cols-1 sm:grid-cols-12 gap-4">
            <div className="sm:col-span-6">
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Domain <span className="text-rose-400">*</span>
              </label>
              <div className="relative">
                <input
                  type="text"
                  value={domain}
                  onChange={(e) => setDomain(e.target.value)}
                  placeholder="linear.app or stripe.com"
                  className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl px-4 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition"
                  required
                />
              </div>
            </div>

            <div className="sm:col-span-4">
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Company Name <span className="text-slate-500 text-[11px]">(Optional)</span>
              </label>
              <input
                type="text"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                placeholder="e.g. Linear"
                className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl px-4 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition"
              />
            </div>

            <div className="sm:col-span-2 flex items-end">
              <button
                type="submit"
                disabled={loading || !domain.trim()}
                className="w-full h-[42px] bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium text-sm rounded-xl flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/20 transition cursor-pointer"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Analyzing
                  </>
                ) : (
                  <>
                    <Search className="w-4 h-4" />
                    Analyze
                  </>
                )}
              </button>
            </div>
          </form>

          {/* Quick suggestions */}
          <div className="mt-4 flex items-center gap-2 text-xs text-slate-400">
            <span>Examples:</span>
            {['linear.app', 'supabase.com', 'postman.com'].map((ex) => (
              <button
                key={ex}
                type="button"
                onClick={() => {
                  setDomain(ex);
                  setCompanyName(ex.split('.')[0].charAt(0).toUpperCase() + ex.split('.')[0].slice(1));
                }}
                className="px-2 py-0.5 rounded bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 border border-slate-700 transition cursor-pointer"
              >
                {ex}
              </button>
            ))}
          </div>
        </section>

        {/* Error State */}
        {error && (
          <div className="bg-rose-500/10 border border-rose-500/30 rounded-2xl p-4 flex items-start gap-3 text-rose-300 text-sm">
            <AlertCircle className="w-5 h-5 shrink-0 text-rose-400 mt-0.5" />
            <div>
              <p className="font-semibold text-rose-200">Analysis Error</p>
              <p>{error}</p>
            </div>
          </div>
        )}

        {/* Loading State Skeleton */}
        {loading && (
          <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-12 text-center space-y-4">
            <div className="inline-flex items-center justify-center p-3 rounded-2xl bg-indigo-600/10 text-indigo-400 border border-indigo-500/20 animate-pulse">
              <Loader2 className="w-8 h-8 animate-spin" />
            </div>
            <div className="space-y-1">
              <h3 className="text-base font-medium text-slate-200">Analyzing Target Company Evidence</h3>
              <p className="text-xs text-slate-400 max-w-md mx-auto">
                Crawling website pages, filtering business news signals, evaluating 7 Brandhero opportunity criteria, and computing deterministic score...
              </p>
            </div>
          </div>
        )}

        {/* Results View */}
        {result && !loading && (
          <div className="space-y-8 animate-in fade-in duration-300">
            {/* Top Score Banner */}
            <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
              {/* Company & Score */}
              <div className="md:col-span-8 bg-slate-900/60 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2 text-xs font-medium text-slate-400 mb-1">
                      <Building2 className="w-3.5 h-3.5 text-indigo-400" />
                      Target Company Evaluation
                    </div>
                    <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
                      {result.company_name}
                      <a
                        href={`https://${result.domain}`}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs text-slate-400 hover:text-indigo-400 flex items-center gap-1 font-normal"
                      >
                        {result.domain} <ExternalLink className="w-3 h-3" />
                      </a>
                    </h2>
                  </div>
                  <div
                    className={`px-3 py-1 rounded-full text-xs font-semibold border ${
                      TIER_COLORS[result.scoring?.tier] || 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    Tier: {result.scoring?.tier || 'N/A'}
                  </div>
                </div>

                <div className="mt-6 grid grid-cols-3 gap-4 pt-4 border-t border-slate-800/80 text-center">
                  <div>
                    <div className="text-xs text-slate-400">Opportunity Score</div>
                    <div className="text-2xl font-bold text-indigo-400 mt-0.5">
                      {result.scoring?.score ?? 0}
                      <span className="text-xs text-slate-500 font-normal"> / 100</span>
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-400">Pages Analyzed</div>
                    <div className="text-xl font-semibold text-slate-200 mt-0.5">
                      {result.evidence_summary?.pages_count ?? 0}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-400">Filtered News</div>
                    <div className="text-xl font-semibold text-slate-200 mt-0.5">
                      {result.evidence_summary?.news_count ?? 0}
                    </div>
                  </div>
                </div>
              </div>

              {/* Brandhero Need Verdict Card */}
              <div className="md:col-span-4 bg-slate-900/60 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between">
                <div>
                  <div className="text-xs font-medium text-slate-400 mb-1 flex items-center gap-1.5">
                    <Target className="w-3.5 h-3.5 text-indigo-400" />
                    Agency Relevance
                  </div>
                  <div className="text-sm font-semibold text-slate-200">Likely Brandhero Need</div>
                </div>

                <div className="my-4">
                  {result.opportunity?.likely_brandhero_need ? (
                    <div className="flex items-center gap-2.5 text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3.5 py-2.5 rounded-xl">
                      <CheckCircle2 className="w-5 h-5 shrink-0" />
                      <span className="font-semibold text-sm">
                        YES — {result.opportunity?.opportunity_tier || 'Qualified Opportunity'}
                      </span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2.5 text-slate-400 bg-slate-800/60 border border-slate-700/60 px-3.5 py-2.5 rounded-xl">
                      <XCircle className="w-5 h-5 shrink-0" />
                      <span className="font-medium text-sm">
                        NO — {result.opportunity?.opportunity_tier || 'No Opportunity'}
                      </span>
                    </div>
                  )}
                </div>

                <div className="text-xs text-slate-400">
                  Evidence-based Opportunity Tier:{' '}
                  <span className="font-medium text-slate-200">
                    {result.opportunity?.opportunity_tier || 'No Opportunity'}
                  </span>
                </div>

                <div className="text-xs text-slate-400">
                  Confidence:{' '}
                  <span className="font-medium text-slate-200">
                    {Math.round((result.opportunity?.confidence || 0) * 100)}%
                  </span>
                </div>
              </div>
            </div>

            {/* Opportunity Hypothesis & Outreach Card */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-6">
              <div className="flex items-center gap-2 pb-3 border-b border-slate-800">
                <Sparkles className="w-5 h-5 text-indigo-400" />
                <h3 className="font-semibold text-base text-slate-100">Brandhero Opportunity Hypothesis</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="space-y-1">
                  <div className="text-xs font-medium text-slate-400 flex items-center gap-1.5">
                    <Layers className="w-3.5 h-3.5 text-indigo-400" /> Primary Need
                  </div>
                  <div className="text-sm text-slate-200 bg-slate-950/60 border border-slate-800 p-3 rounded-xl min-h-[50px]">
                    {result.opportunity?.primary_need || 'No immediate primary need detected based on supplied evidence.'}
                  </div>
                </div>

                <div className="space-y-1">
                  <div className="text-xs font-medium text-slate-400 flex items-center gap-1.5">
                    <UserCheck className="w-3.5 h-3.5 text-indigo-400" /> Relevant Stakeholder
                  </div>
                  <div className="text-sm text-slate-200 bg-slate-950/60 border border-slate-800 p-3 rounded-xl min-h-[50px]">
                    {result.opportunity?.relevant_stakeholder || 'N/A'}
                  </div>
                </div>

                <div className="space-y-1">
                  <div className="text-xs font-medium text-slate-400 flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5 text-indigo-400" /> Why Now
                  </div>
                  <div className="text-sm text-slate-200 bg-slate-950/60 border border-slate-800 p-3 rounded-xl min-h-[50px]">
                    {result.opportunity?.why_now || 'No active time-sensitive trigger observed.'}
                  </div>
                </div>
              </div>

              {/* Personalized Outreach Angle */}
              <div className="space-y-2 pt-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-indigo-400 flex items-center gap-1.5">
                    <Send className="w-3.5 h-3.5" /> Personalized Outreach Angle
                  </span>
                  {result.opportunity?.personalized_outreach_angle && (
                    <button
                      type="button"
                      onClick={() => copyOutreach(result.opportunity.personalized_outreach_angle)}
                      className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 border border-slate-700 cursor-pointer transition"
                    >
                      {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                      {copied ? 'Copied' : 'Copy Angle'}
                    </button>
                  )}
                </div>
                <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 text-sm text-slate-300 leading-relaxed font-mono whitespace-pre-wrap">
                  {result.opportunity?.personalized_outreach_angle ||
                    'Outreach angle will only be synthesized when actionable Brandhero-relevant signals are detected.'}
                </div>
              </div>
            </div>

            {/* Seven Signals Detailed Grid */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-lg text-slate-100 flex items-center gap-2">
                    <BarChart3 className="w-5 h-5 text-indigo-400" />
                    Seven Opportunity Signals
                  </h3>
                  <p className="text-xs text-slate-400">
                    Deterministic evaluation based solely on collected pages and verified news.
                  </p>
                </div>
              </div>

              <div className="space-y-3">
                {Object.entries(SIGNAL_LABELS).map(([key, meta]) => {
                  const signal = result.signals?.[key] || {};
                  const isDetected = signal.detected;
                  const isExpanded = expandedSignals[key];
                  const breakdownItem = result.scoring?.breakdown?.[key];

                  return (
                    <div
                      key={key}
                      className={`border rounded-2xl transition overflow-hidden ${
                        isDetected
                          ? 'bg-slate-900/80 border-indigo-500/30 shadow-md shadow-indigo-500/5'
                          : 'bg-slate-900/40 border-slate-800/70'
                      }`}
                    >
                      {/* Signal Header Row */}
                      <div
                        onClick={() => toggleSignal(key)}
                        className="p-4 flex items-center justify-between cursor-pointer hover:bg-slate-800/30 transition select-none"
                      >
                        <div className="flex items-center gap-3">
                          {isDetected ? (
                            <div className="w-6 h-6 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0">
                              <CheckCircle2 className="w-4 h-4" />
                            </div>
                          ) : (
                            <div className="w-6 h-6 rounded-full bg-slate-800 text-slate-500 flex items-center justify-center shrink-0">
                              <XCircle className="w-4 h-4" />
                            </div>
                          )}

                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-semibold text-sm text-slate-100">{meta.title}</span>
                              <span
                                className={`text-[11px] px-2 py-0.5 rounded-full font-medium border ${
                                  isDetected
                                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                                    : 'bg-slate-800 text-slate-400 border-slate-700'
                                }`}
                              >
                                {isDetected ? 'DETECTED' : 'NOT DETECTED'}
                              </span>
                            </div>
                            <p className="text-xs text-slate-400 mt-0.5">{meta.desc}</p>
                          </div>
                        </div>

                        <div className="flex items-center gap-4">
                          <div className="text-right hidden sm:block">
                            <div className="text-xs font-semibold text-slate-200">
                              {breakdownItem?.points?.toFixed(1) || '0.0'} / {breakdownItem?.max_points || 0} pts
                            </div>
                            <div className="text-[11px] text-slate-500">
                              conf: {signal.confidence || 0} · rel: {signal.brandhero_relevance || 0}
                            </div>
                          </div>
                          {isExpanded ? (
                            <ChevronUp className="w-4 h-4 text-slate-400" />
                          ) : (
                            <ChevronDown className="w-4 h-4 text-slate-400" />
                          )}
                        </div>
                      </div>

                      {/* Expanded Signal Details & Evidence */}
                      {isExpanded && (
                        <div className="px-4 pb-4 pt-1 border-t border-slate-800/80 space-y-3 text-xs bg-slate-950/40">
                          {isDetected ? (
                            <>
                              {signal.observation && (
                                <div>
                                  <span className="font-medium text-slate-400">Observation:</span>
                                  <p className="text-slate-200 mt-0.5">{signal.observation}</p>
                                </div>
                              )}

                              {signal.brandhero_reason && (
                                <div>
                                  <span className="font-medium text-slate-400">Brandhero Relevance:</span>
                                  <p className="text-indigo-300 mt-0.5">{signal.brandhero_reason}</p>
                                </div>
                              )}

                              <div>
                                <span className="font-medium text-slate-400">Evidence Citations:</span>
                                {signal.evidence && signal.evidence.length > 0 ? (
                                  <div className="mt-1 space-y-1.5">
                                    {signal.evidence.map((ev, i) => (
                                      <div
                                        key={i}
                                        className="bg-slate-900 border border-slate-800 p-2.5 rounded-lg flex items-start justify-between gap-3"
                                      >
                                        <span className="text-slate-300">{ev.claim}</span>
                                        {ev.url && (
                                          <a
                                            href={ev.url}
                                            target="_blank"
                                            rel="noreferrer"
                                            className="text-indigo-400 hover:text-indigo-300 shrink-0 flex items-center gap-1 font-mono text-[11px]"
                                          >
                                            Source <ExternalLink className="w-3 h-3" />
                                          </a>
                                        )}
                                      </div>
                                    ))}
                                  </div>
                                ) : (
                                  <p className="text-slate-500 italic mt-0.5">No direct citations provided.</p>
                                )}
                              </div>
                            </>
                          ) : (
                            <p className="text-slate-500 py-1">
                              No verifiable evidence found in the crawled pages or news to substantiate this signal.
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Collected Pages Sources Reference */}
            {result.evidence_summary?.pages && result.evidence_summary.pages.length > 0 && (
              <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-5">
                <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
                  <ShieldCheck className="w-3.5 h-3.5 text-indigo-400" /> Crawled Pages Reference
                </h4>
                <div className="flex flex-wrap gap-2">
                  {result.evidence_summary.pages.map((p, i) => (
                    <a
                      key={i}
                      href={p.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-xs px-2.5 py-1 rounded-lg bg-slate-950 border border-slate-800 text-slate-400 hover:text-indigo-300 hover:border-slate-700 flex items-center gap-1.5 transition"
                    >
                      <span>{p.title || p.url}</span>
                      <ExternalLink className="w-3 h-3 text-slate-500" />
                    </a>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/60 py-6 text-center text-xs text-slate-500">
        Brandhero Opportunity Intelligence System · Evidence-First & Deterministic
      </footer>
    </div>
  );
}
