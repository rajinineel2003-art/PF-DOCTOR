import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import type { FeedbackRequest } from "@/lib/pf";

interface FeedbackCardProps {
  category: FeedbackRequest["category"];
  technicalStatus: string;
  onSubmit: (feedback: FeedbackRequest) => Promise<void>;
}

export default function FeedbackCard({ category, technicalStatus, onSubmit }: FeedbackCardProps) {
  const [helpful, setHelpful] = useState<boolean | null>(null);
  const [feedbackText, setFeedbackText] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState("");
  if (submitted) return <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900" data-testid="feedback-success">Rating recorded. Your optional free-text comment was not stored for privacy.</div>;
  const submit = async () => {
    if (helpful === null) { setError("Choose Yes or No before sending."); return; }
    try { setError(""); await onSubmit({ category, helpful, feedback_text: feedbackText, app_version: "4.1", technical_status: technicalStatus }); setSubmitted(true); } catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Feedback could not be sent."); }
  };
  return <section className="rounded-xl border border-slate-200 bg-slate-50 p-5" data-testid="feedback-card"><p className="text-sm font-semibold text-slate-800" data-testid="feedback-question">Was this helpful?</p><p className="mt-1 text-xs leading-5 text-slate-500" data-testid="feedback-privacy-warning">Please do not include UAN, Aadhaar, PAN, bank details, phone numbers, names, or emails.</p><div className="mt-3 flex gap-2"><Button size="sm" variant={helpful === true ? "default" : "outline"} onClick={() => setHelpful(true)} data-testid="feedback-yes-button">Yes</Button><Button size="sm" variant={helpful === false ? "default" : "outline"} onClick={() => setHelpful(false)} data-testid="feedback-no-button">No</Button></div><Textarea className="mt-3 min-h-20 bg-white text-sm" maxLength={1000} value={feedbackText} onChange={(event) => setFeedbackText(event.target.value)} placeholder="Optional: what could we improve?" data-testid="feedback-text-input" /><div className="mt-3 flex items-center justify-between gap-3"><span className="text-xs text-slate-500">Optional · max 1000 characters</span><Button size="sm" onClick={submit} data-testid="feedback-submit-button">Send feedback</Button></div>{error ? <p className="mt-2 text-xs text-red-700" data-testid="feedback-error">{error}</p> : null}</section>;
}