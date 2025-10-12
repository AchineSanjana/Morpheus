import React, { useEffect, useState } from "react";
import { supabase } from "../lib/supabaseClient";
import morpheusLogo from "../assets/morpheus_logo.jpg";

export default function ResetPassword() {
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [status, setStatus] = useState<{ type: "idle" | "success" | "error"; msg?: string }>({ type: "idle" });
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // Parse tokens from URL (either search or hash)
  function readParams(): Record<string, string> {
    const params: Record<string, string> = {};
    try {
      const u = new URL(window.location.href);
      u.searchParams.forEach((v, k) => (params[k] = v));
      // also parse hash fragment
      if (u.hash && u.hash.startsWith("#")) {
        const hash = new URLSearchParams(u.hash.substring(1));
        hash.forEach((v, k) => (params[k] = v));
      }
    } catch (e) {
      // ignore
    }
    return params;
  }

  useEffect(() => {
    // nothing to do on mount except maybe check params
  }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setStatus({ type: "idle" });
    if (!newPassword || newPassword.length < 6) {
      setStatus({ type: "error", msg: "Password must be at least 6 characters." });
      return;
    }
    if (newPassword !== confirmPassword) {
      setStatus({ type: "error", msg: "Passwords do not match." });
      return;
    }
    setLoading(true);
    const params = readParams();

    try {
      // If the recovery flow provided an access_token in the URL, set it as session
      // so updateUser can run. Supabase exposes a method to set session via auth.setSession
      if (params.access_token) {
        // set session so the client is authorized to update the user
        await supabase.auth.setSession({ access_token: params.access_token, refresh_token: params.refresh_token || "" });
      }

      // call updateUser to set the new password
      const { error } = await supabase.auth.updateUser({ password: newPassword });
      if (error) {
        setStatus({ type: "error", msg: error.message });
      } else {
        setStatus({ type: "success", msg: "Password updated. Please sign in with your new password." });
        // sign out to clear any session
        await supabase.auth.signOut();
      }
    } catch (err: any) {
      setStatus({ type: "error", msg: err?.message || String(err) });
    } finally {
      setLoading(false);
    }
  }

  function goToLogin() {
    try {
      const u = new URL(window.location.href);
      // clear search and hash so the app doesn't treat it as a recovery link
      u.search = "";
      u.hash = "";
      // navigate to root of the app
      window.location.href = u.origin + (u.pathname || '/');
    } catch (e) {
      window.location.href = '/';
    }
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
        {/* Main reset password card */}
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
              Set a new password
            </h1>
            <p className="text-slate-400 text-sm mt-2">
              Enter a new password for your account.
            </p>
          </div>

          <form onSubmit={submit} className="space-y-5">
            <label className="flex flex-col gap-2 text-sm">
              <span className="font-medium text-slate-200 flex items-center gap-2">
                🔒 New password
              </span>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  minLength={6}
                  required
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

            <label className="flex flex-col gap-2 text-sm">
              <span className="font-medium text-slate-200 flex items-center gap-2">
                🔒 Confirm password
              </span>
              <div className="relative">
                <input
                  type={showConfirmPassword ? "text" : "password"}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  minLength={6}
                  required
                  className="bg-slate-800/80 border border-slate-600/50 p-3 rounded-xl transition-all duration-200 focus:border-indigo-400 focus:bg-slate-800 focus:ring-2 focus:ring-indigo-400/20 focus:outline-none w-full"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(s => !s)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200 p-1"
                  aria-label={showConfirmPassword ? "Hide password" : "Show password"}
                >
                  {showConfirmPassword ? (
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
              {confirmPassword && newPassword !== confirmPassword && (
                <p className="text-xs text-rose-400 mt-1">Passwords do not match</p>
              )}
            </label>

            {/* Status message */}
            {status.type !== "idle" && (
              <div className={`p-3 rounded-xl text-sm border ${
                status.type === "success" 
                  ? "bg-emerald-900/20 border-emerald-500/30 text-emerald-400" 
                  : "bg-red-900/20 border-red-500/30 text-red-400"
              }`}>
                {status.msg}
              </div>
            )}

            {/* Submit button */}
            <button
              type="submit"
              disabled={loading || !newPassword || newPassword !== confirmPassword}
              className="w-full bg-gradient-to-r from-indigo-600 to-cyan-600 disabled:from-slate-600 disabled:to-slate-600 disabled:cursor-not-allowed hover:from-indigo-500 hover:to-cyan-500 py-3 rounded-xl text-sm font-medium transition-all duration-200 shadow-lg hover:shadow-xl disabled:shadow-none transform hover:scale-[1.02] disabled:scale-100 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  Setting password...
                </>
              ) : (
                "🚀 Set new password"
              )}
            </button>
          </form>

          {/* Footer */}
          <div className="mt-6 pt-6 border-t border-slate-700/50">
            <p className="text-xs text-slate-500 text-center leading-relaxed">
              Remember your password?{" "}
              <button
                type="button"
                onClick={goToLogin}
                className="text-cyan-400 hover:text-cyan-300 underline"
              >
                Back to sign in
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
