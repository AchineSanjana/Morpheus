import { useEffect, useState } from "react";
import { supabase } from "./lib/supabaseClient";
import { Auth } from "./components/Auth";
import { SleepLogForm } from "./components/SleepLogForm";
import { Chat } from "./components/Chat";
import "./index.css";

export default function App() {
  const [authed,setAuthed]=useState(false);
  useEffect(()=>{
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_e, session)=>{
      setAuthed(!!session);
    });
    supabase.auth.getSession().then(({data})=>setAuthed(!!data.session));
    return ()=>subscription.unsubscribe();
  }, []);
  if (!authed) return <Auth onAuthed={()=>setAuthed(true)} />;
  return (
    <div className="max-w-3xl mx-auto p-4 space-y-3">
      <h1 className="text-2xl font-semibold">Morpheus</h1>
      <SleepLogForm />
      <Chat />
      <p className="text-xs text-zinc-400">Not medical advice. If you have ongoing sleep issues, consult a clinician.</p>
    </div>
  );
}
