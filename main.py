import asyncio
import datetime

from core.llm import LLMClient
from core.schemas import StockBase
from core.stock import StockVideo
from utils.config import config


async def main():
    llm_client = LLMClient()
    stock_client = StockVideo(llm_client)

    stock_name = "平安银行"
    stock_code = "000001"
    start_date = (datetime.datetime.now() - datetime.timedelta(365)).strftime("%Y%m%d")
    end_date = datetime.datetime.now().strftime("%Y%m%d")

    stock = StockBase(
        name=stock_name, symbol=stock_code, start_date=start_date, end_date=end_date, adjust="qfq", period="daily"
    )
    await stock_client.generate_video(stock, config.tts, config.video)


if __name__ == "__main__":
    asyncio.run(main())
