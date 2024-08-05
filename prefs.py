import bpy
from bpy.props import BoolProperty, IntProperty, PointerProperty, StringProperty
from bpy.types import AddonPreferences, PropertyGroup

from .keymaps import keymap_layout
from .ui import refreshable_classes
from . import utils


def refresh_ui(self, _context):
    for cls in refreshable_classes:
        cls.bl_category = self.panel_category
        
        if hasattr(bpy.types, getattr(cls, "bl_idname", cls.__name__)):
            bpy.utils.unregister_class(cls)
        bpy.utils.register_class(cls)


class CopyFromActiveGroupProps(PropertyGroup):
    description : BoolProperty(name="Description", default=False)
    color_tag   : BoolProperty(name="Color Tag", default=True)
    is_modifier : BoolProperty(name="Modifier Flag", default=True)
    is_tool     : BoolProperty(name="Tool Flag", default=True)

    def properties(self):
        tree = utils.fetch_tree_of_active_node()

        props = self.__annotations__
        if tree.bl_idname != "GeometryNodeTree":
            props = tuple(p for p in props if p not in {"is_modifier", "is_tool"})

        return props

    @property
    def props_to_copy(self):
        for prop in self.properties():
            if getattr(self, prop):
                yield prop
    

class GroupEditToolsPrefs(AddonPreferences):
    bl_idname = __package__

    copy_from_active : PointerProperty(type=CopyFromActiveGroupProps)

    panel_category : StringProperty(
        name="Panel Category",
        default="Edit Group",
        description="Specifies which sidebar category this addon's UI appears in",
        update=refresh_ui,
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "panel_category")
        
        keymap_layout.draw_keyboard_shorcuts(self, layout, context)


keymap_layout.register_properties(preferences=GroupEditToolsPrefs)


classes = (
    CopyFromActiveGroupProps,
    GroupEditToolsPrefs,
    )


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
