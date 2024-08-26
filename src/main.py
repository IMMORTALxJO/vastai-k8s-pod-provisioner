import os
import time
import logging
import json
from jinja2 import Environment, FileSystemLoader
from models.vast import VastController


def getenv(envname: str, default: str | None = None):
    v = os.getenv(envname)
    if v:
        return v
    if not default:
        raise Exception(f"Env var {envname} is not defined")
    return default


pod_name = getenv("POD_NAME")
vast_api_key = getenv("VAST_API_KEY")
template_name = getenv("VAST_TEMPLATE_NAME")
template_image = getenv("VAST_TEMPLATE_IMAGE")
nginx_config_path = getenv("NGINX_CONFIG_PATH", "/etc/nginx/http.d/default.conf")
docker_login = getenv("DOCKER_LOGIN")
vast_search_query = json.loads(getenv("VAST_SEARCH_QUERY"))
nginx_listen_port = getenv("NGINX_LISTEN_PORT", "3000")
nginx_max_body_size = getenv("NGINX_MAX_BODY_SIZE", "10M")
log_debug = getenv("DEBUG", "false")

logging.basicConfig(level=logging.DEBUG if log_debug.lower() == "true" else logging.INFO, format="%(asctime)s:%(levelname)s:%(name)s:%(message)s", datefmt="%Y-%m-%dT%H:%M:%S")
logging.info({"template_name": template_name, "template_image": template_image, "pod_name": pod_name})

vast = VastController(api_key=vast_api_key)

# get template by name
logging.info(f"Searching template with name '{template_name}' ...")
template = vast.getTemplateByName(template_name)
if not template:
    raise Exception(f"Template with name '{template_name}' not found")
logging.info(template)

# check if instance already exists
instance_label = f"k8s_pod={pod_name}"
logging.info(f"Searching instance with label '{instance_label}' ...")
instance = vast.getInstanceByLabel(instance_label)
if instance:
    logging.info(instance)
    if instance.image != template_image or instance.template_hash_id != template.id or instance.status == "offline":
        logging.info("Destroying instance...")
        instance.destroy()
        instance = None
    else:
        logging.info("Instance image and template are up-to-date")

# create instance if not exists or not up-to-date
if not instance:
    vast.createInstance(template=template, label=instance_label, docker_login=docker_login, search_query=vast_search_query, image=template_image)

# wait for instance become online
while True:
    instance = vast.getInstanceByLabel(instance_label)
    if not instance:
        raise Exception("Instance not found")
    logging.info(instance)
    if instance and instance.status == "running" and instance.port > 0:
        break
    logging.info("Waiting for instance become online ...")
    time.sleep(10)
logging.info("Instance is ready to accept connections")


# generate nginx config
environment = Environment(loader=FileSystemLoader("./"), autoescape=True)
nginx_template = environment.get_template("nginx.conf.j2")
nginx_conf = nginx_template.render({"ip": instance.ip, "port": instance.port, "listen_port": nginx_listen_port, "max_body_size": nginx_max_body_size})
logging.info(f"Final nginx config:\n{nginx_conf}")
with open(nginx_config_path, "w") as nginx_conf_file:
    nginx_conf_file.write(nginx_conf)
logging.info("Nginx config saved")
