import asyncio, aiohttp, json, os, math
from bs4 import BeautifulSoup

INPUT_FILE = 'product_ids.txt'
OUTPUT_DIR = 'output'
CHUNK_SIZE = 1000
CONCURRENT_REQUESTS = 50
API_URL = 'https://api.tiki.vn/product-detail/api/v1/products/{}'

os.makedirs(OUTPUT_DIR, exist_ok=True)

def read_ids():
    with open(INPUT_FILE) as f:
        return [l.strip() for l in f if l.strip().isdigit()]

def clean_desc(html):
    return BeautifulSoup(html or '', 'html.parser').get_text(' ', strip=True)

async def fetch(session, sem, pid):
    async with sem:
        try:
            async with session.get(API_URL.format(pid), timeout=10) as r:
                if r.status==200:
                    d = await r.json()
                    return {
                        'id': d['id'],
                        'name': d['name'],
                        'url_key': d.get('url_key'),
                        'price': d.get('price'),
                        'description': clean_desc(d.get('description')),
                        'images': [img.get('url') for img in d.get('images',[])]
                    }
        except Exception as e:
            print(f"Error {pid}: {e}")
    return None

async def run_chunk(i, ids):
    sem = asyncio.Semaphore(CONCURRENT_REQUESTS)
    conn = aiohttp.TCPConnector(limit=CONCURRENT_REQUESTS)
    async with aiohttp.ClientSession(connector=conn) as s:
        tasks = [fetch(s, sem, pid) for pid in ids]
        res = [r for r in await asyncio.gather(*tasks) if r]
    fn = os.path.join(OUTPUT_DIR, f'products_{i+1}.json')
    with open(fn,'w',encoding='utf8') as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print(f'Chunk {i+1}: {len(res)} items → {fn}')

def main():
    ids = read_ids()
    total = math.ceil(len(ids)/CHUNK_SIZE)
    async def runner():
        for i in range(total):
            start, end = i*CHUNK_SIZE, (i+1)*CHUNK_SIZE
            await run_chunk(i, ids[start:end])
    asyncio.run(runner())

if __name__=='__main__':
    main()
