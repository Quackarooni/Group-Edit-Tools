from .keymap_ui import KeymapItemDef, KeymapStructure, KeymapLayout
from .operators import (
    GROUP_TOOLS_OT_copy_from_active,
)


keymap_info = {"keymap_name" : "Node Editor", "space_type" : "NODE_EDITOR",}
keymap_info_2 = {"keymap_name" : "User Interface", "space_type" : "EMPTY",}


keymap_structure = KeymapStructure(
    {
    "Group": (
        ),
    "Active Nodegroup": (
        KeymapItemDef(GROUP_TOOLS_OT_copy_from_active.bl_idname, **keymap_info),
        ),
    }
)

keymap_layout = KeymapLayout(layout_structure=keymap_structure)


def register():
    keymap_structure.register()


def unregister():
    keymap_structure.unregister()
