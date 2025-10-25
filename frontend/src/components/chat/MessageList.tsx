import { useMemo, useState } from "react";
import { AudioPlayer } from "../AudioPlayer";
import { GenerateAudioButton } from "./GenerateAudioButton.tsx";
import type { Msg } from "../../lib/types";

type Props = {
  msgs: Msg[];
  isAssistantTyping: boolean;
  compactMode: boolean;
  sidebarCollapsed: boolean;
  onQuick: (text: string) => void;
  setMsgs: React.Dispatch<React.SetStateAction<Msg[]>>;
  // Editing controls (managed by parent Chat)
  editingIndex?: number | null;
  editText?: string;
  onEditStart?: (index: number, initial: string) => void;
  onEditChange?: (text: string) => void;
  onEditCancel?: () => void;
  onEditSave?: (index: number) => void;
  disableEditing?: boolean;
};

/** Detects if the assistant message is the addiction selection menu. */
function isAddictionMenu(content: string) {
  const lc = content.toLowerCase();
  return (
    lc.includes("i'm here to help with addiction concerns") ||
    lc.includes("what would you like support with today?")
  );
}

/** Detects the initial welcome quick-actions menu. */
function isWelcomeMenu(content: string) {
  const lc = content.toLowerCase();
  return (
    lc.includes("sleep coordinator") &&
    (lc.includes("here are some things you can try") ||
      lc.includes("predict tonight's sleep"))
  );
}

/**
 * Formats message content with very small markdown-like replacements.
 * Supports bold, italic, bullets, and newlines -> <br/>
 */
function formatMessage(content: string) {
  const html = content
    .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-cyan-300">$1</strong>')
    .replace(/\*(.*?)\*/g, '<em class="italic text-slate-300">$1</em>')
    .replace(/•/g, '<span class="text-cyan-400">•</span>')
    .replace(/\n/g, '<br/>');
  return (
    <div
      dangerouslySetInnerHTML={{ __html: html }}
      className="leading-relaxed whitespace-pre-wrap"
    />
  );
}

// Heuristics to detect long, plan-like coaching responses
function isLongPlan(content: string | undefined) {
  if (!content) return false;
  const lc = content.toLowerCase();
  const hasPlanKeywords = [
    "priority action plan",
    "this week's focus",
    "7-day",
    "7 day",
    "optimization tips",
    "progress tracking",
    "reduction plan",
  ].some((k) => lc.includes(k));
  return hasPlanKeywords || content.length > 800 || content.split("\n").length > 18;
}

// Create a concise summary: take 4-6 most actionable bullet points
function summarizePlan(content: string): string {
  const lines = content.split("\n").map((l) => l.trim()).filter(Boolean);

  // Specialized summarization for addiction reduction plans
  if (/reduction plan/i.test(content)) {
    // Split into sections by markdown headers like "### 🎯 Alcohol Reduction Plan"
    const sections = content.split(/\n(?=#+\s)/).map((s) => s.trim());
    const summaryBullets: string[] = [];
    for (const sec of sections) {
      const headerMatch = sec.match(/###\s*[^\n]*?([A-Za-z]+)\s+Reduction Plan/i);
      if (!headerMatch) continue;
      const substance = headerMatch[1];
      const timeline = (sec.match(/\*\*Timeline\*\*:\s*([^\n]+)/i)?.[1] || "").trim();

      // Collect first 1-2 steps
      const stepLines = sec.split("\n").filter((l) => /^(\d+\.|[-•])\s/.test(l));
      const steps = stepLines
        .slice(0, 2)
        .map((l) => l.replace(/^(\d+\.|[-•])\s+/, "").trim())
        .filter(Boolean);

      const parts = [] as string[];
      if (timeline) parts.push(timeline);
      if (steps.length) parts.push(steps.join("; "));
      if (parts.length) {
        summaryBullets.push(`• ${substance}: ${parts.join(" — ")}`);
      }
    }

    if (summaryBullets.length) {
      return `Here’s a quick summary:\n\n${summaryBullets.join("\n")}`;
    }
  }

  // Prefer bullets after the Priority Action Plan or This Week's Focus section
  const startIdx = lines.findIndex((l) => /priority action plan|this week's focus/i.test(l));
  const scanFrom = startIdx >= 0 ? startIdx : 0;

  const bullets: string[] = [];
  for (let i = scanFrom; i < lines.length && bullets.length < 6; i++) {
    const l = lines[i];
    if (/^(\d+\.|[-•])\s/.test(l)) {
      // Strip numbering/bullet symbol for compactness
      const compact = l.replace(/^(\d+\.|[-•])\s+/, "");
      bullets.push(`• ${compact}`);
    }
  }

  // Fallback: take first 2-3 sentences if no bullets found
  if (bullets.length === 0) {
    const text = lines.join(" ");
    const sentences = text.split(/(?<=[.!?])\s+/).slice(0, 3).join(" ");
    return `Here’s a quick summary:\n\n${sentences}`;
  }

  const header = "Here’s your quick plan summary:";
  const body = bullets.slice(0, 5).join("\n");
  return `${header}\n\n${body}`;
}

// Only show summary for specific agents (sleep plan = coach, and information)
function allowSummaryForAgent(msg: Msg): boolean {
  const agent = (msg?.data as any)?.agent?.toString().toLowerCase();
  return agent === "coach" || agent === "information";
}

function shouldSummarize(msg: Msg): boolean {
  return allowSummaryForAgent(msg) && isLongPlan(msg.content);
}

/**
 * MessageList renders chat bubbles and related actions (edit last user message,
 * quick action menus, audio generation). It also conditionally summarizes long
 * assistant plans and lets users expand/collapse details.
 */
export function MessageList({
  msgs,
  isAssistantTyping,
  compactMode,
  sidebarCollapsed,
  onQuick,
  setMsgs,
  editingIndex = null,
  editText = "",
  onEditStart,
  onEditChange,
  onEditCancel,
  onEditSave,
  disableEditing,
}: Props) {
  const [collapsed, setCollapsed] = useState<Record<number, boolean>>({});
  const bubbleBase = useMemo(
    () =>
      compactMode
        ? "rounded-xl px-3 py-2 text-[13px] leading-[1.45]"
        : "rounded-2xl px-4 py-3 text-sm leading-relaxed",
    [compactMode]
  );
  const lastUserIndex = useMemo(() => {
    for (let j = msgs.length - 1; j >= 0; j--) {
      if (msgs[j].role === 'user') return j;
    }
    return -1;
  }, [msgs]);

  return (
    <>
      {msgs.map((m, i) => (
        <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
          <div
            className={`${sidebarCollapsed ? 'max-w-[min(98%,760px)]' : 'max-w-[min(96%,760px)]'} ${bubbleBase} ${
              m.role === "user"
                ? "bg-gradient-to-r from-indigo-600 to-cyan-600 text-white shadow-lg"
                : "bg-slate-800/80 border border-slate-700/50 text-slate-100 shadow-md"
            }`}
          >
            {m.role === "assistant" ? (
              <div className={compactMode ? "space-y-2" : "space-y-3"}>
                <div className={compactMode ? "text-[13px] leading-[1.55]" : "text-sm leading-relaxed"}>
                  {m.content ? (
                    shouldSummarize(m) && (collapsed[i] ?? true)
                      ? (
                          <>
                            {formatMessage(summarizePlan(m.content))}
                            <div className="mt-2">
                              <button
                                onClick={() => setCollapsed((prev) => ({ ...prev, [i]: false }))}
                                className="text-xs text-cyan-300 hover:text-white underline"
                              >
                                {((m.data as any)?.agent?.toString().toLowerCase() === 'coach') ? 'Show full plan' : 'Show full message'}
                              </button>
                            </div>
                          </>
                        )
                      : (
                          <>
                            {formatMessage(m.content)}
                            {shouldSummarize(m) && (
                              <div className="mt-2">
                                <button
                                  onClick={() => setCollapsed((prev) => ({ ...prev, [i]: true }))}
                                  className="text-xs text-cyan-300 hover:text-white underline"
                                >
                                  Show less
                                </button>
                              </div>
                            )}
                          </>
                        )
                  ) : isAssistantTyping ? (
                    <div className="flex items-center gap-2 text-slate-400">
                      <div className="flex gap-1">
                        <div className="w-2 h-2 bg-slate-400 rounded-full animate-pulse"></div>
                        <div className="w-2 h-2 bg-slate-400 rounded-full animate-pulse [animation-delay:0.2s]"></div>
                        <div className="w-2 h-2 bg-slate-400 rounded-full animate-pulse [animation-delay:0.4s]"></div>
                      </div>
                    </div>
                  ) : (
                    <span className="text-slate-500">...</span>
                  )}
                </div>

                {m.content && isAddictionMenu(m.content) && (
                  <div className="flex flex-wrap gap-2 pt-1">
                    {[
                      { label: "☕ Caffeine", value: "I'm addicted to caffeine" },
                      { label: "🍷 Alcohol", value: "I'm addicted to alcohol" },
                      { label: "🚬 Nicotine", value: "I'm addicted to nicotine/tobacco" },
                      { label: "📱 Digital/Screen", value: "I'm addicted to digital/screen time" },
                    ].map((opt, idx) => (
                      <button
                        key={idx}
                        onClick={() => onQuick(opt.value)}
                        className="text-xs text-indigo-300 hover:text-white bg-indigo-500/10 hover:bg-indigo-500/20 px-3 py-1.5 rounded-lg border border-indigo-400/20 transition-colors"
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                )}

                {m.content && isWelcomeMenu(m.content) && (
                  <div className="flex flex-wrap gap-2 pt-2">
                    <div className="w-full text-xs text-slate-400 mb-1">💡 Quick Actions:</div>
                    {[
                      { label: " Predict Tonight", value: "How will I sleep tonight?", color: "purple" },
                      { label: " Optimal Bedtime", value: "What's my optimal bedtime?", color: "blue" },
                      { label: " Analyze 7 Days", value: "Analyze my last 7 days", color: "green" },
                      { label: " Sleep Tips", value: "Give me a 7-day improvement plan", color: "yellow" },
                      { label: " Bedtime Story", value: "Tell me a bedtime story", color: "pink" },
                      // Information agent
                      { label: "ℹ Caffeine Info", value: "Explain how caffeine affects sleep", color: "blue" },
                      // Nutrition (personalized from logs)
                      { label: " From My Logs: Caffeine", value: "Based on my logs, when should I have my last coffee?", color: "green" },
                      { label: " Reduce Screens Plan", value: "Based on my logs, help me reduce screen time before bed", color: "yellow" },
                      // Addiction agent
                      { label: " Quit Alcohol Help", value: "I'm addicted to alcohol; help me make a safe reduction plan", color: "purple" },
                      { label: " Quit Caffeine", value: "I'm addicted to caffeine; help me quit", color: "pink" },
                    ].map((opt, idx) => (
                      <button
                        key={idx}
                        onClick={() => onQuick(opt.value)}
                        className={`text-xs hover:text-white px-3 py-1.5 rounded-lg border transition-colors ${
                          opt.color === "purple"
                            ? "text-purple-300 bg-purple-500/10 hover:bg-purple-500/20 border-purple-400/20"
                            : opt.color === "blue"
                            ? "text-blue-300 bg-blue-500/10 hover:bg-blue-500/20 border-blue-400/20"
                            : opt.color === "green"
                            ? "text-green-300 bg-green-500/10 hover:bg-green-500/20 border-green-400/20"
                            : opt.color === "yellow"
                            ? "text-yellow-300 bg-yellow-500/10 hover:bg-yellow-500/20 border-yellow-400/20"
                            : "text-pink-300 bg-pink-500/10 hover:bg-pink-500/20 border-pink-400/20"
                        }`}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                )}

                {m.audioId && (
                  <AudioPlayer
                    audioData={{
                      available: true,
                      file_id: m.audioId,
                      metadata: {
                        estimated_duration_minutes: Math.ceil(((m.content || "").split(" ").length || 0) / 130),
                        estimated_duration_seconds:
                          Math.ceil(((m.content || "").split(" ").length || 0) / 130) * 60,
                        word_count: (m.content || "").split(" ").filter(Boolean).length,
                      },
                    }}
                  />
                )}

                {/* Generate Audio Button for Storyteller */}
                <GenerateAudioButton message={m} messageIndex={i} setMsgs={setMsgs} />
              </div>
            ) : (
              <div className={compactMode ? "text-[13px] leading-[1.55] font-medium" : "text-sm font-medium"}>
                {editingIndex === i ? (
                  <div className="space-y-2">
                    <textarea
                      className={`w-full bg-slate-900/60 border border-slate-600/50 ${compactMode ? 'p-2.5 rounded-lg text-[13px]' : 'p-3 rounded-xl text-sm'} focus:outline-none focus:ring-2 focus:ring-indigo-400/20`}
                      rows={compactMode ? 3 : 4}
                      value={editText}
                      onChange={(e) => onEditChange?.(e.target.value)}
                    />
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => onEditSave?.(i)}
                        className="text-xs px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white"
                      >Save</button>
                      <button
                        onClick={() => onEditCancel?.()}
                        className="text-xs px-3 py-1.5 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-200"
                      >Cancel</button>
                    </div>
                  </div>
                ) : (
                  <div className="relative group">
                    <div>{m.content}</div>
                    {i === lastUserIndex && !disableEditing && (
                      <button
                        onClick={() => onEditStart?.(i, m.content)}
                        className="absolute -top-2 -right-2 opacity-0 group-hover:opacity-100 text-[11px] px-2 py-0.5 rounded-md bg-slate-700 text-slate-200 border border-slate-600/60 transition-opacity"
                        title="Edit message"
                      >Edit</button>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      ))}
    </>
  );
}
