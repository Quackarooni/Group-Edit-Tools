from bpy.types import Operator

from . import draw
from .. import utils


class PopupPanelOperator(Operator):
    bl_options = {"INTERNAL"}

    @classmethod
    def poll(cls, context):
        ...

    def draw(self, context):
        ...

    def execute(self, context):
        return {"CANCELLED"}

    def invoke(self, context, event):
        popup_width = utils.fetch_user_preferences("popup_width")
        return context.window_manager.invoke_popup(self, width=popup_width)


class GROUP_TOOLS_OT_active_nodegroup_sockets_popup(PopupPanelOperator):
    bl_label = "Active Group Sockets"
    bl_idname = "group_edit_tools.active_group_sockets_popup"
    bl_description = "Calls the pop-up panel for group sockets"

    poll = classmethod(utils.active_group_poll)

    def draw(self, context):        
        self.layout.label(text=f"{self.bl_label}", icon="NODETREE")

        group = utils.fetch_tree_of_active_node(context)
        draw.group_sockets(group, self.layout, context)
        return


class GROUP_TOOLS_OT_active_nodegroup_properties_popup(PopupPanelOperator):
    bl_label = "Active Group Properties"
    bl_idname = "group_edit_tools.active_group_properties_popup"
    bl_description = "Calls the pop-up panel for group properties"

    poll = classmethod(utils.active_group_poll)

    def draw(self, context):        
        self.layout.label(text="Active Group", icon="NODETREE")

        group = utils.fetch_tree_of_active_node(context)
        draw.active_group_properties(group, self.layout, context)
        return


class GROUP_TOOLS_OT_group_sockets_popup(PopupPanelOperator):
    bl_label = "Group Sockets"
    bl_idname = "group_edit_tools.group_sockets_popup"
    bl_description = "Calls the pop-up panel for group sockets"

    @classmethod
    def poll(cls, context):
        snode = context.space_data
        if snode is None:
            return False
        group = snode.edit_tree
        if group is None:
            return False
        if group.is_embedded_data:
            return False
        return True

    def draw(self, context):        
        self.layout.label(text=f"{self.bl_label}", icon="NODETREE")

        group = context.space_data.edit_tree
        draw.group_sockets(group, self.layout, context)
        return


classes = (
    GROUP_TOOLS_OT_active_nodegroup_properties_popup,
    GROUP_TOOLS_OT_active_nodegroup_sockets_popup,
    GROUP_TOOLS_OT_group_sockets_popup,
)