import { useEffect, useState } from "react";
import { supabase, supabaseSession } from "./lib/supabaseClient";
import { Auth } from "./components/Auth";
import { SleepLogForm } from "./components/SleepLogForm";
import { Chat } from "./components/Chat";
import "./index.css";

export default function App() {
  const [authed,setAuthed]=useState(false);
  const [user, setUser] = useState<any>(null);

  useEffect(()=>{
    // Subscribe to auth state changes for both clients (localStorage and sessionStorage clients)
    const { data: { subscription: subA } } = supabase.auth.onAuthStateChange((_e, session)=>{
      setAuthed(!!session);
      setUser(session?.user || null);
    });
    const { data: { subscription: subB } } = supabaseSession.auth.onAuthStateChange((_e, session)=>{
      setAuthed(!!session);
      setUser(session?.user || null);
    });

    // Initialize from either client that has an active session
    Promise.all([supabase.auth.getSession(), supabaseSession.auth.getSession()])
      .then(([a, b]) => {
        if (a?.data?.session) {
          setAuthed(true);
          setUser(a.data.session.user || null);
        } else if (b?.data?.session) {
          setAuthed(true);
          setUser(b.data.session.user || null);
        } else {
          setAuthed(false);
          setUser(null);
        }
      });

    return ()=>{ subA.unsubscribe(); subB.unsubscribe(); };
  }, []);

  async function logout() {
  // sign out both clients to clear sessions regardless of which stored it
  await supabase.auth.signOut();
  await supabaseSession.auth.signOut();
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
