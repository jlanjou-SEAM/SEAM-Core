import requests
import concurrent.futures
from requests.adapters import HTTPAdapter

SESSION = requests.Session()

adapter = HTTPAdapter(
    max_retries=0,
    pool_connections=64,
    pool_maxsize=64
)

SESSION.mount("http://", adapter)
SESSION.mount("https://", adapter)

CONNECT_TIMEOUT = 1
READ_TIMEOUT = 1
MAX_WORKERS = 32

def fetch_source(source):

    name = source["name"]
    url = source["url"]

    try:

        response = SESSION.get(
            url,
            timeout=(
                CONNECT_TIMEOUT,
                READ_TIMEOUT
            ),
            allow_redirects=False,
            stream=False
        )

        return {
            "name": name,
            "status": response.status_code,
            "success": response.ok
        }

    except Exception as e:

        return {
            "name": name,
            "status": "ERROR",
            "success": False,
            "error": str(e)
        }

def acquire_all(sources):

    results = []

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:

        futures = [
            executor.submit(
                fetch_source,
                source
            )
            for source in sources
        ]

        for future in concurrent.futures.as_completed(futures):
            results.append(
                future.result()
            )

    return results

print()
print("=== CLEAN-ROOM ACQUISITION PERFORMANCE FIX ===")
print()
print("Parallel acquisition enabled")
print(f"Workers: {MAX_WORKERS}")
print(f"Timeouts: connect={CONNECT_TIMEOUT}s read={READ_TIMEOUT}s")
print("Retries: disabled")
print("Redirects: disabled")
print()
