import { useEffect, useState } from "react";
import { supabase } from "../lib/supabaseClient";

export function Auth({ onAuthed }:{ onAuthed:()=>void }) {
  const [email,setEmail]=useState(""); 
  const [password,setPassword]=useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [mode,setMode]=useState<"signin"|"signup">("signin");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<{type:"idle"|"success"|"error";msg?:string}>({type:"idle"});

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
      const {error}=await supabase.auth.signUp({ email, password });
      if (error) {
        setStatus({type:"error", msg: error.message});
      } else {
        setStatus({type:"success", msg: "Check your email to confirm your account!"});
      }
    } else {
      const {error}=await supabase.auth.signInWithPassword({ email, password });
      if (error) {
        setStatus({type:"error", msg: error.message});
      } else {
        setStatus({type:"success", msg: "Welcome back!"});
        onAuthed();
      }
    }
    setLoading(false);
  }

  // Forgot / reset password
  async function resetPassword() {
    setStatus({type: "idle"});
    if (!email) {
      setStatus({type: "error", msg: "Enter your email address to reset password."});
      return;
    }
    setLoading(true);
    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email);
      if (error) {
        setStatus({type: "error", msg: error.message});
      } else {
        setStatus({type: "success", msg: "Password reset email sent — check your inbox (and spam)."});
      }
    } catch (err: any) {
      setStatus({type: "error", msg: err?.message || "Failed to send reset email."});
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-zinc-900 via-zinc-800 to-zinc-900 flex items-center justify-center p-4">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-violet-500/20 rounded-full blur-3xl"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-emerald-500/20 rounded-full blur-3xl"></div>
      </div>

      <div className="relative w-full max-w-md">
        {/* Main auth card */}
        <div className="bg-zinc-900/80 backdrop-blur-xl border border-zinc-700/50 rounded-2xl p-8 shadow-2xl">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-gradient-to-br from-violet-500 to-emerald-500 rounded-2xl flex items-center justify-center text-3xl mb-4 mx-auto">
              💤
            </div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-violet-400 to-emerald-400 bg-clip-text text-transparent">
              Morpheus
            </h1>
            <p className="text-zinc-400 text-sm mt-2">
              Your AI-powered sleep improvement companion
            </p>
          </div>

          {/* Tab switcher */}
          <div className="flex bg-zinc-800/50 rounded-xl p-1 mb-6">
            <button
              type="button"
              onClick={() => {setMode("signin"); setStatus({type:"idle"});}}
              className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-all duration-200 ${
                mode === "signin" 
                  ? "bg-gradient-to-r from-violet-600 to-emerald-600 text-white shadow-lg" 
                  : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => {setMode("signup"); setStatus({type:"idle"});}}
              className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-all duration-200 ${
                mode === "signup" 
                  ? "bg-gradient-to-r from-violet-600 to-emerald-600 text-white shadow-lg" 
                  : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              Sign Up
            </button>
          </div>

          {/* Form */}
          <form onSubmit={submit} className="space-y-6">
            <div className="space-y-4">
              <label className="flex flex-col gap-2 text-sm">
                <span className="font-medium text-zinc-200 flex items-center gap-2">
                  📧 Email
                </span>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="bg-zinc-800/80 border border-zinc-600/50 p-3 rounded-xl transition-all duration-200 focus:border-violet-400 focus:bg-zinc-800 focus:ring-2 focus:ring-violet-400/20 focus:outline-none"
                  placeholder="your@email.com"
                />
              </label>

              {mode === "signin" && (
                <div className="text-right mt-2">
                  <button
                    type="button"
                    onClick={resetPassword}
                    disabled={loading}
                    className="text-xs text-emerald-400 hover:underline"
                  >
                    Forgot password?
                  </button>
                </div>
              )}

              <label className="flex flex-col gap-2 text-sm">
                <span className="font-medium text-zinc-200 flex items-center gap-2">
                  🔑 Password
                </span>
                <div className="relative">
                  <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={e=>setPassword(e.target.value)}
                    required
                    className="w-full bg-zinc-800/80 border border-zinc-600/50 p-3 pr-12 rounded-xl transition-all duration-200 focus:border-violet-400 focus:bg-zinc-800 focus:ring-2 focus:ring-violet-400/20 focus:outline-none"
                    placeholder="••••••••"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-0 top-0 h-full px-4 text-zinc-400 hover:text-emerald-400 transition-colors"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? (
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                    ) : (
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.542-7 1.274-4.057 5.064 7 9.542 7 .645 0 1.278.066 1.88.188M15 12a3 3 0 11-6 0 3 3 0 016 0zm6 0a9.953 9.953 0 01-1.88 5.812M12 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                    )}
                  </button>
                </div>
              </label>
            </div>

            {/* Status messages */}
            {status.type !== "idle" && (
              <div className={`flex items-center gap-2 p-3 rounded-xl text-sm ${
                status.type === "success" 
                  ? "bg-emerald-500/10 border border-emerald-500/20 text-emerald-400" 
                  : "bg-rose-500/10 border border-rose-500/20 text-rose-400"
              }`}>
                <span>{status.type === "success" ? "✅" : "❌"}</span>
                <span>{status.msg}</span>
              </div>
            )}

            {/* Submit button */}
            <button
              disabled={loading || !email || !password}
              className="w-full bg-gradient-to-r from-violet-600 to-emerald-600 disabled:from-zinc-600 disabled:to-zinc-600 disabled:cursor-not-allowed hover:from-violet-500 hover:to-emerald-500 py-3 rounded-xl text-sm font-medium transition-all duration-200 shadow-lg hover:shadow-xl disabled:shadow-none transform hover:scale-[1.02] disabled:scale-100 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  {mode === "signin" ? "Signing in..." : "Creating account..."}
                </>
              ) : (
                <>
                  {mode === "signin" ? "🚀 Sign In" : "✨ Create Account"}
                </>
              )}
            </button>
          </form>

          {/* Footer */}
          <div className="mt-6 pt-6 border-t border-zinc-700/50">
            <p className="text-xs text-zinc-500 text-center leading-relaxed">
              {mode === "signin" ? (
                <>
                  New to Morpheus?{" "}
                  <button
                    type="button"
                    onClick={() => {setMode("signup"); setStatus({type:"idle"});}}
                    className="text-emerald-400 hover:text-emerald-300 underline"
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
                    className="text-violet-400 hover:text-violet-300 underline"
                  >
                    Sign in
                  </button>
                </>
              )}
            </p>
            <p className="text-xs text-zinc-600 text-center mt-3">
              By continuing, you agree to our Terms of Service and Privacy Policy
            </p>
          </div>
        </div>

        {/* Bottom tagline */}
        <div className="text-center mt-6">
          <p className="text-zinc-500 text-sm">
            Transform your sleep with AI-powered insights and coaching
          </p>
        </div>
      </div>
    </div>
  );
}
