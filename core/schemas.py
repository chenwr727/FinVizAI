from pydantic import BaseModel


class StockBase(BaseModel):
    name: str
    symbol: str
    start_date: str
    end_date: str
    adjust: str = ""
    period: str = "daily"


class LLMResponse(BaseModel):
    status: str
    search_with_text: str
    reasoner: str
    text: str


class SubtitleBase(BaseModel):
    start_time: float
    end_time: float
    text: str
    audio_file: str
