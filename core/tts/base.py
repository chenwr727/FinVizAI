import os
import time
from abc import ABC, abstractmethod
from typing import List

from moviepy import AudioFileClip
from tqdm import tqdm

from core.schemas import SubtitleBase


class TextToSpeechConverter(ABC):

    def __init__(self, voices: List[str]):
        self.voices = voices
        self.folder = None

    async def text_to_speech(
        self, contents: List[str], output_folder: str, interval: float = 0.2
    ) -> List[SubtitleBase]:
        duration_start = 0
        subtitles = []
        for i, content in tqdm(enumerate(contents), desc="Text to speech", total=len(contents)):
            file_name = os.path.join(output_folder, f"{i:02d}.mp3")
            if not os.path.exists(file_name):
                await self.process_dialogue(self.voices[0], content, file_name)

            audio_clip = AudioFileClip(file_name)
            subtitles.append(
                SubtitleBase(
                    text=content,
                    start_time=duration_start,
                    end_time=duration_start + audio_clip.duration + interval,
                    audio_file=file_name,
                )
            )

            duration_start += audio_clip.duration + interval

        return subtitles

    async def process_dialogue(self, voice: str, content: List[str], file_name: str, max_retries: int = 3):
        for _ in range(max_retries):
            try:
                await self.generate_audio(content, voice, file_name)
                break
            except Exception:
                if os.path.exists(file_name):
                    os.remove(file_name)
                time.sleep(3)
                continue
        else:
            raise ValueError("Error generate audio")

    @abstractmethod
    async def generate_audio(self, content: str, voice: str, file_name: str):
        pass
