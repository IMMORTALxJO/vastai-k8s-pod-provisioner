import redis
import logging
import time


class Blacklist:
    _redis_conn: redis.Redis
    _ban_ttl: int

    def __init__(self, redis_url: str, ban_ttl: int = 3600, restarts_ttl: int = 3600):
        """
        Initializes the Blacklist class.

        :param redis_url: URL of the Redis instance.
        :param db: Redis database index to use.
        :param ban_ttl: Time-to-live (TTL) for each ban record in seconds.
        """
        self._ban_ttl = ban_ttl
        self._restarts_record_ttl = restarts_ttl
        self._redis_conn = redis.StrictRedis.from_url(url=redis_url)
        self._logger = logging.getLogger("blacklist")
        self._logger.info(f"initialized with ttl={self._ban_ttl}")

    _ban_key_prefix: str = "ban_"

    def _getBanKey(self, key: str) -> str:
        return f"{self._ban_key_prefix}{key}"

    def isBanned(self, key: str) -> bool:
        """
        Checks if the given key is in the blacklist.

        :param key: The string to check.
        :return: True if the key is banned, False otherwise.
        """
        return self._redis_conn.exists(self._getBanKey(key)) == 1

    def add(self, key: str, reason: str = "slow_startup"):
        """
        Adds the given key to the blacklist with the specified TTL.

        :param key: The string to ban.
        """
        self._redis_conn.setex(self._getBanKey(key), self._ban_ttl, reason)
        self._logger.info(f"added '{key}' ttl={self._ban_ttl}")

    def list(self) -> list[str]:
        """
        Retrieves all currently banned keys (IDs) from the blacklist.

        :return: A list of currently banned keys.
        """
        banned_keys = []
        cursor, keys = self._redis_conn.scan(match=f"{self._ban_key_prefix}*", count=100)
        banned_keys.extend(keys)
        while cursor != 0:
            cursor, keys = self._redis_conn.scan(cursor=cursor, match=f"{self._ban_key_prefix}*", count=100)
            banned_keys.extend(keys)
        key_len = len(self._ban_key_prefix)
        return [key.decode("utf-8")[key_len:] for key in banned_keys]

    _wait_time_key_prefix: str = "wait_"
    _wait_time_record_ttl: int = 24 * 60 * 60  # 1day

    def getInstanceStartTime(self, instance_id: str) -> int:
        """
        Returns the time difference (in seconds) between the current time and the stored timestamp for the given instance.
        If no timestamp is found, it sets the current time as the start time.

        :param instance_id: Vast instance id.
        :return: Time difference in seconds.
        """
        key = f"{self._wait_time_key_prefix}{instance_id}"
        start_time_str = self._redis_conn.get(key)

        if start_time_str is None:
            start_time = int(time.time())
            self._redis_conn.setex(key, self._wait_time_record_ttl, str(start_time))
        else:
            start_time = int(start_time_str)

        self._logger.info(f"got '{instance_id}' start time - {start_time}")
        return start_time

    def delInstanceStartTime(self, instance_id: str):
        """
        Deletes the stored wait time for the given instance.

        :param instance_id: Vast instance id.
        """
        self._redis_conn.delete(f"{self._wait_time_key_prefix}{instance_id}")
        self._logger.info(f"deleted '{instance_id}' wait time")

    _restarts_key_prefix: str = "restarts_"
    _restarts_record_ttl: int = 60 * 60  # 1hour

    def getAndIncreaseInstanceRestarts(self, instance_id: str) -> int:
        key = f"{self._restarts_key_prefix}{instance_id}"
        restarts = self._redis_conn.get(key)
        restarts = int(restarts) if restarts else 0
        restarts += 1
        self._redis_conn.setex(key, self._restarts_record_ttl, restarts)
        self._logger.info(f"got '{instance_id}' restarts counter - {restarts}")
        return restarts

    def cleanInstanceKeys(self, instance_id: str):
        self._redis_conn.delete(f"{self._restarts_key_prefix}{instance_id}")
        self._redis_conn.delete(f"{self._wait_time_key_prefix}{instance_id}")
