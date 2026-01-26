"""Redis client and connection management."""

import redis
from redis.connection import ConnectionPool
import structlog
import os

logger = structlog.get_logger()

# Get Redis URL from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_MAX_CONNECTIONS = int(os.getenv("REDIS_MAX_CONNECTIONS", "50"))

# Create connection pool
pool = ConnectionPool.from_url(
    REDIS_URL,
    db=REDIS_DB,
    max_connections=REDIS_MAX_CONNECTIONS,
    decode_responses=True,  # Automatically decode responses to strings
)

# Create Redis client
redis_client = redis.Redis(connection_pool=pool)


def get_redis():
    """Get Redis client instance."""
    return redis_client


def check_redis_connection() -> bool:
    """Check if Redis connection is healthy."""
    try:
        redis_client.ping()
        return True
    except Exception as e:
        logger.error("Redis connection check failed", error=str(e))
        return False


class RedisCache:
    """Redis cache wrapper with common operations."""
    
    def __init__(self, client=None):
        self.client = client or redis_client
    
    def get(self, key: str):
        """Get value from cache."""
        try:
            return self.client.get(key)
        except Exception as e:
            logger.error("Redis GET failed", key=key, error=str(e))
            return None
    
    def set(self, key: str, value: str, ttl: int = None):
        """Set value in cache with optional TTL (seconds)."""
        try:
            if ttl:
                return self.client.setex(key, ttl, value)
            else:
                return self.client.set(key, value)
        except Exception as e:
            logger.error("Redis SET failed", key=key, error=str(e))
            return False
    
    def delete(self, key: str):
        """Delete key from cache."""
        try:
            return self.client.delete(key)
        except Exception as e:
            logger.error("Redis DELETE failed", key=key, error=str(e))
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists."""
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error("Redis EXISTS failed", key=key, error=str(e))
            return False
    
    def expire(self, key: str, ttl: int):
        """Set expiration on existing key."""
        try:
            return self.client.expire(key, ttl)
        except Exception as e:
            logger.error("Redis EXPIRE failed", key=key, error=str(e))
            return False
    
    def hget(self, name: str, key: str):
        """Get hash field value."""
        try:
            return self.client.hget(name, key)
        except Exception as e:
            logger.error("Redis HGET failed", name=name, key=key, error=str(e))
            return None
    
    def hset(self, name: str, key: str, value: str):
        """Set hash field value."""
        try:
            return self.client.hset(name, key, value)
        except Exception as e:
            logger.error("Redis HSET failed", name=name, key=key, error=str(e))
            return False
    
    def hgetall(self, name: str):
        """Get all hash fields."""
        try:
            return self.client.hgetall(name)
        except Exception as e:
            logger.error("Redis HGETALL failed", name=name, error=str(e))
            return {}


# Global cache instance
cache = RedisCache()
