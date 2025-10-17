import os
import tempfile
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import hashlib
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time
import json
import re

import httpx

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

# Optional Edge TTS (Microsoft neural voices similar to Google Assistant)
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    edge_tts = None

# Try to import audio processing libraries for gentle effects
try:
    from pydub import AudioSegment
    from pydub.effects import normalize
    AUDIO_PROCESSING_AVAILABLE = True
except ImportError:
    AUDIO_PROCESSING_AVAILABLE = False
    AudioSegment = None
    normalize = None

ELEVENLABS_API_KEY_ENV = os.getenv("ELEVENLABS_API_KEY")
TTS_AVAILABLE = PYTTSX3_AVAILABLE or GTTS_AVAILABLE or bool(ELEVENLABS_API_KEY_ENV) or EDGE_TTS_AVAILABLE

if not TTS_AVAILABLE:
    logging.warning("Text-to-speech libraries not available. Install pyttsx3 and gTTS for audio features.")
elif not PYTTSX3_AVAILABLE:
    logging.warning("pyttsx3 not available, using gTTS only.")
elif not GTTS_AVAILABLE:
    logging.warning("gTTS not available, using pyttsx3 only.")

if not AUDIO_PROCESSING_AVAILABLE:
    logging.info("Audio processing (pydub) not available - gentle effects will use basic processing only.")

logger = logging.getLogger(__name__)

class AudioService:
    """Text-to-speech service for storyteller with caching and multiple engines"""
    
    def __init__(self):
        self.audio_cache_dir = Path("audio_cache")
        self.audio_cache_dir.mkdir(exist_ok=True)
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Audio settings optimized for gentle bedtime stories
        self.settings = {
            "speed": 120,        # Much slower for deeply relaxing speech (was 150)
            "volume": 0.7,       # Slightly softer volume for gentleness (was 0.8)
            "voice": "female",   # Preferred voice gender
            "language": "en",    # Language code
            "pitch": -10,        # Slightly lower pitch for more soothing voice (was 0)
            "pause_multiplier": 1.5,  # Longer pauses between sentences
            "gentle_mode": True,  # Enable gentle speech patterns
            # Provider preference (prefer Edge TTS neural voices if available)
            "provider": os.getenv("TTS_PROVIDER") or ("edge-tts" if EDGE_TTS_AVAILABLE else ("pyttsx3" if PYTTSX3_AVAILABLE else ("gtts" if GTTS_AVAILABLE else "none"))),
            # Edge TTS defaults (calming female voice similar to Google Assistant)
            "edge_tts_voice": os.getenv("EDGE_TTS_VOICE", "en-US-JennyNeural"),
            "edge_tts_rate": os.getenv("EDGE_TTS_RATE", "-10%"),
            # Edge TTS pitch expects values like "+0Hz"/"-2Hz" (not percentage). Use a gentle, slightly lower pitch.
            "edge_tts_pitch": os.getenv("EDGE_TTS_PITCH", "-2Hz"),
            # ElevenLabs (kept for compatibility, not required)
            "neural_provider": os.getenv("ELEVENLABS_API_PROVIDER", "elevenlabs"),
            "elevenlabs_api_key": os.getenv("ELEVENLABS_API_KEY"),
            "elevenlabs_voice_id": os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM"),
            "elevenlabs_model": os.getenv("ELEVENLABS_MODEL", "eleven_multilingual_v2"),
            # Diagnostics for status
            "selected_voice_name": None,
            "selected_voice_id": None,
        }
        
        # Initialize TTS engine
        self.tts_engine = None
        self._use_neural = bool(self.settings.get("elevenlabs_api_key"))
        if PYTTSX3_AVAILABLE:
            try:
                self.tts_engine = pyttsx3.init()
                self._configure_voice()
            except Exception as e:
                logger.warning(f"Failed to initialize pyttsx3: {e}")
                self.tts_engine = None
    
    def _configure_voice(self):
        """Configure the TTS voice for gentle bedtime stories."""
        if not self.tts_engine:
            return
            
        try:
            # Set slower speech rate for deeply relaxing effect
            self.tts_engine.setProperty('rate', self.settings["speed"])
            
            # Set gentler volume
            self.tts_engine.setProperty('volume', self.settings["volume"])
            
            # Try to select the most gentle, natural voice
            voices = self.tts_engine.getProperty('voices')
            if voices:
                # Prioritize voices for bedtime stories (gentle, soothing voices)
                preferred_voices = []
                
                # Look for specifically gentle voices first
                gentle_keywords = ['zira', 'hazel', 'susan', 'anna', 'emma', 'linda', 'natural', 'soft', 'jenny', 'aria', 'eva', 'olivia', 'sara']
                for voice in voices:
                    if voice and voice.name:
                        voice_name_lower = voice.name.lower()
                        for keyword in gentle_keywords:
                            if keyword in voice_name_lower:
                                preferred_voices.append(voice)
                                break
                
                # If no specifically gentle voices found, look for female voices
                if not preferred_voices:
                    female_voices = [v for v in voices if v and v.name and (
                        'female' in v.name.lower() or 'woman' in v.name.lower()
                    )]
                    if female_voices:
                        preferred_voices = female_voices
                
                # Use the best available voice
                if preferred_voices:
                    selected_voice = preferred_voices[0]
                    self.tts_engine.setProperty('voice', selected_voice.id)
                    self.settings["selected_voice_name"] = getattr(selected_voice, 'name', None)
                    self.settings["selected_voice_id"] = getattr(selected_voice, 'id', None)
                    logger.info(f"Selected gentle voice: {selected_voice.name}")
                else:
                    # Fallback to first available voice
                    self.tts_engine.setProperty('voice', voices[0].id)
                    self.settings["selected_voice_name"] = getattr(voices[0], 'name', None)
                    self.settings["selected_voice_id"] = getattr(voices[0], 'id', None)
                    logger.info(f"Using fallback voice: {voices[0].name}")
                    
        except Exception as e:
            logger.warning(f"Failed to configure TTS voice: {e}")
    
    def _preprocess_text_for_gentle_speech(self, text: str) -> str:
        """Preprocess text to make speech more gentle and natural."""
        if not text:
            return text
        
        # Add natural pauses and breathing points
        processed_text = text
        
        # Add longer pauses after sentences (for more relaxed delivery)
        processed_text = processed_text.replace('. ', '... ')
        processed_text = processed_text.replace('! ', '... ')
        processed_text = processed_text.replace('? ', '... ')
        
        # Add breathing pauses after commas
        processed_text = processed_text.replace(', ', ', ... ')
        
        # Add gentle pauses before dialogue
        processed_text = processed_text.replace('"', '... "')
        
        # Add calming pauses around transitional phrases
        transition_phrases = [
            ('And so', '... And so'),
            ('Meanwhile', '... Meanwhile'),
            ('As the', '... As the'),
            ('In the distance', '... In the distance'),
            ('Slowly', '... Slowly'),
            ('Gently', '... Gently'),
            ('Quietly', '... Quietly'),
            ('Softly', '... Softly')
        ]
        
        for original, replacement in transition_phrases:
            processed_text = processed_text.replace(original, replacement)
        
        # Clean up excessive pauses (no more than 3 dots in a row)
        while '....' in processed_text:
            processed_text = processed_text.replace('....', '...')
        
        return processed_text
    
    def _apply_gentle_audio_effects(self, audio_file_path: str) -> str:
        """Apply gentle audio effects (normalize, soften, fades) for bedtime listening."""
        if not AUDIO_PROCESSING_AVAILABLE:
            logger.info("Audio processing not available, returning original file")
            return audio_file_path
        
        try:
            # Load the audio file
            audio = AudioSegment.from_file(audio_file_path)
            
            # Apply gentle effects for bedtime listening
            
            # 1. Normalize volume to prevent sudden loud parts
            audio = normalize(audio)
            
            # 2. Reduce overall volume slightly for gentleness
            audio = audio - 3  # Reduce by 3dB
            
            # 3. Add gentle fade in and fade out
            fade_duration = min(2000, len(audio) // 10)  # 2 seconds or 10% of duration
            audio = audio.fade_in(fade_duration).fade_out(fade_duration)
            
            # 4. Apply subtle low-pass filter to soften harsh frequencies
            # This makes the voice warmer and more soothing
            if len(audio) > 0:
                # Simple way to soften: slightly reduce higher frequencies
                # by applying a gentle compression-like effect
                audio = audio.compress_dynamic_range(
                    threshold=-20.0,
                    ratio=2.0,
                    attack=50.0,
                    release=200.0
                ) if hasattr(audio, 'compress_dynamic_range') else audio
            
            # Save the processed audio
            processed_path = audio_file_path.replace('.', '_gentle.')
            audio.export(processed_path, format="mp3", bitrate="128k")
            
            # Remove original file and replace with processed version
            if os.path.exists(processed_path):
                os.remove(audio_file_path)
                os.rename(processed_path, audio_file_path)
                logger.info("Applied gentle audio effects for bedtime listening")
            
            return audio_file_path
            
        except Exception as e:
            logger.warning(f"Failed to apply gentle audio effects: {e}")
            return audio_file_path  # Return original file if processing fails
    
    def _get_cache_key(self, text: str, settings: Dict[str, Any]) -> str:
        """Generate a stable cache key for the audio content and settings."""
        provider = settings.get("provider") or ("edge-tts" if EDGE_TTS_AVAILABLE else ("pyttsx3" if PYTTSX3_AVAILABLE else ("gtts" if GTTS_AVAILABLE else "none")))
        voice_key = settings.get('edge_tts_voice') if provider == 'edge-tts' else (
            settings.get('elevenlabs_voice_id') if provider == 'elevenlabs' else settings.get('selected_voice_id', '')
        )
        content = f"{provider}_{voice_key}_{text}_{settings['speed']}_{settings['voice']}_{settings['language']}_{settings.get('pitch', 0)}_{settings.get('gentle_mode', False)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def text_to_speech_file(
        self, 
        text: str, 
        output_format: str = "mp3",
        use_cache: bool = True
    ) -> Optional[str]:
        """Convert text to speech and return file path (cached when possible)."""
        
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
        """Generate audio file using the selected/available TTS engine with fallbacks."""
        provider = self.settings.get("provider")
        # For neural-like providers, keep original text to avoid over-pausing
        processed_text = text if provider in ("edge-tts", "elevenlabs") else self._preprocess_text_for_gentle_speech(text)

        # Preferred: Edge TTS (smooth neural voice similar to Google Assistant)
        if provider == "edge-tts" and EDGE_TTS_AVAILABLE:
            try:
                return await self._generate_with_edge_tts(processed_text, output_path, format)
            except Exception as e:
                logger.warning(f"Edge TTS failed, trying next provider: {e}")

        # ElevenLabs (only if explicitly chosen and key present)
        if provider == "elevenlabs" and self.settings.get("elevenlabs_api_key"):
            try:
                return await self._generate_with_elevenlabs(processed_text, output_path, format)
            except Exception as e:
                logger.warning(f"ElevenLabs failed, trying next provider: {e}")

        # Offline/local pyttsx3
        if self.tts_engine:
            try:
                return await self._generate_with_pyttsx3(processed_text, output_path)
            except Exception as e:
                logger.warning(f"pyttsx3 failed, trying gTTS: {e}")

        # Fallback: gTTS
        try:
            return await self._generate_with_gtts(processed_text, output_path, format)
        except Exception as e:
            logger.error(f"All TTS engines failed: {e}")
            return None
    
    async def _generate_with_pyttsx3(self, text: str, output_path: Path) -> str:
        """Generate audio using pyttsx3 (offline) with gentle post-processing."""
        
        def _generate():
            temp_file = str(output_path.with_suffix('.wav'))
            # Remove existing temp file if it exists
            if os.path.exists(temp_file):
                os.remove(temp_file)
            self.tts_engine.save_to_file(text, temp_file)
            self.tts_engine.runAndWait()
            return temp_file
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        audio_file = await loop.run_in_executor(self.executor, _generate)
        
        # Convert to MP3 if needed
        if output_path.suffix == '.mp3':
            final_path = str(output_path)
            if os.path.exists(audio_file):
                # Remove existing MP3 file if it exists
                if os.path.exists(final_path):
                    os.remove(final_path)
                os.rename(audio_file, final_path)
                audio_file = final_path
        
        # Apply gentle audio effects for better sleep experience
        if os.path.exists(audio_file):
            audio_file = self._apply_gentle_audio_effects(audio_file)
        
        return audio_file

    async def _generate_with_elevenlabs(self, text: str, output_path: Path, format: str) -> str:
        """Generate audio using ElevenLabs neural TTS for human-like narration."""
        api_key = self.settings.get("elevenlabs_api_key")
        voice_id = self.settings.get("elevenlabs_voice_id")
        model = self.settings.get("elevenlabs_model")
        if not api_key:
            raise Exception("ElevenLabs API key not configured")

        headers = {
            "xi-api-key": api_key,
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
        }
        payload = {
            "text": text,
            "model_id": model,
            # Gentle, narrative voice settings
            "voice_settings": {
                "stability": 0.45,
                "similarity_boost": 0.85,
                "style": 0.6,           # more expressive
                "use_speaker_boost": True
            }
        }

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        # Write directly to the expected mp3 path
        out_path = str(output_path.with_suffix(".mp3")) if output_path.suffix.lower() != ".mp3" else str(output_path)

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(url, headers=headers, content=json.dumps(payload))
            if resp.status_code >= 400:
                raise Exception(f"ElevenLabs TTS error {resp.status_code}: {resp.text[:200]}")
            # Save audio content
            # Remove existing file if present
            if os.path.exists(out_path):
                os.remove(out_path)
            with open(out_path, "wb") as f:
                f.write(resp.content)

        # Optional: still apply gentle audio effects (fade/normalize)
        if os.path.exists(out_path):
            _ = self._apply_gentle_audio_effects(out_path)
        return out_path
    
    async def _generate_with_edge_tts(self, text: str, output_path: Path, format: str) -> str:
        """Generate audio using Edge TTS neural voices."""
        if not EDGE_TTS_AVAILABLE:
            raise Exception("edge-tts not available")

        voice = self.settings.get("edge_tts_voice", "en-US-AriaNeural")
        rate = self.settings.get("edge_tts_rate", "-10%")
        pitch = self.settings.get("edge_tts_pitch", "-2Hz")

        # Validate and normalize rate/pitch for edge-tts
        # rate must be like "+0%" or "-10%"; pitch should be like "+0Hz"/"-2Hz"
        if not isinstance(rate, str) or not re.match(r"^[+-]?\d+%$", rate):
            logger.warning(f"Invalid Edge TTS rate '{rate}', falling back to -10%")
            rate = "-10%"
        if not isinstance(pitch, str) or not re.match(r"^[+-]?\d+Hz$", pitch):
            logger.warning(f"Invalid Edge TTS pitch '{pitch}', falling back to -2Hz")
            pitch = "-2Hz"

        # Track selected voice
        self.settings["selected_voice_name"] = voice
        self.settings["selected_voice_id"] = voice

        out_path = str(output_path.with_suffix(".mp3")) if output_path.suffix.lower() != ".mp3" else str(output_path)
        if os.path.exists(out_path):
            os.remove(out_path)

        communicate = edge_tts.Communicate(text, voice=voice, rate=rate, pitch=pitch)
        with open(out_path, "wb") as f:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])

        if os.path.exists(out_path):
            _ = self._apply_gentle_audio_effects(out_path)
        return out_path
    
    async def _generate_with_gtts(self, text: str, output_path: Path, format: str) -> str:
        """Generate audio using Google TTS (online) with gentle settings and post-processing"""
        
        if not GTTS_AVAILABLE:
            raise Exception("gTTS not available")
        
        def _generate():
            tts = gTTS(
                text=text, 
                lang=self.settings["language"], 
                slow=False,  # Natural pacing; rely on light preprocessing
                tld='com'   # Use .com domain for most natural voice
            )
            
            output_file = str(output_path)
            # Remove existing file if it exists
            if os.path.exists(output_file):
                os.remove(output_file)
            tts.save(output_file)
            return output_file
        
        # Run in thread pool
        loop = asyncio.get_event_loop()
        audio_file = await loop.run_in_executor(self.executor, _generate)
        
        # Apply gentle audio effects for better sleep experience
        if os.path.exists(audio_file):
            audio_file = self._apply_gentle_audio_effects(audio_file)
        
        return audio_file
    
    def get_audio_metadata(self, text: str) -> Dict[str, Any]:
        """Get metadata about the audio that would be generated"""
        word_count = len(text.split())
        # Account for the gentler speech rate and added pauses
        effective_speed = self.settings["speed"] * 0.8  # Slower due to pauses
        estimated_duration = (word_count / effective_speed) * 60  # seconds
        
        return {
            "estimated_duration_seconds": int(estimated_duration),
            "estimated_duration_minutes": round(estimated_duration / 60, 1),
            "word_count": word_count,
            "speech_rate": self.settings["speed"],
            "effective_speech_rate": int(effective_speed),
            "voice_settings": self.settings.copy(),
            "provider": self.settings.get("provider"),
            "selected_voice": self.settings.get("selected_voice_name"),
            "gentle_mode": self.settings.get("gentle_mode", False),
            "audio_effects": {
                "gentle_processing": AUDIO_PROCESSING_AVAILABLE,
                "fade_in_out": True,
                "volume_normalization": True,
                "natural_pauses": True
            },
            "format": "mp3",
            "size_estimate_mb": round(estimated_duration * 0.1, 1)  # Rough estimate
        }

    def get_status(self) -> Dict[str, Any]:
        """Expose provider/voice and feature flags for status endpoint."""
        provider = self.settings.get("provider")
        return {
            "provider": provider,
            "selected_voice": {
                "name": self.settings.get("selected_voice_name"),
                "id": self.settings.get("selected_voice_id"),
            },
            "providers_available": {
                "edge_tts": EDGE_TTS_AVAILABLE,
                "pyttsx3": PYTTSX3_AVAILABLE,
                "gtts": GTTS_AVAILABLE,
                "elevenlabs": bool(self.settings.get("elevenlabs_api_key")),
            },
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