import { useMutation, useQuery } from "@tanstack/react-query";
import { useRef, useState } from "react";
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  ClipboardPaste,
  FileImage,
  Languages,
  LockKeyhole,
  Menu,
  ShieldCheck,
  Sparkles,
  UploadCloud,
} from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import PipelinePanel from "@/components/pf/PipelinePanel";
import ResultPanel from "@/components/pf/ResultPanel";
import { ApiError, apiGet, apiPost, apiPostForm } from "@/lib/api";
import { CATEGORY_LABELS } from "@/lib/pf";
import type {
  AnalysisMode,
  AnalysisResult,
  ConfigResponse,
  FeedbackRequest,
  FeedbackResponse,
  MaskResponse,
  OcrResponse,
  PipelineStage,
  TamilTranslation,
} from "@/lib/pf";

const demoSamples = [
  { id: "name-dob", label: "Name / DOB", text: "Claim rejected because the member name and date of birth do not match the EPFO record." },
  { id: "aadhaar-uan", label: "Aadhaar / UAN", text: "Aadhaar details could not be matched with the UAN profile." },
  { id: "exit-date", label: "Exit date", text: "Claim cannot proceed because the date of exit overlaps with another employment record." },
  { id: "bank-ifsc", label: "Bank / IFSC", text: "Bank account or IFSC details could not be validated." },
  { id: "kyc", label: "KYC pending", text: "KYC is pending employer approval." },
  { id: "form-15g", label: "15G / PAN", text: "PAN or Form 15G information is required for this claim." },
];

const emptyStages: PipelineStage[] = [
  ["input", "Input validation"],
  ["ocr", "OCR / vision"],
  ["masking", "PII masking"],
  ["rules", "Rule signals"],
  ["retrieval", "Knowledge retrieval"],
  ["ai", "Gemini reasoning"],
  ["validation", "Response validation"],
  ["confidence", "Confidence calculation"],
  ["actions", "Action plan"],
  ["final", "Final result"],
].map(([key, label]) => ({ key, label, status: "PENDING", detail: "" }));

function errorDetails(error: unknown): { message: string; pipeline?: PipelineStage[] } {
  if (error instanceof ApiError) {
    const body = error.body as { detail?: string | { message?: string; pipeline?: PipelineStage[] } } | null;
    if (typeof body?.detail === "string") return { message: body.detail };
    return {
      message: body?.detail?.message ?? "The backend could not complete this request.",
      pipeline: body?.detail?.pipeline,
    };
  }
  return { message: error instanceof Error ? error.message : "The request could not be completed." };
}

export default function Home() {
  const [language, setLanguage] = useState<"en" | "ta">("en");
  const [translation, setTranslation] = useState<TamilTranslation | null>(null);
  const [translationStatus, setTranslationStatus] = useState<"IDLE" | "LOADING" | "SUCCESS" | "NOT_CONFIGURED" | "ERROR">("IDLE");
  const [mode, setMode] = useState<AnalysisMode>("live");
  const [inputTab, setInputTab] = useState<"paste" | "upload">("paste");
  const [text, setText] = useState("");
  const [maskedPreview, setMaskedPreview] = useState("");
  const [fileMeta, setFileMeta] = useState({ name: "", size: "", type: "" });
  const [ocrState, setOcrState] = useState<OcrResponse | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [stages, setStages] = useState<PipelineStage[]>(emptyStages);
  const [error, setError] = useState("");
  const [judgeOpen, setJudgeOpen] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const configQuery = useQuery({
    queryKey: ["pf-config"],
    queryFn: () => apiGet<ConfigResponse>("/config"),
    retry: false,
  });

  const ocrMutation = useMutation({
    mutationFn: async (file: File) => {
      const form = new FormData();
      form.append("file", file);
      return apiPostForm<OcrResponse>("/ocr", form);
    },
    onSuccess: (response) => {
      setOcrState(response);
      setStages(response.pipeline);
      setJudgeOpen(true);
      if (response.status === "SUCCESS") {
        setText(response.extracted_text);
        setError("");
        toast.success("Screenshot text extracted. Review and edit it before analysis.");
      } else {
        setError(response.warnings[0] ?? "We couldn't reliably read this screenshot. Please upload a clearer image or paste the rejection text.");
      }
    },
    onError: (requestError) => setError(errorDetails(requestError).message),
  });

  const maskMutation = useMutation({
    mutationFn: (input: { text: string }) => apiPost<MaskResponse>("/mask-preview", input),
  });

  const analysisMutation = useMutation({
    mutationFn: (input: { text: string; mode: AnalysisMode }) => apiPost<AnalysisResult>("/analyze-rejection", input),
    onSuccess: (response) => {
      setResult(response);
      setStages(response.pipeline);
      setTranslation(null);
      setTranslationStatus("IDLE");
      setError("");
      setJudgeOpen(true);
      toast.success(response.status === "DEMO" ? "Demo result ready — no live AI call was made." : "Analysis complete. Review the uncertainty before acting.");
    },
    onError: (requestError) => {
      const details = errorDetails(requestError);
      setError(details.message);
      if (details.pipeline) setStages(details.pipeline);
      setJudgeOpen(true);
    },
  });

  const translationMutation = useMutation({
    mutationFn: (diagnosis: AnalysisResult) => apiPost<{ translation: TamilTranslation }>("/translate-result", { diagnosis }),
    onSuccess: (response) => {
      setTranslation(response.translation);
      setTranslationStatus("SUCCESS");
    },
    onError: (requestError) => {
      const message = errorDetails(requestError).message;
      setTranslationStatus(message.toLowerCase().includes("not configured") ? "NOT_CONFIGURED" : "ERROR");
    },
  });

  const feedbackMutation = useMutation({
    mutationFn: (feedback: FeedbackRequest) => apiPost<FeedbackResponse>("/feedback", feedback),
  });

  const handleFile = (file?: File) => {
    if (!file) return;
    setFileMeta({ name: file.name, size: `${(file.size / 1024).toFixed(0)} KB`, type: file.type || "Unknown type" });
    setOcrState(null);
    setText("");
    setError("");
    ocrMutation.mutate(file);
  };

  const handleAnalyze = async () => {
    if (!text.trim()) {
      setError("Paste the rejection wording or upload a screenshot before continuing.");
      return;
    }
    setError("");
    setResult(null);
    setStages(emptyStages);
    try {
      const masked = await maskMutation.mutateAsync({ text });
      setMaskedPreview(masked.masked_text);
      await analysisMutation.mutateAsync({ text, mode });
    } catch {
      // Mutations own their truthful error and pipeline states.
    }
  };

  const handleLanguageToggle = () => {
    const next = language === "en" ? "ta" : "en";
    setLanguage(next);
    if (next === "ta" && result) {
      if (configQuery.data?.translation_available) {
        setTranslationStatus("LOADING");
        translationMutation.mutate(result);
      } else {
        setTranslationStatus("NOT_CONFIGURED");
      }
    }
  };

  const chooseSample = (sample: (typeof demoSamples)[number]) => {
    setMode("demo");
    setInputTab("paste");
    setText(sample.text);
    setMaskedPreview("");
    setError("");
    document.getElementById("workbench")?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const speak = () => {
    if (!result || !("speechSynthesis" in window)) {
      toast.error("Browser speech is unavailable on this device.");
      return;
    }
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(new SpeechSynthesisUtterance(`${result.issue_title}. ${result.plain_language_explanation}`));
  };

  const configured = configQuery.data?.gemini_configured === true;
  const liveLabel = configQuery.isPending ? "CHECKING" : configured ? "LIVE READY" : "NOT CONFIGURED";

  return (
    <div className="min-h-svh bg-[#f8fafc] text-slate-900" data-testid="pf-doctor-app">
      <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/90 backdrop-blur-xl" data-testid="app-header">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6">
          <a href="#top" className="flex items-center gap-3" data-testid="brand-link">
            <span className="brand-mark"><ShieldCheck size={18} /></span>
            <span><span className="block text-sm font-bold tracking-tight">PF Doctor</span><span className="block font-mono text-[9px] uppercase tracking-[0.2em] text-emerald-700">EPFO rejection decoder</span></span>
          </a>
          <nav className="hidden items-center gap-6 md:flex" data-testid="desktop-navigation">
            <a href="#workbench" data-testid="nav-analyze-link">Analyze</a>
            <a href="#how-it-works" data-testid="nav-how-link">How it works</a>
            <a href="#supported-issues" data-testid="nav-issues-link">Supported issues</a>
          </nav>
          <div className="flex items-center gap-2">
            <button className="language-toggle" onClick={handleLanguageToggle} data-testid="language-toggle"><Languages size={15} /> {language === "en" ? "தமிழ்" : "English"}</button>
            <button className="judge-toggle" onClick={() => setJudgeOpen(!judgeOpen)} data-testid="judge-mode-toggle"><Sparkles size={15} /> Judge Mode</button>
            <button className="icon-only md:hidden" aria-label="Open menu" data-testid="mobile-menu-button"><Menu size={18} /></button>
          </div>
        </div>
      </header>

      <main id="top" className="mx-auto max-w-7xl px-4 pb-20 pt-10 sm:px-6 lg:pt-16">
        <section className="grid items-end gap-8 lg:grid-cols-[1.2fr_0.8fr]" data-testid="hero-section">
          <div>
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1.5 font-mono text-[10px] font-bold uppercase tracking-widest text-emerald-800" data-testid="independent-badge"><span className="h-1.5 w-1.5 rounded-full bg-emerald-600" /> Independent assistance tool · V4.1</div>
            <h1 className="max-w-3xl text-4xl font-bold leading-[1.04] tracking-[-0.045em] text-slate-950 sm:text-6xl" data-testid="hero-title">Confusing rejection.<br /><span className="text-emerald-700">Clear next step.</span></h1>
            <p className="mt-6 max-w-2xl text-base leading-8 text-slate-600 sm:text-lg" data-testid="hero-description">PF Doctor turns EPFO rejection wording into evidence, uncertainty, and a practical action plan — without pretending to be EPFO.</p>
            <div className="mt-8 flex flex-wrap gap-3"><Button size="lg" onClick={() => document.getElementById("workbench")?.scrollIntoView({ behavior: "smooth" })} data-testid="hero-start-button">Start with rejection text <ArrowRight size={17} /></Button><a href="#how-it-works" className="inline-flex h-10 items-center rounded-md border border-slate-200 bg-white px-4 text-sm font-medium text-slate-700 shadow-sm" data-testid="hero-how-link">See how it works</a></div>
          </div>
          <div className="relative overflow-hidden rounded-2xl border border-slate-200 bg-slate-950 p-6 text-white shadow-xl" data-testid="hero-proof-card">
            <p className="font-mono text-[10px] uppercase tracking-[0.22em] text-emerald-300">The output is designed to show</p>
            <div className="mt-6 space-y-4">{[["01", "What was detected", "Facts before interpretation"], ["02", "Who acts next", "Employee · employer · EPFO"], ["03", "What is uncertain", "Human verification stays visible"]].map(([number, title, detail]) => <div className="flex gap-4" key={number} data-testid={`hero-proof-${number}`}><span className="font-mono text-xs text-emerald-400">{number}</span><div><p className="text-sm font-semibold">{title}</p><p className="mt-1 text-xs leading-5 text-slate-400">{detail}</p></div></div>)}</div>
          </div>
        </section>

        <section className="mt-14" id="workbench" data-testid="workbench">
          <div className="mb-5 flex flex-wrap items-end justify-between gap-4">
            <div><p className="eyebrow">Workbench / 01</p><h2 className="mt-2 text-2xl font-semibold tracking-tight sm:text-3xl" data-testid="workbench-title">Start with the message you received</h2></div>
            <div className="flex rounded-lg border border-slate-200 bg-white p-1 shadow-sm" data-testid="analysis-mode-switch">
              <button className={`mode-button ${mode === "live" ? "mode-active" : ""}`} onClick={() => setMode("live")} data-testid="live-ai-mode-button"><span className="mode-dot bg-emerald-500" /> Live AI</button>
              <button className={`mode-button ${mode === "demo" ? "mode-demo-active" : ""}`} onClick={() => setMode("demo")} data-testid="demo-mode-button"><span className="mode-dot bg-amber-500" /> Demo Mode</button>
            </div>
          </div>

          <div className={`mb-4 rounded-xl border p-3 text-sm ${configured ? "border-emerald-200 bg-emerald-50 text-emerald-900" : "border-amber-200 bg-amber-50 text-amber-950"}`} data-testid="live-ai-config-status">
            <strong>Live AI — {liveLabel}.</strong> {configured ? "Gemini analysis, vision OCR, and Tamil translation are available through the backend." : "Add GEMINI_API_KEY to the server environment to enable Gemini analysis, vision OCR, and Tamil translation. Demo Mode remains separate."}
          </div>

          <div className="grid items-start gap-6 lg:grid-cols-12">
            <div className="space-y-4 lg:col-span-5">
              <Card className="border-slate-200 shadow-sm" data-testid="input-card">
                <CardHeader className="p-6 pb-4">
                  <div className="flex items-start justify-between gap-3">
                    <div><CardTitle className="text-lg" data-testid="input-card-title">Your rejection</CardTitle><p className="mt-1 text-sm leading-6 text-slate-500" data-testid="input-card-description">Use the exact wording where possible. Basic masking runs before Live AI.</p></div>
                    <Badge variant={mode === "demo" ? "secondary" : "outline"} data-testid="input-mode-badge">{mode === "demo" ? "DEMO" : liveLabel}</Badge>
                  </div>
                  <div className="mt-5 flex border-b border-slate-200" data-testid="input-tabs">
                    <button className={`input-tab ${inputTab === "paste" ? "input-tab-active" : ""}`} onClick={() => setInputTab("paste")} data-testid="paste-text-tab"><ClipboardPaste size={15} /> Paste text</button>
                    <button className={`input-tab ${inputTab === "upload" ? "input-tab-active" : ""}`} onClick={() => setInputTab("upload")} data-testid="upload-screenshot-tab"><FileImage size={15} /> Upload screenshot</button>
                  </div>
                </CardHeader>
                <CardContent className="p-6 pt-0">
                  {inputTab === "paste" ? (
                    <div><Textarea className="min-h-52 resize-y border-slate-200 bg-slate-50/70 text-sm leading-7" value={text} onChange={(event) => { setText(event.target.value); setMaskedPreview(""); }} placeholder="Paste the rejection message here…" data-testid="rejection-text-input" /><p className="mt-2 text-xs text-slate-500" data-testid="text-privacy-hint">Do not paste passwords, OTPs, or full identity numbers. Basic masking is not perfect protection.</p></div>
                  ) : (
                    <div>
                      <button className="upload-zone" onClick={() => fileInputRef.current?.click()} disabled={ocrMutation.isPending} data-testid="upload-dropzone"><UploadCloud size={25} className="text-emerald-700" /><span className="mt-3 text-sm font-semibold">{ocrMutation.isPending ? "Inspecting screenshot…" : "Choose a screenshot"}</span><span className="mt-1 text-xs text-slate-500">PNG, JPG, JPEG, WEBP · max 8 MB</span>{fileMeta.name ? <span className="mt-4 rounded-lg bg-white px-3 py-2 font-mono text-xs text-slate-600" data-testid="uploaded-file-meta">{fileMeta.name} · {fileMeta.type} · {fileMeta.size}</span> : null}</button>
                      <input ref={fileInputRef} type="file" accept="image/png,image/jpeg,image/webp" className="hidden" onChange={(event) => handleFile(event.target.files?.[0])} data-testid="upload-screenshot-input" />
                      {ocrState ? <div className={`mt-3 rounded-lg border p-3 text-xs ${ocrState.status === "SUCCESS" ? "border-emerald-200 bg-emerald-50 text-emerald-800" : "border-amber-200 bg-amber-50 text-amber-900"}`} data-testid="ocr-status"><p className="font-semibold">OCR / vision: {ocrState.extraction_status}{ocrState.extraction_confidence !== "UNAVAILABLE" ? ` · ${ocrState.extraction_confidence}` : " · Quality assessment unavailable"}</p>{ocrState.warnings.map((warning) => <p className="mt-1 leading-5" key={warning}>{warning}</p>)}</div> : null}
                      {text ? <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-4" data-testid="extracted-text-review"><div className="flex items-center justify-between gap-3"><p className="font-mono text-[10px] font-bold uppercase tracking-widest text-slate-500">Extracted rejection text · review and edit</p><CheckCircle2 size={15} className="text-emerald-600" /></div><Textarea className="mt-3 min-h-36 bg-white text-sm leading-6" value={text} onChange={(event) => { setText(event.target.value); setMaskedPreview(""); }} data-testid="extracted-text-editor" /><button className="mt-2 text-xs font-semibold text-slate-500 hover:text-red-700" onClick={() => setText("")} data-testid="clear-extracted-text-button">Clear extracted text</button></div> : null}
                    </div>
                  )}

                  {maskedPreview ? <div className="mt-4 rounded-xl border border-blue-200 bg-blue-50/70 p-4" data-testid="masked-text-preview"><p className="font-mono text-[10px] font-bold uppercase tracking-widest text-blue-700">Basic PII masking preview</p><p className="mt-2 whitespace-pre-wrap text-xs leading-6 text-blue-950" data-testid="masked-text-content">{maskedPreview}</p></div> : null}
                  <Button className="mt-5 w-full" size="lg" onClick={handleAnalyze} disabled={analysisMutation.isPending || maskMutation.isPending || ocrMutation.isPending} data-testid="analyze-rejection-button">{analysisMutation.isPending ? "Running real pipeline…" : mode === "demo" ? "Run labelled demo" : "Analyze rejection"}<ArrowRight size={17} /></Button>
                  {error ? <div className="mt-4 flex gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm leading-6 text-red-900" role="alert" data-testid="analysis-error"><AlertTriangle size={17} className="mt-0.5 shrink-0" /><span>{error}</span></div> : null}
                </CardContent>
              </Card>

              <Card className="border-slate-200 bg-white/70 shadow-sm" data-testid="demo-samples-card"><CardHeader className="p-5 pb-3"><div className="flex items-center justify-between gap-3"><CardTitle className="text-sm">Try a labelled sample</CardTitle><span className="font-mono text-[10px] uppercase tracking-widest text-amber-700">Demo only</span></div></CardHeader><CardContent className="flex flex-wrap gap-2 p-5 pt-2">{demoSamples.map((sample) => <button className="sample-chip" key={sample.id} onClick={() => chooseSample(sample)} data-testid={`demo-sample-${sample.id}`}>{sample.label}</button>)}</CardContent></Card>
              <div className="rounded-xl border border-slate-200 bg-white/60 p-4 text-xs leading-6 text-slate-500" data-testid="privacy-notice"><div className="flex gap-2"><LockKeyhole size={15} className="mt-0.5 shrink-0 text-emerald-700" /><p><strong className="text-slate-700">Data minimization.</strong> Screenshots are processed in memory and not stored by PF Doctor. Basic automatic masking is applied before Live AI; it is not complete privacy protection.</p></div></div>
            </div>

            <div className="lg:col-span-7"><ResultPanel result={result} language={language} onPrint={() => window.print()} onSpeak={speak} translation={translation} translationStatus={translationStatus} onFeedback={(feedback) => feedbackMutation.mutateAsync(feedback).then(() => undefined)} inputText={text} /></div>
          </div>
        </section>

        {judgeOpen ? <section className="mt-6" data-testid="judge-mode-section"><PipelinePanel stages={stages} language={language} /></section> : null}

        <section className="mt-20 grid gap-6 lg:grid-cols-[0.85fr_1.15fr]" id="how-it-works" data-testid="how-it-works">
          <div><p className="eyebrow">Method / 02</p><h2 className="mt-2 max-w-md text-3xl font-semibold tracking-tight" data-testid="how-title">A diagnosis is only useful when its limits are visible.</h2><p className="mt-4 max-w-md text-sm leading-7 text-slate-600" data-testid="how-description">The system separates user-provided facts, deterministic signals, retrieved sources, AI interpretation, and what still needs a human.</p></div>
          <div className="grid gap-3 sm:grid-cols-2">{[["01", "Extract", "Read pasted text or use configured vision OCR."], ["02", "Mask", "Reduce exposure of common identifiers."], ["03", "Reason", "Combine signals, sources, and configured Gemini."], ["04", "Act", "Build a category-specific plan and checklist."]].map(([number, title, detail]) => <div className="method-card" key={number} data-testid={`method-step-${number}`}><span className="font-mono text-xs text-emerald-700">{number}</span><h3 className="mt-4 text-base font-semibold">{title}</h3><p className="mt-2 text-sm leading-6 text-slate-500">{detail}</p></div>)}</div>
        </section>

        <section className="mt-20" id="supported-issues" data-testid="supported-issues"><div className="mb-5"><p className="eyebrow">Coverage / 03</p><h2 className="mt-2 text-2xl font-semibold tracking-tight" data-testid="supported-issues-title">Supported issue families</h2></div><div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{Object.entries(CATEGORY_LABELS).map(([key, label]) => <div className="rounded-xl border border-slate-200 bg-white p-4" key={key} data-testid={`supported-category-${key}`}><p className="font-mono text-[10px] font-bold uppercase tracking-wider text-emerald-700">{key}</p><p className="mt-2 text-sm font-semibold">{label.en}</p><p className="mt-1 text-xs text-slate-500">{label.ta}</p></div>)}</div></section>
      </main>

      <footer className="border-t border-slate-200 bg-white" data-testid="app-footer"><div className="mx-auto flex max-w-7xl flex-col gap-5 px-4 py-8 sm:px-6 md:flex-row md:items-center md:justify-between"><div><p className="text-sm font-bold">PF Doctor</p><p className="mt-1 text-xs text-slate-500">Independent assistance for understanding PF claim rejection wording.</p></div><div className="flex items-center gap-4 text-xs text-slate-500"><a href="https://www.epfindia.gov.in" target="_blank" rel="noreferrer" data-testid="official-epfo-link">Official EPFO</a><span data-testid="footer-disclaimer">Not affiliated with EPFO · No approval guarantee</span></div></div></footer>
    </div>
  );
}