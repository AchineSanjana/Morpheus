import { useEffect, useRef, useState } from "react";
import { supabase } from "../lib/supabaseClient";
import { streamChat, listConversations, getConversationMessages, renameConversation, deleteConversation, recoverConversations } from "../lib/api";
import { useLayout } from "../lib/LayoutContext";
import { MessageList } from "./chat/MessageList";
import { MessageInput } from "./chat/MessageInput";
import type { Msg } from "../lib/types";

// Msg type moved to lib/types

// GenerateAudioButton moved to components/chat/GenerateAudioButton and used inside MessageList

export function Chat() {
  const { compactMode, sidebarCollapsed, toggleCompactMode, toggleSidebarCollapsed } = useLayout();
  const [msgs, setMsgs] = useState<Msg[]>([
    { 
      role: "assistant", 
      content: "Hi! I'm your sleep coordinator. 🌙\n\nHere are some things you can try:"
    }
  ]);
  const [input, setInput] = useState(""); 
  const [loading, setLoading] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editText, setEditText] = useState<string>("");
  const [status, setStatus] = useState<{type:"idle"|"typing"|"error";msg?:string}>({type:"idle"});
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [conversationTitle, setConversationTitle] = useState<string | null>(null);
  const [conversations, setConversations] = useState<{ id: string; title: string; updated_at: string }[]>([]);
  const [showDrawer, setShowDrawer] = useState(false);
  const viewport = useRef<HTMLDivElement>(null);
  const autoScrollRef = useRef<boolean>(true);
  
  useEffect(() => { 
    const el = viewport.current;
    if (!el) return;
    if (autoScrollRef.current) {
      el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
    }
  }, [msgs]);
  
  function handleScroll() {
    const el = viewport.current;
    if (!el) return;
    const nearBottom = el.scrollTop + el.clientHeight >= el.scrollHeight - 40; // 40px threshold
    autoScrollRef.current = nearBottom;
  }

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
        content: "Hi! I'm your sleep coordinator Morpheus. 🌙\n\nHere are some things you can try:"
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
  // Ensure any previous stream is stopped
  try { abortRef.current?.abort(); } catch {}
  abortRef.current = new AbortController();
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
      }, conversationId, abortRef.current.signal);
      // Refresh list after message stored
      refreshConversations();
      setStatus({type:"idle"});
    } catch (e: any) {
      if (e?.name === 'AbortError') {
        // User stopped the stream: keep partial message, clear typing state
        setStatus({ type: 'idle' });
      } else {
        setStatus({type:"error", msg: e.message || "Something went wrong"});
        // Remove the empty assistant message on error
        setMsgs(m => m.slice(0, -1));
      }
    }
    setLoading(false);
  }

  // Editing handlers
  function handleEditStart(index: number, initial: string) {
    if (loading) return; // avoid editing while streaming to keep state simple
    setEditingIndex(index);
    setEditText(initial);
  }

  function handleEditCancel() {
    setEditingIndex(null);
    setEditText("");
  }

  async function handleEditSave(index: number) {
    const newText = editText.trim();
    if (!newText) { handleEditCancel(); return; }

    // Stop any in-flight stream
    stopStreaming();

    // Replace the edited user message and remove any assistant message that follows it
    setMsgs(prev => {
      const copy = [...prev];
      copy[index] = { ...copy[index], content: newText };
      // If next message is assistant (response to old text), remove it to avoid mismatch
      if (copy[index + 1]?.role === 'assistant') {
        copy.splice(index + 1, 1);
      }
      return copy;
    });

    setEditingIndex(null);
    setEditText("");
    await sendInternal(newText);
  }

  function stopStreaming() {
    try { abortRef.current?.abort(); } catch {}
    abortRef.current = null;
    setStatus({ type: 'idle' });
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

  // Use fixed height instead of flex-1 to enable proper scrolling
  const containerHeight = 'h-[800px] min-h-[500px] max-h-[90vh]';
  const messageGap = compactMode ? 'space-y-3' : 'space-y-4';

  return (
    <div className="relative">
  {/* Simplified background for performance (removed heavy blur filter). Fixed height container. */}
  <div className={`relative flex flex-col md:flex-row ${containerHeight} bg-gradient-to-br from-slate-900/95 to-slate-800/95 border border-slate-700/50 rounded-2xl shadow-2xl shadow-black/20`}>
  {/* Sidebar: Conversations */}
  <div id="chat-history-panel" className={`${sidebarCollapsed ? 'hidden' : 'hidden md:flex'} md:w-80 flex-col border-r border-slate-700/50 p-3 gap-2 overflow-y-auto show-scrollbar min-h-0`} aria-label="Conversations">
          <div className="flex items-center justify-between mb-1">
            <div className="text-slate-300 text-sm font-semibold">Chat History</div>
            <div className="flex items-center gap-2">
              {/* Collapse sidebar (md+) */}
              <button
                className="hidden md:inline-flex items-center justify-center w-8 h-8 rounded-full border border-slate-400/30 text-slate-300 hover:text-white hover:border-slate-300 transition"
                onClick={toggleSidebarCollapsed}
                aria-label="Collapse history"
                aria-controls="chat-history-panel"
                aria-expanded={!sidebarCollapsed}
                title="Collapse history"
              >
                <svg className="w-4 h-4 rotate-180" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M9 6l6 6-6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>
              <button
                onClick={() => { setConversationId(null); setConversationTitle(null); setMsgs(getWelcome()); localStorage.removeItem('activeConversationId'); localStorage.removeItem('activeConversationTitle'); }}
                className="text-xs text-cyan-300 hover:text-white"
              >New</button>
            </div>
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
  <div className="flex-1 min-h-0 flex flex-col min-w-0">
          {/* Header */}
          <div className={`flex items-center gap-3 ${compactMode ? 'p-3' : 'p-4'} border-b border-slate-700/50`}>
            {/* Expand history (md+) placed at far-left near history area */}
            {sidebarCollapsed && (
              <button
                className="hidden md:inline-flex items-center justify-center w-8 h-8 rounded-full border border-slate-400/30 text-slate-300 hover:text-white hover:border-slate-300 transition -ml-1"
                onClick={toggleSidebarCollapsed}
                aria-label="Expand history"
                aria-controls="chat-history-panel"
                aria-expanded={!sidebarCollapsed}
                title="Expand history"
              >
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M9 6l6 6-6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>
            )}
            <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-cyan-500 rounded-full flex items-center justify-center text-white text-sm font-bold">🤖</div>
            <div className="flex flex-col">
              <h3 className={`${compactMode ? 'text-base' : 'text-lg'} font-semibold bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent`}>
                {conversationTitle || 'Sleep Coach Chat'}
              </h3>
              {/* Chat ID hidden intentionally */}
            </div>
            {/* Mobile: open history */}
            <div className="ml-auto flex items-center gap-2">
              {/* Expand history button is placed on the far-left of header when collapsed */}
              <button className="md:hidden text-xs text-cyan-300 hover:text-white border border-cyan-400/30 rounded px-2 py-1" onClick={() => setShowDrawer(true)} aria-label="History">History</button>
              {/* md+ controls (sidebar toggle moved into sidebar) */}
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
                <button className="ml-2 text-rose-300 hover:text-white border border-rose-400/30 rounded px-2 py-0.5" onClick={stopStreaming}>Stop</button>
              </div>
            )}
          </div>

          {/* Mobile drawer overlay */}
          {showDrawer && (
            <div className="fixed inset-0 z-50 md:hidden">
              <div className="absolute inset-0 bg-black/60" onClick={() => setShowDrawer(false)}></div>
              <div className="absolute left-0 top-0 bottom-0 w-4/5 max-w-sm bg-slate-900 border-r border-slate-700/50 p-4 overflow-y-auto show-scrollbar">
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
          <div ref={viewport} onScroll={handleScroll} className={`flex-1 min-h-0 overflow-y-auto ${compactMode ? 'p-3' : 'p-4'} ${messageGap} show-scrollbar`}>
            <MessageList
              msgs={msgs}
              isAssistantTyping={isAssistantTyping}
              compactMode={compactMode}
              sidebarCollapsed={sidebarCollapsed}
              onQuick={(text) => sendQuick(text)}
              setMsgs={setMsgs}
              editingIndex={editingIndex}
              editText={editText}
              onEditStart={handleEditStart}
              onEditChange={setEditText}
              onEditCancel={handleEditCancel}
              onEditSave={handleEditSave}
              disableEditing={loading}
            />
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
          <MessageInput
            value={input}
            onChange={setInput}
            onSend={sendInput}
            loading={loading}
            onStop={stopStreaming}
            compactMode={compactMode}
            suggestions={[
              "Analyze my last 7 days",
              "Make me a sleep plan",
              "Why is Sleep important?",
              "Tell me about caffeine",
              "Explain how alcohol affects sleep",
              "Tell me a story to help me relax",
              "How should I stop caffeine",
              "What’s my optimal bedtime?",
              "Predict tonight’s sleep quality"
            ]}
          />
        </div>
      </div>
    </div>
  );
}
