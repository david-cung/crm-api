import redis
from app.core.config import settings

# Initialize Redis client
# Using from_url for easy configuration from settings
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

def get_redis():
    """Helper function to get redis client if needed (for dependency injection)"""
    return redis_client
