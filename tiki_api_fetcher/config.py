INPUT_FILE = 'product_ids.txt'
OUTPUT_DIR = '../output'
CHUNK_SIZE = 1000
CONCURRENT_REQUESTS = 50
API_URL = 'https://api.tiki.vn/product-detail/api/v1/products/{}'
MAX_RETRIES = 3
BACKOFF_BASE = 1