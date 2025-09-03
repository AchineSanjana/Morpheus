import React, { useEffect, useState } from "react";
import { supabase } from "../lib/supabaseClient";

export default function ResetPassword() {
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [status, setStatus] = useState<{ type: "idle" | "success" | "error"; msg?: string }>({ type: "idle" });
  const [loading, setLoading] = useState(false);

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
    <div className="min-h-screen bg-gradient-to-br from-zinc-900 via-zinc-800 to-zinc-900 flex items-center justify-center p-4">
      <div className="relative w-full max-w-md">
        <div className="bg-zinc-900/80 backdrop-blur-xl border border-zinc-700/50 rounded-2xl p-8 shadow-2xl">
          <div className="text-center mb-6">
            <h2 className="text-xl font-semibold">Set a new password</h2>
            <p className="text-sm text-zinc-400 mt-2">Enter a new password for your account.</p>
          </div>

          <form onSubmit={submit} className="space-y-4">
            <label className="flex flex-col gap-2 text-sm">
              <span className="font-medium text-zinc-200">New password</span>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                minLength={6}
                required
                className="bg-zinc-800/80 border border-zinc-600/50 p-3 rounded-xl focus:border-violet-400 focus:ring-2 focus:ring-violet-400/20"
                placeholder="••••••••"
              />
            </label>

            <label className="flex flex-col gap-2 text-sm">
              <span className="font-medium text-zinc-200">Confirm password</span>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                minLength={6}
                required
                className="bg-zinc-800/80 border border-zinc-600/50 p-3 rounded-xl focus:border-violet-400 focus:ring-2 focus:ring-violet-400/20"
                placeholder="••••••••"
              />
              {confirmPassword && newPassword !== confirmPassword && (
                <p className="text-xs text-rose-400 mt-1">Passwords do not match</p>
              )}
            </label>

            {status.type !== "idle" && (
              <div className={`p-3 rounded-xl text-sm ${status.type === "success" ? "bg-emerald-500/10 border border-emerald-500/20 text-emerald-400" : "bg-rose-500/10 border border-rose-500/20 text-rose-400"}`}>
                <span>{status.msg}</span>
              </div>
            )}

            <div className="flex gap-2">
              <button
                type="submit"
                disabled={loading}
                className="flex-1 bg-gradient-to-r from-violet-600 to-emerald-600 py-3 rounded-xl text-sm font-medium"
              >
                {loading ? "Saving..." : "Set new password"}
              </button>
            </div>

            <div className="mt-4 text-center">
              <button
                type="button"
                onClick={goToLogin}
                className="text-sm text-emerald-400 hover:text-emerald-300 underline"
              >
                Back to sign in
              </button>
            </div>

          </form>
        </div>
      </div>
    </div>
  );
}
