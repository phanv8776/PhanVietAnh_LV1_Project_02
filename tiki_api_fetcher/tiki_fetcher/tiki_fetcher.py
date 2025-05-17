import asyncio, aiohttp, json, os, math
from bs4 import BeautifulSoup
from tiki_api_fetcher import config as config
from aiohttp import ClientError, ClientResponseError

os.makedirs(config.OUTPUT_DIR, exist_ok=True)

def read_ids():
    with open(config.INPUT_FILE) as f:
        return [l.strip() for l in f if l.strip().isdigit()]

def clean_desc(html):
    return BeautifulSoup(html or '', 'html.parser').get_text(' ', strip=True)

import asyncio, aiohttp
from aiohttp import ClientError, ClientResponseError


async def fetch(session, sem, pid):
    async with sem:
        for attempt in range(config.MAX_RETRIES):
            try:
                async with session.get(config.API_URL.format(pid), timeout=10) as r:
                    if r.status == 200:
                        d = await r.json()
                        return {
                            'id': d['id'],
                            'name': d['name'],
                            'url_key': d.get('url_key'),
                            'price': d.get('price'),
                            'description': clean_desc(d.get('description')),
                            'images': [img.get('url') for img in d.get('images', [])]
                        }
                    elif r.status in {429, 500, 502, 503, 504}:
                        # Retryable HTTP errors
                        wait = config.BACKOFF_BASE * (2 ** attempt)
                        print(f"Retry {attempt+1}/{config.MAX_RETRIES} for {pid}: HTTP {r.status}, waiting {wait}s")
                        await asyncio.sleep(wait)
                    else:
                        print(f"Failed {pid}: HTTP {r.status} – not retryable")
                        return None
            except (asyncio.TimeoutError, ClientError) as e:
                wait = config.BACKOFF_BASE * (2 ** attempt)
                print(f"Retry {attempt+1}/{config.MAX_RETRIES} for {pid}: {type(e).__name__}, waiting {wait}s")
                await asyncio.sleep(wait)
            except Exception as e:
                print(f"Unexpected error {pid}: {e}")
                return None
    print(f"Failed after {config.MAX_RETRIES} retries: {pid}")
    return None


async def run_chunk(i, ids):
    sem = asyncio.Semaphore(config.CONCURRENT_REQUESTS)
    conn = aiohttp.TCPConnector(limit=config.CONCURRENT_REQUESTS)
    async with aiohttp.ClientSession(connector=conn) as s:
        tasks = [fetch(s, sem, pid) for pid in ids]
        res = [r for r in await asyncio.gather(*tasks) if r]
    fn = os.path.join(config.OUTPUT_DIR, f'products_{i + 1}.json')
    with open(fn,'w',encoding='utf8') as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print(f'Chunk {i+1}: {len(res)} items → {fn}')

