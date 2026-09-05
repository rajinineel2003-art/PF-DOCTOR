import { Check, CircleAlert, CircleDashed, LoaderCircle, Minus, X } from "lucide-react";
import type { PipelineStage, PipelineStatus } from "@/lib/pf";

interface PipelinePanelProps {
  stages: PipelineStage[];
  language: "en" | "ta";
}

const statusCopy: Record<PipelineStatus, { en: string; ta: string }> = {
  PENDING: { en: "Pending", ta: "நிலுவை" },
  RUNNING: { en: "Running", ta: "இயங்குகிறது" },
  SUCCESS: { en: "Success", ta: "வெற்றி" },
  FAILED: { en: "Failed", ta: "தோல்வி" },
  SKIPPED: { en: "Skipped", ta: "தவிர்க்கப்பட்டது" },
  NOT_CONFIGURED: { en: "Not configured", ta: "அமைக்கப்படவில்லை" },
};

function StatusIcon({ status }: { status: PipelineStatus }) {
  if (status === "SUCCESS") return <Check size={15} strokeWidth={2.5} />;
  if (status === "FAILED") return <X size={15} strokeWidth={2.5} />;
  if (status === "NOT_CONFIGURED") return <CircleAlert size={15} />;
  if (status === "RUNNING") return <LoaderCircle className="animate-spin" size={15} />;
  if (status === "SKIPPED") return <Minus size={15} />;
  return <CircleDashed size={15} />;
}

export default function PipelinePanel({ stages, language }: PipelinePanelProps) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white/80 p-5 shadow-sm backdrop-blur" data-testid="judge-mode-panel">
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <p className="eyebrow" data-testid="judge-mode-eyebrow">Judge Mode · execution trace</p>
          <h2 className="mt-1 text-lg font-semibold tracking-tight text-slate-900" data-testid="judge-mode-title">
            {language === "ta" ? "உண்மையான செயல்முறை நிலை" : "Truthful pipeline state"}
          </h2>
        </div>
        <span className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 font-mono text-[10px] font-bold uppercase tracking-widest text-slate-500" data-testid="judge-mode-live-badge">No fake progress</span>
      </div>
      <div className="space-y-2" data-testid="judge-mode-stage-list">
        {stages.map((stage) => {
          const copy = statusCopy[stage.status];
          return (
            <div className={`pipeline-row pipeline-${stage.status.toLowerCase()}`} key={stage.key} data-testid={`pipeline-stage-${stage.key}`}>
              <div className="flex min-w-0 items-center gap-3">
                <span className="pipeline-icon" data-testid={`pipeline-status-icon-${stage.key}`}><StatusIcon status={stage.status} /></span>
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-slate-800" data-testid={`pipeline-stage-label-${stage.key}`}>{stage.label}</p>
                  {stage.detail ? <p className="mt-0.5 truncate text-xs text-slate-500" data-testid={`pipeline-stage-detail-${stage.key}`}>{stage.detail}</p> : null}
                </div>
              </div>
              <span className="shrink-0 font-mono text-[10px] font-bold uppercase tracking-wider" data-testid={`pipeline-stage-status-${stage.key}`}>{language === "ta" ? copy.ta : copy.en}</span>
            </div>
          );
        })}
      </div>
    </section>
  );
}