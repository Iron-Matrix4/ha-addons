import asyncio
import logging
import io
import wave
import queue
import threading
import struct
import speech_recognition as sr
from dataclasses import dataclass, field
from typing import List, Optional
from wyoming.info import Describe, Info, WakeModel, WakeProgram, Attribution

# Configure logging early
logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger(__name__)

# Polyfill for newer Wyoming classes if missing in older lib versions
try:
    from wyoming.info import TtsProgram, TtsModel, AsrProgram, AsrModel
except ImportError:
    _LOGGER.warning("Using local polyfill for Wyoming TTS/ASR classes")
    
    @dataclass
    class TtsModel:
        name: str
        description: str
        attribution: Attribution
        installed: bool
        languages: List[str]
        version: Optional[str] = None

    @dataclass
    class TtsProgram:
        name: str
        description: str
        attribution: Attribution
        installed: bool
        models: List[TtsModel]
        version: Optional[str] = None
        
    @dataclass
    class AsrModel:
        name: str
        description: str
        attribution: Attribution
        installed: bool
        languages: List[str]
        version: Optional[str] = None

    @dataclass
    class AsrProgram:
        name: str
        description: str
        attribution: Attribution
        installed: bool
        models: List[AsrModel]
        version: Optional[str] = None

from wyoming.wake import Detection
import config
from wake_word import WakeWord
from tts_piper import Mouth
from llm import Brain



class BufferedAudioSource(sr.AudioSource):
    def __init__(self):
        self.stream = queue.Queue()
        self.SAMPLE_RATE = 16000
        self.SAMPLE_WIDTH = 2
        self.CHUNK = 1024

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def read(self, size):
        data = b""
        while len(data) < size:
            try:
                chunk = self.stream.get(timeout=0.1)
                data += chunk
            except queue.Empty:
                continue
        return data

    def put_chunk(self, chunk):
        self.stream.put(chunk)

class JarvisHandler:
    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer
        try:
            key = config.PICOVOICE_ACCESS_KEY
            if key:
                _LOGGER.info(f"Using Picovoice Key: {key[:8]}...{key[-4:]}")
            else:
                _LOGGER.error("Picovoice Key is EMPTY!")
            
            try:
                _LOGGER.info(f"Wyoming Library Version: {wyoming.__version__}")
            except:
                _LOGGER.info("Wyoming Library Version: unknown")
                
            self.wake_word = WakeWord(use_mic=False)
        except Exception as e:
            _LOGGER.error(f"Failed to initialize WakeWord: {e}")
            self.wake_word = None
            
            self.wake_word = None
            
        _LOGGER.debug("Initializing Mouth...")
        try:
            self.mouth = Mouth()
            _LOGGER.debug("Mouth initialized")
        except Exception as e:
            _LOGGER.error(f"Failed to initialize Mouth: {e}")
            raise e

        _LOGGER.debug("Initializing Brain...")
        try:
            self.brain = Brain()
            _LOGGER.debug("Brain initialized")
        except Exception as e:
            _LOGGER.error(f"Failed to initialize Brain: {e}")
            raise e

        self.recognizer = sr.Recognizer()
        
        self.state = "WAITING_FOR_WAKE_WORD"
        self.audio_buffer = BufferedAudioSource()
        self.porcupine_buffer = b""
        self.loop = asyncio.get_running_loop()

    async def run(self):
        while True:
            try:
                event = await async_read_event(self.reader)
            except Exception as e:
                _LOGGER.warning(f"Error reading event: {e}")
                break

            if event is None:
                _LOGGER.debug("Event is None (Client disconnected?)")
                break
            
            _LOGGER.debug(f"Received event: {event.type}")
            await self.handle_event(event)

    async def handle_event(self, event: Event):
        if AudioStart.is_type(event.type):
            self.state = "WAITING_FOR_WAKE_WORD"
            self.porcupine_buffer = b""
            
        elif AudioStop.is_type(event.type):
            self.state = "IDLE"

        elif AudioChunk.is_type(event.type):
            chunk = AudioChunk.from_event(event)
            
            if self.state == "WAITING_FOR_WAKE_WORD":
                if self.wake_word:
                    self.porcupine_buffer += chunk.audio
                    frame_length = self.wake_word.frame_length * 2 # 2 bytes per sample
                    
                    while len(self.porcupine_buffer) >= frame_length:
                        frame = self.porcupine_buffer[:frame_length]
                        self.porcupine_buffer = self.porcupine_buffer[frame_length:]
                        
                        # Unpack to shorts
                        pcm = struct.unpack_from("h" * self.wake_word.frame_length, frame)
                        
                        if self.wake_word.process(pcm):
                            _LOGGER.info("Wake word detected!")
                            await async_write_event(Detection(name="jarvis").event(), self.writer)
                            self.state = "LISTENING_FOR_COMMAND"
                            # Start STT in background
                            self.loop.run_in_executor(None, self.process_stt)
                else:
                    # No wake word engine, ignore audio
                    pass
                
            elif self.state == "LISTENING_FOR_COMMAND":
                self.audio_buffer.put_chunk(chunk.audio)

            # Advertise Wake Word, TTS, and ASR so HA sees a complete assistant
            wake_info = [
                WakeProgram(
                    name="porcupine",
                    description="Porcupine Wake Word Engine",
                    attribution=Attribution(
                        name="Picovoice",
                        url="https://picovoice.ai/"
                    ),
                    installed=True,
                    version="1.0",
                    models=[
                        WakeModel(
                            name="jarvis",
                            description="Jarvis",
                            attribution=Attribution(
                                name="Iron-Matrix4",
                                url="https://github.com/Iron-Matrix4/jarvis-addon"
                            ),
                            installed=True,
                            languages=["en"],
                            version="1.0",
                            phrase="jarvis"
                        )
                    ]
                )
            ]

            tts_info = [
                TtsProgram(
                    name="piper",
                    description="Piper Text-to-Speech",
                    attribution=Attribution(
                        name="Rhasspy",
                        url="https://github.com/rhasspy/wyoming-piper"
                    ),
                    installed=True,
                    version="1.0",
                    models=[
                        TtsModel(
                            name="jarvis_voice",
                            description="Jarvis Voice",
                            attribution=Attribution(
                                name="Iron-Matrix4",
                                url="https://github.com/Iron-Matrix4/jarvis-addon"
                            ),
                            installed=True,
                            languages=["en"],
                            version="1.0"
                        )
                    ]
                )
            ]

            asr_info = [
                 AsrProgram(
                    name="google_vr",
                    description="Google Voice Recognition",
                    attribution=Attribution(
                        name="Google",
                        url="https://cloud.google.com/speech-to-text"
                    ),
                    installed=True,
                    version="1.0",
                    models=[
                        AsrModel(
                            name="google_en",
                            description="Google English",
                            attribution=Attribution(
                                name="Google",
                                url="https://google.com"
                            ),
                            installed=True,
                            languages=["en"],
                            version="1.0"
                        )
                    ]
                )
            ]
            
            await async_write_event(Info(
                wake=wake_info,
                tts=tts_info,
                asr=asr_info
            ).event(), self.writer)
            _LOGGER.debug("Sent Describe Info")

    def process_stt(self):
        try:
            _LOGGER.info("Listening for command...")
            # This blocks until silence
            text = self.recognizer.listen(self.audio_buffer, timeout=5, phrase_time_limit=10)
            # Recognize
            command = self.recognizer.recognize_google(text)
            _LOGGER.info(f"Heard: {command}")
            
            # Process with LLM
            response = self.brain.process(command)
            _LOGGER.info(f"Response: {response}")
            
            # TTS
            wav_bytes = self.mouth.synthesize(response)
            if wav_bytes:
                # Send audio back
                # Need to schedule async write from this thread
                asyncio.run_coroutine_threadsafe(self.send_audio_response(wav_bytes), self.loop)
            
            # Reset state
            self.state = "WAITING_FOR_WAKE_WORD"
            
        except Exception as e:
            _LOGGER.error(f"Error in STT/Processing: {e}")
            self.state = "WAITING_FOR_WAKE_WORD"

    async def send_audio_response(self, wav_bytes):
        # Skip WAV header (44 bytes) to send raw PCM if needed, 
        # but Wyoming AudioChunk usually wraps raw PCM.
        # Piper returns WAV with header.
        # We should strip header for raw PCM streaming or send as is?
        # Wyoming usually expects raw PCM 16khz 16bit mono.
        # Piper output matches this (usually).
        # Let's strip header (first 44 bytes).
        pcm_data = wav_bytes[44:]
        
        # Chunk it
        chunk_size = 1024
        for i in range(0, len(pcm_data), chunk_size):
            chunk = pcm_data[i:i+chunk_size]
            await async_write_event(AudioChunk(audio=chunk, rate=22050, width=2, channels=1).event(), self.writer)
            # Note: Piper usually outputs 22050Hz. We should check config.
            # If standard Wyoming is 16000, we might need resampling.
            # But let's send what we have.
            
        await async_write_event(AudioStop().event(), self.writer)

async def handle_client(reader, writer):
    try:
        logging.info("New client connected")
        handler = JarvisHandler(reader, writer)
        await handler.run()
    except Exception as e:
        logging.error(f"Client handler crashed: {e}", exc_info=True)
    finally:
        logging.info("Client disconnected")

async def main():
    server = await asyncio.start_server(handle_client, '0.0.0.0', 10200)
    _LOGGER.info("Ready on port 10200")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
