import argparse
import asyncio
from .config import load_config
from .platform import TradingPlatform


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="backtest", help="backtest|paper|live")
    args = parser.parse_args()

    config = load_config()
    config.mode = args.mode
    platform = TradingPlatform(config)
    await platform.run()


if __name__ == "__main__":
    asyncio.run(main())
