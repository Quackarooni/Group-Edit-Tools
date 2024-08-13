from .keymap_ui import KeymapItemDef, KeymapStructure, KeymapLayout
from .operators import (
    GROUP_TOOLS_OT_copy_from_active,
)

from .ui.popups import (
    GROUP_TOOLS_OT_active_nodegroup_properties_popup,
    GROUP_TOOLS_OT_active_nodegroup_sockets_popup,
    GROUP_TOOLS_OT_group_sockets_popup,
)


keymap_info = {"keymap_name" : "Node Editor", "space_type" : "NODE_EDITOR",}



keymap_structure = KeymapStructure(
    {
    "Group": (
        ),
    "Active Nodegroup": (
        KeymapItemDef(GROUP_TOOLS_OT_copy_from_active.bl_idname, **keymap_info),
        ),
    "Pop-ups": (
        KeymapItemDef(GROUP_TOOLS_OT_group_sockets_popup.bl_idname, **keymap_info),
        KeymapItemDef(GROUP_TOOLS_OT_active_nodegroup_sockets_popup.bl_idname, **keymap_info),
        KeymapItemDef(GROUP_TOOLS_OT_active_nodegroup_properties_popup.bl_idname, **keymap_info),
        ),
    }
)

keymap_layout = KeymapLayout(layout_structure=keymap_structure)


def register():
    keymap_structure.register()


def unregister():
    keymap_structure.unregister()
