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
        layout.menu("GROUP_TOOLS_MT_parent_to_panel", icon="DOWNARROW_HLT")
        return
    

if bpy.app.version >= (4, 4, 0):
    class GROUP_TOOLS_MT_parent_to_panel(Menu):
        bl_label = "Parent to Panel"

        @staticmethod
        def valid_panels(context):
            tree = context.group_edit_tree_to_edit
            active_item = context.group_edit_active_item

            if active_item.item_type == "PANEL": 
                for panel in utils.fetch_group_items(tree, item_type="PANEL", include_base_panel=True):
                    if panel != active_item.parent:
                        if panel != active_item and not utils.is_child_of(panel, active_item):
                            yield panel

            else:
                for panel in utils.fetch_group_items(tree, item_type="PANEL", include_base_panel=True):
                    if panel != active_item.parent:
                        yield panel

        @classmethod
        def poll(self, context):
            return context.group_edit_active_item is not None and len(tuple(self.valid_panels(context))) > 0

        def draw(self, context):
            layout = self.layout

            # Don't let cache persist between menu draws
            utils.is_child_of.cache_clear()

            # TODO: Add support for parenting panels inside of panels in 4.4
            for panel in self.valid_panels(context):
                panel_name = panel.name if (panel.index != -1) else "(None)"
                
                props = layout.operator("group_edit_tools.parent_to_panel", text=panel_name)
                props.parent_index = panel.index
            
            return
else:
    class GROUP_TOOLS_MT_parent_to_panel(Menu):
        bl_label = "Parent to Panel"

        @staticmethod
        def valid_panels(context):
            tree = context.group_edit_tree_to_edit
            active_item = context.group_edit_active_item

            for panel in utils.fetch_group_items(tree, item_type="PANEL", include_base_panel=True):
                if panel != active_item.parent:
                    yield panel

        @classmethod
        def poll(self, context):
            try:
                return context.group_edit_active_item.item_type == 'SOCKET' and len(tuple(self.valid_panels(context))) > 0
            except AttributeError:
                return False

        def draw(self, context):
            layout = self.layout

            # TODO: Add support for parenting panels inside of panels in 4.4
            for panel in self.valid_panels(context):
                panel_name = panel.name if (panel.index != -1) else "(None)"
                
                props = layout.operator("group_edit_tools.parent_to_panel", text=panel_name)
                props.parent_index = panel.index
            
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
    GROUP_TOOLS_MT_parent_to_panel
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    for cls in refreshable_classes:
        cls.reset_bl_category()