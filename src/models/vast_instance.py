import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .vast import VastController


class VastInstance:
    def __init__(self, instance: dict, vast: "VastController"):
        self.__raw_template = instance
        self.__vast = vast
        self.__logger = logging.getLogger(f"instance:{self.id}")

    @property
    def id(self) -> str:
        return str(self.__raw_template["id"])

    @property
    def status(self) -> str:
        return str(self.__raw_template["actual_status"])

    @property
    def ip(self) -> str:
        return str(self.__raw_template["public_ipaddr"])

    @property
    def port(self) -> int:
        return int(self.__raw_template["direct_port_start"])

    @property
    def nginx_upstream(self) -> str:
        return "%s:%s" % (self.ip, self.port)

    @property
    def template_hash_id(self) -> str:
        return str(self.__raw_template["template_hash_id"])

    @property
    def image(self) -> str:
        return str(self.__raw_template["image_uuid"])

    def destroy(self):
        result = self.__vast.delete(f"/api/v0/instances/{self.id}/")
        if "success" not in result or not result["success"]:
            self.__logger.error(result)
            raise Exception("Instance deletion failed")
        self.__logger.info("Instance has been destroyed")

    def __str__(self):
        s = [f"Instance {self.id}"]
        for t in ["image_uuid", "template_hash_id", "cpu_name", "cpu_cores", "actual_status", "status_msg", "public_ipaddr", "direct_port_start"]:
            s.append("\t%s = %s" % (t, self.__raw_template[t]))
        return "\n".join(s)
