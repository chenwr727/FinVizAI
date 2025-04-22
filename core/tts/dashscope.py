import dashscope
from dashscope.audio.tts_v2 import SpeechSynthesizer

from utils.config import TTSDashscopeConfig

from .base import TextToSpeechConverter


class DashscopeTextToSpeechConverter(TextToSpeechConverter):
    def __init__(self, config: TTSDashscopeConfig):
        self.api_key = config.api_key
        self.model = config.model
        dashscope.api_key = self.api_key
        super().__init__(config.voices)

    async def generate_audio(self, content: str, voice: str, file_name: str):
        synthesizer = SpeechSynthesizer(model=self.model, voice=voice, speech_rate=1)
        audio = synthesizer.call(content)
        with open(file_name, "wb") as f:
            f.write(audio)
