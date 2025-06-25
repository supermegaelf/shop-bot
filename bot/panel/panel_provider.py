from panel import Panel
from .marzban_panel import MarzbanPanel
from .remnawave_panel import RemnawavePanel

import glv

def _init_panel() -> Panel:
    panel_type = glv.config["PANEL_TYPE"]
    panel_registry = {
        "MARZBAN": MarzbanPanel,
        "REMNAWAVE": RemnawavePanel
    }
    panel_class = panel_registry.get(panel_type)
    if not panel_class:
        raise ValueError(f"Unknown panel type: {panel_type}")
    return panel_class()

panel = _init_panel()

def get_panel() -> Panel:
    return panel