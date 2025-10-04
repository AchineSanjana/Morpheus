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
  storyText: string;
}

export function AudioPlayer({ audioData, storyText }: AudioPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [loading, setLoading] = useState(false);
  const audioRef = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleTimeUpdate = () => setCurrentTime(audio.currentTime);
    const handleDurationChange = () => setDuration(audio.duration);
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

    const seekTime = (parseFloat(e.target.value) / 100) * duration;
    audio.currentTime = seekTime;
    setCurrentTime(seekTime);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (!audioData?.available) {
    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
            🎵
          </div>
          <div>
            <h3 className="font-medium text-blue-900">Audio Playback</h3>
            <p className="text-sm text-blue-700">
              {audioData?.error || "Say 'read to me' or 'audio' to get voice narration!"}
            </p>
          </div>
        </div>
      </div>
    );
  }

  const audioUrl = audioData.file_id ? 
    `http://localhost:8000/audio/${audioData.file_id}` : 
    '';

  return (
    <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-4 mb-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
            🎧
          </div>
          <div>
            <h3 className="font-medium text-purple-900">Audio Story</h3>
            <p className="text-sm text-purple-700">
              {audioData.metadata ? 
                `${audioData.metadata.estimated_duration_minutes} min • ${audioData.metadata.word_count} words` :
                'Ready to play'
              }
            </p>
          </div>
        </div>
        
        {loading && (
          <div className="w-5 h-5 border-2 border-purple-300 border-t-purple-600 rounded-full animate-spin"></div>
        )}
      </div>

      <audio
        ref={audioRef}
        src={audioUrl}
        preload="metadata"
      />

      <div className="flex items-center space-x-3">
        <button
          onClick={togglePlayPause}
          disabled={loading}
          className="w-10 h-10 bg-purple-600 hover:bg-purple-700 disabled:bg-purple-300 text-white rounded-full flex items-center justify-center transition-colors"
        >
          {loading ? (
            <div className="w-4 h-4 border border-white border-t-transparent rounded-full animate-spin"></div>
          ) : isPlaying ? (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 002 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          ) : (
            <svg className="w-5 h-5 ml-0.5" fill="currentColor" viewBox="0 0 20 20">
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
            className="w-full h-2 bg-purple-200 rounded-lg appearance-none cursor-pointer"
            style={{
              background: `linear-gradient(to right, #7c3aed 0%, #7c3aed ${duration ? (currentTime / duration) * 100 : 0}%, #ddd6fe ${duration ? (currentTime / duration) * 100 : 0}%, #ddd6fe 100%)`
            }}
          />
          <div className="flex justify-between text-xs text-purple-600 mt-1">
            <span>{formatTime(currentTime)}</span>
            <span>{formatTime(duration)}</span>
          </div>
        </div>
      </div>

      <div className="mt-3 text-xs text-purple-600 flex items-center justify-between">
        <span>🎵 Optimized for bedtime with slower speech and calming pace</span>
        {audioData.metadata && (
          <span className="text-purple-500">
            {audioData.metadata.word_count} words • {Math.round(audioData.metadata.estimated_duration_minutes)} min read
          </span>
        )}
      </div>
    </div>
  );
}