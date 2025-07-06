import bpy

from .. import utils


field_socket_types = {
    "NodeSocketInt",
    "NodeSocketColor",
    "NodeSocketVector",
    "NodeSocketBool",
    "NodeSocketFloat",
}


if bpy.app.version >= (4, 5, 0):
    def add_item(layout):
        layout.menu("GROUP_TOOLS_MT_interface_item_new", icon='ADD', text="")
else:
    def add_item(layout):
        layout.operator_menu_enum("group_edit_tools.interface_item_new", "item_type", icon='ADD', text="")


def side_buttons(tree, layout):
    col = layout.column(align=True)
    col.enabled = tree.library is None

    col.context_pointer_set("group_edit_tree_to_edit", tree)
    col.context_pointer_set("group_edit_active_item", tree.interface.active)

    add_item(col)
    col.operator("group_edit_tools.interface_item_remove", icon='REMOVE', text="")
    col.separator()
    col.menu("GROUP_TOOLS_MT_active_interface_context_menu", icon='DOWNARROW_HLT', text="")
    col.separator()

    col.operator("group_edit_tools.active_interface_item_move", icon='TRIA_UP', text="").direction = "UP"
    col.operator("group_edit_tools.active_interface_item_move", icon='TRIA_DOWN', text="").direction = "DOWN"
    col.separator()


def group_sockets(tree, layout, context):
    layout.use_property_split = True
    layout.use_property_decorate = False

    row = layout.row()
    row.enabled = tree.library is None
    row.template_node_tree_interface(tree.interface)

    side_buttons(tree, layout=row)

    active_item = tree.interface.active
    if active_item is None:
        return

    if active_item.item_type == 'SOCKET':
        layout.prop(active_item, "socket_type", text="Type")
        layout.prop(active_item, "description")

        if tree.type == 'GEOMETRY':
            if active_item.socket_type in field_socket_types:
                if 'OUTPUT' in active_item.in_out:
                    layout.prop(active_item, "attribute_domain")
                layout.prop(active_item, "default_attribute_name")
        active_item.draw(context, layout)

    if active_item.item_type == 'PANEL':
        layout.prop(active_item, "description")
        layout.prop(active_item, "default_closed", text="Closed by Default")


if bpy.app.version >= (4, 3, 0):
    def group_properties(tree, layout, context, **settings):
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(tree, "name", text="Name")
        default_width_operator = settings.get("default_width_operator", "node.default_group_width_set")
        is_active_group = settings.get("is_active_group", False)

        if tree.asset_data:
            layout.prop(tree.asset_data, "description", text="Description")
        else:
            layout.prop(tree, "description", text="Description")

        layout.prop(tree, "color_tag")
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(tree, "default_group_node_width", text="Default Width")
        row.operator(default_width_operator, text="", icon='NODE')

        if is_active_group:
            row = col.row(align=True)
            row.prop(context.active_node, "width", text="Node Width")
            row.operator("group_edit_tools.selected_group_reset_to_default_width", text="", icon='NODE')

        if tree.bl_idname == "GeometryNodeTree":
            header, body = layout.panel("group_usage")
            header.label(text="Usage")
            if body:
                col = body.column(align=True)
                col.prop(tree, "is_modifier")
                col.prop(tree, "is_tool")

elif bpy.app.version >= (4, 2, 0):
    def group_properties(tree, layout, context):
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(tree, "name", text="Name")

        if tree.asset_data:
            layout.prop(tree.asset_data, "description", text="Description")
        else:
            layout.prop(tree, "description", text="Description")

        layout.prop(tree, "color_tag")

        if tree.bl_idname == "GeometryNodeTree":
            header, body = layout.panel("group_usage")
            header.label(text="Usage")
            if body:
                col = body.column(align=True)
                col.prop(tree, "is_modifier")
                col.prop(tree, "is_tool")

else:
    def group_properties(tree, layout, context):
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column()
        col.prop(tree, "is_modifier")
        col.prop(tree, "is_tool")


if bpy.app.version >= (4, 3, 0):
    def active_group_properties(tree, layout, context):
        layout.use_property_split = True
        layout.use_property_decorate = False

        group_properties(tree, layout, context, 
            is_active_group=True,
            default_width_operator="group_edit_tools.selected_group_default_width_set"
            )

        header, body = layout.panel("copy_attributes")
        header.label(text="Copy Attributes")
        if body:
            copy_properties(body)
            
elif bpy.app.version >= (4, 1, 0):
    def active_group_properties(tree, layout, context):
        layout.use_property_split = True
        layout.use_property_decorate = False

        group_properties(tree, layout, context)

        header, body = layout.panel("copy_attributes")
        header.label(text="Copy Attributes")
        if body:
            copy_properties(body)
            
else:
    def active_group_properties(tree, layout, context):
        layout.use_property_split = True
        layout.use_property_decorate = False

        group_properties(tree, layout, context)


def copy_properties(layout):
    layout.use_property_split = True
    layout.use_property_decorate = False
    
    col = layout.column(align=True)
    copy_props = utils.fetch_user_preferences("copy_from_active")
    for prop_name in copy_props.properties():
        col.prop(copy_props, prop_name)

    layout.operator("node.group_edit_copy_from_active")