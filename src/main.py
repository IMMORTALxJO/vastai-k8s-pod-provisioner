import time
import logging
from jinja2 import Environment, FileSystemLoader
from models.vast import VastController
from models.blacklist import Blacklist
from settings import Settings
from typing import Optional

logging.basicConfig(level=logging.DEBUG if Settings.log_debug else logging.INFO, format="%(asctime)s:%(levelname)s:%(name)s:%(message)s", datefmt="%Y-%m-%dT%H:%M:%S")
logging.info({"template_name": Settings.template_name, "template_image": Settings.template_image, "pod_name": Settings.pod_name})

vast = VastController(api_key=Settings.vast_api_key)
blacklist: Optional[Blacklist] = None
if Settings.blacklist_enabled:
    blacklist = Blacklist(redis_url=Settings.blacklist_redis, ban_ttl=Settings.blacklist_ban_ttl_seconds)

# get template by name
logging.info(f"Searching template with name '{Settings.template_name}' ...")
template = vast.getTemplateByName(Settings.template_name)
if not template:
    raise Exception(f"Template with name '{Settings.template_name}' not found")
logging.info(template)

# check if instance already exists
instance_label = f"k8s_pod={Settings.pod_name}"
logging.info(f"Searching instance with label '{instance_label}' ...")
instance = vast.getInstanceByLabel(instance_label)
if instance:
    logging.info(instance)
    destroy_reason = ""
    if instance.image != Settings.template_image:
        destroy_reason = "instance has wrong image"
    elif instance.template_hash_id != template.id:
        destroy_reason = "instance has wrong template"
    elif instance.status == "offline":
        destroy_reason = "instance is Offline"
    elif blacklist and blacklist.isBanned(instance.hostId):
        destroy_reason = "instance host is banned"
    if destroy_reason:
        logging.info(f"Destroying instance, {destroy_reason}...")
        instance.destroy()
        instance = None
    else:
        logging.info("Instance image and template are up-to-date")

# create instance if not exists or not up-to-date
# TODO: find a way to get docker_login from the template
if not instance:
    vast.createInstance(
        template=template,
        label=instance_label,
        docker_login=Settings.docker_login,
        search_query=Settings.vast_search_query,
        image=Settings.template_image,
        blacklist_host_ids=blacklist.get() if blacklist else [],
    )

# wait for instance become online
wait_start_time = time.time()
while True:
    instance = vast.getInstanceByLabel(instance_label)
    if not instance:
        raise Exception("Instance not found")
    logging.info(instance)
    if instance and instance.status == "running" and instance.port > 0:
        break
    if blacklist and time.time() - wait_start_time > Settings.blacklist_ban_after_seconds:
        logging.info("Too long waiting, instance host will be banned for some time...")
        blacklist.add(instance.hostId)
        instance.destroy()
        raise Exception(f"Host {instance.hostId} marked as banned due to long startup waiting")
    logging.info("Waiting for instance become online ...")
    time.sleep(10)
logging.info("Instance is ready to accept connections")

# generate nginx config
environment = Environment(loader=FileSystemLoader("./"), autoescape=True)
nginx_template = environment.get_template("nginx.conf.j2")
nginx_conf = nginx_template.render({"ip": instance.ip, "port": instance.port, "listen_port": Settings.nginx_listen_port, "max_body_size": Settings.nginx_max_body_size})
logging.info(f"Final nginx config:\n{nginx_conf}")
with open(Settings.nginx_config_path, "w") as nginx_conf_file:
    nginx_conf_file.write(nginx_conf)
logging.info("Nginx config saved")
