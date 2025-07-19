import asyncio
import queue
import threading
import time
from typing import Dict, Any, Optional, Callable, List

from google.cloud import speech
from google.api_core import exceptions as gcp_exceptions

from adapters.loggers.logger_adapter import app_logger
from core.interfaces.google_stt_streaming_client_interface import (
    GoogleSTTStreamingClientInterface,
)


class GoogleSTTEndlessStreamingClient(GoogleSTTStreamingClientInterface):
    STREAMING_LIMIT = 240000
    SAMPLE_RATE = 16000
    CHUNK_SIZE = int(SAMPLE_RATE / 10)

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
        self.audio_input: List[bytes] = []
        self.last_audio_input: List[bytes] = []

        self.is_streaming = False
        self._stop_event = threading.Event()
        self.closed = False

        self.start_time = self._get_current_time()
        self.restart_counter = 0
        self.result_end_time = 0
        self.is_final_end_time = 0
        self.final_request_end_time = 0
        self.bridging_offset = 0
        self.last_transcript_was_final = False
        self.new_stream = True

        self.result_callback: Optional[Callable[[Dict[str, Any]], None]] = None

    @staticmethod
    def _get_current_time() -> int:
        return int(round(time.time() * 1000))

    def setup_config(self, config_data: Dict[str, Any]) -> None:
        encoding_str = config_data.get("encoding", "LINEAR16").upper()
        if encoding_str not in [
            "WEBM_OPUS",
            "LINEAR16",
            "FLAC",
            "OGG_OPUS",
            "AMR",
            "AMR_WB",
        ]:
            encoding_str = "LINEAR16"
        encoding = getattr(speech.RecognitionConfig.AudioEncoding, encoding_str)

        sample_rate = config_data.get("sampleRateHertz", self.SAMPLE_RATE)

        self.config = speech.RecognitionConfig(
            encoding=encoding,
            sample_rate_hertz=sample_rate,
            language_code=config_data.get("languageCode", "en-US"),
            max_alternatives=config_data.get("maxAlternatives", 1),
            enable_word_time_offsets=config_data.get("enableWordTimeOffsets", False),
            enable_automatic_punctuation=config_data.get(
                "enableAutomaticPunctuation", True
            ),
            model=config_data.get("model", "latest_long"),
        )

        self.streaming_config = speech.StreamingRecognitionConfig(
            config=self.config,
            interim_results=config_data.get("interimResults", True),
            single_utterance=False,
        )

        self.audio_queue = queue.Queue()
        self._stop_event.clear()
        self.closed = False
        app_logger.info("Endless STT streaming configuration setup completed")

    def add_audio_chunk(self, audio_data: bytes) -> None:
        if self.audio_queue and not self._stop_event.is_set() and not self.closed:
            self.audio_queue.put(audio_data)
            self.audio_input.append(audio_data)

    def _audio_generator(self):
        while not self.closed and not self._stop_event.is_set():
            data = []

            if self.new_stream and self.last_audio_input:
                chunk_time = (
                    self.STREAMING_LIMIT / len(self.last_audio_input)
                    if self.last_audio_input
                    else 0
                )

                if chunk_time != 0:
                    if self.bridging_offset < 0:
                        self.bridging_offset = 0

                    if self.bridging_offset > self.final_request_end_time:
                        self.bridging_offset = self.final_request_end_time

                    chunks_from_ms = round(
                        (self.final_request_end_time - self.bridging_offset)
                        / chunk_time
                    )

                    self.bridging_offset = round(
                        (len(self.last_audio_input) - chunks_from_ms) * chunk_time
                    )

                    for i in range(chunks_from_ms, len(self.last_audio_input)):
                        data.append(self.last_audio_input[i])

                self.new_stream = False

            try:
                chunk = self.audio_queue.get(timeout=0.1)
                if chunk is None:
                    break
                data.append(chunk)

                while True:
                    try:
                        chunk = self.audio_queue.get(block=False)
                        if chunk is None:
                            break
                        data.append(chunk)
                    except queue.Empty:
                        break

                if data:
                    yield b"".join(data)

            except (queue.Empty, ValueError, TypeError):
                continue
            except gcp_exceptions.GoogleAPICallError as e:
                app_logger.error("Error in endless audio generator: %s", e)
                break

    def _process_response(
        self, response, stream_start_time: int
    ) -> Optional[Dict[str, Any]]:

        if self._get_current_time() - stream_start_time > self.STREAMING_LIMIT:
            return {"restart_needed": True}

        if not response.results:
            return None

        result = response.results[0]
        if not result.alternatives:
            return None

        transcript = result.alternatives[0].transcript

        result_seconds = (
            result.result_end_time.seconds if result.result_end_time.seconds else 0
        )
        result_micros = (
            result.result_end_time.microseconds
            if result.result_end_time.microseconds
            else 0
        )
        self.result_end_time = int((result_seconds * 1000) + (result_micros / 1000))

        corrected_time = (
            self.result_end_time
            - self.bridging_offset
            + (self.STREAMING_LIMIT * self.restart_counter)
        )

        payload = {
            "type": "final_result" if result.is_final else "interim_result",
            "transcript": transcript,
            "confidence": getattr(result.alternatives[0], "confidence", 0.0),
            "corrected_time": corrected_time,
            "restart_count": self.restart_counter,
        }

        if result.is_final:
            self.is_final_end_time = self.result_end_time
            self.last_transcript_was_final = True

            if (
                hasattr(result.alternatives[0], "words")
                and result.alternatives[0].words
            ):
                payload["wordTimestamps"] = [
                    {
                        "word": w.word,
                        "startTime": w.start_time.total_seconds(),
                        "endTime": w.end_time.total_seconds(),
                    }
                    for w in result.alternatives[0].words
                ]
        else:
            self.last_transcript_was_final = False

        return payload

    async def start_streaming(
        self, result_callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        if not self.config or not self.streaming_config:
            raise ValueError("Configuration not set. Call setup_config() first.")

        self.result_callback = result_callback
        self.is_streaming = True
        self.closed = False
        self.start_time = self._get_current_time()

        app_logger.info("Starting endless STT streaming recognition")

        try:
            await result_callback(
                {
                    "type": "streaming_started",
                    "message": "Endless streaming started",
                    "restart_count": self.restart_counter,
                }
            )

            while not self.closed and not self._stop_event.is_set():
                stream_start_time = self._get_current_time()

                await result_callback(
                    {
                        "type": "stream_restart",
                        "message": f"Stream restart #{self.restart_counter}",
                        "restart_count": self.restart_counter,
                        "time_offset": self.STREAMING_LIMIT * self.restart_counter,
                    }
                )

                self.audio_input = []

                try:

                    def request_generator():
                        for audio_chunk in self._audio_generator():
                            if self.closed or self._stop_event.is_set():
                                break
                            yield speech.StreamingRecognizeRequest(
                                audio_content=audio_chunk
                            )

                    responses = self.client.streaming_recognize(
                        self.streaming_config, request_generator()
                    )

                    for response in responses:
                        if self.closed or self._stop_event.is_set():
                            break

                        result = self._process_response(response, stream_start_time)
                        if result:
                            if result.get("restart_needed"):
                                app_logger.info("Time limit reached, restarting stream")
                                break

                            await result_callback(result)

                except gcp_exceptions.GoogleAPICallError as e:
                    app_logger.error("Google API error during endless streaming: %s", e)
                    await result_callback(
                        {
                            "type": "error",
                            "message": f"Google API error: {e}",
                            "restart_count": self.restart_counter,
                        }
                    )

                except (ValueError, TypeError, RuntimeError) as e:
                    app_logger.error("Unexpected error during endless streaming: %s", e)
                    await result_callback(
                        {
                            "type": "error",
                            "message": f"Streaming error: {e}",
                            "restart_count": self.restart_counter,
                        }
                    )

                if self.result_end_time > 0:
                    self.final_request_end_time = self.is_final_end_time

                self.result_end_time = 0
                self.last_audio_input = self.audio_input.copy()
                self.audio_input = []
                self.restart_counter += 1
                self.new_stream = True

                if not self.closed and not self._stop_event.is_set():
                    await asyncio.sleep(0.1)

        except (ValueError, TypeError, RuntimeError) as e:
            app_logger.error("Fatal error in endless streaming: %s", e)
            await result_callback(
                {"type": "fatal_error", "message": f"Fatal streaming error: {e}"}
            )
        finally:
            self.is_streaming = False
            app_logger.info("Endless STT streaming recognition stopped")

    def stop_streaming(self) -> None:
        app_logger.info("Stopping endless STT streaming recognition")
        self.closed = True
        self._stop_event.set()

        if self.audio_queue:
            self.audio_queue.put(None)

        self.is_streaming = False

    def is_active(self) -> bool:
        return self.is_streaming and not self._stop_event.is_set() and not self.closed
