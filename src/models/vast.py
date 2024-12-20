from vastai import VastAI
from typing import Any
import json
import requests
import logging
from .vast_instance import VastInstance
from .vast_template import VastTemplate
from requests.adapters import HTTPAdapter, Retry


class VastController:
    def __init__(self, api_key: str):
        self.__vast_api = VastAI(api_key=api_key)
        self.__logger = logging.getLogger("vast")
        self.req = requests.Session()
        self.req.mount(self.__vast_api.server_url, HTTPAdapter(max_retries=Retry(total=5, backoff_factor=5, status_forcelist=[429, 500, 502, 503, 504])))

    def getTemplateByName(self, name: str) -> VastTemplate | None:
        templates = self.get("/api/v0/users/me/created-templates/")["templates"]
        for t in templates:
            template = VastTemplate(t)
            if template.name == name:
                return template
        return None

    def getInstanceByLabel(self, label: str) -> VastInstance | None:
        instances = self.get("/api/v0/instances/")["instances"]
        for instance in instances:
            if instance["label"] == label:
                return VastInstance(instance, self)
        return None

    def createInstance(self, template: VastTemplate, label: str, docker_login: str, search_query: dict, image: str, blacklist_host_ids: list[str] = []):
        self.__logger.info(f"Creating instance, blacklist_host_ids={blacklist_host_ids}")
        best_offer = None
        for offer in self.get("/api/v0/bundles/", params={"q": json.dumps({**search_query, **{"disk_space": {"gte": template.disk_space}, "allocated_storage": template.disk_space}})})["offers"]:
            if str(offer["host_id"]) in blacklist_host_ids:
                self.__logger.info(f"Offer {offer['id']} skipped, host {offer['host_id']} in blacklist")
                continue
            best_offer = offer
            break
        if not best_offer:
            raise Exception("Offer not found")
        self.__logger.info(f"Found offer is {best_offer['id']}, creating instance ...")
        self.__logger.debug(f"Offer: {best_offer}")
        result = self.put(f"/api/v0/asks/{best_offer['id']}/", {"client_id": "me", "image_login": docker_login, "image": image, "template_hash_id": template.id, "label": label})
        if "success" not in result or not result["success"]:
            logging.error(result)
            raise Exception("Instance creation request is not succeed")
        self.__logger.info(f"Order result is {result}")

    def get(self, path: str, params: dict = {}):
        result = self.req.get(f"{self.__vast_api.server_url}{path}", headers={"Authorization": f"Bearer {self.__vast_api.api_key}"}, params=params, timeout=10).json()
        return result

    def delete(self, path: str):
        result = self.req.delete(f"{self.__vast_api.server_url}{path}", headers={"Authorization": f"Bearer {self.__vast_api.api_key}"}, timeout=10).json()
        return result

    def post(self, path: str, data: Any):
        result = self.req.post(f"{self.__vast_api.server_url}{path}", headers={"Authorization": f"Bearer {self.__vast_api.api_key}"}, json=data, timeout=10).json()
        return result

    def put(self, path: str, data: Any):
        result = self.req.put(f"{self.__vast_api.server_url}{path}", headers={"Authorization": f"Bearer {self.__vast_api.api_key}"}, json=data, timeout=10).json()
        return result
