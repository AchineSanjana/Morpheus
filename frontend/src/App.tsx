import { useEffect, useState } from "react";
import { supabase, supabaseSession } from "./lib/supabaseClient";
import { Auth } from "./components/Auth";
import { SleepLogForm } from "./components/SleepLogForm";
import { Chat } from "./components/Chat";
import { Account } from "./components/Account";
import PrivacyPolicy from "./components/PrivacyPolicy";
import morpheusLogo from "./assets/morpheus_logo.jpg";
import "./index.css";
import { useLayout } from "./lib/LayoutContext";

export default function App() {
  const { fullWidthChat } = useLayout();
  const [authed,setAuthed]=useState(false);
  const [user, setUser] = useState<any>(null);
  const [showAccount, setShowAccount] = useState(false);
  const [showPrivacy, setShowPrivacy] = useState(false);

  useEffect(()=>{
    // Subscribe to auth state changes for both clients (localStorage and sessionStorage clients)
    const { data: { subscription: subA } } = supabase.auth.onAuthStateChange((event, session)=>{
      setAuthed(!!session);
      setUser(session?.user || null);
      // When the user signs out from any tab/client, clear any active conversation state
      if (event === 'SIGNED_OUT') {
        localStorage.removeItem('activeConversationId');
        localStorage.removeItem('activeConversationTitle');
      }
    });
    const { data: { subscription: subB } } = supabaseSession.auth.onAuthStateChange((event, session)=>{
      setAuthed(!!session);
      setUser(session?.user || null);
      if (event === 'SIGNED_OUT') {
        localStorage.removeItem('activeConversationId');
        localStorage.removeItem('activeConversationTitle');
      }
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
  localStorage.removeItem('activeConversationId');
  localStorage.removeItem('activeConversationTitle');
  }

  if (!authed) return <Auth onAuthed={()=>setAuthed(true)} />;
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 relative">
      <div className="absolute inset-0 bg-animated-gradient"></div>
      <div className="absolute inset-0 bg-moving-clouds"></div>
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="bg-orb absolute -top-40 -right-40 w-80 h-80 bg-indigo-400/15 rounded-full blur-3xl [animation-delay:0s] motion-reduce:[animation:none]"></div>
        <div className="bg-orb absolute -bottom-40 -left-40 w-80 h-80 bg-cyan-400/15 rounded-full blur-3xl [animation-delay:3s] motion-reduce:[animation:none]"></div>
        <div className="bg-orb absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-purple-400/10 rounded-full blur-3xl [animation-delay:6s] motion-reduce:[animation:none]"></div>
      </div>
      
  <div className="relative max-w-7xl mx-auto p-4 space-y-6">
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
        
  {!fullWidthChat && <SleepLogForm />}
        <Chat />
        
        {/* Footer */}
        <div className="text-center">
          <p className="text-xs text-slate-500 bg-slate-900/50 backdrop-blur-sm px-4 py-2 rounded-xl border border-slate-700/30">
            Not medical advice. If you have ongoing sleep issues, consult a clinician.
          </p>
          <div className="mt-2">
            <button
              type="button"
              onClick={() => setShowPrivacy(true)}
              className="text-xs text-slate-400 hover:text-slate-200 underline"
            >
              Privacy Policy
            </button>
          </div>
        </div>
      </div>
      
      {/* Account Modal */}
      {showAccount && user && (
        <Account 
          user={user} 
          onClose={() => setShowAccount(false)} 
        />
      )}

      {/* Privacy Policy Modal */}
      {showPrivacy && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/70" onClick={() => setShowPrivacy(false)} />
          <div className="relative bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl max-w-4xl w-[95%] max-h-[85vh] overflow-y-auto p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-slate-100">Privacy Policy</h3>
              <button
                onClick={() => setShowPrivacy(false)}
                className="text-slate-400 hover:text-slate-200"
                aria-label="Close privacy policy"
              >
                ✕
              </button>
            </div>
            <PrivacyPolicy />
          </div>
        </div>
      )}
    </div>
  );
}
