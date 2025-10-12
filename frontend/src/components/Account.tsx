import { useEffect, useState } from "react";
import { supabase, supabaseSession } from "../lib/supabaseClient";
import { fetchProfile, updateProfile, uploadAvatar, type ProfileData } from "../lib/api";
import type { User } from "@supabase/supabase-js";

interface AccountProps {
  user: User;
  onClose: () => void;
}



export function Account({ user, onClose }: AccountProps) {
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [profile, setProfile] = useState<ProfileData | null>(null);
  
  // Form states
  const [editMode, setEditMode] = useState<"profile" | "email" | "password" | null>(null);
  const [newEmail, setNewEmail] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [status, setStatus] = useState<{type: "idle" | "success" | "error"; msg?: string}>({type: "idle"});

  useEffect(() => {
    if (user) {
      setNewEmail(user.email || "");
      getProfile();
    }
  }, [user]);

  const getActiveClient = () => {
    // Determine which client is being used based on stored preferences
    const storedRemember = localStorage.getItem("morpheus:remember");
    return storedRemember === "1" ? supabase : supabaseSession;
  };

  async function getProfile() {
    try {
      setLoading(true);
      const client = getActiveClient();
      const { data: { session } } = await client.auth.getSession();
      
      if (!session) {
        throw new Error("No active session");
      }

      const profileData = await fetchProfile(user.id, session.access_token);
      if (profileData) {
        setProfile(profileData);
      } else {
        // Create empty profile if none exists
        setProfile({
          id: user.id,
          full_name: null,
          username: null,
          avatar_url: null,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        });
      }
    } catch (error) {
      console.error("Error loading user data:", error);
      setStatus({ type: "error", msg: "Failed to load profile data" });
    } finally {
      setLoading(false);
    }
  }

  async function updateProfileData(updates: Partial<ProfileData>) {
    try {
      setLoading(true);
      const client = getActiveClient();
      const { data: { session } } = await client.auth.getSession();
      
      if (!session) {
        throw new Error("No active session");
      }

      const updatedProfile = await updateProfile(user.id, updates, session.access_token);
      setProfile(updatedProfile);
      setStatus({ type: "success", msg: "Profile updated successfully!" });
      setEditMode(null);
    } catch (error: any) {
      setStatus({ type: "error", msg: error.message });
    } finally {
      setLoading(false);
    }
  }

  async function handleAvatarUpload(event: React.ChangeEvent<HTMLInputElement>) {
    try {
      setUploading(true);
      setStatus({ type: "idle" });

      if (!event.target.files || event.target.files.length === 0) {
        throw new Error("You must select an image to upload.");
      }

      const file = event.target.files[0];
      const client = getActiveClient();
      const { data: { session } } = await client.auth.getSession();
      
      if (!session) {
        throw new Error("No active session");
      }

      const avatarUrl = await uploadAvatar(file, user.id, session.access_token);
      
      // Update local profile state
      setProfile(prev => prev ? { ...prev, avatar_url: avatarUrl } : null);
      setStatus({ type: "success", msg: "Profile picture updated successfully!" });
    } catch (error: any) {
      setStatus({ type: "error", msg: error.message });
    } finally {
      setUploading(false);
    }
  }

  async function updateEmail() {
    try {
      setLoading(true);
      setStatus({ type: "idle" });

      if (!newEmail || newEmail === user.email) {
        setStatus({ type: "error", msg: "Please enter a new email address." });
        return;
      }

      const client = getActiveClient();
      const { error } = await client.auth.updateUser({ email: newEmail });

      if (error) throw error;

      setStatus({ 
        type: "success", 
        msg: "Check your email (both old and new) to confirm the change!" 
      });
      setEditMode(null);
    } catch (error: any) {
      setStatus({ type: "error", msg: error.message });
    } finally {
      setLoading(false);
    }
  }

  async function updatePassword() {
    try {
      setLoading(true);
      setStatus({ type: "idle" });

      if (newPassword !== confirmPassword) {
        setStatus({ type: "error", msg: "New passwords do not match." });
        return;
      }

      if (newPassword.length < 6) {
        setStatus({ type: "error", msg: "Password must be at least 6 characters long." });
        return;
      }

      const client = getActiveClient();
      
      // First verify current password by attempting to re-authenticate
      const { error: verifyError } = await client.auth.signInWithPassword({
        email: user.email!,
        password: currentPassword,
      });

      if (verifyError) {
        setStatus({ type: "error", msg: "Current password is incorrect." });
        return;
      }

      // Update password
      const { error } = await client.auth.updateUser({ password: newPassword });

      if (error) throw error;

      setStatus({ type: "success", msg: "Password updated successfully!" });
      setEditMode(null);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (error: any) {
      setStatus({ type: "error", msg: error.message });
    } finally {
      setLoading(false);
    }
  }

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (editMode === "profile") {
      updateProfileData({
        full_name: (e.currentTarget as any).full_name.value,
        username: (e.currentTarget as any).username.value,
      });
    } else if (editMode === "email") {
      updateEmail();
    } else if (editMode === "password") {
      updatePassword();
    }
  };

  if (loading && !profile) {
    return (
  <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
        <div className="bg-gradient-to-br from-slate-900 to-slate-800 p-8 rounded-2xl border border-slate-700/50">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400 mx-auto"></div>
          <p className="text-slate-300 mt-4">Loading profile...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-gradient-to-br from-slate-900/95 to-slate-800/95 border border-slate-700/50 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-700/50">
          <h2 className="text-2xl font-bold bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent">
            Account Settings
          </h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-6 space-y-8">
          {/* Status Messages */}
          {status.type !== "idle" && (
            <div className={`p-4 rounded-lg border ${
              status.type === "success" 
                ? "bg-green-900/20 border-green-500/30 text-green-400" 
                : "bg-red-900/20 border-red-500/30 text-red-400"
            }`}>
              {status.msg}
            </div>
          )}

          {/* Profile Picture Section */}
          <div className="flex flex-col items-center space-y-4">
            <div className="relative">
              <div className="w-24 h-24 rounded-full overflow-hidden bg-gradient-to-br from-indigo-500 to-cyan-500 flex items-center justify-center">
                {profile?.avatar_url ? (
                  <img
                    src={profile.avatar_url}
                    alt="Avatar"
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <span className="text-white text-2xl font-bold">
                    {profile?.full_name?.charAt(0) || user.email?.charAt(0) || "?"}
                  </span>
                )}
              </div>
              <label className="absolute bottom-0 right-0 bg-indigo-600 hover:bg-indigo-700 text-white p-2 rounded-full cursor-pointer transition-colors shadow-lg">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleAvatarUpload}
                  disabled={uploading}
                  className="hidden"
                />
              </label>
            </div>
            {uploading && (
              <p className="text-sm text-cyan-400">Uploading image...</p>
            )}
          </div>

          {/* Profile Information */}
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-white">Profile Information</h3>
              <button
                onClick={() => setEditMode(editMode === "profile" ? null : "profile")}
                className="text-cyan-400 hover:text-cyan-300 transition-colors"
              >
                {editMode === "profile" ? "Cancel" : "Edit"}
              </button>
            </div>

            {editMode === "profile" ? (
              <form onSubmit={handleFormSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Full Name
                  </label>
                  <input
                    name="full_name"
                    type="text"
                    defaultValue={profile?.full_name || ""}
                    className="w-full p-3 bg-slate-800/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-transparent"
                    placeholder="Enter your full name"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Username
                  </label>
                  <input
                    name="username"
                    type="text"
                    defaultValue={profile?.username || ""}
                    className="w-full p-3 bg-slate-800/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-transparent"
                    placeholder="Enter your username"
                  />
                </div>
                <div className="flex gap-3">
                  <button
                    type="submit"
                    disabled={loading}
                    className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-cyan-600 text-white rounded-lg hover:from-indigo-700 hover:to-cyan-700 transition-all disabled:opacity-50"
                  >
                    {loading ? "Saving..." : "Save Changes"}
                  </button>
                  <button
                    type="button"
                    onClick={() => setEditMode(null)}
                    className="px-4 py-2 bg-slate-600 text-white rounded-lg hover:bg-slate-700 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            ) : (
              <div className="space-y-3">
                <div>
                  <p className="text-sm text-slate-400">Full Name</p>
                  <p className="text-white">{profile?.full_name || "Not set"}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400">Username</p>
                  <p className="text-white">{profile?.username || "Not set"}</p>
                </div>
              </div>
            )}
          </div>

          {/* Email Section */}
          <div className="space-y-6 border-t border-slate-700/50 pt-6">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-white">Email Address</h3>
              <button
                onClick={() => setEditMode(editMode === "email" ? null : "email")}
                className="text-cyan-400 hover:text-cyan-300 transition-colors"
              >
                {editMode === "email" ? "Cancel" : "Change"}
              </button>
            </div>

            {editMode === "email" ? (
              <form onSubmit={handleFormSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Current Email
                  </label>
                  <input
                    type="email"
                    value={user.email || ""}
                    disabled
                    className="w-full p-3 bg-slate-700/50 border border-slate-600 rounded-lg text-slate-400"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    New Email
                  </label>
                  <input
                    type="email"
                    value={newEmail}
                    onChange={(e) => setNewEmail(e.target.value)}
                    className="w-full p-3 bg-slate-800/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-transparent"
                    placeholder="Enter new email address"
                    required
                  />
                </div>
                <div className="flex gap-3">
                  <button
                    type="submit"
                    disabled={loading}
                    className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-cyan-600 text-white rounded-lg hover:from-indigo-700 hover:to-cyan-700 transition-all disabled:opacity-50"
                  >
                    {loading ? "Updating..." : "Update Email"}
                  </button>
                  <button
                    type="button"
                    onClick={() => setEditMode(null)}
                    className="px-4 py-2 bg-slate-600 text-white rounded-lg hover:bg-slate-700 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            ) : (
              <p className="text-white">{user.email}</p>
            )}
          </div>

          {/* Password Section */}
          <div className="space-y-6 border-t border-slate-700/50 pt-6">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-white">Password</h3>
              <button
                onClick={() => setEditMode(editMode === "password" ? null : "password")}
                className="text-cyan-400 hover:text-cyan-300 transition-colors"
              >
                {editMode === "password" ? "Cancel" : "Change"}
              </button>
            </div>

            {editMode === "password" ? (
              <form onSubmit={handleFormSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Current Password
                  </label>
                  <input
                    type="password"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    className="w-full p-3 bg-slate-800/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-transparent"
                    placeholder="Enter current password"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    New Password
                  </label>
                  <input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="w-full p-3 bg-slate-800/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-transparent"
                    placeholder="Enter new password"
                    required
                    minLength={6}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Confirm New Password
                  </label>
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full p-3 bg-slate-800/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-transparent"
                    placeholder="Confirm new password"
                    required
                    minLength={6}
                  />
                </div>
                <div className="flex gap-3">
                  <button
                    type="submit"
                    disabled={loading}
                    className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-cyan-600 text-white rounded-lg hover:from-indigo-700 hover:to-cyan-700 transition-all disabled:opacity-50"
                  >
                    {loading ? "Updating..." : "Update Password"}
                  </button>
                  <button
                    type="button"
                    onClick={() => setEditMode(null)}
                    className="px-4 py-2 bg-slate-600 text-white rounded-lg hover:bg-slate-700 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            ) : (
              <p className="text-slate-400">••••••••</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}