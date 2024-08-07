from .keymap_ui import KeymapItemDef, KeymapStructure, KeymapLayout
from .operators import (
    GROUP_TOOLS_OT_copy_from_active,
)


keymap_info = {"keymap_name" : "Node Editor", "space_type" : "NODE_EDITOR",}


keymap_structure = KeymapStructure([
    KeymapItemDef(GROUP_TOOLS_OT_copy_from_active.bl_idname, **keymap_info),
    ]
)

keymap_layout = KeymapLayout(layout_structure=keymap_structure)


def register():
    keymap_structure.register()


def unregister():
    keymap_structure.unregister()
