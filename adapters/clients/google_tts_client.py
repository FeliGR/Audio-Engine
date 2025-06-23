"""
Google TTS Client Module

This module provides the implementation for Google Cloud Text-to-Speech client.
It handles authentication, voice synthesis, and response formatting.
"""

import base64
import os

from google.cloud import texttospeech
from google.api_core import exceptions as gcp_exceptions

from core.domain.tts_model import TTSRequest, TTSResponse
from core.interfaces.google_tts_client_interface import GoogleTTSClientInterface


class GoogleTTSClient(
    GoogleTTSClientInterface
):  # pylint: disable=too-few-public-methods
    """
    Google Cloud Text-to-Speech client implementation.

    This class provides the implementation for synthesizing speech using
    Google Cloud Text-to-Speech API.
    """

    def __init__(self) -> None:
        """
        Initialize the Google TTS client.

        Sets up authentication using the GOOGLE_APPLICATION_CREDENTIALS
        environment variable or defaults to 'tts-key.json'.
        """
        creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "tts-key.json")
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds
        self.client = texttospeech.TextToSpeechClient()

    def synthesize_speech(self, request: TTSRequest) -> TTSResponse:
        """
        Synthesize speech from text using Google Cloud TTS.

        Args:
            request: TTS request containing text and voice configuration.

        Returns:
            TTSResponse containing the synthesized audio or error information.
        """
        try:
            synthesis_input = texttospeech.SynthesisInput(text=request.text)

            voice = texttospeech.VoiceSelectionParams(
                language_code=request.voice_config.language_code,
                name=request.voice_config.name,
                ssml_gender=getattr(
                    texttospeech.SsmlVoiceGender, request.voice_config.ssml_gender
                ),
            )

            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=request.voice_config.speaking_rate,
                pitch=request.voice_config.pitch,
            )

            response = self.client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )

            audio_b64 = base64.b64encode(response.audio_content).decode("utf-8")
            return TTSResponse(audio_content=audio_b64, success=True)

        except (
            gcp_exceptions.GoogleAPICallError,
            ValueError,
            AttributeError,
        ) as e:
            return TTSResponse(
                audio_content="",
                success=False,
                error_message=f"TTS synthesis failed: {str(e)}",
            )
        except (OSError, IOError, RuntimeError) as system_error:
            # Handle system-level errors that might occur during API calls
            return TTSResponse(
                audio_content="",
                success=False,
                error_message=f"System error during TTS synthesis: {str(system_error)}",
            )
