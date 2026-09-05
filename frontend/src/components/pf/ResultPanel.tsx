import { ExternalLink, FileText, Volume2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { AnalysisResult, FeedbackRequest, TamilTranslation } from "@/lib/pf";
import FeedbackCard from "@/components/pf/FeedbackCard";

type TranslationState = "IDLE" | "LOADING" | "SUCCESS" | "NOT_CONFIGURED" | "ERROR";

interface ResultPanelProps {
  result: AnalysisResult | null;
  language: "en" | "ta";
  onPrint: () => void;
  onSpeak: () => void;
  translation: TamilTranslation | null;
  translationStatus: TranslationState;
  onFeedback: (feedback: FeedbackRequest) => Promise<void>;
  inputText: string;
}

const labels = {
  en: { detected: "Issue detected", confidence: "AI confidence score", why: "Why this points here", facts: "What we detected", actions: "What to do next", documents: "What may be needed", uncertainty: "What remains uncertain", sources: "Supporting official sources", sourceUnavailable: "Authoritative source not found for this specific recommendation.", independent: "PF Doctor is an independent AI assistance tool. This guidance is not a guarantee of claim approval or correction." },
  ta: { detected: "கண்டறியப்பட்ட சிக்கல்", confidence: "AI நம்பிக்கை மதிப்பீடு", why: "இது ஏன் இந்த சிக்கலைக் குறிக்கிறது", facts: "நாங்கள் கண்டறிந்தது", actions: "அடுத்து செய்ய வேண்டியது", documents: "தேவைப்படக்கூடியவை", uncertainty: "இன்னும் உறுதியாகாதவை", sources: "ஆதரிக்கும் அதிகாரப்பூர்வ ஆதாரங்கள்", sourceUnavailable: "இந்த குறிப்பிட்ட பரிந்துரைக்கு அதிகாரப்பூர்வ ஆதாரம் கிடைக்கவில்லை.", independent: "PF Doctor ஒரு சுயாதீன AI உதவி கருவி. இது claim approval அல்லது correction-க்கு உத்தரவாதம் அல்ல." },
};

export default function ResultPanel({ result, language, onPrint, onSpeak, translation, translationStatus, onFeedback, inputText }: ResultPanelProps) {
  const copy = labels[language];
  if (!result) {
    return (
      <Card className="result-empty" data-testid="result-empty-state">
        <CardContent className="flex min-h-[470px] flex-col justify-between p-7">
          <div>
            <p className="eyebrow">Output / output</p>
            <h2 className="mt-2 max-w-md text-3xl font-semibold tracking-tight text-slate-900" data-testid="result-empty-title">Your clear next step starts with the exact rejection wording.</h2>
            <p className="mt-4 max-w-lg text-sm leading-7 text-slate-600" data-testid="result-empty-description">Paste the message or upload a screenshot. PF Doctor will show what was detected, what remains uncertain, and whether Live AI is actually configured.</p>
          </div>
          <div className="grid gap-3 sm:grid-cols-3" data-testid="result-promise-list">
            {[["01", "Evidence", "Signals before conclusions"], ["02", "Action", "A category-specific path"], ["03", "Honesty", "No invented verification"]].map(([number, title, detail]) => <div className="rounded-xl border border-slate-200 bg-slate-50/80 p-4" key={number} data-testid={`result-promise-${number}`}><span className="font-mono text-xs text-emerald-700">{number}</span><p className="mt-3 text-sm font-semibold text-slate-800">{title}</p><p className="mt-1 text-xs leading-5 text-slate-500">{detail}</p></div>)}
          </div>
        </CardContent>
      </Card>
    );
  }
  const translated = language === "ta" && translationStatus === "SUCCESS" && translation ? translation : null;
  const title = translated?.issue_title ?? result.issue_title;
  const explanation = translated?.plain_language_explanation ?? result.plain_language_explanation;
  const facts = translated?.facts_detected ?? result.facts_detected;
  const why = translated?.why_this_matches ?? result.why_this_matches;
  const actions = translated?.recommended_actions ?? result.recommended_actions;
  const documents = translated?.documents_needed ?? result.documents_needed;
  const uncertainties = translated?.uncertainties ?? result.uncertainties;
  return (
    <div className="space-y-4 print-report" data-testid="analysis-result">
      <section className="print-only" data-testid="print-report-header">
        <h1>PF Doctor Guidance Report</h1>
        <p>PF Doctor is an independent AI assistance tool and is not an official EPFO service.</p>
        <h2>Input summary / extracted rejection text</h2>
        <p>{inputText}</p>
      </section>
      <Card className="overflow-hidden border-emerald-200 bg-white shadow-sm" data-testid="result-summary-card">
        <CardHeader className="border-b border-emerald-100 bg-emerald-50/60 p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div><p className="eyebrow text-emerald-700" data-testid="result-mode-label">{result.status === "DEMO" ? "Demo Mode · predefined example" : "Live AI · backend response"}</p><CardTitle className="mt-2 text-2xl tracking-tight text-slate-900" data-testid="result-issue-title">{title}</CardTitle></div>
            <Badge variant={result.status === "DEMO" ? "secondary" : "default"} data-testid="result-status-badge">{result.status === "DEMO" ? "DEMO" : "LIVE AI"}</Badge>
          </div>
          <div className="mt-5 flex flex-wrap items-center gap-3"><span className={`confidence-pill confidence-${result.confidence.level}`} data-testid="result-confidence-level">{result.confidence.level.toUpperCase()}</span><span className="font-mono text-sm text-slate-600" data-testid="result-confidence-score">{result.confidence.score}/100 · {copy.confidence}</span><span className="h-1 w-1 rounded-full bg-slate-300" /><span className="text-xs text-slate-500" data-testid="result-human-verification">Human verification required</span></div>
        </CardHeader>
        <CardContent className="p-6"><p className="text-[15px] leading-7 text-slate-700" data-testid="result-explanation">{explanation}</p>{language === "ta" && translationStatus === "LOADING" ? <div className="mt-5 rounded-xl border border-blue-200 bg-blue-50 p-4 text-sm leading-6 text-blue-950" data-testid="translation-loading-notice">Translating the validated English diagnosis…</div> : null}{language === "ta" && ["NOT_CONFIGURED", "ERROR"].includes(translationStatus) ? <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-950" data-testid="translation-fallback-notice">Tamil translation is not configured or unavailable. Showing the canonical English diagnosis.</div> : null}<div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-950" data-testid="result-source-notice">{translated?.source_explanation ?? (result.source_notice || copy.independent)}</div><div className="mt-4 flex flex-wrap gap-2"><Button variant="outline" size="sm" onClick={onPrint} data-testid="print-guidance-button"><FileText size={15} /> Print / save PDF</Button><Button variant="ghost" size="sm" onClick={onSpeak} data-testid="browser-speech-button"><Volume2 size={15} /> Browser speech</Button></div></CardContent>
      </Card>
      <Card data-testid="result-evidence-card"><CardHeader className="p-6 pb-3"><CardTitle className="text-base" data-testid="result-facts-heading">{copy.facts}</CardTitle></CardHeader><CardContent className="grid gap-3 p-6 pt-2 sm:grid-cols-2">{facts.map((fact, index) => <div className="evidence-item" key={`${fact}-${index}`} data-testid={`result-fact-${index}`}>{fact}</div>)}</CardContent></Card>
      <Card data-testid="result-reasoning-card"><CardHeader className="p-6 pb-3"><CardTitle className="text-base" data-testid="result-why-heading">{copy.why}</CardTitle></CardHeader><CardContent className="p-6 pt-2"><ul className="space-y-3 text-sm leading-6 text-slate-600">{why.map((item, index) => <li className="flex gap-3" key={`${item}-${index}`} data-testid={`result-reason-${index}`}><span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-600" />{item}</li>)}</ul></CardContent></Card>
      <Card data-testid="result-actions-card"><CardHeader className="p-6 pb-3"><CardTitle className="text-base" data-testid="result-actions-heading">{copy.actions}</CardTitle></CardHeader><CardContent className="space-y-3 p-6 pt-2">{actions.map((action) => <div className="action-item" key={action.step} data-testid={`result-action-${action.step}`}><span className="action-number">{String(action.step).padStart(2, "0")}</span><div><p className="text-sm leading-6 text-slate-700">{action.action}</p><p className="mt-1 font-mono text-[10px] font-bold uppercase tracking-widest text-emerald-700">Who: {action.responsible_party}</p>{action.documents_needed.length ? <p className="mt-2 text-xs text-slate-500">Needs: {action.documents_needed.join(", ")}</p> : null}</div></div>)}</CardContent></Card>
      <div className="grid gap-4 sm:grid-cols-2"><Card data-testid="result-documents-card"><CardHeader className="p-6 pb-3"><CardTitle className="text-base">{copy.documents}</CardTitle></CardHeader><CardContent className="p-6 pt-2"><ul className="space-y-2 text-sm leading-6 text-slate-600">{documents.map((item, index) => <li key={`${item}-${index}`} data-testid={`result-document-${index}`}>• {item}</li>)}</ul></CardContent></Card><Card data-testid="result-uncertainties-card"><CardHeader className="p-6 pb-3"><CardTitle className="text-base">{copy.uncertainty}</CardTitle></CardHeader><CardContent className="p-6 pt-2"><ul className="space-y-2 text-sm leading-6 text-slate-600">{uncertainties.map((item, index) => <li key={`${item}-${index}`} data-testid={`result-uncertainty-${index}`}>• {item}</li>)}</ul></CardContent></Card></div>
      {result.document_assistant.length ? <Card data-testid="document-assistant-card"><CardHeader className="p-6 pb-3"><CardTitle className="text-base">Document Assistant · guidance only</CardTitle></CardHeader><CardContent className="space-y-3 p-6 pt-2">{result.document_assistant.map((document, index) => <div className="rounded-lg border border-slate-200 p-3" key={`${document.name}-${index}`} data-testid={`document-assistant-item-${index}`}><p className="text-sm font-medium text-slate-800">{document.name}</p><p className="mt-1 text-xs leading-5 text-slate-500">{document.why_relevant}</p><p className="mt-2 text-xs text-slate-600">Information: {document.information_required.join(", ")}</p>{document.official_source ? <a className="source-link mt-2" href={document.official_source} target="_blank" rel="noreferrer" data-testid={`document-assistant-source-${index}`}>Open official source <ExternalLink size={13} /></a> : <p className="mt-2 text-xs text-slate-500">Source link unavailable</p>}</div>)}</CardContent></Card> : null}
      <Card data-testid="result-sources-card"><CardHeader className="p-6 pb-3"><CardTitle className="text-base">{copy.sources}</CardTitle></CardHeader><CardContent className="space-y-3 p-6 pt-2">{result.sources.length ? result.sources.map((source) => <div className="rounded-lg border border-slate-200 p-3" key={source.document_id} data-testid={`result-source-${source.document_id}`}><div className="flex items-start justify-between gap-4"><div><p className="text-sm font-medium text-slate-800">{source.title}</p><p className="mt-1 text-xs text-slate-500">{source.issuing_authority} · {source.document_type}{source.date ? ` · ${source.date}` : ""}</p></div>{source.official_url ? <a className="source-link" href={source.official_url} target="_blank" rel="noreferrer" data-testid={`result-source-link-${source.document_id}`}>Open source <ExternalLink size={13} /></a> : <span className="text-xs text-slate-500">Source link unavailable</span>}</div><p className="mt-3 text-xs leading-5 text-slate-600" data-testid={`result-source-excerpt-${source.document_id}`}>{source.relevant_excerpt}</p><p className="mt-2 font-mono text-[10px] text-slate-500">Relevance {Math.round(source.relevance_score * 100)}% · {source.section || "Section unavailable"}</p></div>) : <p className="text-sm leading-6 text-slate-600" data-testid="result-source-unavailable">{copy.sourceUnavailable}</p>}</CardContent></Card>
      <p className="px-1 text-xs leading-5 text-slate-500" data-testid="result-disclaimer">{copy.independent} Always verify the latest instructions, circulars, and SOPs through official EPFO channels.</p>
      <FeedbackCard category={result.category} technicalStatus={`${result.status}:${result.knowledge_status}`} onSubmit={onFeedback} />
    </div>
  );
}