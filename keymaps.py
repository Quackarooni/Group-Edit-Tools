import bpy

from .keymap_ui import KeymapItemDef, KeymapStructure, KeymapLayout
from .operators import (
    GROUP_TOOLS_OT_copy_from_active,
    GROUP_TOOLS_OT_selected_group_default_width_set,

)


keymap_info = {"keymap_name" : "Node Editor", "space_type" : "NODE_EDITOR",}

if bpy.app.version >= (4, 3, 0):
    keymap_structure = KeymapStructure([
        KeymapItemDef(GROUP_TOOLS_OT_copy_from_active.bl_idname, **keymap_info),
        KeymapItemDef(GROUP_TOOLS_OT_selected_group_default_width_set.bl_idname, **keymap_info),
        ]
    )
else:
    keymap_structure = KeymapStructure([
        KeymapItemDef(GROUP_TOOLS_OT_copy_from_active.bl_idname, **keymap_info),
        ]
    )

keymap_layout = KeymapLayout(layout_structure=keymap_structure)


def register():
    keymap_structure.register()


def unregister():
    keymap_structure.unregister()
