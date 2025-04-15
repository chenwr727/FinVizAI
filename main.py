import asyncio
import datetime

from core.fetcher import FuturesDataFetcher, StockDataFetcher
from core.finance import FinanceVideo
from utils.config import config


async def main():
    name = "比亚迪"
    symbol = "002594"
    start_date = (datetime.datetime.now() - datetime.timedelta(365)).strftime("%Y%m%d")
    end_date = datetime.datetime.now().strftime("%Y%m%d")
    fetcher_client = StockDataFetcher(
        name=name, symbol=symbol, start_date=start_date, end_date=end_date, period="daily", adjust="qfq"
    )

    stock_client = FinanceVideo(fetcher_client, "stock")
    await stock_client.generate_video(config.tts, config.video, force=False)

    name = "塑料主连"
    symbol = "塑料主连"
    start_date = (datetime.datetime.now() - datetime.timedelta(365)).strftime("%Y%m%d")
    end_date = datetime.datetime.now().strftime("%Y%m%d")
    fetcher_client = FuturesDataFetcher(
        name=name, symbol=symbol, start_date=start_date, end_date=end_date, period="daily"
    )

    stock_client = FinanceVideo(fetcher_client, "futures")
    await stock_client.generate_video(config.tts, config.video, force=False)


if __name__ == "__main__":
    asyncio.run(main())
