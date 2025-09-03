import base64
import os
from typing import Dict, Any

from google.cloud import speech
from google.api_core import exceptions as gcp_exceptions

from core.domain.stt_model import STTRequest, STTResponse, WordTimestamp
from core.interfaces.google_stt_client_interface import GoogleSTTClientInterface


class GoogleSTTClient(GoogleSTTClientInterface):
    FORMAT_MAPPING: Dict[str, Any] = {
        "webm": speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
        "wav": speech.RecognitionConfig.AudioEncoding.LINEAR16,
        "flac": speech.RecognitionConfig.AudioEncoding.FLAC,
        "opus": speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
        "amr": speech.RecognitionConfig.AudioEncoding.AMR,
        "amr_wb": speech.RecognitionConfig.AudioEncoding.AMR_WB,
    }

    def __init__(self) -> None:
        creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "audio-engine-key.json")
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds
        self.client = speech.SpeechClient()

    def transcribe_speech(self, request: STTRequest) -> STTResponse:
        try:

            audio_data = base64.b64decode(request.audio_data)

            encoding = self.FORMAT_MAPPING.get(request.format.lower())
            if not encoding:
                return STTResponse(
                    transcription="",
                    confidence=0.0,
                    success=False,
                    error_message=f"Unsupported audio format: {request.format}",
                )

            config = speech.RecognitionConfig(
                encoding=encoding,
                sample_rate_hertz=request.sample_rate,
                language_code=request.language,
                enable_automatic_punctuation=request.enable_automatic_punctuation,
                enable_word_time_offsets=request.enable_word_timestamps,
                model=request.model,
            )

            audio = speech.RecognitionAudio(content=audio_data)

            response = self.client.recognize(config=config, audio=audio)

            if response.results:
                result = response.results[0]
                alternative = result.alternatives[0]
                transcription = alternative.transcript
                confidence = alternative.confidence or 0.0

                word_timestamps = None
                if request.enable_word_timestamps and hasattr(alternative, "words"):
                    word_timestamps = [
                        WordTimestamp(
                            word=word.word,
                            start_time=word.start_time.total_seconds(),
                            end_time=word.end_time.total_seconds(),
                        )
                        for word in alternative.words
                    ]

                return STTResponse(
                    transcription=transcription,
                    confidence=confidence,
                    success=True,
                    word_timestamps=word_timestamps,
                )
            else:
                return STTResponse(
                    transcription="",
                    confidence=0.0,
                    success=False,
                    error_message="No speech detected",
                )

        except (
            gcp_exceptions.GoogleAPICallError,
            AttributeError,
        ) as e:
            return STTResponse(
                transcription="",
                confidence=0.0,
                success=False,
                error_message=f"STT transcription failed: {str(e)}",
            )
        except (UnicodeDecodeError, TypeError) as decode_error:

            return STTResponse(
                transcription="",
                confidence=0.0,
                success=False,
                error_message=f"Audio data decoding error: {str(decode_error)}",
            )
        except ValueError as value_error:
            return STTResponse(
                transcription="",
                confidence=0.0,
                success=False,
                error_message=f"Invalid request parameters: {str(value_error)}",
            )
        except (OSError, IOError, RuntimeError) as system_error:

            return STTResponse(
                transcription="",
                confidence=0.0,
                success=False,
                error_message=f"System error during STT transcription: {str(system_error)}",
            )
