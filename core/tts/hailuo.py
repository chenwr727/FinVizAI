from openai import OpenAI

from utils.config import TTSHaiLuoConfig

from .base import TextToSpeechConverter


class HaiLuoTextToSpeechConverter(TextToSpeechConverter):
    def __init__(self, config: TTSHaiLuoConfig):
        self.client = OpenAI(api_key=config.api_key, base_url=config.base_url)
        super().__init__(config.voices)

    async def generate_audio(self, content: str, voice: str, file_name: str):
        with self.client.audio.speech.with_streaming_response.create(
            model="hailuo", voice=voice, input=content, speed=1.2
        ) as response:
            response.stream_to_file(file_name)
