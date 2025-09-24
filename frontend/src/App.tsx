import { useEffect, useState } from "react";
import { supabase, supabaseSession } from "./lib/supabaseClient";
import { Auth } from "./components/Auth";
import { SleepLogForm } from "./components/SleepLogForm";
import { Chat } from "./components/Chat";
import { Account } from "./components/Account";
import morpheusLogo from "./assets/morpheus_logo.jpg";
import "./index.css";

export default function App() {
  const [authed,setAuthed]=useState(false);
  const [user, setUser] = useState<any>(null);
  const [showAccount, setShowAccount] = useState(false);

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
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-indigo-400/15 rounded-full blur-3xl"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-cyan-400/15 rounded-full blur-3xl"></div>
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-purple-400/10 rounded-full blur-3xl"></div>
      </div>
      
      <div className="relative max-w-3xl mx-auto p-4 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between p-4 bg-slate-900/80 backdrop-blur-xl border border-slate-700/50 rounded-2xl shadow-2xl">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-cyan-500 rounded-xl flex items-center justify-center overflow-hidden p-1">
              <img 
                src={morpheusLogo} 
                alt="Morpheus Logo" 
                className="w-full h-full object-contain rounded-lg"
              />
            </div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent">Morpheus</h1>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-slate-400">{user?.email}</span>
            <button
              onClick={() => setShowAccount(true)}
              className="text-sm text-cyan-400 hover:text-cyan-300 px-3 py-1 rounded-lg hover:bg-cyan-400/10 transition-colors flex items-center gap-2"
              title="Account Settings"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              Account
            </button>
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
        
        {/* Footer */}
        <div className="text-center">
          <p className="text-xs text-slate-500 bg-slate-900/50 backdrop-blur-sm px-4 py-2 rounded-xl border border-slate-700/30">
            Not medical advice. If you have ongoing sleep issues, consult a clinician.
          </p>
        </div>
      </div>
      
      {/* Account Modal */}
      {showAccount && user && (
        <Account 
          user={user} 
          onClose={() => setShowAccount(false)} 
        />
      )}
    </div>
  );
}
