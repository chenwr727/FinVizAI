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


def add_image_clips(image_files: List[str], duration: float) -> List[ImageClip]:
    return [ImageClip(image_file).with_duration(duration / len(image_files)) for image_file in image_files]


async def create_video(
    report_frames: List[str],
    image_files: List[str],
    title: str,
    subtitles: List[SubtitleBase],
    video_config: VideoConfig,
    output_file: str,
):
    frames = []
    frames.extend(add_image_clips(report_frames, video_config.title.interval))
    frames.extend(add_image_clips(image_files, subtitles[-1].end_time))

    video = concatenate_videoclips(frames, method="compose")

    text_clips = []
    audio_clips = []

    if title:
        text_clip = await create_subtitle(title, video.size[0], video.size[1], video_config.title)
        text_clip = text_clip.with_duration(video_config.title.interval)
        text_clips.append(text_clip)

    for subtitle in tqdm(subtitles, desc="Creating subtitles"):
        audio = AudioFileClip(subtitle.audio_file)

        text_clip = await create_subtitle(subtitle.text, video.size[0], video.size[1], video_config.subtitle)
        text_clip = text_clip.with_duration(audio.duration).with_start(
            subtitle.start_time + video_config.title.interval
        )
        text_clips.append(text_clip)

        audio_clip = audio.with_start(subtitle.start_time + video_config.title.interval)
        audio_clips.append(audio_clip)

    if video_config.background_audio:
        final_duration = video_config.title.interval + subtitles[-1].end_time
        bg_audio = AudioFileClip(video_config.background_audio).with_duration(final_duration)
        bg_audio = bg_audio.with_volume_scaled(video_config.background_audio_volume)
        audio_clips.insert(0, bg_audio)

    final_video = CompositeVideoClip([video] + text_clips)
    final_audio = CompositeAudioClip(audio_clips)
    final_video = final_video.with_audio(final_audio)

    final_video.write_videofile(output_file, fps=video_config.fps, codec="libx264", threads=2)
