class SidebarLink:
    url: str
    display_name: str
    material_icon: str
    is_active: bool

    def __init__(self, url: str, display_name: str, material_icon: str):
        self.url = url
        self.display_name = display_name
        self.material_icon = material_icon


class SidebarLinkGroup:
    name: str
    links: []
    ordering: int

    def __init__(self, name: str, links: [], ordering):
        self.name = name
        self.links = links
        self.ordering = ordering
