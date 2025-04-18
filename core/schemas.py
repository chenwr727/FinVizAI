from typing import List, Optional

from pydantic import BaseModel


class SearchWithText(BaseModel):
    url: str
    title: str
    publish_time: str


class LLMResponse(BaseModel):
    chat_id: str
    status: str
    search_with_text: Optional[List[SearchWithText]] = None
    reasoner: str
    text: str


class SubtitleBase(BaseModel):
    start_time: float
    end_time: float
    text: str
    audio_file: str
