import { useEffect, useState } from "react";
import { supabase } from "../lib/supabaseClient";

export function Auth({ onAuthed }:{ onAuthed:()=>void }) {
  const [email,setEmail]=useState(""); const [password,setPassword]=useState("");
  const [mode,setMode]=useState<"signin"|"signup">("signin");
  useEffect(()=>{ supabase.auth.getSession().then(({data})=>{
    if (data.session) onAuthed();
  }); }, []);
  async function submit(e:React.FormEvent){
    e.preventDefault();
    if (mode==="signup"){
      const {error}=await supabase.auth.signUp({ email, password });
      if (error) alert(error.message); else alert("Check your email to confirm.");
    } else {
      const {error}=await supabase.auth.signInWithPassword({ email, password });
      if (error) alert(error.message); else onAuthed();
    }
  }
  return (
    <div className="max-w-sm mx-auto pt-24">
      <h1 className="text-2xl font-semibold mb-4">Morpheus</h1>
      <form onSubmit={submit} className="space-y-3">
        <input className="w-full bg-zinc-800 p-2 rounded" placeholder="email" value={email} onChange={e=>setEmail(e.target.value)} />
        <input className="w-full bg-zinc-800 p-2 rounded" type="password" placeholder="password" value={password} onChange={e=>setPassword(e.target.value)} />
        <button className="w-full bg-indigo-600 hover:bg-indigo-500 p-2 rounded">
          {mode==="signin" ? "Sign in" : "Sign up"}
        </button>
      </form>
      <button className="text-sm mt-3 underline" onClick={()=>setMode(mode==="signin"?"signup":"signin")}>
        {mode==="signin" ? "Create an account" : "Have an account? Sign in"}
      </button>
    </div>
  );
}
