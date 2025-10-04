import { useEffect, useRef, useState } from "react";
import { supabase } from "../lib/supabaseClient";
import { streamChat } from "../lib/api";
import { ResponseAnalysis } from "./ResponsibleAI";
import { AudioPlayer } from "./AudioPlayer";

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
  const isStorytellerResponse = message.data?.agent === "storyteller" || 
                              (message.content.length > 100 && 
                               (message.content.toLowerCase().includes("once upon") || 
                                message.content.toLowerCase().includes("story") ||
                                message.content.toLowerCase().includes("bedtime")));
  
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

      const response = await fetch('http://localhost:8000/audio/generate', {
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
      await streamChat(text, session.access_token, (chunk, responsibleAIData, data) => {
        setMsgs(m => {
          const copy = [...m]; 
          copy[copy.length - 1] = { 
            role: "assistant", 
            content: copy[copy.length - 1].content + chunk,
            responsibleAIChecks: responsibleAIData?.responsibleAIChecks,
            responsibleAIPassed: responsibleAIData?.responsibleAIPassed,
            responsibleAIRiskLevel: responsibleAIData?.responsibleAIRiskLevel,
            data: data
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
      .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-cyan-300">$1</strong>')
      .replace(/\*(.*?)\*/g, '<em class="italic text-slate-300">$1</em>')
      .replace(/•/g, '<span class="text-cyan-400">•</span>')
      .split('\n').map((line, i) => (
        <span key={i} dangerouslySetInnerHTML={{__html: line}} className="block" />
      ));
  }

  return (
    <div className="relative">
      {/* Background gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-indigo-400/10 via-transparent to-cyan-400/10 rounded-2xl blur-xl"></div>
      
      <div className="relative flex flex-col h-[70vh] bg-gradient-to-br from-slate-900/95 to-slate-800/95 backdrop-blur-sm border border-slate-700/50 rounded-2xl shadow-2xl shadow-black/20">
        {/* Header */}
        <div className="flex items-center gap-3 p-4 border-b border-slate-700/50">
          <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-cyan-500 rounded-full flex items-center justify-center text-white text-sm font-bold">🤖</div>
          <h3 className="text-lg font-semibold bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent">
            Sleep Coach Chat
          </h3>
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

        {/* Messages */}
        <div ref={viewport} className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-track-slate-800 scrollbar-thumb-slate-600">
          {msgs.map((m, i) => (
            <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                m.role === "user" 
                  ? "bg-gradient-to-r from-indigo-600 to-cyan-600 text-white shadow-lg" 
                  : "bg-slate-800/80 border border-slate-700/50 text-slate-100 shadow-md"
              }`}>
                {m.role === "assistant" ? (
                  <div className="space-y-3">
                    {/* Text content */}
                    <div className="text-sm leading-relaxed">
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
                        storyText={m.content} 
                      />
                    )}
                    
                    {/* Generate Audio Button for Storyteller */}
                    <GenerateAudioButton message={m} messageIndex={i} setMsgs={setMsgs} />
                    
                    {/* Show responsible AI analysis if available */}
                    {m.content && m.responsibleAIChecks && (
                      <div className="mt-3">
                        <ResponseAnalysis responsibleAIChecks={m.responsibleAIChecks} />
                      </div>
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
          <div className="px-4 py-2 border-t border-slate-700/50 bg-rose-500/10">
            <div className="flex items-center gap-2 text-rose-400 text-xs">
              <span>❌</span>
              <span>{status.msg}</span>
            </div>
          </div>
        )}

        {/* Input area */}
        <div className="p-4 border-t border-slate-700/50 bg-slate-900/50">
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <input 
                className="w-full bg-slate-800/80 border border-slate-600/50 p-3 pr-12 rounded-xl transition-all duration-200 focus:border-indigo-400 focus:bg-slate-800 focus:ring-2 focus:ring-indigo-400/20 focus:outline-none text-sm" 
                placeholder="Ask for analysis, plan, or explanation..." 
                value={input} 
                onChange={e => setInput(e.target.value)} 
                onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
                disabled={loading}
              />
              {input && (
                <button
                  onClick={() => setInput("")}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200 transition-colors"
                >
                  ✕
                </button>
              )}
            </div>
            <button 
              disabled={loading || !input.trim()} 
              onClick={send} 
              className="bg-gradient-to-r from-indigo-600 to-cyan-600 disabled:from-slate-600 disabled:to-slate-600 disabled:cursor-not-allowed hover:from-indigo-500 hover:to-cyan-500 px-6 py-3 rounded-xl text-sm font-medium transition-all duration-200 shadow-lg hover:shadow-xl disabled:shadow-none transform hover:scale-105 disabled:scale-100 flex items-center gap-2"
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
                className="text-xs text-cyan-400 hover:text-cyan-300 bg-cyan-400/10 hover:bg-cyan-400/20 px-3 py-1 rounded-lg border border-cyan-400/20 transition-colors disabled:opacity-50"
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
