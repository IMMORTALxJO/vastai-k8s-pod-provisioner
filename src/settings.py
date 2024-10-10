import os
import json


def getenv(envname: str, default: str | None = None):
    v = os.getenv(envname)
    if v:
        return v
    if not default:
        raise Exception(f"Env var {envname} is not defined")
    return default


class Settings:
    pod_name = getenv("POD_NAME")
    vast_api_key = getenv("VAST_API_KEY")
    template_name = getenv("VAST_TEMPLATE_NAME")
    template_image = getenv("VAST_TEMPLATE_IMAGE")
    nginx_config_path = getenv("NGINX_CONFIG_PATH", "/etc/nginx/http.d/default.conf")
    docker_login = getenv("DOCKER_LOGIN")
    vast_search_query = json.loads(getenv("VAST_SEARCH_QUERY"))
    nginx_listen_port = getenv("NGINX_LISTEN_PORT", "3000")
    nginx_max_body_size = getenv("NGINX_MAX_BODY_SIZE", "10M")
    log_debug = getenv("DEBUG", "false").lower() == "true"
    blacklist_enabled = getenv("BLACKLIST_ENABLED", "false").lower() == "true"
    blacklist_redis = getenv("BLACKLIST_REDIS", "redis://redis:6379/10")
    blacklist_ban_ttl_seconds = int(getenv("BLACKLIST_BAN_TTL_SECONDS", str(24 * 60 * 60)))  # 1 day
    blacklist_ban_after_seconds = int(getenv("BLACKLIST_BAN_AFTER_SECONDS", str(20 * 60)))  # 20 minutes
    blacklist_restart_ttl_seconds = int(getenv("BLACKLIST_RESTART_TTL_SECONDS", str(60 * 60)))  # 1 hour
    blacklist_restart_threshold = int(getenv("BLACKLIST_RESTART_THRESHOLD", "5"))
