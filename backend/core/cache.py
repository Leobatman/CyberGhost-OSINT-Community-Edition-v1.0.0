import json
import functools
from typing import Any, Callable
import structlog
from fastapi import Request, Response
from redis.asyncio import Redis

from backend.core.config import settings

log = structlog.get_logger(__name__)

# Basic Redis client for caching
redis_client = Redis.from_url(settings.redis.url, decode_responses=True)

def cache(ttl: int = 60) -> Callable:
    """
    Redis cache decorator for FastAPI endpoints.
    Uses the request path and query string as the cache key.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(request: Request, *args: Any, **kwargs: Any) -> Any:
            # Generate cache key from request URL
            cache_key = f"cache:{request.url.path}?{request.url.query}"
            
            try:
                cached_data = await redis_client.get(cache_key)
                if cached_data:
                    log.debug("cache_hit", key=cache_key)
                    # For simplicity, returning JSONResponse directly could be tricky if 
                    # FastAPI expects a Pydantic model. We just parse JSON and return dict.
                    return json.loads(cached_data)
            except Exception as e:
                log.warning("redis_cache_error", error=str(e))
                
            # Execute original endpoint
            response = await func(request, *args, **kwargs)
            
            try:
                # If response is a Pydantic model (which it usually is in this API)
                if hasattr(response, "model_dump_json"):
                    data = response.model_dump_json()
                elif hasattr(response, "dict"):
                    data = json.dumps(response.dict())
                else:
                    data = json.dumps(response)
                    
                await redis_client.setex(cache_key, ttl, data)
                log.debug("cache_set", key=cache_key)
            except Exception as e:
                log.warning("redis_cache_set_error", error=str(e))
                
            return response
        return wrapper
    return decorator
