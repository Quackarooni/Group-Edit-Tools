import bpy
from bpy.props import BoolProperty, PointerProperty, StringProperty
from bpy.types import AddonPreferences, PropertyGroup

from .keymaps import keymap_layout
from . import utils
from .ui import (
    refreshable_classes,
    register_overriding_classes, 
    unregister_overriding_classes,
    should_display_warning,
    RefreshableBaseClass,
)

def refresh_ui(self=None, _context=None):
    if self is None:
        self = utils.fetch_user_preferences()
        
    for cls in refreshable_classes:
        cls.bl_category = self.panel_category
        
        if hasattr(bpy.types, getattr(cls, "bl_idname", cls.__name__)):
            bpy.utils.unregister_class(cls)
        bpy.utils.register_class(cls)


def toggle_overriding_ui(self, _context):
    if self.override_default_ui:
        register_overriding_classes()
    else:
        unregister_overriding_classes()


class CopyFromActiveGroupProps(PropertyGroup):
    if bpy.app.version >= (4, 2, 0):
        description : BoolProperty(name="Description", default=False)
        color_tag   : BoolProperty(name="Color Tag", default=True)
        
    is_modifier : BoolProperty(name="Modifier Flag", default=True)
    is_tool     : BoolProperty(name="Tool Flag", default=True)

    def properties(self):
        tree = utils.fetch_tree_of_active_node()

        props = self.__annotations__
        if (tree is None) or (tree.bl_idname != "GeometryNodeTree"):
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

    override_default_ui: BoolProperty(
        name="Override Default UI",
        default=True,
        description="Apply changes to the built-in \"Group\" interface to match this addon's features",
        update=toggle_overriding_ui,
    )

    panel_category : StringProperty(
        name="Panel Category",
        default=RefreshableBaseClass.default_bl_category,
        description="Specifies which sidebar category this addon's UI appears in",
        update=refresh_ui,
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "panel_category")
        layout.prop(self, "override_default_ui")
        if not self.override_default_ui and should_display_warning():
            layout.label(text="For changes to fully apply, please restart Blender.", icon="ERROR")
        
        keymap_layout.draw_keyboard_shorcuts(self, layout, context)


keymap_layout.register_properties(preferences=GroupEditToolsPrefs)


classes = (
    CopyFromActiveGroupProps,
    GroupEditToolsPrefs,
    )


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    prefs = utils.fetch_user_preferences()
    
    if prefs.override_default_ui:
        register_overriding_classes()

    refresh_ui()


def unregister():
    if utils.fetch_user_preferences("override_default_ui"):
        unregister_overriding_classes()

    for cls in classes:
        bpy.utils.unregister_class(cls)
