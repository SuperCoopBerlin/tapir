from typing import Callable


class SidebarLink:
    url: str
    display_name: str
    material_icon: str
    html_id: str | None
    required_permissions: list
    is_active = False
    ordering: int
    on_render: Callable
    required_feature_flag: str | None


class SidebarLinkGroup:
    name: str
    ordering: int
    links: list[SidebarLink]

    def __init__(self, name: str, ordering: int | None):
        self.name = name
        self.ordering = ordering
        self.links = []

    def add_link(
        self,
        display_name: str,
        material_icon: str,
        url: str,
        ordering: int,
        required_permissions=None,
        required_feature_flag=None,
        html_id=None,
        on_render=None,
    ):
        if self.links is None:
            self.links = []

        if required_permissions is None:
            required_permissions = []

        link = SidebarLink()
        link.url = url
        link.display_name = display_name
        link.material_icon = material_icon
        link.ordering = ordering
        link.html_id = html_id
        link.required_permissions = required_permissions
        link.on_render = on_render
        link.required_feature_flag = required_feature_flag

        self.links.append(link)


class SidebarLinkGroups:
    groups: dict[str, SidebarLinkGroup] = {}

    def get_group(
        self, group_name: str, ordering: int | None = None
    ) -> SidebarLinkGroup:
        if group_name not in self.groups.keys():
            group = SidebarLinkGroup(group_name, ordering)
            self.groups[group_name] = group

        if ordering is not None:
            self.groups[group_name].ordering = ordering

        return self.groups[group_name]

    def get_groups_and_links_for_user(self, user, url: str) -> []:
        visible_groups = []
        for group_original in self.groups.values():
            group_copy = SidebarLinkGroup(
                name=group_original.name, ordering=group_original.ordering
            )
            group_copy.links = [
                link for link in group_original.links if self.is_link_shown(user, link)
            ]
            if len(group_copy.links) > 0:
                visible_groups.append(group_copy)

        for visible_group in visible_groups:
            visible_group.links.sort(key=lambda link: link.ordering)
            for link in visible_group.links:
                if link.on_render:
                    link.on_render(link)
                link.is_active = link.url == url

        visible_groups.sort(key=lambda group: group.ordering)

        return visible_groups

    @staticmethod
    def is_link_shown(user, link: SidebarLink):
        from tapir.core.models import FeatureFlag

        if link.required_feature_flag and not FeatureFlag.get_flag_value(
            link.required_feature_flag
        ):
            return False
        for permission in link.required_permissions:
            if not user.has_perm(permission):
                return False
        return True
