import bpy
from bpy.types import Menu, Panel

from bl_ui import space_node
from bl_ui.space_node import NODE_PT_node_tree_interface, NODE_PT_node_tree_properties

if bpy.app.version >= (4, 5, 0):
    from bl_ui.space_node import NODE_PT_node_tree_interface_panel_toggle

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

if bpy.app.version >= (4, 5, 0):
    class GROUP_TOOLS_PT_active_group_panel_toggle(RefreshableBaseClass, Panel):
        bl_label = "Panel Toggle"
        bl_space_type = 'NODE_EDITOR'
        bl_region_type = 'UI'
        bl_parent_id = "GROUP_TOOLS_PT_PANEL"

        @classmethod
        @utils.return_false_when(AttributeError, IndexError)
        def poll(self, context):
            tree = utils.fetch_tree_of_active_node(context)
            active_item = tree.interface.active
            first_item = active_item.interface_items[0]
            return getattr(first_item, "is_panel_toggle", False)
        
        def draw(self, context):
            layout = self.layout
            tree = utils.fetch_tree_of_active_node(context)
            active_item = tree.interface.active
            panel_toggle_item = active_item.interface_items[0]

            layout.use_property_split = True
            layout.use_property_decorate = False

            layout.prop(panel_toggle_item, "default_value", text="Default")

            col = layout.column(align=True)
            col.prop(panel_toggle_item, "hide_in_modifier")
            col.prop(panel_toggle_item, "force_non_field")
            return
        
    class GROUP_TOOLS_MT_interface_item_new(Menu):
        bl_label = "New Item"
        bl_description = "Add a new item to the interface"

        def draw(self, context):
            layout = self.layout
            
            group = context.group_edit_tree_to_edit
            active_item = group.interface.active

            layout.operator("group_edit_tools.interface_item_new", text='Input').item_type='INPUT'
            layout.operator("group_edit_tools.interface_item_new", text='Output').item_type='OUTPUT'
            layout.operator("group_edit_tools.interface_item_new", text='Panel').item_type='PANEL'

            if active_item.item_type == 'PANEL':
                layout.separator(type='LINE')
                layout.operator("group_edit_tools.interface_item_new_panel_toggle", text='Toggle', icon='NODE_SOCKET_BOOLEAN')

        
    version_specific_classes = (
        GROUP_TOOLS_PT_active_group_panel_toggle,
    )

elif bpy.app.version >= (4, 1, 0):
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

    if bpy.app.version >= (4, 5, 0):
        def draw(self, context):
            layout = self.layout
            
            group = context.group_edit_tree_to_edit
            active_item = group.interface.active

            layout.operator("group_edit_tools.active_interface_item_duplicate", icon='DUPLICATE')
            layout.operator("group_edit_tools.active_interface_item_swap_io_type", icon='ARROW_LEFTRIGHT')
            layout.menu("GROUP_TOOLS_MT_parent_to_panel", icon="DOWNARROW_HLT")
            layout.separator()
            if active_item.item_type == 'SOCKET':
                layout.operator("group_edit_tools.interface_item_make_panel_toggle", icon="NODE_SOCKET_BOOLEAN")
            elif active_item.item_type == 'PANEL':
                layout.operator("group_edit_tools.interface_item_unlink_panel_toggle", icon="NODE_SOCKET_BOOLEAN")

    else:
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
        @utils.return_false_when(AttributeError)
        def poll(self, context):
            return context.group_edit_active_item.item_type == 'SOCKET' and len(tuple(self.valid_panels(context))) > 0

        def draw(self, context):
            layout = self.layout

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
    

class NODE_PT_modified_node_tree_interface_panel_toggle(Panel):
    bl_idname = "NODE_PT_node_tree_interface_panel_toggle"
    bl_label = "Panel Toggle"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = "UI"
    bl_parent_id = "NODE_PT_node_tree_interface"
    bl_category = "Group"

    @classmethod
    @utils.return_false_when(AttributeError, IndexError)
    def poll(self, context):
        tree = context.space_data.edit_tree
        active_item = tree.interface.active
        first_item = active_item.interface_items[0]
        return getattr(first_item, "is_panel_toggle", False)
    
    def draw(self, context):
        layout = self.layout
        tree = context.space_data.edit_tree
        active_item = tree.interface.active
        panel_toggle_item = active_item.interface_items[0]

        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(panel_toggle_item, "default_value", text="Default")

        col = layout.column(align=True)
        col.prop(panel_toggle_item, "hide_in_modifier")
        col.prop(panel_toggle_item, "force_non_field")
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


if bpy.app.version >= (4, 5, 0):
    overriding_classes = (
        NODE_PT_modified_node_tree_interface,
        NODE_PT_modified_node_tree_properties,
        NODE_PT_modified_node_tree_interface_panel_toggle,
    )
else:
    overriding_classes = (
        NODE_PT_modified_node_tree_interface,
        NODE_PT_modified_node_tree_properties,
    )

refreshable_classes = (
    GROUP_TOOLS_PT_PANEL,
    GROUP_TOOLS_PT_active_group_properties,
    *version_specific_classes
)

if bpy.app.version >= (4, 5, 0):
    classes = (
        *refreshable_classes,
        GROUP_TOOLS_MT_interface_item_new,
        GROUP_TOOLS_MT_active_interface_context_menu,
        GROUP_TOOLS_MT_parent_to_panel,
    )
else:
    classes = (
        *refreshable_classes,
        GROUP_TOOLS_MT_active_interface_context_menu,
        GROUP_TOOLS_MT_parent_to_panel,
    )


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    for cls in refreshable_classes:
        cls.reset_bl_category()