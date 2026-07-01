import { Header } from "./Header";

interface SetupViewProps {
  status: string;
  isUsable: boolean;
  onUpload: (file: File) => void;
  jobDescription: string;
  onJobDescriptionChange: (value: string) => void;
  maxJd: number;
  canStart: boolean;
  isStarting: boolean;
  startHint: string;
  startError: string;
  onStart: () => void;
}

export function SetupView({
  status,
  isUsable,
  onUpload,
  jobDescription,
  onJobDescriptionChange,
  maxJd,
  canStart,
  isStarting,
  startHint,
  startError,
  onStart,
}: SetupViewProps) {
  return (
    <div className="flex h-dvh w-full flex-col font-sans">
      <div className="shrink-0 bg-surface">
        <Header />
      </div>

      {/* Form fills the width, below the app bar */}
      <div className="flex-1 overflow-y-auto bg-canvas px-4 py-8 sm:px-6">
        <div className="w-full">
          <h1 className="font-display text-2xl font-bold tracking-tight text-ink">
            Set up your interview
          </h1>
          <p className="mt-1.5 text-sm leading-relaxed text-muted">
            Two inputs and we&apos;ll tailor a screen to you.
          </p>

          {/* CV upload */}
          <div className="mt-7">
            <div className="text-[13px] font-semibold text-ink">Your CV</div>
            {isUsable ? (
              <div className="mt-2.5 flex w-fit items-center gap-2 rounded-lg bg-success-bg px-3 py-2 text-xs font-medium text-success">
                <span className="font-bold">✓</span>
                CV parsed — ready to go
              </div>
            ) : (
              <label className="mt-2.5 flex cursor-pointer items-center justify-center rounded-lg border border-line-strong bg-surface px-4 py-4 text-[13px] text-muted transition-colors hover:border-primary hover:text-primary">
                <input
                  type="file"
                  accept="application/pdf"
                  className="hidden"
                  onChange={(e) =>
                    e.target.files?.[0] && onUpload(e.target.files[0])
                  }
                />
                Upload your CV (PDF)
              </label>
            )}
            {status && !isUsable && (
              <p className="mt-2 text-xs text-warning">{status}</p>
            )}
          </div>

          {/* Job description */}
          <div className="mt-7">
            <div className="text-[13px] font-semibold text-ink">
              Job description
            </div>
            <textarea
              placeholder="Paste the job description you're interviewing for…"
              value={jobDescription}
              maxLength={maxJd}
              onChange={(e) => onJobDescriptionChange(e.target.value)}
              className="mt-2.5 h-36 w-full resize-none rounded-[10px] border border-line-strong bg-surface p-3.5 text-[13px] leading-relaxed text-body outline-none placeholder:text-faint focus:border-primary"
            />
            <div className="mt-1 text-right text-[11px] text-faint">
              {jobDescription.length} / {maxJd}
            </div>
          </div>

          {/* Start */}
          <div className="mt-6 flex flex-col items-center gap-2.5">
            <button
              disabled={!canStart || isStarting}
              onClick={onStart}
              className="w-full rounded-[10px] bg-primary py-3 text-sm font-semibold text-white shadow-lg shadow-primary/30 transition-opacity hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {isStarting ? "Starting…" : "Start interview →"}
            </button>
            {startError ? (
              <span className="text-[11.5px] text-warning">{startError}</span>
            ) : (
              <span className="text-[11.5px] text-faint">
                {startHint || "~8–12 questions · about 15 min"}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
