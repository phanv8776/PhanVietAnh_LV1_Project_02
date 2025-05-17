import asyncio
import math

import tiki_fetcher as tiki_fetcher
from tiki_api_fetcher import config as config
def main():
    ids = tiki_fetcher.read_ids()
    total = math.ceil(len(ids) / config.CHUNK_SIZE)
    async def runner():
        for i in range(total):
            start, end = i * config.CHUNK_SIZE, (i + 1) * config.CHUNK_SIZE
            await tiki_fetcher.run_chunk(i, ids[start:end])
    asyncio.run(runner())

if __name__=='__main__':
    main()