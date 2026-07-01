import type { ReactNode } from "react";

export function Header({ right }: { right?: ReactNode }) {
  return (
    <div className="flex items-center justify-between border-b border-line px-5 py-3.5">
      <div className="flex items-center gap-2">
        <span className="h-[18px] w-[18px] rounded-[5px] bg-primary" />
        <span className="text-sm font-bold tracking-tight text-ink">
          Interview Prep
        </span>
      </div>
      {right}
    </div>
  );
}
