class SidebarLinkGroup:
    name: str
    links: []

    def __init__(self, name: str):
        self.name = name
        self.links = []

    def add_link(self, display_name: str, material_icon: str, url: str, html_id=""):
        self.links.append(
            {
                "url": url,
                "display_name": display_name,
                "material_icon": material_icon,
                "html_id": html_id,
            }
        )
