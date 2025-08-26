import { useEffect, useRef, useState } from "react";
import { supabase } from "../lib/supabaseClient";
import { streamChat } from "../lib/api";

type Msg = { role: "user" | "assistant"; content: string };

export function Chat() {
  const [msgs,setMsgs]=useState<Msg[]>([
    { role:"assistant", content:"Hi! I’m your sleep coordinator. Log last night below, or ask me to analyze your last 7 days."}
  ]);
  const [input,setInput]=useState(""); const [loading,setLoading]=useState(false);
  const viewport = useRef<HTMLDivElement>(null);
  useEffect(()=>{ viewport.current?.scrollTo({ top: 9e9, behavior: "smooth" }); }, [msgs]);
  async function send() {
    if (!input.trim()) return;
    const text = input; setInput("");
    setMsgs(m=>[...m,{role:"user", content:text},{role:"assistant", content:""}]);
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) { alert("Please sign in."); return; }
    setLoading(true);
    try {
      await streamChat(text, session.access_token, (chunk)=>{
        setMsgs(m=>{
          const copy=[...m]; copy[copy.length-1] = { role:"assistant", content: copy[copy.length-1].content + chunk };
          return copy;
        });
      });
    } catch (e:any) { alert(e.message); }
    setLoading(false);
  }
  return (
    <div className="flex flex-col h-[70vh] bg-zinc-900 rounded">
      <div ref={viewport} className="flex-1 overflow-y-auto p-4 space-y-3">
        {msgs.map((m,i)=>(
          <div key={i} className={m.role==="user" ? "text-right" : "text-left"}>
            <span className={m.role==="user" ? "inline-block bg-indigo-600 rounded px-3 py-2" : "inline-block bg-zinc-800 rounded px-3 py-2"}>
              {m.content}
            </span>
          </div>
        ))}
      </div>
      <div className="p-3 border-t border-zinc-800 flex gap-2">
        <input className="flex-1 bg-zinc-800 p-2 rounded" placeholder="Ask for analysis, plan, or explanation..." value={input} onChange={e=>setInput(e.target.value)} onKeyDown={(e)=>e.key==="Enter" && send()} />
        <button disabled={loading} onClick={send} className="bg-indigo-600 hover:bg-indigo-500 px-3 rounded">Send</button>
      </div>
    </div>
  );
}
