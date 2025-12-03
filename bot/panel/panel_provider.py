from .panel import Panel
from .remnawave_panel import RemnawavePanel

def _init_panel() -> Panel:
    return RemnawavePanel()

panel = _init_panel()

def get_panel() -> Panel:
    return panel