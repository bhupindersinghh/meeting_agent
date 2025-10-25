import os
import base64
import io
import asyncio
from typing import Optional, Dict, Any
from openai import OpenAI
from pydub import AudioSegment
from pydub.playback import play
import speech_recognition as sr
from models.chatbot_models import VoiceConfig

class VoiceService:
    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Configure microphone
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
    
    async def text_to_speech(
        self, 
        text: str, 
        config: VoiceConfig = VoiceConfig()
    ) -> str:
        """Convert text to speech and return base64 encoded audio"""
        try:
            response = self.client.audio.speech.create(
                model="tts-1",
                voice=config.voice_id,
                input=text,
                speed=config.speed
            )
            
            # Convert to base64
            audio_data = response.content
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            return audio_base64
            
        except Exception as e:
            print(f"Error in text-to-speech: {e}")
            return ""
    
    async def speech_to_text(self, audio_data: str) -> str:
        """Convert base64 encoded audio to text"""
        try:
            # Decode base64 audio
            audio_bytes = base64.b64decode(audio_data)
            
            # Convert to AudioSegment for processing
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))
            
            # Convert to WAV format for speech recognition
            wav_data = io.BytesIO()
            audio_segment.export(wav_data, format="wav")
            wav_data.seek(0)
            
            # Use OpenAI Whisper for transcription
            wav_data.name = "audio.wav"
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=wav_data
            )
            
            return transcript.text
            
        except Exception as e:
            print(f"Error in speech-to-text: {e}")
            return ""
    
    async def listen_for_audio(self, timeout: int = 5) -> Optional[str]:
        """Listen for audio input from microphone and return transcribed text"""
        try:
            with self.microphone as source:
                print("Listening...")
                audio = self.recognizer.listen(source, timeout=timeout)
                
                # Use OpenAI Whisper for better accuracy
                audio_data = io.BytesIO(audio.get_wav_data())
                audio_data.name = "audio.wav"
                
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_data
                )
                
                return transcript.text
                
        except sr.WaitTimeoutError:
            print("No speech detected")
            return None
        except Exception as e:
            print(f"Error in audio listening: {e}")
            return None
    
    async def play_audio(self, audio_base64: str) -> None:
        """Play base64 encoded audio"""
        try:
            audio_data = base64.b64decode(audio_base64)
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_data))
            play(audio_segment)
            
        except Exception as e:
            print(f"Error playing audio: {e}")
    
    def get_available_voices(self) -> Dict[str, str]:
        """Get available voice options"""
        return {
            "alloy": "Alloy - Neutral, balanced tone",
            "echo": "Echo - Warm, friendly tone", 
            "fable": "Fable - Expressive, storytelling tone",
            "onyx": "Onyx - Deep, authoritative tone",
            "nova": "Nova - Bright, energetic tone",
            "shimmer": "Shimmer - Soft, gentle tone"
        }
    
    async def create_voice_response(
        self, 
        text: str, 
        voice_id: str = "alloy",
        speed: float = 1.0
    ) -> str:
        """Create a voice response with specified parameters"""
        config = VoiceConfig(voice_id=voice_id, speed=speed)
        return await self.text_to_speech(text, config)
    
    def analyze_audio_quality(self, audio_data: str) -> Dict[str, Any]:
        """Analyze audio quality and provide feedback"""
        try:
            audio_bytes = base64.b64decode(audio_data)
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))
            
            # Analyze audio properties
            duration = len(audio_segment) / 1000.0  # seconds
            sample_rate = audio_segment.frame_rate
            channels = audio_segment.channels
            
            # Calculate volume level
            volume = audio_segment.dBFS
            
            quality_score = 0
            feedback = []
            
            # Check duration
            if 1 <= duration <= 30:
                quality_score += 25
            else:
                feedback.append("Audio should be 1-30 seconds long")
            
            # Check volume
            if -20 <= volume <= -5:
                quality_score += 25
            elif volume < -20:
                feedback.append("Audio is too quiet")
            else:
                feedback.append("Audio is too loud")
            
            # Check sample rate
            if sample_rate >= 16000:
                quality_score += 25
            else:
                feedback.append("Audio quality is low")
            
            # Check channels
            if channels == 1:
                quality_score += 25
            else:
                feedback.append("Mono audio is preferred")
            
            return {
                "quality_score": quality_score,
                "duration": duration,
                "volume": volume,
                "sample_rate": sample_rate,
                "channels": channels,
                "feedback": feedback,
                "is_good_quality": quality_score >= 75
            }
            
        except Exception as e:
            return {
                "quality_score": 0,
                "error": str(e),
                "is_good_quality": False
            }
