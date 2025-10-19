import { useEffect, useState } from "react";
import { supabase, supabaseSession } from "../lib/supabaseClient";
import morpheusLogo from "../assets/morpheus_logo.jpg";
import PrivacyPolicy from "./PrivacyPolicy";
import TermsAndConditions from "./TermsAndConditions";

export function Auth({ onAuthed }:{ onAuthed:()=>void }) {
  const [email,setEmail]=useState(""); 
  const [password,setPassword]=useState("");
  const [mode,setMode]=useState<"signin"|"signup"|"reset">("signin");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<{type:"idle"|"success"|"error";msg?:string}>({type:"idle"});
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [showPrivacy, setShowPrivacy] = useState(false);
  const [showTerms, setShowTerms] = useState(false);
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [confirmationMessage, setConfirmationMessage] = useState<string | null>(null);

  // Handle email confirmations from URL parameters
  useEffect(() => {
    const handleUrlParams = () => {
      try {
        const u = new URL(window.location.href);
        const searchParams = u.searchParams;
        const hashParams = new URLSearchParams(u.hash.startsWith('#') ? u.hash.substring(1) : '');
        
        const type = searchParams.get('type') || hashParams.get('type');
        const accessToken = searchParams.get('access_token') || hashParams.get('access_token');
        
        if (type === 'signup' && accessToken) {
          // Email confirmation for new signup
          setConfirmationMessage("Email confirmed successfully! Please sign in to continue. ✅");
          setMode("signin"); // Switch to signin mode
          // Clear URL parameters
          window.history.replaceState({}, document.title, window.location.pathname);
          // Clear message after 8 seconds
          setTimeout(() => setConfirmationMessage(null), 8000);
        } else if (type === 'email_change' && accessToken) {
          // Email change confirmation
          setConfirmationMessage("Email updated successfully! Please sign in with your new email. ✅");
          setMode("signin"); // Switch to signin mode
          window.history.replaceState({}, document.title, window.location.pathname);
          setTimeout(() => setConfirmationMessage(null), 8000);
        }
      } catch (e) {
        console.error('Error handling URL parameters:', e);
      }
    };

    handleUrlParams();
  }, []);

  // Clear stored password when rememberMe is unchecked
  useEffect(() => {
    if (!rememberMe) {
      try {
        localStorage.removeItem("morpheus:password");
      } catch (e) {
        // ignore storage errors
      }
    }
  }, [rememberMe]);

  // Prefill email and password from previous "remember" choice
  useEffect(() => {
    try {
      const storedRemember = localStorage.getItem("morpheus:remember");
      const storedEmail = localStorage.getItem("morpheus:email");
      const storedPassword = localStorage.getItem("morpheus:password");
      
      if (storedRemember === "1" && storedEmail) {
        setEmail(storedEmail);
        setRememberMe(true);
        // Only restore password if remember me was explicitly enabled
        if (storedPassword) {
          setPassword(storedPassword);
        }
      } else if (storedEmail) {
        // if email stored but remember flag absent, set it as not remembered
        setEmail(storedEmail);
        setRememberMe(false);
      }
    } catch (e) {
      // ignore storage errors
    }
  }, []);

  useEffect(()=>{ 
    supabase.auth.getSession().then(({data})=>{
      if (data.session) onAuthed();
    }); 
  }, [onAuthed]);

  async function submit(e:React.FormEvent){
    e.preventDefault();
    setLoading(true);
    setStatus({type:"idle"});

    if (mode==="signup"){
      if (!acceptedTerms) {
        setStatus({type:"error", msg: "You must accept the Terms and Conditions to create an account."});
        setLoading(false);
        return;
      }
      const {error}=await supabase.auth.signUp({ email, password });
      if (error) {
        setStatus({type:"error", msg: error.message});
      } else {
        setStatus({type:"success", msg: "Check your email to confirm your account!"});
      }
  } else if (mode === "reset") {
      // send password reset email
      const { error } = await supabase.auth.resetPasswordForEmail(email);
      if (error) {
        setStatus({ type: "error", msg: error.message });
      } else {
        setStatus({ type: "success", msg: "Check your email for password reset instructions." });
        // return user to sign-in screen after requesting reset
        setMode("signin");
      }
    } else {
      // choose client based on rememberMe. If rememberMe === false, use session-only client.
      const client = rememberMe ? supabase : supabaseSession;
      const {error}=await client.auth.signInWithPassword({ email, password });
      if (error) {
        setStatus({type:"error", msg: error.message});
      } else {
        // persist email and password if requested
        try {
          if (rememberMe) {
            localStorage.setItem("morpheus:email", email);
            localStorage.setItem("morpheus:password", password);
            localStorage.setItem("morpheus:remember", "1");
          } else {
            // keep email to help with autofill but clear the remember flag and password
            localStorage.removeItem("morpheus:remember");
            localStorage.removeItem("morpheus:password");
            // optionally remove email as well to be strict
            // localStorage.removeItem("morpheus:email");
          }
        } catch (e) {}

        setStatus({type:"success", msg: "Welcome back!"});
        onAuthed();
      }
    }
    setLoading(false);
  }

  return (
    <div className="min-h-svh bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 flex items-center justify-center px-3 sm:px-4 py-4 relative pt-safe pb-safe">
      <div className="absolute inset-0 bg-aurora"></div>
      <div className="absolute inset-0 bg-animated-gradient"></div>
      <div className="absolute inset-0 bg-moving-clouds"></div>
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="bg-orb absolute -top-40 -right-40 w-80 h-80 bg-indigo-400/20 rounded-full blur-3xl [animation-delay:0s] motion-reduce:[animation:none]"></div>
        <div className="bg-orb absolute -bottom-40 -left-40 w-80 h-80 bg-cyan-400/20 rounded-full blur-3xl [animation-delay:3s] motion-reduce:[animation:none]"></div>
        <div className="bg-orb absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-purple-400/15 rounded-full blur-3xl [animation-delay:6s] motion-reduce:[animation:none]"></div>
      </div>

      <div className="relative w-full max-w-md">
        {/* Main auth card */}
  <div className="bg-slate-900/85 border border-slate-700/50 rounded-2xl p-8 shadow-2xl">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-gradient-to-br from-indigo-500 to-cyan-500 rounded-2xl flex items-center justify-center mb-4 mx-auto overflow-hidden p-1">
              <img 
                src={morpheusLogo} 
                alt="Morpheus Logo" 
                className="w-full h-full object-contain rounded-xl"
              />
            </div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent">
              Morpheus
            </h1>
            <p className="text-slate-400 text-sm mt-2">
              Your AI-powered sleep improvement companion
            </p>
          </div>

          {/* Tab switcher */}
          <div className="flex bg-slate-800/60 rounded-xl p-1 mb-6">
            <button
              type="button"
              onClick={() => {
                setMode("signin"); 
                setStatus({type:"idle"});
                setAcceptedTerms(false);
                // Clear password when switching to signin to allow fresh login
                if (mode !== "signin") setPassword("");
              }}
              className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-all duration-200 ${
                mode === "signin" 
                  ? "bg-gradient-to-r from-indigo-600 to-cyan-600 text-white shadow-lg" 
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => {
                setMode("signup"); 
                setStatus({type:"idle"});
                setAcceptedTerms(false);
                // Clear password when switching to signup for security
                setPassword("");
              }}
              className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-all duration-200 ${
                mode === "signup" 
                  ? "bg-gradient-to-r from-indigo-600 to-cyan-600 text-white shadow-lg" 
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Sign Up
            </button>
          </div>

          {/* Form */}
          <form onSubmit={submit} className="space-y-6">
            <div className="space-y-4">
              <label className="flex flex-col gap-2 text-sm">
                <span className="font-medium text-slate-200 flex items-center gap-2">
                  📧 Email
                </span>
                <input
                  type="email"
                  name="email"
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="bg-slate-800/80 border border-slate-600/50 p-3 rounded-xl transition-all duration-200 focus:border-indigo-400 focus:bg-slate-800 focus:ring-2 focus:ring-indigo-400/20 focus:outline-none"
                  placeholder="your@email.com"
                />
              </label>
              {/* Only show password input when not in reset mode */}
              {mode !== "reset" && (
                <label className="flex flex-col gap-2 text-sm">
                  <span className="font-medium text-slate-200 flex items-center gap-2">
                    🔒 Password
                  </span>
                  <div className="relative">
                    <input
                      type={showPassword ? "text" : "password"}
                      name="password"
                      autoComplete={mode === "signin" ? "current-password" : "new-password"}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      minLength={6}
                      className="bg-slate-800/80 border border-slate-600/50 p-3 rounded-xl transition-all duration-200 focus:border-indigo-400 focus:bg-slate-800 focus:ring-2 focus:ring-indigo-400/20 focus:outline-none w-full"
                      placeholder="••••••••"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(s => !s)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200 p-1"
                      aria-label={showPassword ? "Hide password" : "Show password"}
                    >
                      {showPassword ? (
                        // eye-off icon
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-5.523 0-10-4.477-10-10a9.96 9.96 0 012.141-5.8M6.1 6.1A9.956 9.956 0 0112 5c5.523 0 10 4.477 10 10 0 .9-.12 1.77-.35 2.6M3 3l18 18" />
                        </svg>
                      ) : (
                        // eye icon
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.477 0 8.268 2.943 9.542 7-1.274 4.057-5.065 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                          <circle cx="12" cy="12" r="3" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />
                        </svg>
                      )}
                    </button>
                  </div>
                </label>
              )}

              {/* Terms and Conditions acceptance for signup */}
              {mode === "signup" && (
                <label htmlFor="acceptTerms" className="flex items-start gap-3 text-sm">
                  <input
                    id="acceptTerms"
                    type="checkbox"
                    checked={acceptedTerms}
                    onChange={(e) => setAcceptedTerms(e.target.checked)}
                    className="w-4 h-4 mt-1 accent-cyan-500"
                    required
                  />
                  <span className="text-slate-400 leading-relaxed">
                    I agree to the{" "}
                    <button
                      type="button"
                      onClick={() => setShowTerms(true)}
                      className="text-cyan-400 hover:text-cyan-300 underline"
                    >
                      Terms and Conditions
                    </button>
                    {" "}and{" "}
                    <button
                      type="button"
                      onClick={() => setShowPrivacy(true)}
                      className="text-cyan-400 hover:text-cyan-300 underline"
                    >
                      Privacy Policy
                    </button>
                  </span>
                </label>
              )}

              {/* (moved) */}
            </div>
            {/* Inline row: Remember me (left) and Forgot password (right) */}
            {mode === "signin" && (
              <div className="flex items-center justify-between mt-2">
                <label htmlFor="remember" className="flex items-center gap-2 text-sm text-slate-400">
                  <input
                    id="remember"
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="w-4 h-4"
                  />
                  <span>Remember me</span>
                </label>

                <button
                  type="button"
                  onClick={() => { setMode("reset"); setStatus({ type: "idle" }); }}
                  className="text-xs text-cyan-400 hover:text-cyan-300 underline"
                >
                  Forgot password?
                </button>
              </div>
            )}

            {/* Email confirmation message */}
            {confirmationMessage && (
              <div className="flex items-center gap-2 p-3 rounded-xl text-sm bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 animate-in slide-in-from-top-2 duration-300">
                <span>✅</span>
                <span>{confirmationMessage}</span>
              </div>
            )}

            {/* Status messages */}
            {status.type !== "idle" && (
              <div className={`flex items-center gap-2 p-3 rounded-xl text-sm ${
                status.type === "success" 
                  ? "bg-cyan-500/10 border border-cyan-500/20 text-cyan-400" 
                  : "bg-rose-500/10 border border-rose-500/20 text-rose-400"
              }`}>
                <span>{status.type === "success" ? "✅" : "❌"}</span>
                <span>{status.msg}</span>
              </div>
            )}

            {/* Submit button */}
            <button
              disabled={loading || !email || (mode !== "reset" && !password) || (mode === "signup" && !acceptedTerms)}
              className="w-full bg-gradient-to-r from-indigo-600 to-cyan-600 disabled:from-slate-600 disabled:to-slate-600 disabled:cursor-not-allowed hover:from-indigo-500 hover:to-cyan-500 py-3 rounded-xl text-sm font-medium transition-all duration-200 shadow-lg hover:shadow-xl disabled:shadow-none transform hover:scale-[1.02] disabled:scale-100 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  {mode === "signin" ? "Signing in..." : mode === "signup" ? "Creating account..." : "Sending..."}
                </>
              ) : (
                <>
                  {mode === "signin" ? "🚀 Sign In" : mode === "signup" ? "✨ Create Account" : "✉️ Send reset link"}
                </>
              )}
            </button>
          </form>

          {/* Footer */}
          <div className="mt-6 pt-6 border-t border-slate-700/50">
            <p className="text-xs text-slate-500 text-center leading-relaxed">
              {mode === "signin" ? (
                <>
                  New to Morpheus?{" "}
                  <button
                    type="button"
                    onClick={() => {setMode("signup"); setStatus({type:"idle"});}}
                    className="text-cyan-400 hover:text-cyan-300 underline"
                  >
                    Create an account
                  </button>
                </>
              ) : (
                <>
                  Already have an account?{" "}
                  <button
                    type="button"
                    onClick={() => {setMode("signin"); setStatus({type:"idle"});}}
                    className="text-indigo-400 hover:text-indigo-300 underline"
                  >
                    Sign in
                  </button>
                </>
              )}
            </p>
           <p className="text-xs text-slate-600 text-center mt-3">
              {/* Legal notice: Terms and Privacy Policy */}
              By continuing, you agree to our Terms of Service and Privacy Policy.
              
            </p>
          </div>
        </div>

        {/* Bottom tagline */}
        <div className="text-center mt-6">
          <p className="text-slate-500 text-sm">
            Transform your sleep with AI-powered insights and coaching
          </p>
        </div>
      </div>

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

      {/* Terms and Conditions Modal */}
      {showTerms && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/70" onClick={() => setShowTerms(false)} />
          <div className="relative bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl max-w-4xl w-[95%] max-h-[85vh] overflow-y-auto p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-slate-100">Terms and Conditions</h3>
              <button
                onClick={() => setShowTerms(false)}
                className="text-slate-400 hover:text-slate-200"
                aria-label="Close terms and conditions"
              >
                ✕
              </button>
            </div>
            <TermsAndConditions />
          </div>
        </div>
      )}
    </div>
  );
}
