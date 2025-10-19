import React, { useState, useRef, useEffect } from 'react';

interface AudioPlayerProps {
  audioData: {
    available: boolean;
    file_id?: string;
    metadata?: {
      estimated_duration_minutes: number;
      estimated_duration_seconds: number;
      word_count: number;
    };
    error?: string;
  } | null;
}

export function AudioPlayer({ audioData }: AudioPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [loading, setLoading] = useState(false);
  const audioRef = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleTimeUpdate = () => setCurrentTime(audio.currentTime);
    const handleDurationChange = () => setDuration(audio.duration || 0);
    const handleEnded = () => setIsPlaying(false);
    const handleLoadStart = () => setLoading(true);
    const handleCanPlay = () => setLoading(false);

    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('durationchange', handleDurationChange);
    audio.addEventListener('ended', handleEnded);
    audio.addEventListener('loadstart', handleLoadStart);
    audio.addEventListener('canplay', handleCanPlay);

    return () => {
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('durationchange', handleDurationChange);
      audio.removeEventListener('ended', handleEnded);
      audio.removeEventListener('loadstart', handleLoadStart);
      audio.removeEventListener('canplay', handleCanPlay);
    };
  }, []);

  const togglePlayPause = () => {
    const audio = audioRef.current;
    if (!audio) return;

    if (isPlaying) {
      audio.pause();
    } else {
      audio.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const audio = audioRef.current;
    if (!audio) return;

    const seekPct = parseFloat(e.target.value);
    const seekTime = (seekPct / 100) * (duration || 0);
    audio.currentTime = seekTime;
    setCurrentTime(seekTime);
  };

  const formatTime = (seconds: number) => {
    const safe = isFinite(seconds) && seconds >= 0 ? seconds : 0;
    const mins = Math.floor(safe / 60);
    const secs = Math.floor(safe % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Dark-theme empty state to match app styling
  if (!audioData?.available) {
    return (
      <div className="bg-slate-800/70 border border-slate-700/50 rounded-2xl p-4 text-slate-200">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-cyan-500 rounded-full flex items-center justify-center text-white">🎵</div>
          <div>
            <h3 className="text-sm font-semibold">Audio Playback</h3>
            <p className="text-xs text-slate-400">
              {audioData?.error || "Say 'read to me' or 'audio' to get voice narration!"}
            </p>
          </div>
        </div>
      </div>
    );
  }

  const API_BASE = import.meta.env.VITE_API_URL as string;
  const audioUrl = audioData.file_id ? `${API_BASE}/audio/${audioData.file_id}` : '';

  return (
    <div className="bg-slate-800/80 border border-slate-700/50 rounded-2xl p-4 md:p-5 text-slate-100 shadow-md">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-cyan-500 rounded-full flex items-center justify-center text-white">🎧</div>
          <div>
            <h3 className="text-sm font-semibold">Audio Story</h3>
            <p className="text-xs text-slate-400">
              {audioData.metadata ? 
                `${Math.max(1, Math.round(audioData.metadata.estimated_duration_minutes))} min • ${audioData.metadata.word_count} words` :
                'Ready to play'}
            </p>
          </div>
        </div>
        {loading && (
          <div className="w-5 h-5 border-2 border-slate-500 border-t-indigo-400 rounded-full animate-spin" aria-label="Loading"></div>
        )}
      </div>

      <audio ref={audioRef} src={audioUrl} preload="metadata" />

      <div className="flex items-center gap-3">
        <button
          onClick={togglePlayPause}
          disabled={loading}
          className="w-10 h-10 rounded-full bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 disabled:from-slate-600 disabled:to-slate-600 text-white flex items-center justify-center shadow-lg shadow-black/20 ring-1 ring-slate-700/60 transition-colors"
          aria-label={isPlaying ? 'Pause' : 'Play'}
        >
          {loading ? (
            <div className="w-4 h-4 border border-white/70 border-t-transparent rounded-full animate-spin"></div>
          ) : isPlaying ? (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 002 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          ) : (
            <svg className="w-5 h-5 ml-0.5" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
            </svg>
          )}
        </button>

        <div className="flex-1">
          <input
            type="range"
            min="0"
            max="100"
            value={duration ? (currentTime / duration) * 100 : 0}
            onChange={handleSeek}
            className="w-full h-2 rounded-lg appearance-none cursor-pointer bg-slate-700/60"
            style={{
              background: `linear-gradient(to right, #22d3ee 0%, #22d3ee ${duration ? (currentTime / duration) * 100 : 0}%, #334155 ${duration ? (currentTime / duration) * 100 : 0}%, #334155 100%)`
            }}
            aria-label="Seek"
          />
          <div className="flex justify-between text-[11px] text-slate-400 mt-1">
            <span>{formatTime(currentTime)}</span>
            <span>{formatTime(duration)}</span>
          </div>
        </div>
      </div>

      <div className="mt-3 text-[11px] text-slate-400 flex items-center justify-between">
        <span>🎵 Optimized for bedtime with slower speech and calming pace</span>
        {audioData.metadata && (
          <span className="text-slate-400/80">
            {audioData.metadata.word_count} words • {Math.max(1, Math.round(audioData.metadata.estimated_duration_minutes))} min read
          </span>
        )}
      </div>
    </div>
  );
}