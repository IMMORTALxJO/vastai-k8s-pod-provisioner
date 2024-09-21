import redis
import logging


class Blacklist:
    _redis_conn: redis.Redis
    _ban_ttl: int

    def __init__(self, redis_url: str, ban_ttl: int = 3600):
        """
        Initializes the Blacklist class.

        :param redis_url: URL of the Redis instance.
        :param db: Redis database index to use.
        :param ban_ttl: Time-to-live (TTL) for each ban record in seconds.
        """
        self.__ban_ttl = ban_ttl
        self.__redis_conn = redis.StrictRedis.from_url(url=redis_url)
        self.__logger = logging.getLogger("blacklist")
        self.__logger.info(f"initialized with ttl={self.__ban_ttl}")

    def isBanned(self, key: str) -> bool:
        """
        Checks if the given key is in the blacklist.

        :param key: The string to check.
        :return: True if the key is banned, False otherwise.
        """
        return self.__redis_conn.exists(key) == 1

    def add(self, key: str):
        """
        Adds the given key to the blacklist with the specified TTL.

        :param key: The string to ban.
        """
        self.__redis_conn.setex(key, self.__ban_ttl, "ban")
        self.__logger.info(f"added '{key}' ttl={self.__ban_ttl}")

    def get(self) -> list[str]:
        """
        Retrieves all currently banned keys (IDs) from the blacklist.

        :return: A list of currently banned keys.
        """
        banned_keys = []
        cursor, keys = self.__redis_conn.scan(match="*", count=100)
        banned_keys.extend(keys)
        while cursor != 0:
            cursor, keys = self.__redis_conn.scan(cursor=cursor, match="*", count=100)
            banned_keys.extend(keys)
        return [key.decode("utf-8") for key in banned_keys]
