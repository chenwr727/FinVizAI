from enum import Enum
from typing import List, Optional

import toml
from openai import BaseModel


class TTSSource(str, Enum):
    dashscope = "dashscope"
    hailuo = "hailuo"


class LLMConfig(BaseModel):
    base_url: str
    api_key: str
    model: str
    hy_user: str
    agent_id: str
    chat_id: str = ""
    should_remove_conversation: bool = False


class TTSDashscopeConfig(BaseModel):
    api_key: str = ""
    model: str = ""
    voices: List[str] = []


class TTSHaiLuoConfig(BaseModel):
    api_key: str = ""
    base_url: str = ""
    voices: List[str] = []


class TTSConfig(BaseModel):
    source: TTSSource
    dashscope: Optional[TTSDashscopeConfig] = None
    hailuo: Optional[TTSHaiLuoConfig] = None


class JsConfig(BaseModel):
    js_host: str


class SubtitleConfig(BaseModel):
    font: str
    width_ratio: float = 0.8
    font_size_ratio: int = 17
    position_ratio: float = 0.88
    color: str = "white"
    stroke_color: str = "black"
    stroke_width: int = 1
    text_align: str = "center"
    interval: float = 0.2


class TitleConfig(SubtitleConfig):
    pass


class VideoConfig(BaseModel):
    fps: int
    background_audio: str
    background_audio_volume: float = 0.2
    width: int
    height: int
    subtitle: SubtitleConfig
    title: TitleConfig


class Config(BaseModel):
    llm: LLMConfig
    tts: TTSConfig
    js: JsConfig
    video: VideoConfig


def load_config(config_file: str = "config.toml") -> dict:
    with open(config_file, "r", encoding="utf-8") as f:
        config = toml.load(f)
    return config


_cfg = load_config()
config = Config.model_validate(_cfg)
