"""
Google STT Streaming Client Module

This module provides the implementation for Google Cloud Speech-to-Text streaming client.
It handles real-time audio streaming, configuration, and bidirectional communication.
"""

import asyncio
import json
import queue
import threading
from typing import Dict, Any, Optional, Callable

from google.cloud import speech
from google.api_core import exceptions as gcp_exceptions

from adapters.loggers.logger_adapter import app_logger
from core.domain.stt_model import WordTimestamp
from core.interfaces.google_stt_streaming_client_interface import GoogleSTTStreamingClientInterface


class GoogleSTTStreamingClient(GoogleSTTStreamingClientInterface):
    FORMAT_MAPPING: Dict[str, Any] = {
        "webm": speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
        "webm_opus": speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
        "wav": speech.RecognitionConfig.AudioEncoding.LINEAR16,
        "linear16": speech.RecognitionConfig.AudioEncoding.LINEAR16,
        "flac": speech.RecognitionConfig.AudioEncoding.FLAC,
        "opus": speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
        "ogg_opus": speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
        "amr": speech.RecognitionConfig.AudioEncoding.AMR,
        "amr_wb": speech.RecognitionConfig.AudioEncoding.AMR_WB,
    }

    def __init__(self) -> None:
        self.client = speech.SpeechClient()
        self.config: Optional[speech.RecognitionConfig] = None
        self.streaming_config: Optional[speech.StreamingRecognitionConfig] = None
        self.audio_queue: Optional[queue.Queue] = None
        self.is_streaming = False
        self._stop_event = threading.Event()

    def setup_config(self, config_data: Dict[str, Any]) -> None:
        encoding_str = config_data.get("encoding", "WEBM_OPUS").upper()
        if encoding_str not in ["WEBM_OPUS","LINEAR16","FLAC","OGG_OPUS","AMR","AMR_WB"]:
            encoding_str = "WEBM_OPUS"
        encoding = getattr(speech.RecognitionConfig.AudioEncoding, encoding_str)

        self.config = speech.RecognitionConfig(
            encoding=encoding,
            sample_rate_hertz=config_data.get("sampleRateHertz", 48000),
            language_code=config_data.get("languageCode", "en-US"),
            max_alternatives=config_data.get("maxAlternatives", 1),
            enable_word_time_offsets=config_data.get("enableWordTimeOffsets", False),
            enable_automatic_punctuation=config_data.get("enableAutomaticPunctuation", True),
            model=config_data.get("model", "latest_long")
        )
        self.streaming_config = speech.StreamingRecognitionConfig(
            config=self.config,
            interim_results=config_data.get("interimResults", True),
            single_utterance=config_data.get("singleUtterance", False),
        )

        self.audio_queue = queue.Queue()
        self._stop_event.clear()
        app_logger.info("STT streaming configuration setup completed")

    def add_audio_chunk(self, audio_data: bytes) -> None:
        if self.audio_queue and not self._stop_event.is_set():
            self.audio_queue.put(audio_data)

    def _audio_generator(self):
        while not self._stop_event.is_set():
            try:
                chunk = self.audio_queue.get(timeout=0.1)
                if chunk is None:
                    break
                yield chunk
            except queue.Empty:
                continue
            except Exception as e:
                app_logger.error("Error in audio generator: %s", e)
                break

    async def start_streaming(self, result_callback: Callable[[Dict[str, Any]], None]) -> None:
        if not self.config or not self.streaming_config:
            raise ValueError("Configuration not set. Call setup_config() first.")
        self.is_streaming = True

        def request_generator():
            
            for audio_chunk in self._audio_generator():
                yield speech.StreamingRecognizeRequest(audio_content=audio_chunk)

        app_logger.info("Starting STT streaming recognition")

        
        responses = self.client.streaming_recognize(
            self.streaming_config,
            request_generator()
        )

        try:
            for response in responses:
                if self._stop_event.is_set():
                    break

                
                if getattr(response, "speech_event_type", None) == \
                   speech.StreamingRecognizeResponse.SpeechEventType.END_OF_SINGLE_UTTERANCE:
                    await result_callback({"type": "end_of_utterance"})
                    continue

                
                for result in response.results:
                    if not result.alternatives:
                        continue
                    alt = result.alternatives[0]
                    ts = None
                    if hasattr(alt, "words") and alt.words:
                        ts = [{
                            "word": w.word,
                            "startTime": w.start_time.total_seconds(),
                            "endTime": w.end_time.total_seconds()
                        } for w in alt.words]
                    payload = {
                        "type": "final_result" if result.is_final else "interim_result",
                        "transcript": alt.transcript,
                        "confidence": getattr(alt, "confidence", 0.0)
                    }
                    if result.is_final:
                        payload["wordTimestamps"] = ts
                    await result_callback(payload)

        except gcp_exceptions.GoogleAPICallError as e:
            app_logger.error("Google API error during streaming: %s", e)
            await result_callback({"type": "error", "message": f"Google API error: {e}"})
        except Exception as e:
            app_logger.error("Unexpected error during streaming: %s", e)
            await result_callback({"type": "error", "message": f"Streaming error: {e}"})
        finally:
            self.is_streaming = False
            app_logger.info("STT streaming recognition stopped")

    def stop_streaming(self) -> None:
        app_logger.info("Stopping STT streaming recognition")
        self._stop_event.set()
        if self.audio_queue:
            self.audio_queue.put(None)
        self.is_streaming = False

    def is_active(self) -> bool:
        return self.is_streaming and not self._stop_event.is_set()
