import bpy
from bpy.types import Operator
from bpy.props import EnumProperty, IntProperty

from bl_operators.node import NodeInterfaceOperator

from . import utils


class GROUP_TOOLS_OT_copy_from_active(Operator):
    bl_idname = "node.group_edit_copy_from_active"
    bl_label = "Copy From Active"
    bl_description = "Apply properties from the active group onto other selected groups"
    bl_options = {'REGISTER', 'UNDO_GROUPED'} 

    @classmethod
    def poll(cls, context):
        active_node = context.active_node
        selected_nodes = context.selected_nodes
        prefs = utils.fetch_user_preferences()
        copy_props = tuple(prefs.copy_from_active.props_to_copy)

        return all((
            getattr(active_node, "select", False), 
            hasattr(active_node, "node_tree"), 
            len(selected_nodes) > 1, 
            len(copy_props)
            ))

    @staticmethod
    def fetch_prop_values(tree, prop_names):
        for prop in prop_names:
            if prop == "description" and (tree.asset_data is not None):
                yield getattr(tree.asset_data, prop)
            else:
                yield getattr(tree, prop)

    @staticmethod
    def set_prop_values(tree, prop_names, prop_values):
        for prop, prop_value in zip(prop_names, prop_values):
            if prop == "description" and (tree.asset_data is not None):
                setattr(tree.asset_data, prop, prop_value)
            else:
                setattr(tree, prop, prop_value)

    def execute(self, context):
        active_group = context.active_node.node_tree
        selected_groups = (node.node_tree for node in context.selected_nodes if hasattr(node, "node_tree"))
        prefs = utils.fetch_user_preferences()

        copy_props = tuple(prefs.copy_from_active.props_to_copy)

        active_group_props = tuple(self.fetch_prop_values(active_group, copy_props))
        for group in selected_groups:
            self.set_prop_values(group, copy_props, active_group_props)

        prop_count = len(copy_props)
        self.report({'INFO'}, f"Successfully copied {prop_count} {'properties' if prop_count != 1 else 'properties'} from group: \"{active_group.name}\"")

        return {'FINISHED'}


class GROUP_TOOLS_OT_interface_item_move(NodeInterfaceOperator, Operator):
    '''Move the active interface item to the specified direction'''
    bl_idname = "group_edit_tools.active_interface_item_move"
    bl_label = "Move Item"
    bl_options = {'REGISTER', 'UNDO'}

    direction: EnumProperty(
        name="Direction",
        description="Specifies which location the active item is moved to",
        items=(
            ('UP', "Move Up", ""),
            ('DOWN', "Move Down", "")
        ),
    )

    @classmethod
    def poll(cls, context):
        try:
            tree = context.group_edit_tree_to_edit

            return all((
                tree is not None,
                not tree.is_embedded_data,
                tree.interface.active is not None
            ))
        except AttributeError:
            return False

    @staticmethod
    def fetch_all_parents(interface):
        # The root panel that sockets are parented to by default is not directly accessible
        # Hence we retrieve it by creating a new socket and getting its parent
        new_socket = interface.new_socket(name="DUMMY_SOCKET")
        yield new_socket.parent
        interface.remove(new_socket)

        # Retrieve all other panels
        for item in interface.items_tree:
            if item.item_type == 'PANEL':
                yield item

    @staticmethod
    def get_prev_parent(parents, current_parent):
        prev_parent = parents[0]

        for parent in parents:
            if parent == current_parent:
                break

            prev_parent = parent
        
        return prev_parent

    @staticmethod
    def get_next_parent(parents, current_parent):
        iter_parents = iter(parents)
        for parent in iter_parents:
            if parent == current_parent:
                break

        try:
            next_parent = next(iter_parents)
        except StopIteration:
            next_parent = parent
        
        return next_parent

    def execute(self, context):
        interface = context.group_edit_tree_to_edit.interface
        active_item = interface.active

        offset = -1 if self.direction == 'UP' else 2

        old_position = active_item.position
        interface.move(active_item, active_item.position + offset)

        if old_position == active_item.position and active_item.item_type == 'SOCKET':
            parents = tuple(self.fetch_all_parents(interface))

            if self.direction == 'UP':
                new_parent = self.get_prev_parent(parents, active_item.parent)
                new_position = len(new_parent.interface_items)
            else:
                new_parent = self.get_next_parent(parents, active_item.parent)
                new_position = 0

            if new_parent != active_item.parent:
                interface.move_to_parent(active_item, new_parent, new_position)
            else:
                return {'CANCELLED'}

        interface.active_index = active_item.index
        return {'FINISHED'}


class GROUP_TOOLS_OT_active_interface_item_new(Operator):
    '''Add a new item to the interface'''
    bl_idname = "group_edit_tools.interface_item_new"
    bl_label = "New Item"
    bl_options = {'REGISTER', 'UNDO'}

    item_type: EnumProperty(
        name="Item Type",
        description="Type of the item to create",
        items=(
            ('INPUT', "Input", ""),
            ('OUTPUT', "Output", ""),
            ('PANEL', "Panel", ""),
        ),
        default='INPUT',
    )

    @classmethod
    def poll(cls, context):
        try:
            tree = context.group_edit_tree_to_edit
            return not (tree is None or tree.is_embedded_data)
        except AttributeError:
            return False

    # Returns a valid socket type for the given tree or None.
    @staticmethod
    def find_valid_socket_type(tree):
        socket_type = 'NodeSocketFloat'
        # Socket type validation function is only available for custom
        # node trees. Assume that 'NodeSocketFloat' is valid for
        # built-in node tree types.
        if not hasattr(tree, "valid_socket_type") or tree.valid_socket_type(socket_type):
            return socket_type
        # Custom nodes may not support float sockets, search all
        # registered socket subclasses.
        types_to_check = [bpy.types.NodeSocket]
        while types_to_check:
            t = types_to_check.pop()
            idname = getattr(t, "bl_idname", "")
            if tree.valid_socket_type(idname):
                return idname
            # Test all subclasses
            types_to_check.extend(t.__subclasses__())

    def execute(self, context):
        tree = context.group_edit_tree_to_edit
        interface = tree.interface

        # Remember active item and position to determine target position.
        active_item = interface.active
        active_pos = active_item.position if active_item else -1

        if self.item_type == 'INPUT':
            item = interface.new_socket("Socket", socket_type=self.find_valid_socket_type(tree), in_out='INPUT')
        elif self.item_type == 'OUTPUT':
            item = interface.new_socket("Socket", socket_type=self.find_valid_socket_type(tree), in_out='OUTPUT')
        elif self.item_type == 'PANEL':
            item = interface.new_panel("Panel")
        else:
            return {'CANCELLED'}

        if active_item is not None:
            # Insert into active panel if possible, otherwise insert after active item.
            if active_item.item_type == 'PANEL' and item.item_type != 'PANEL':
                interface.move_to_parent(item, active_item, len(active_item.interface_items))
            else:
                interface.move_to_parent(item, active_item.parent, active_pos + 1)

        interface.active = item
        return {'FINISHED'}


class GROUP_TOOLS_OT_active_interface_item_duplicate(Operator):
    '''Add a copy of the active item to the interface'''
    bl_idname = "group_edit_tools.active_interface_item_duplicate"
    bl_label = "Duplicate Item"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        try:
            tree = context.group_edit_tree_to_edit
            if not (tree is None or tree.is_embedded_data):
                return (tree.interface.active is not None)
        except AttributeError:
            return False

    def execute(self, context):
        tree = context.group_edit_tree_to_edit
        interface = tree.interface
        item = interface.active

        item_copy = interface.copy(item)
        interface.active = item_copy

        return {'FINISHED'}


class GROUP_TOOLS_OT_active_interface_item_swap_io_type(Operator):
    '''Swap the input/output type of active item to the opposite type'''
    bl_idname = "group_edit_tools.active_interface_item_swap_io_type"
    bl_label = "Swap Input/Output Type"
    bl_options = {'REGISTER', 'UNDO'}

    props = (
            "name", 
            "description", 
            "hide_value", 
            "subtype",
            "default_attribute_name",
            "default_value",
            "min_value",
            "max_value",
            )

    @staticmethod
    def relative_position(active_item):
        base_pos = 0
        offset = 0

        inputs = (i for i in active_item.parent.interface_items if i.in_out == "INPUT")

        if active_item.in_out == "INPUT":
            base_pos = 0
            for i, item in enumerate(inputs):
                if item == active_item:
                    offset = i
                    break
        else:
            for item in inputs:
                base_pos = item.position
                break
            offset = active_item.position

        return base_pos + offset

    @classmethod
    def poll(cls, context):
        try:
            tree = context.group_edit_tree_to_edit
            if not (tree is None or tree.is_embedded_data) and (tree.interface.active is not None):
                active_item = tree.interface.active
                return active_item.item_type == "SOCKET" and active_item.socket_type != "NodeSocketMenu"
                    
        except AttributeError:
            return False

    def execute(self, context):
        tree = context.group_edit_tree_to_edit
        interface = tree.interface

        # Remember active item and position to determine target position.
        active_item = interface.active

        if active_item.in_out == "OUTPUT":
            opposite_type = "INPUT"
        else:
            opposite_type = "OUTPUT"
        item = interface.new_socket("Socket", socket_type=active_item.socket_type, in_out=opposite_type)

        for prop in self.props:
            if hasattr(item, prop):
                setattr(item, prop, getattr(active_item, prop))

        if active_item is not None:
            interface.move_to_parent(item, active_item.parent, self.relative_position(active_item))

        interface.remove(active_item)
        interface.active = item
        return {'FINISHED'}


class GROUP_TOOLS_OT_active_interface_item_remove(Operator):
    '''Remove active item from the interface'''
    bl_idname = "group_edit_tools.interface_item_remove"
    bl_label = "Remove Item"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        try:
            tree = context.group_edit_tree_to_edit
            if not (tree is None or tree.is_embedded_data):
                return (tree.interface.active is not None)
        except AttributeError:
            return False

    def execute(self, context):
        tree = context.group_edit_tree_to_edit
        interface = tree.interface
        item = interface.active

        if item is None:
            return {'CANCELLED'}

        interface.remove(item)
        interface.active_index = min(interface.active_index, len(interface.items_tree) - 1)

        return {'FINISHED'}
    
    
class GROUP_TOOLS_OT_parent_to_panel(Operator):
    '''Parents the active item to the specified panel'''
    bl_idname = "group_edit_tools.parent_to_panel"
    bl_label = "Parent to Panel"
    bl_options = {'REGISTER', 'UNDO'}

    parent_index : IntProperty(name="Parent Index", default=0)


    if bpy.app.version >= (4, 4, 0):
        @classmethod
        def poll(cls, context):
            try:
                tree = context.group_edit_tree_to_edit
                if not (tree is None or tree.is_embedded_data) and (tree.interface.active is not None):
                    return context.group_edit_active_item is not None
                
            except AttributeError:
                return False
    else:
        @classmethod
        def poll(cls, context):
            try:
                tree = context.group_edit_tree_to_edit
                if not (tree is None or tree.is_embedded_data) and (tree.interface.active is not None):
                    return context.group_edit_active_item.item_type == 'SOCKET'
                
            except AttributeError:
                return False
                

    def execute(self, context):
        tree = context.group_edit_tree_to_edit
        interface = tree.interface
        active_item = context.group_edit_active_item

        if active_item is None:
            return {'CANCELLED'}

        if self.parent_index != -1:
            parent = interface.items_tree[self.parent_index]
        else:
            parent = utils.fetch_base_panel(tree)

        interface.move_to_parent(active_item, parent, len(parent.interface_items))
        interface.active = active_item

        return {'FINISHED'}


if bpy.app.version >= (4, 3, 0):
    class GROUP_TOOLS_OT_selected_group_default_width_set(Operator):
        '''Set the width based on the current context (applies to all selected nodegroups)'''
        bl_idname = "group_edit_tools.selected_group_default_width_set"
        bl_label = "Set Default Group Width"
        bl_options = {'REGISTER', 'UNDO'}

        @classmethod
        def poll(cls, context):
            try:
                selected_nodegroups = tuple(n for n in context.selected_nodes if hasattr(n, "node_tree"))
                return len(selected_nodegroups)
            except AttributeError:
                return False

        def execute(self, context):
            selected_nodegroups = tuple(n for n in context.selected_nodes if hasattr(n, "node_tree"))
            old_widths = tuple(n.node_tree.default_group_node_width for n in selected_nodegroups)

            for node in selected_nodegroups:
                tree = node.node_tree
            
                tree.default_group_node_width = int(node.width)

            new_widths = tuple(n.node_tree.default_group_node_width for n in selected_nodegroups)
            updated_widths = tuple(True for old_width, new_width in zip(old_widths, new_widths) if (old_width != new_width))
            updated_count = len(updated_widths)

            if updated_count > 0:
                self.report({"INFO"}, f"Succesfully updated the default width of {updated_count} nodegroups.")
            else:
                self.report({"WARNING"}, "Nodegroup widths are already up-to-date.")

            return {'FINISHED'}


    class GROUP_TOOLS_OT_selected_group_reset_to_default_width(Operator):
        '''Set the nodegroup width back to its default (applies to all selected nodegroups)'''
        bl_idname = "group_edit_tools.selected_group_reset_to_default_width"
        bl_label = "Reset to Default Width"
        bl_options = {'REGISTER', 'UNDO'}

        @classmethod
        def poll(cls, context):
            try:
                selected_nodegroups = tuple(n for n in context.selected_nodes if hasattr(n, "node_tree"))
                return len(selected_nodegroups)
            except AttributeError:
                return False

        def execute(self, context):
            selected_nodegroups = tuple(n for n in context.selected_nodes if hasattr(n, "node_tree"))
            old_widths = tuple(n.width for n in selected_nodegroups)

            for node in selected_nodegroups:
                tree = node.node_tree
                node.width = tree.default_group_node_width

            new_widths = tuple(n.width for n in selected_nodegroups)
            updated_widths = tuple(True for old_width, new_width in zip(old_widths, new_widths) if (old_width != new_width))
            updated_count = len(updated_widths)

            if updated_count > 0:
                self.report({"INFO"}, f"Succesfully updated the width of {updated_count} nodegroups.")
            else:
                self.report({"WARNING"}, "Nodegroup widths are already up-to-date.")

            return {'FINISHED'}


if bpy.app.version >= (4, 3, 0):
    version_specific_classes = (
        GROUP_TOOLS_OT_selected_group_default_width_set,
        GROUP_TOOLS_OT_selected_group_reset_to_default_width,
    )
else:
    version_specific_classes = (
    )


classes = (
    *version_specific_classes,
    GROUP_TOOLS_OT_active_interface_item_new,
    GROUP_TOOLS_OT_active_interface_item_duplicate,
    GROUP_TOOLS_OT_active_interface_item_remove,
    GROUP_TOOLS_OT_active_interface_item_swap_io_type,
    GROUP_TOOLS_OT_copy_from_active,
    GROUP_TOOLS_OT_interface_item_move,
    GROUP_TOOLS_OT_parent_to_panel,

)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
        