import { useEffect, useRef, useState } from "react";
import { supabase } from "../lib/supabaseClient";
import { streamChat } from "../lib/api";

type Msg = { role: "user" | "assistant"; content: string };

export function Chat() {
  const [msgs, setMsgs] = useState<Msg[]>([
    { 
      role: "assistant", 
      content: "Hi! I'm your sleep coordinator. 🌙\n\nLog last night below, or ask me to:\n• **Analyze my last 7 days**\n• **Make me a sleep plan**\n• **Tell me about caffeine and sleep**"
    }
  ]);
  const [input, setInput] = useState(""); 
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<{type:"idle"|"typing"|"error";msg?:string}>({type:"idle"});
  const viewport = useRef<HTMLDivElement>(null);
  
  useEffect(() => { 
    viewport.current?.scrollTo({ top: 9e9, behavior: "smooth" }); 
  }, [msgs]);

  const isAssistantTyping = loading && msgs[msgs.length - 1]?.role === "assistant" && !msgs[msgs.length - 1]?.content;

  async function send() {
    if (!input.trim() || loading) return;
    const text = input.trim(); 
    setInput("");
    setStatus({type:"idle"});
    
    setMsgs(m => [...m, {role: "user", content: text}, {role: "assistant", content: ""}]);
    
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) { 
      setStatus({type:"error", msg:"Please sign in first"});
      return; 
    }
    
    setLoading(true);
    setStatus({type:"typing", msg:"AI is thinking..."});
    
    try {
      await streamChat(text, session.access_token, (chunk) => {
        setMsgs(m => {
          const copy = [...m]; 
          copy[copy.length - 1] = { 
            role: "assistant", 
            content: copy[copy.length - 1].content + chunk 
          };
          return copy;
        });
      });
      setStatus({type:"idle"});
    } catch (e: any) { 
      setStatus({type:"error", msg: e.message || "Something went wrong"});
      // Remove the empty assistant message on error
      setMsgs(m => m.slice(0, -1));
    }
    setLoading(false);
  }

  function formatMessage(content: string) {
    // Simple markdown-like formatting
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-emerald-300">$1</strong>')
      .replace(/\*(.*?)\*/g, '<em class="italic text-zinc-300">$1</em>')
      .replace(/•/g, '<span class="text-emerald-400">•</span>')
      .split('\n').map((line, i) => (
        <span key={i} dangerouslySetInnerHTML={{__html: line}} className="block" />
      ));
  }

  return (
    <div className="relative">
      {/* Background gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-violet-500/5 via-transparent to-emerald-500/5 rounded-2xl blur-xl"></div>
      
      <div className="relative flex flex-col h-[70vh] bg-gradient-to-br from-zinc-900/95 to-zinc-800/95 backdrop-blur-sm border border-zinc-700/50 rounded-2xl shadow-2xl shadow-black/20">
        {/* Header */}
        <div className="flex items-center gap-3 p-4 border-b border-zinc-700/50">
          <div className="w-8 h-8 bg-gradient-to-br from-violet-500 to-emerald-500 rounded-full flex items-center justify-center text-white text-sm font-bold">🤖</div>
          <h3 className="text-lg font-semibold bg-gradient-to-r from-violet-400 to-emerald-400 bg-clip-text text-transparent">
            Sleep Coach Chat
          </h3>
          {status.type === "typing" && (
            <div className="flex items-center gap-2 text-xs text-emerald-400">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                <div className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                <div className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce"></div>
              </div>
              <span>Thinking...</span>
            </div>
          )}
        </div>

        {/* Messages */}
        <div ref={viewport} className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-track-zinc-800 scrollbar-thumb-zinc-600">
          {msgs.map((m, i) => (
            <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                m.role === "user" 
                  ? "bg-gradient-to-r from-violet-600 to-emerald-600 text-white shadow-lg" 
                  : "bg-zinc-800/80 border border-zinc-700/50 text-zinc-100 shadow-md"
              }`}>
                {m.role === "assistant" ? (
                  <div className="text-sm leading-relaxed">
                    {m.content ? formatMessage(m.content) : (
                      isAssistantTyping ? (
                        <div className="flex items-center gap-2 text-zinc-400">
                          <div className="flex gap-1">
                            <div className="w-2 h-2 bg-zinc-400 rounded-full animate-pulse"></div>
                            <div className="w-2 h-2 bg-zinc-400 rounded-full animate-pulse [animation-delay:0.2s]"></div>
                            <div className="w-2 h-2 bg-zinc-400 rounded-full animate-pulse [animation-delay:0.4s]"></div>
                          </div>
                        </div>
                      ) : (
                        <span className="text-zinc-500">...</span>
                      )
                    )}
                  </div>
                ) : (
                  <div className="text-sm font-medium">{m.content}</div>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Status */}
        {status.type === "error" && (
          <div className="px-4 py-2 border-t border-zinc-700/50 bg-rose-500/10">
            <div className="flex items-center gap-2 text-rose-400 text-xs">
              <span>❌</span>
              <span>{status.msg}</span>
            </div>
          </div>
        )}

        {/* Input area */}
        <div className="p-4 border-t border-zinc-700/50 bg-zinc-900/50">
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <input 
                className="w-full bg-zinc-800/80 border border-zinc-600/50 p-3 pr-12 rounded-xl transition-all duration-200 focus:border-violet-400 focus:bg-zinc-800 focus:ring-2 focus:ring-violet-400/20 focus:outline-none text-sm" 
                placeholder="Ask for analysis, plan, or explanation..." 
                value={input} 
                onChange={e => setInput(e.target.value)} 
                onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
                disabled={loading}
              />
              {input && (
                <button
                  onClick={() => setInput("")}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-200 transition-colors"
                >
                  ✕
                </button>
              )}
            </div>
            <button 
              disabled={loading || !input.trim()} 
              onClick={send} 
              className="bg-gradient-to-r from-violet-600 to-emerald-600 disabled:from-zinc-600 disabled:to-zinc-600 disabled:cursor-not-allowed hover:from-violet-500 hover:to-emerald-500 px-6 py-3 rounded-xl text-sm font-medium transition-all duration-200 shadow-lg hover:shadow-xl disabled:shadow-none transform hover:scale-105 disabled:scale-100 flex items-center gap-2"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  <span className="hidden sm:inline">Sending...</span>
                </>
              ) : (
                <>
                  <span>Send</span>
                  <span className="text-xs opacity-70">↵</span>
                </>
              )}
            </button>
          </div>
          
          {/* Quick actions */}
          <div className="flex flex-wrap gap-2 mt-3">
            {[
              "Analyze my last 7 days",
              "Make me a sleep plan", 
              "Tell me about caffeine",
              "Why is consistency important?"
            ].map((suggestion, i) => (
              <button
                key={i}
                onClick={() => setInput(suggestion)}
                disabled={loading}
                className="text-xs text-emerald-400 hover:text-emerald-300 bg-emerald-400/10 hover:bg-emerald-400/20 px-3 py-1 rounded-lg border border-emerald-400/20 transition-colors disabled:opacity-50"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
