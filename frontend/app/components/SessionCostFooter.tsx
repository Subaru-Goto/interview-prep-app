export type SessionCost = {
  turns: number;
  prompt_tokens: number;
  completion_tokens: number;
  cost_usd: number;
  is_stub: boolean;
};

interface SessionCostFooterProps {
  sessionCost: SessionCost;
}

export function SessionCostFooter({ sessionCost }: SessionCostFooterProps) {
  const totalTokens = sessionCost.prompt_tokens + sessionCost.completion_tokens;
  const costLabel = sessionCost.is_stub
    ? "$0.00 (stub mode)"
    : `~$${sessionCost.cost_usd.toFixed(4)}`;

  return (
    <div className="pt-1 text-center text-[11px] text-faint">
      {sessionCost.turns} question{sessionCost.turns === 1 ? "" : "s"} ·{" "}
      {totalTokens.toLocaleString()} tokens · {costLabel}
    </div>
  );
}
