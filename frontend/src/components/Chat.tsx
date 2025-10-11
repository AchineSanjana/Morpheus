import { useEffect, useRef, useState } from "react";
import { supabase } from "../lib/supabaseClient";
import { streamChat, listConversations, getConversationMessages, renameConversation, deleteConversation, recoverConversations } from "../lib/api";
import { AudioPlayer } from "./AudioPlayer";
import { useLayout } from "../lib/LayoutContext";

type Msg = { 
  role: "user" | "assistant"; 
  content: string; 
  responsibleAIChecks?: Record<string, any>;
  responsibleAIPassed?: boolean;
  responsibleAIRiskLevel?: string;
  data?: Record<string, any>;
  audioId?: string;  // For generated audio
};

// Component for the Generate Audio button
function GenerateAudioButton({ message, messageIndex, setMsgs }: { 
  message: Msg; 
  messageIndex: number; 
  setMsgs: React.Dispatch<React.SetStateAction<Msg[]>>; 
}) {
  const [isGenerating, setIsGenerating] = useState(false);
  
  // Check if this is a storyteller response that can have audio
  const isStorytellerResponse = message.data?.agent === "storyteller";
  
  // Don't show button if audio already generated or not a story
  if (!isStorytellerResponse || message.audioId || !message.content.trim()) {
    return null;
  }

  const generateAudio = async () => {
    setIsGenerating(true);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        throw new Error("Please sign in to generate audio");
      }

      const response = await fetch(`${import.meta.env.VITE_API_URL}/audio/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({ text: message.content })
      });

      if (!response.ok) {
        throw new Error('Failed to generate audio');
      }

      const audioData = await response.json();

      // Update the message with audio ID
      setMsgs(msgs => {
        const updatedMsgs = [...msgs];
        updatedMsgs[messageIndex] = { 
          ...updatedMsgs[messageIndex], 
          audioId: audioData.audio_id 
        };
        return updatedMsgs;
      });

    } catch (error: any) {
      console.error('Audio generation error:', error);
      alert(error.message || 'Failed to generate audio');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="mt-3">
      <button
        onClick={generateAudio}
        disabled={isGenerating}
        className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 disabled:from-gray-600 disabled:to-gray-700 text-white text-sm font-medium rounded-lg transition-all duration-200 shadow-lg hover:shadow-xl disabled:cursor-not-allowed"
      >
        {isGenerating ? (
          <>
            <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
            <span>Generating Audio...</span>
          </>
        ) : (
          <>
            <span className="text-lg">🎵</span>
            <span>Generate Audio</span>
          </>
        )}
      </button>
    </div>
  );
}

export function Chat() {
  const { fullWidthChat, compactMode, sidebarCollapsed, toggleFullWidthChat, toggleCompactMode, toggleSidebarCollapsed } = useLayout();
  const [msgs, setMsgs] = useState<Msg[]>([
    { 
      role: "assistant", 
      content: "Hi! I'm your sleep coordinator. 🌙\n\nLog last night below, or ask me to:\n• **Analyze my last 7 days**\n• **Make me a sleep plan**\n• **Tell me about caffeine and sleep**"
    }
  ]);
  const [input, setInput] = useState(""); 
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<{type:"idle"|"typing"|"error";msg?:string}>({type:"idle"});
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [conversationTitle, setConversationTitle] = useState<string | null>(null);
  const [conversations, setConversations] = useState<{ id: string; title: string; updated_at: string }[]>([]);
  const [showDrawer, setShowDrawer] = useState(false);
  const viewport = useRef<HTMLDivElement>(null);
  
  useEffect(() => { 
    viewport.current?.scrollTo({ top: 9e9, behavior: "smooth" }); 
  }, [msgs]);

  const isAssistantTyping = loading && msgs[msgs.length - 1]?.role === "assistant" && !msgs[msgs.length - 1]?.content;

  function timeAgo(iso?: string) {
    if (!iso) return "";
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "just now";
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    const days = Math.floor(hrs / 24);
    return `${days}d ago`;
  }

  async function refreshConversations() {
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) return;
      const list = await listConversations(session.access_token);
      // Sort by updated_at desc (backend already does, we re-assert)
      setConversations(list.sort((a,b) => (b.updated_at || '').localeCompare(a.updated_at || '')));
    } catch (e) {
      // ignore
    }
  }

  useEffect(() => { refreshConversations(); }, []);

  // Welcome message factory
  function getWelcome(): Msg[] {
    return [
      { 
        role: "assistant", 
        content: "Hi! I'm your sleep coordinator. 🌙\n\nLog last night below, or ask me to:\n• **Analyze my last 7 days**\n• **Make me a sleep plan**\n• **Tell me about caffeine and sleep**"
      }
    ];
  }

  // Load last active conversation from localStorage
  useEffect(() => {
    const lastId = localStorage.getItem('activeConversationId');
    const lastTitle = localStorage.getItem('activeConversationTitle');
    if (lastId) {
      setConversationId(lastId);
      setConversationTitle(lastTitle);
      // Attempt to load existing conversation
      loadConversation(lastId);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Persist active conversation to localStorage
  useEffect(() => {
    if (conversationId) localStorage.setItem('activeConversationId', conversationId);
    else localStorage.removeItem('activeConversationId');
  }, [conversationId]);

  useEffect(() => {
    if (conversationTitle) localStorage.setItem('activeConversationTitle', conversationTitle);
    else localStorage.removeItem('activeConversationTitle');
  }, [conversationTitle]);

  async function loadConversation(id: string) {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) return;
    try {
      const res = await getConversationMessages(session.access_token, id);
      const loadedMsgs: Msg[] = res.messages.map(m => ({ role: m.role, content: m.content, data: { agent: m.agent } }));
      setMsgs(loadedMsgs);
      setConversationId(id);
      const conv = conversations.find(c => c.id === id);
      setConversationTitle(conv?.title ?? null);
    } catch (e: any) {
      // If conversation cannot be loaded (e.g., 404/401), try recovery once on 404 then retry
      const statusCode = e?.status ?? undefined;
      if (statusCode === 404) {
        try {
          const { data: { session } } = await supabase.auth.getSession();
          if (session) {
            const result = await recoverConversations(session.access_token);
            if (result?.recovered > 0) {
              await refreshConversations();
              // Retry fetch after recovery
              const res = await getConversationMessages(session.access_token, id);
              const loadedMsgs: Msg[] = res.messages.map(m => ({ role: m.role, content: m.content, data: { agent: m.agent } }));
              setMsgs(loadedMsgs);
              setConversationId(id);
              const conv = conversations.find(c => c.id === id);
              setConversationTitle(conv?.title ?? null);
              return;
            }
          }
        } catch (re) {
          // fall through to show error
        }
      }
      if (statusCode === 401) {
        setStatus({ type: 'error', msg: 'Session expired. Please sign in again.' });
      } else if (statusCode === 404) {
        setStatus({ type: 'error', msg: 'Conversation not found (it may have been deleted).' });
      } else {
        setStatus({ type: 'error', msg: e?.message || 'Failed to load conversation' });
      }
      setConversationId(null);
      setConversationTitle(null);
      setMsgs(getWelcome());
      localStorage.removeItem('activeConversationId');
      localStorage.removeItem('activeConversationTitle');
    }
  }

  async function sendInternal(text: string) {
    if (!text.trim() || loading) return;
    setStatus({type:"idle"});

    setMsgs(m => [...m, {role: "user", content: text}, {role: "assistant", content: ""}]);

    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
      setStatus({type:"error", msg:"Please sign in first"});
      // Remove the empty assistant message we just appended
      setMsgs(m => m.slice(0, -2));
      return;
    }

    setLoading(true);
    setStatus({type:"typing", msg:"AI is thinking..."});

    try {
      await streamChat(text, session.access_token, (chunk, responsibleAIData, data) => {
        setMsgs(m => {
          const copy = [...m];
          const prev = copy[copy.length - 1];
          const updated: Msg = {
            ...prev,
            role: "assistant",
            content: (prev?.content || "") + chunk,
            responsibleAIChecks: responsibleAIData?.responsibleAIChecks ?? prev.responsibleAIChecks,
            responsibleAIPassed: responsibleAIData?.responsibleAIPassed ?? prev.responsibleAIPassed,
            responsibleAIRiskLevel: responsibleAIData?.responsibleAIRiskLevel ?? prev.responsibleAIRiskLevel,
            data: (responsibleAIData || data) ? {
              ...(prev.data || {}),
              ...(data || {}),
              ...(responsibleAIData ? { responsibleAI: responsibleAIData } : {}),
            } : prev.data
          };
          copy[copy.length - 1] = updated;
          return copy;
        });
        // Capture conversation_id and title from first metadata
        if (data?.conversation_id && !conversationId) {
          setConversationId(data.conversation_id);
        }
        if (data?.conversation_title && !conversationTitle) {
          setConversationTitle(data.conversation_title);
        }
      }, conversationId);
      // Refresh list after message stored
      refreshConversations();
      setStatus({type:"idle"});
    } catch (e: any) {
      setStatus({type:"error", msg: e.message || "Something went wrong"});
      // Remove the empty assistant message on error
      setMsgs(m => m.slice(0, -1));
    }
    setLoading(false);
  }

  async function sendInput() {
    const text = input.trim();
    if (!text) return;
    setInput("");
    await sendInternal(text);
  }

  async function sendQuick(text: string) {
    await sendInternal(text);
  }

  function formatMessage(content: string) {
    // Markdown-like formatting and explicit <br/> for newlines
    const html = content
      .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-cyan-300">$1</strong>')
      .replace(/\*(.*?)\*/g, '<em class="italic text-slate-300">$1</em>')
      .replace(/•/g, '<span class="text-cyan-400">•</span>')
      .replace(/\n/g, '<br/>');
    return <div dangerouslySetInnerHTML={{ __html: html }} className="leading-relaxed whitespace-pre-wrap" />;
  }

  // Detect if a message is the generic addiction support menu
  function isAddictionMenu(content: string) {
    const lc = content.toLowerCase();
    return lc.includes("i'm here to help with addiction concerns") || lc.includes("what would you like support with today?");
  }

  const bubbleBase = compactMode ? 'rounded-xl px-3 py-2 text-[13px] leading-[1.45]' : 'rounded-2xl px-4 py-3 text-sm leading-relaxed';
  const containerHeight = compactMode ? 'h-[82vh]' : 'h-[78vh]';
  const messageGap = compactMode ? 'space-y-3' : 'space-y-4';

  return (
    <div className="relative">
      {/* Background gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-indigo-400/10 via-transparent to-cyan-400/10 rounded-2xl blur-xl"></div>
      
  <div className={`relative flex flex-col md:flex-row ${containerHeight} bg-gradient-to-br from-slate-900/95 to-slate-800/95 backdrop-blur-sm border border-slate-700/50 rounded-2xl shadow-2xl shadow-black/20`}>
        {/* Sidebar: Conversations */}
        <div className={`${sidebarCollapsed ? 'hidden' : 'hidden md:flex'} md:w-80 flex-col border-r border-slate-700/50 p-3 gap-2 overflow-y-auto`} aria-label="Conversations">
          <div className="flex items-center justify-between mb-1">
            <div className="text-slate-300 text-sm font-semibold">Conversations</div>
            <button
              onClick={() => { setConversationId(null); setConversationTitle(null); setMsgs(getWelcome()); localStorage.removeItem('activeConversationId'); localStorage.removeItem('activeConversationTitle'); }}
              className="text-xs text-cyan-300 hover:text-white"
            >New</button>
          </div>
          <div className="flex flex-col gap-1">
            {conversations.length === 0 && (
              <div className="text-[11px] text-slate-400 px-2 py-3">No conversations yet. Start a new one!</div>
            )}
            {conversations.map(c => (
              <div key={c.id} className={`group rounded-lg px-3 py-2 text-xs cursor-pointer ${conversationId===c.id? 'bg-slate-800/80 border border-slate-700/50' : 'hover:bg-slate-800/40'}`}>
                <div className="flex items-center gap-2" onClick={() => loadConversation(c.id)}>
                  <div className="flex-1 min-w-0">
                    <div className="truncate text-slate-200" title={c.title}>{c.title || 'Untitled'}</div>
                    <div className="text-[10px] text-slate-400">{timeAgo(c.updated_at)}</div>
                  </div>
                  <div className="flex items-center gap-1 opacity-60 group-hover:opacity-100">
                    <button aria-label="Rename" title="Rename" className="text-[10px] text-indigo-300 hover:text-white" onClick={async (e) => { e.stopPropagation(); const title = prompt('Rename conversation', c.title); if (title) { const { data: { session } } = await supabase.auth.getSession(); if (session) { await renameConversation(session.access_token, c.id, title); refreshConversations(); if (conversationId===c.id) setConversationTitle(title); } } }}>Rename</button>
                    <button aria-label="Delete" title="Delete" className="text-[10px] text-rose-300 hover:text-white" onClick={async (e) => { e.stopPropagation(); if (confirm('Delete conversation?')) { const { data: { session } } = await supabase.auth.getSession(); if (session) { await deleteConversation(session.access_token, c.id); refreshConversations(); if (conversationId===c.id) { setConversationId(null); setMsgs(getWelcome()); setConversationTitle(null);} } } }}>Delete</button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
        {/* Right panel: header + messages + status + input stacked */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Header */}
          <div className={`flex items-center gap-3 ${compactMode ? 'p-3' : 'p-4'} border-b border-slate-700/50`}>
            <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-cyan-500 rounded-full flex items-center justify-center text-white text-sm font-bold">🤖</div>
            <div className="flex flex-col">
              <h3 className={`${compactMode ? 'text-base' : 'text-lg'} font-semibold bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent`}>
                {conversationTitle || 'Sleep Coach Chat'}
              </h3>
              {/* Chat ID hidden intentionally */}
            </div>
            {/* Mobile: open history */}
            <div className="ml-auto flex items-center gap-2">
              <button className="md:hidden text-xs text-cyan-300 hover:text-white border border-cyan-400/30 rounded px-2 py-1" onClick={() => setShowDrawer(true)} aria-label="History">History</button>
              {/* md+ controls */}
              <button className="hidden md:inline text-xs text-slate-300 hover:text-white border border-slate-400/30 rounded px-2 py-1" onClick={toggleSidebarCollapsed} aria-label="Toggle sidebar">
                {sidebarCollapsed ? 'Show Sidebar' : 'Hide Sidebar'}
              </button>
              <button className="text-xs text-cyan-300 hover:text-white border border-cyan-400/30 rounded px-2 py-1" onClick={toggleFullWidthChat} aria-label="Full width">
                {fullWidthChat ? 'Exit Full Width' : 'Full Width'}
              </button>
              <button className="text-xs text-indigo-300 hover:text-white border border-indigo-400/30 rounded px-2 py-1" onClick={toggleCompactMode} aria-label="Compact mode">
                {compactMode ? 'Comfort Mode' : 'Compact Mode'}
              </button>
              {conversationId && (
                <>
                  <button className="text-xs text-indigo-300 hover:text-white border border-indigo-400/30 rounded px-2 py-1" onClick={async () => { const title = prompt('Rename conversation', conversationTitle || ''); if (title) { const { data: { session } } = await supabase.auth.getSession(); if (session) { await renameConversation(session.access_token, conversationId, title); setConversationTitle(title); refreshConversations(); } } }} aria-label="Rename">Rename</button>
                  <button className="text-xs text-rose-300 hover:text-white border border-rose-400/30 rounded px-2 py-1" onClick={async () => { if (confirm('Delete conversation?')) { const { data: { session } } = await supabase.auth.getSession(); if (session) { await deleteConversation(session.access_token, conversationId); setConversationId(null); setConversationTitle(null); setMsgs(getWelcome()); refreshConversations(); } } }} aria-label="Delete">Delete</button>
                </>
              )}
            </div>
            {status.type === "typing" && (
              <div className="flex items-center gap-2 text-xs text-cyan-400">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                  <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                  <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce"></div>
                </div>
                <span>Thinking...</span>
              </div>
            )}
          </div>

          {/* Mobile drawer overlay */}
          {showDrawer && (
            <div className="fixed inset-0 z-50 md:hidden">
              <div className="absolute inset-0 bg-black/60" onClick={() => setShowDrawer(false)}></div>
              <div className="absolute left-0 top-0 bottom-0 w-4/5 max-w-sm bg-slate-900 border-r border-slate-700/50 p-4 overflow-y-auto">
                <div className="flex items-center justify-between mb-3">
                  <div className="text-slate-200 font-semibold">Conversations</div>
                  <button className="text-slate-300" onClick={() => setShowDrawer(false)}>✕</button>
                </div>
                <div className="flex items-center justify-between mb-2">
                  <button
                    onClick={() => { setConversationId(null); setConversationTitle(null); setMsgs(getWelcome()); localStorage.removeItem('activeConversationId'); localStorage.removeItem('activeConversationTitle'); setShowDrawer(false); }}
                    className="text-xs text-cyan-300 hover:text-white border border-cyan-400/30 rounded px-2 py-1"
                  >New</button>
                </div>
                <div className="flex flex-col gap-2">
                  {conversations.length === 0 && (
                    <div className="text-[11px] text-slate-400 px-1 py-3">No conversations yet. Start a new one!</div>
                  )}
                  {conversations.map(c => (
                    <div key={c.id} className={`group rounded-lg p-2 text-xs ${conversationId===c.id? 'bg-slate-800/80 border border-slate-700/50' : 'hover:bg-slate-800/40'}`}>
                      <div className="flex items-center justify-between gap-2">
                        <button className="text-left flex-1 truncate" title={c.title} onClick={() => { loadConversation(c.id); setShowDrawer(false); }}>
                          <div className="text-slate-200 truncate">{c.title || 'Untitled'}</div>
                          <div className="text-[10px] text-slate-400">{timeAgo(c.updated_at)}</div>
                        </button>
                        <div className="flex items-center gap-2 opacity-70 group-hover:opacity-100">
                          <button className="text-[10px] text-indigo-300 hover:text-white" onClick={async (e) => { e.stopPropagation(); const title = prompt('Rename conversation', c.title); if (title) { const { data: { session } } = await supabase.auth.getSession(); if (session) { await renameConversation(session.access_token, c.id, title); refreshConversations(); if (conversationId===c.id) setConversationTitle(title); } } }}>Rename</button>
                          <button className="text-[10px] text-rose-300 hover:text-white" onClick={async (e) => { e.stopPropagation(); if (confirm('Delete conversation?')) { const { data: { session } } = await supabase.auth.getSession(); if (session) { await deleteConversation(session.access_token, c.id); refreshConversations(); if (conversationId===c.id) { setConversationId(null); setMsgs(getWelcome()); setConversationTitle(null);} } } }}>Delete</button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Messages */}
          <div ref={viewport} className={`flex-1 overflow-y-auto ${compactMode ? 'p-3' : 'p-4'} ${messageGap} scrollbar-thin scrollbar-track-slate-800 scrollbar-thumb-slate-600`}>
            {msgs.map((m, i) => (
              <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`${sidebarCollapsed ? 'max-w-[98%]' : 'max-w-[92%]'} ${bubbleBase} ${
                  m.role === "user" 
                    ? "bg-gradient-to-r from-indigo-600 to-cyan-600 text-white shadow-lg" 
                    : "bg-slate-800/80 border border-slate-700/50 text-slate-100 shadow-md"
                }`}>
                  {m.role === "assistant" ? (
                    <div className={compactMode ? 'space-y-2' : 'space-y-3'}>
                      {/* Text content */}
                      <div className={compactMode ? 'text-[13px] leading-[1.55]' : 'text-sm leading-relaxed'}>
                        {m.content ? formatMessage(m.content) : (
                          isAssistantTyping ? (
                            <div className="flex items-center gap-2 text-slate-400">
                              <div className="flex gap-1">
                                <div className="w-2 h-2 bg-slate-400 rounded-full animate-pulse"></div>
                                <div className="w-2 h-2 bg-slate-400 rounded-full animate-pulse [animation-delay:0.2s]"></div>
                                <div className="w-2 h-2 bg-slate-400 rounded-full animate-pulse [animation-delay:0.4s]"></div>
                              </div>
                            </div>
                          ) : (
                            <span className="text-slate-500">...</span>
                          )
                        )}
                      </div>

                      {/* Quick-select buttons for Addiction menu */}
                      {m.content && isAddictionMenu(m.content) && (
                        <div className="flex flex-wrap gap-2 pt-1">
                          {[
                            { label: "☕ Caffeine", value: "I'm addicted to caffeine" },
                            { label: "🍷 Alcohol", value: "I'm addicted to alcohol" },
                            { label: "🚬 Nicotine", value: "I'm addicted to nicotine/tobacco" },
                            { label: "📱 Digital/Screen", value: "I'm addicted to digital/screen time" }
                          ].map((opt, idx) => (
                            <button
                              key={idx}
                              onClick={() => sendQuick(opt.value)}
                              disabled={loading}
                              className="text-xs text-indigo-300 hover:text-white bg-indigo-500/10 hover:bg-indigo-500/20 px-3 py-1.5 rounded-lg border border-indigo-400/20 transition-colors disabled:opacity-60"
                            >
                              {opt.label}
                            </button>
                          ))}
                        </div>
                      )}
                      
                      {/* Audio Player for generated audio */}
                      {m.audioId && (
                        <AudioPlayer 
                          audioData={{ 
                            available: true,
                            file_id: m.audioId, 
                            metadata: { 
                              estimated_duration_minutes: Math.ceil(m.content.split(' ').length / 130), // ~130 words per minute
                              estimated_duration_seconds: Math.ceil(m.content.split(' ').length / 130) * 60,
                              word_count: m.content.split(' ').length
                            } 
                          }} 
                        />
                      )}
                      
                      {/* Generate Audio Button for Storyteller */}
                      <GenerateAudioButton message={m} messageIndex={i} setMsgs={setMsgs} />
                      
                      {/* Responsible AI analysis hidden per request */}
                    </div>
                  ) : (
                    <div className={compactMode ? 'text-[13px] leading-[1.55] font-medium' : 'text-sm font-medium'}>{m.content}</div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Status */}
          {status.type === "error" && (
            <div className="px-4 py-2 border-t border-slate-700/50 bg-rose-500/10">
              <div className="flex items-center gap-2 text-rose-400 text-xs">
                <span>❌</span>
                <span>{status.msg}</span>
              </div>
            </div>
          )}

          {/* Input area */}
          <div className={`${compactMode ? 'p-3' : 'p-4'} border-t border-slate-700/50 bg-slate-900/50`}>
            <div className="flex gap-3">
              <div className="flex-1 relative">
                <input 
                  className={`w-full bg-slate-800/80 border border-slate-600/50 ${compactMode ? 'p-2.5 pr-10 rounded-lg text-[13px]' : 'p-3 pr-12 rounded-xl text-sm'} transition-all duration-200 focus:border-indigo-400 focus:bg-slate-800 focus:ring-2 focus:ring-indigo-400/20 focus:outline-none`} 
                  placeholder="Ask for analysis, plan, or explanation..." 
                  value={input} 
                  onChange={e => setInput(e.target.value)} 
                  onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendInput()}
                  disabled={loading}
                />
                {input && (
                  <button
                    onClick={() => setInput("")}
                    className={`absolute ${compactMode ? 'right-2' : 'right-3'} top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200 transition-colors`}
                  >
                    ✕
                  </button>
                )}
              </div>
              <button 
                disabled={loading || !input.trim()} 
                onClick={sendInput} 
                className={`bg-gradient-to-r from-indigo-600 to-cyan-600 disabled:from-slate-600 disabled:to-slate-600 disabled:cursor-not-allowed hover:from-indigo-500 hover:to-cyan-500 ${compactMode ? 'px-4 py-2 rounded-lg text-[13px]' : 'px-6 py-3 rounded-xl text-sm'} font-medium transition-all duration-200 shadow-lg hover:shadow-xl disabled:shadow-none transform hover:scale-105 disabled:scale-100 flex items-center gap-2`}
              >
                {loading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                    <span className={`${compactMode ? 'text-[12px]' : ''} hidden sm:inline`}>Sending...</span>
                  </>
                ) : (
                  <>
                    <span className={compactMode ? 'text-[13px]' : ''}>Send</span>
                    <span className={`${compactMode ? 'text-[11px]' : 'text-xs'} opacity-70`}>↵</span>
                  </>
                )}
              </button>
            </div>
            
            {/* Quick actions */}
            <div className={`flex flex-wrap gap-2 ${compactMode ? 'mt-2' : 'mt-3'}`}>
              {[
                "Analyze my last 7 days",
                "Make me a sleep plan", 
                "Why is Sleep important?",
                "Tell me about caffeine",
                "Tell me a story to help me relax"
              ].map((suggestion, i) => (
                <button
                  key={i}
                  onClick={() => setInput(suggestion)}
                  disabled={loading}
                  className={`${compactMode ? 'text-[11px] px-2.5 py-1 rounded-md' : 'text-xs px-3 py-1 rounded-lg'} text-cyan-400 hover:text-cyan-300 bg-cyan-400/10 hover:bg-cyan-400/20 border border-cyan-400/20 transition-colors disabled:opacity-50`}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
