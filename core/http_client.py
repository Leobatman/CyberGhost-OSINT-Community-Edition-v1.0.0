import aiohttp
import asyncio

async def fetch_url(session: aiohttp.ClientSession, url: str, timeout: int = 15, as_json: bool = False, headers: dict = None):
    """Fetch a URL with proper error handling."""
    if headers is None:
        headers = {'User-Agent': 'CyberGhost OSINT (Community Edition) - Research Tool'}
    try:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
            if response.status == 200:
                if as_json:
                    return await response.json(content_type=None)
                return await response.text()
    except asyncio.TimeoutError:
        pass
    except aiohttp.ClientError:
        pass
    except Exception:
        pass
    return None
