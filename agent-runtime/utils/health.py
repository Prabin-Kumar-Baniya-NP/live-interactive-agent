import sys

import httpx


def check_health(url: str = "http://localhost:8081/health") -> bool:
    try:
        response = httpx.get(url, timeout=5.0)
        return response.status_code == 200
    except httpx.RequestError:
        return False


if __name__ == "__main__":
    is_healthy = check_health()
    if is_healthy:
        print("Healthy")
        sys.exit(0)
    else:
        print("Unhealthy")
        sys.exit(1)
