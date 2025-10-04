import os
import tempfile
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import hashlib
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    pyttsx3 = None

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    gTTS = None

TTS_AVAILABLE = PYTTSX3_AVAILABLE or GTTS_AVAILABLE

if not TTS_AVAILABLE:
    logging.warning("Text-to-speech libraries not available. Install pyttsx3 and gTTS for audio features.")
elif not PYTTSX3_AVAILABLE:
    logging.warning("pyttsx3 not available, using gTTS only.")
elif not GTTS_AVAILABLE:
    logging.warning("gTTS not available, using pyttsx3 only.")

logger = logging.getLogger(__name__)

class AudioService:
    """Text-to-speech service for storyteller with caching and multiple engines"""
    
    def __init__(self):
        self.audio_cache_dir = Path("audio_cache")
        self.audio_cache_dir.mkdir(exist_ok=True)
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Audio settings optimized for bedtime stories
        self.settings = {
            "speed": 150,        # Words per minute (slower for bedtime)
            "volume": 0.8,       # Volume level
            "voice": "female",   # Preferred voice gender
            "language": "en",    # Language code
            "pitch": 0,          # Pitch adjustment
        }
        
        # Initialize TTS engine
        self.tts_engine = None
        if PYTTSX3_AVAILABLE:
            try:
                self.tts_engine = pyttsx3.init()
                self._configure_voice()
            except Exception as e:
                logger.warning(f"Failed to initialize pyttsx3: {e}")
                self.tts_engine = None
    
    def _configure_voice(self):
        """Configure the TTS voice for bedtime stories"""
        if not self.tts_engine:
            return
            
        try:
            # Set speech rate (slower for bedtime)
            self.tts_engine.setProperty('rate', self.settings["speed"])
            
            # Set volume
            self.tts_engine.setProperty('volume', self.settings["volume"])
            
            # Try to select a suitable voice
            voices = self.tts_engine.getProperty('voices')
            if voices:
                # Prefer female voices for bedtime stories
                female_voices = [v for v in voices if v and (
                    'female' in v.name.lower() or 'woman' in v.name.lower()
                )]
                if female_voices:
                    self.tts_engine.setProperty('voice', female_voices[0].id)
                else:
                    # Use first available voice
                    self.tts_engine.setProperty('voice', voices[0].id)
                    
        except Exception as e:
            logger.warning(f"Failed to configure TTS voice: {e}")
    
    def _get_cache_key(self, text: str, settings: Dict[str, Any]) -> str:
        """Generate cache key for audio file"""
        content = f"{text}_{settings['speed']}_{settings['voice']}_{settings['language']}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def text_to_speech_file(
        self, 
        text: str, 
        output_format: str = "mp3",
        use_cache: bool = True
    ) -> Optional[str]:
        """Convert text to speech and return file path"""
        
        if not TTS_AVAILABLE:
            logger.error("TTS libraries not available")
            return None
        
        if not text or len(text.strip()) == 0:
            return None
        
        # Check cache first
        cache_key = self._get_cache_key(text, self.settings)
        cached_file = self.audio_cache_dir / f"{cache_key}.{output_format}"
        
        if use_cache and cached_file.exists():
            logger.info(f"Using cached audio file: {cached_file}")
            return str(cached_file)
        
        # Generate new audio file
        try:
            output_file = await self._generate_audio_file(text, cached_file, output_format)
            return output_file
        except Exception as e:
            logger.error(f"Failed to generate audio: {e}")
            return None
    
    async def _generate_audio_file(self, text: str, output_path: Path, format: str) -> Optional[str]:
        """Generate audio file using available TTS engine"""
        
        # Try pyttsx3 first (offline, more natural for longer content)
        if self.tts_engine:
            try:
                return await self._generate_with_pyttsx3(text, output_path)
            except Exception as e:
                logger.warning(f"pyttsx3 failed, trying gTTS: {e}")
        
        # Fallback to gTTS (online, but good quality)
        try:
            return await self._generate_with_gtts(text, output_path, format)
        except Exception as e:
            logger.error(f"All TTS engines failed: {e}")
            return None
    
    async def _generate_with_pyttsx3(self, text: str, output_path: Path) -> str:
        """Generate audio using pyttsx3 (offline)"""
        
        def _generate():
            temp_file = str(output_path.with_suffix('.wav'))
            self.tts_engine.save_to_file(text, temp_file)
            self.tts_engine.runAndWait()
            return temp_file
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        audio_file = await loop.run_in_executor(self.executor, _generate)
        
        # Convert to MP3 if needed (optional enhancement)
        if output_path.suffix == '.mp3':
            # For now, just rename - could add conversion later
            final_path = str(output_path)
            if os.path.exists(audio_file):
                os.rename(audio_file, final_path)
                return final_path
        
        return audio_file
    
    async def _generate_with_gtts(self, text: str, output_path: Path, format: str) -> str:
        """Generate audio using Google TTS (online)"""
        
        if not GTTS_AVAILABLE:
            raise Exception("gTTS not available")
        
        def _generate():
            tts = gTTS(
                text=text, 
                lang=self.settings["language"], 
                slow=True  # Slower speech for bedtime
            )
            
            output_file = str(output_path)
            tts.save(output_file)
            return output_file
        
        # Run in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _generate)
    
    def get_audio_metadata(self, text: str) -> Dict[str, Any]:
        """Get metadata about the audio that would be generated"""
        word_count = len(text.split())
        estimated_duration = (word_count / self.settings["speed"]) * 60  # seconds
        
        return {
            "estimated_duration_seconds": int(estimated_duration),
            "estimated_duration_minutes": round(estimated_duration / 60, 1),
            "word_count": word_count,
            "speech_rate": self.settings["speed"],
            "voice_settings": self.settings.copy(),
            "format": "mp3",
            "size_estimate_mb": round(estimated_duration * 0.1, 1)  # Rough estimate
        }
    
    def cleanup_old_cache(self, max_age_days: int = 7):
        """Clean up old cached audio files"""
        try:
            current_time = time.time()
            max_age_seconds = max_age_days * 24 * 60 * 60
            
            for audio_file in self.audio_cache_dir.glob("*.mp3"):
                if current_time - audio_file.stat().st_mtime > max_age_seconds:
                    audio_file.unlink()
                    logger.info(f"Cleaned up old audio cache: {audio_file}")
                    
            for audio_file in self.audio_cache_dir.glob("*.wav"):
                if current_time - audio_file.stat().st_mtime > max_age_seconds:
                    audio_file.unlink()
                    logger.info(f"Cleaned up old audio cache: {audio_file}")
                    
        except Exception as e:
            logger.warning(f"Cache cleanup failed: {e}")

# Global audio service instance
audio_service = AudioService()