import { useState } from "react";
import type { Msg } from "../../lib/types";
import { supabase } from "../../lib/supabaseClient";

/**
 * GenerateAudioButton renders a round button that triggers audio generation
 * for assistant messages from the Storyteller agent. It calls the backend
 * API, then stores the returned audio file id on the message.
 */
export function GenerateAudioButton({
  message,
  messageIndex,
  setMsgs,
}: {
  message: Msg;
  messageIndex: number;
  setMsgs: React.Dispatch<React.SetStateAction<Msg[]>>;
}) {
  const [isGenerating, setIsGenerating] = useState(false);

  const isStoryteller =
    typeof message?.data?.agent === "string" &&
    message.data.agent.toLowerCase() === "storyteller";
  if (message.role !== "assistant" || !message.content || message.audioId || !isStoryteller)
    return null;

  /**
   * Calls the API to generate audio for the given message and updates the
   * corresponding message with the returned audioId.
   */
  const generateAudio = async () => {
    try {
      setIsGenerating(true);
      const {
        data: { session },
      } = await supabase.auth.getSession();
      if (!session) {
        throw new Error("Please sign in to generate audio");
      }

      const api = import.meta.env.VITE_API_URL as string;
      const response = await fetch(`${api}/audio/generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ text: message.content }),
      });

      if (!response.ok) {
        const text = await response.text().catch(() => "");
        throw new Error(text || "Failed to generate audio");
      }

      const audioData = await response.json();

      setMsgs((prev) => {
        const updatedMsgs = [...prev];
        updatedMsgs[messageIndex] = {
          ...updatedMsgs[messageIndex],
          audioId: audioData.audio_id,
        };
        return updatedMsgs;
      });
    } catch (error: any) {
      console.error("Audio generation error:", error);
      alert(error?.message || "Failed to generate audio");
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="mt-2 flex justify-end">
      <button
        onClick={generateAudio}
        disabled={isGenerating}
        aria-label={isGenerating ? "Generating audio..." : "Generate audio"}
        title={isGenerating ? "Generating audio..." : "Generate audio"}
        className="w-10 h-10 rounded-full bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 disabled:from-slate-600 disabled:to-slate-600 text-white flex items-center justify-center shadow-lg shadow-black/20 ring-1 ring-slate-700/60 transition-colors disabled:cursor-not-allowed"
      >
        {isGenerating ? (
          <div className="w-4 h-4 border-2 border-white/30 border-t-transparent rounded-full animate-spin" />
        ) : (
          <span className="text-lg">🔊</span>
        )}
      </button>
    </div>
  );
}
