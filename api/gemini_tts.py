import os
import wave
import logging
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load env variables globally when this module is imported
load_dotenv(override=True)

# Validate API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

client = genai.Client(api_key=api_key)
logger = logging.getLogger(__name__)

def generate_tts_audio(
    text: str,
    voice_name: str,
    output_file: str = "temp_output.wav",
    style_prompt: str = "",
) -> str:
    """
    Sends the processed text to Gemini for audio generation.
    Returns the path to the saved .wav file.
    
    Args:
        text: The text to convert to speech
        voice_name: Name of the voice to use (e.g., 'puck', 'charon')
        output_file: Path where the WAV file will be saved
        
    Returns:
        Path to the saved audio file
        
    Raises:
        ValueError: If text is empty or invalid
        RuntimeError: If API call fails or audio generation fails
    """
    if not text or not text.strip():
        raise ValueError("Text cannot be empty")
    
    # Validate voice name
    valid_voices = ["puck", "charon", "kore", "fenrir", "aoede"]
    if voice_name.lower() not in valid_voices:
        raise ValueError(f"Invalid voice name: {voice_name}. Must be one of {valid_voices}")
    
    # Guard against the API's combined text+prompt limit (~8 000 UTF-8 bytes).
    # Hebrew chars are ~2 bytes each so a char-based limit is not reliable.
    MAX_TEXT_BYTES = 7000
    encoded = text.encode("utf-8")
    if len(encoded) > MAX_TEXT_BYTES:
        logger.warning("Text too long (%d UTF-8 bytes), truncating to %d bytes",
                       len(encoded), MAX_TEXT_BYTES)
        text = encoded[:MAX_TEXT_BYTES].decode("utf-8", errors="ignore")
    
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-preview-tts")
    
    try:
        # Style prompts must be prepended to the text inside `contents`.
        # The TTS models do not support system_instruction and will return
        # a 500 error if it is set.
        prompt = style_prompt.strip() if style_prompt and style_prompt.strip() else ""
        contents = f"{prompt}\n{text}" if prompt else text

        config = types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voice_name
                    )
                )
            ),
        )

        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=config,
        )
        
        if not response.candidates or not response.candidates[0].content.parts:
            raise RuntimeError("No audio data received from API")

        audio_data = response.candidates[0].content.parts[0].inline_data.data
        
        if not audio_data:
            raise RuntimeError("Empty audio data received")
        
        # Create audio directory if it doesn't exist (if output_file contains a directory)
        output_dir = os.path.dirname(output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        with wave.open(output_file, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes(audio_data)

        return output_file
        
    except Exception as e:
        logger.error(f"TTS generation failed: {e}")
        raise RuntimeError(f"Failed to generate audio: {e}") from e
