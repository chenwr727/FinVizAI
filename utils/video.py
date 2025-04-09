from typing import List

from moviepy import (
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    concatenate_videoclips,
)
from tqdm import tqdm

from core.schemas import SubtitleBase
from utils.config import VideoConfig
from utils.subtitle import create_subtitle


async def create_video(
    image_files: List[str], subtitles: List[SubtitleBase], video_config: VideoConfig, output_file: str
):
    final_duration = subtitles[-1].end_time

    frames = []
    for image_file in image_files:
        image_clip = ImageClip(image_file).with_duration(final_duration / len(image_files))
        frames.append(image_clip)

    video = concatenate_videoclips(frames, method="compose")

    text_clips = []
    audio_clips = []

    for subtitle in tqdm(subtitles, desc="Creating subtitles"):
        audio = AudioFileClip(subtitle.audio_file)

        text_clip = await create_subtitle(
            subtitle.text,
            video.size[0],
            video.size[1],
            video_config.subtitle,
        )
        text_clip = text_clip.with_duration(audio.duration).with_start(subtitle.start_time)
        text_clips.append(text_clip)

        audio_clip = audio.with_start(subtitle.start_time)
        audio_clips.append(audio_clip)

    final_video = CompositeVideoClip([video] + text_clips)
    final_audio = CompositeAudioClip(audio_clips)
    final_video = final_video.with_audio(final_audio)

    final_video.write_videofile(output_file, fps=video_config.fps, codec="libx264", threads=2)
