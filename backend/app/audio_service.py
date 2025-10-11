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
TTS_AVAILABLE = PYTTSX3_AVAILABLE or GTTS_AVAILABLE or bool(ELEVENLABS_API_KEY_ENV)

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
            # Neural TTS provider settings (optional, enabled when API key present)
            "neural_provider": os.getenv("ELEVENLABS_API_PROVIDER", "elevenlabs"),
            "elevenlabs_api_key": os.getenv("ELEVENLABS_API_KEY"),
            # Default voice can be overridden via env: ELEVENLABS_VOICE_ID
            "elevenlabs_voice_id": os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM"),  # Rachel (example)
            # Model name; multilingual v2 is a good default for narration
            "elevenlabs_model": os.getenv("ELEVENLABS_MODEL", "eleven_multilingual_v2"),
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
        """Configure the TTS voice for gentle bedtime stories"""
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
                gentle_keywords = ['zira', 'hazel', 'susan', 'anna', 'emma', 'linda', 'natural', 'soft']
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
                    logger.info(f"Selected gentle voice: {selected_voice.name}")
                else:
                    # Fallback to first available voice
                    self.tts_engine.setProperty('voice', voices[0].id)
                    logger.info(f"Using fallback voice: {voices[0].name}")
                    
        except Exception as e:
            logger.warning(f"Failed to configure TTS voice: {e}")
    
    def _preprocess_text_for_gentle_speech(self, text: str) -> str:
        """Preprocess text to make speech more gentle and natural"""
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
        """Apply gentle audio effects to make the audio more soothing"""
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
        """Generate cache key for audio file"""
        provider = "elevenlabs" if settings.get("elevenlabs_api_key") else ("pyttsx3" if PYTTSX3_AVAILABLE else ("gtts" if GTTS_AVAILABLE else "none"))
        content = f"{provider}_{settings.get('elevenlabs_voice_id','')}_{text}_{settings['speed']}_{settings['voice']}_{settings['language']}_{settings.get('pitch', 0)}_{settings.get('gentle_mode', False)}"
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
        # Preprocess text for gentler speech. For neural voices (ElevenLabs), keep original text
        # to avoid over-pausing; their prosody is already natural.
        processed_text = self._preprocess_text_for_gentle_speech(text) if not self._use_neural else text

        # Prefer neural TTS if available (more natural)
        if self._use_neural:
            try:
                return await self._generate_with_elevenlabs(processed_text, output_path, format)
            except Exception as e:
                logger.warning(f"Neural TTS failed, falling back to local/legacy: {e}")

        # Try pyttsx3 first (offline, more natural for longer content)
        if self.tts_engine:
            try:
                return await self._generate_with_pyttsx3(processed_text, output_path)
            except Exception as e:
                logger.warning(f"pyttsx3 failed, trying gTTS: {e}")
        
        # Fallback to gTTS (online, but good quality)
        try:
            return await self._generate_with_gtts(processed_text, output_path, format)
        except Exception as e:
            logger.error(f"All TTS engines failed: {e}")
            return None
    
    async def _generate_with_pyttsx3(self, text: str, output_path: Path) -> str:
        """Generate audio using pyttsx3 (offline) with gentle post-processing"""
        
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
        """Generate audio using ElevenLabs neural TTS for more human-like narration"""
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
    
    async def _generate_with_gtts(self, text: str, output_path: Path, format: str) -> str:
        """Generate audio using Google TTS (online) with gentle settings and post-processing"""
        
        if not GTTS_AVAILABLE:
            raise Exception("gTTS not available")
        
        def _generate():
            tts = gTTS(
                text=text, 
                lang=self.settings["language"], 
                slow=True,  # Always use slow speech for gentle bedtime stories
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