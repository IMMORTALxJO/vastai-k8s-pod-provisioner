class VastTemplate:
    def __init__(self, template: dict):
        self.__raw_template = template

    @property
    def id(self) -> str:
        return str(self.__raw_template["hash_id"])

    @property
    def name(self) -> str:
        return str(self.__raw_template["name"])

    @property
    def disk_space(self) -> int:
        return int(self.__raw_template["recommended_disk_space"])

    @property
    def image(self) -> str:
        return "%s:%s" % (self.__raw_template["repo"], self.__raw_template["tag"])

    def __str__(self):
        s = [f"Template {self.id}"]
        for t in ["id", "image", "tag", "name", "created_from_id"]:
            s.append("\t%s = %s" % (t, self.__raw_template[t]))
        return "\n".join(s)
