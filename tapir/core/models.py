class SidebarLinkGroups:
    groups = {}

    def add_link(
        self,
        group_name: str,
        display_name: str,
        material_icon: str,
        url: str,
        required_permissions=None,
        html_id=None,
    ):
        if required_permissions is None:
            required_permissions = []

        link = SidebarLink()
        link.url = url
        link.display_name = display_name
        link.material_icon = material_icon
        link.html_id = html_id
        link.required_permissions = required_permissions

        group = self.__get_group(group_name)
        group.append(link)

    def __get_group(self, group_name: str) -> list:
        if group_name not in self.groups:
            self.groups[group_name] = []
        return self.groups[group_name]


class SidebarLink:
    url: str
    display_name: str
    material_icon: str
    html_id: str | None
    required_permissions: list
    is_active = False
