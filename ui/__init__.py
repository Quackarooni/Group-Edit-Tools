import bpy
from bpy.types import Menu, Panel

from bl_ui import space_node
from bl_ui.space_node import NODE_PT_node_tree_interface, NODE_PT_node_tree_properties

from . import draw
from .. import utils


has_ui_been_overridden = False


class RefreshableBaseClass:
    bl_category = "Edit Group"
    default_bl_category = "Edit Group"

    @classmethod
    def reset_bl_category(cls):
        cls.bl_category = cls.default_bl_category


class GROUP_TOOLS_PT_PANEL(RefreshableBaseClass, Panel):
    bl_label = NODE_PT_node_tree_interface.bl_label
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = "UI"
    bl_order = 1

    poll = classmethod(utils.active_group_poll)

    def draw(self, context):
        group = utils.fetch_tree_of_active_node(context)
        draw.group_sockets(group, self.layout, context)
        return


class GROUP_TOOLS_PT_active_group_properties(RefreshableBaseClass, Panel):
    bl_label = "Group"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_order = 2

    if bpy.app.version >= (4, 2, 0):
        poll = classmethod(utils.active_group_poll)
    else:
        poll = classmethod(utils.active_group_old_props_poll)

    def draw(self, context):
        group = utils.fetch_tree_of_active_node(context)
        draw.active_group_properties(group, self.layout, context)
        return


if bpy.app.version >= (4, 1, 0):
    version_specific_classes = []
else:
    class GROUP_TOOLS_PT_active_group_copy_attributes(RefreshableBaseClass, Panel):
        bl_label = "Copy Attributes"
        bl_space_type = 'NODE_EDITOR'
        bl_region_type = 'UI'
        bl_parent_id = GROUP_TOOLS_PT_active_group_properties.__name__
        bl_order = 2

        if bpy.app.version >= (4, 2, 0):
            poll = classmethod(utils.active_group_poll)
        else:
            poll = classmethod(utils.active_group_old_props_poll)

        def draw(self, context):
            layout = self.layout
            draw.copy_properties(layout)
            return

    version_specific_classes = (
        GROUP_TOOLS_PT_active_group_copy_attributes,
    )


class GROUP_TOOLS_MT_active_interface_context_menu(Menu):
    bl_label = "Node Tree Interface Specials"

    def draw(self, _context):
        layout = self.layout
        layout.operator("group_edit_tools.active_interface_item_duplicate", icon='DUPLICATE')
        layout.operator("group_edit_tools.active_interface_item_swap_io_type", icon='ARROW_LEFTRIGHT')
        return


class NODE_PT_modified_node_tree_interface(Panel):
    bl_idname = "NODE_PT_node_tree_interface"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = "UI"
    bl_category = "Group"
    bl_label = NODE_PT_node_tree_interface.bl_label

    poll = classmethod(utils.group_poll)
        
    def draw(self, context):
        group = context.space_data.edit_tree
        draw.group_sockets(group, self.layout, context)
        return


class NODE_PT_modified_node_tree_properties(Panel):
    bl_idname = "NODE_PT_node_tree_properties"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Group"
    bl_label = NODE_PT_node_tree_properties.bl_label

    if bpy.app.version >= (4, 2, 0):
        poll = classmethod(utils.group_poll)
    else:
        poll = classmethod(utils.group_old_props_poll)

    def draw(self, context):
        tree = context.space_data.edit_tree
        draw.group_properties(tree, self.layout, context)
        return


def should_display_warning():
    return has_ui_been_overridden


def register_overriding_classes():
    global has_ui_been_overridden
    has_ui_been_overridden = True

    for cls in overriding_classes:
        original_class_name = getattr(cls, "bl_idname", cls.__name__)
        original_class = getattr(space_node, original_class_name)

        if hasattr(bpy.types, original_class_name):
            bpy.utils.unregister_class(original_class)
        bpy.utils.register_class(cls)


def unregister_overriding_classes():
    for cls in overriding_classes:
        original_class_name = getattr(cls, "bl_idname", cls.__name__)
        original_class = getattr(space_node, original_class_name)

        if hasattr(bpy.types, original_class_name):
            bpy.utils.unregister_class(cls)
        bpy.utils.register_class(original_class)


overriding_classes = (
    NODE_PT_modified_node_tree_interface,
    NODE_PT_modified_node_tree_properties,
)

refreshable_classes = (
    GROUP_TOOLS_PT_PANEL,
    GROUP_TOOLS_PT_active_group_properties,
    *version_specific_classes
)

classes = (
    *refreshable_classes,
    GROUP_TOOLS_MT_active_interface_context_menu,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    for cls in refreshable_classes:
        cls.reset_bl_category()