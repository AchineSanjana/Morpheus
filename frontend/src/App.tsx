import { useEffect, useState } from "react";
import { supabase } from "./lib/supabaseClient";
import { Auth } from "./components/Auth";
import { SleepLogForm } from "./components/SleepLogForm";
import { Chat } from "./components/Chat";
import "./index.css";

export default function App() {
  const [authed,setAuthed]=useState(false);
  const [user, setUser] = useState<any>(null);

  useEffect(()=>{
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_e, session)=>{
      setAuthed(!!session);
      setUser(session?.user || null);
    });
    supabase.auth.getSession().then(({data})=>{
      setAuthed(!!data.session);
      setUser(data.session?.user || null);
    });
    return ()=>subscription.unsubscribe();
  }, []);

  async function logout() {
    await supabase.auth.signOut();
    setAuthed(false);
    setUser(null);
  }

  if (!authed) return <Auth onAuthed={()=>setAuthed(true)} />;
  
  return (
    <div className="max-w-3xl mx-auto p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Morpheus</h1>
        <div className="flex items-center gap-3">
          <span className="text-sm text-zinc-400">{user?.email}</span>
          <button 
            onClick={logout}
            className="text-sm text-rose-400 hover:text-rose-300 px-3 py-1 rounded-lg hover:bg-rose-400/10 transition-colors"
          >
            Sign out
          </button>
        </div>
      </div>
      <SleepLogForm />
      <Chat />
      <p className="text-xs text-zinc-400">Not medical advice. If you have ongoing sleep issues, consult a clinician.</p>
    </div>
  );
}
