import bpy
import functools


def rsetattr(obj, attr, val):
    pre, _, post = attr.rpartition('.')
    return setattr(rgetattr(obj, pre) if pre else obj, post, val)


def rgetattr(obj, attr, *args):
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)
    return functools.reduce(_getattr, [obj] + attr.split('.'))


def fetch_user_preferences(attr_id=None):
    prefs = bpy.context.preferences.addons[__package__].preferences

    if attr_id is None:
        return prefs
    else:
        return getattr(prefs, attr_id)


def fetch_tree_of_active_node(context=None):
    if context is None:
        context = bpy.context

    try:
        tree = context.active_node.node_tree
    except AttributeError:
        tree = None

    return tree

if bpy.app.version >= (4, 4, 0):
    @functools.cache
    def is_child_of(child, parent):
        if child.parent is None:
            return False
        elif child.parent == parent:
            return True
        else:
            return is_child_of(child.parent, parent)
        

def compare_attributes(item, *_, **keywords):
    for key, value in keywords.items():
        if getattr(item, key, None) != value:
            return False
        
    return True


def is_panel_toggle(item):
    return compare_attributes(item, in_out="INPUT", is_panel_toggle=True, socket_type="NodeSocketBool")


def get_panel_toggle(panel):
    try:
        first_item = panel.interface_items[0]
        if is_panel_toggle(first_item):
            return first_item
        else:
            return None
    except (AttributeError, IndexError):
        return None


def fetch_base_panel(group):
    new_socket = group.interface.new_socket(name="DUMMY_SOCKET")
    panel =  new_socket.parent
    group.interface.remove(new_socket)
    return panel


def fetch_group_items(group, item_type=None, include_base_panel=False):
    if item_type is None:
        return group.interface.items_tree
    else:
        if include_base_panel:
            yield fetch_base_panel(group)

        panels = (i for i in group.interface.items_tree if i.item_type == item_type)
        for item in panels:
            yield item


def is_group_valid(tree, context):
    return not (tree is None or tree.is_embedded_data)


# Decorator for allowing poll functions to safely return False
# should they encounter a specific kind of Exception
def return_false_when(*args, **_):
    exceptions = *args,

    def decorator(poll):
        @functools.wraps(poll)
        def wrapper(self, context):
            try:
                return poll(self, context)
            except exceptions:
                return False
            
        return wrapper
    return decorator


@return_false_when(AttributeError)
def active_group_poll(cls, context):
    if not context.active_node.select:
        return False

    tree = fetch_tree_of_active_node(context)
    return is_group_valid(tree, context)


@return_false_when(AttributeError)
def group_poll(cls, context):
    tree = context.space_data.edit_tree
    return is_group_valid(tree, context)


@return_false_when(AttributeError)
def active_group_old_props_poll(cls, context):
    if not context.active_node.select:
        return False

    tree = fetch_tree_of_active_node(context)
    return (tree.bl_idname == "GeometryNodeTree") and is_group_valid(tree, context)


@return_false_when(AttributeError)
def group_old_props_poll(cls, context):
    tree = context.space_data.edit_tree
    return (tree.bl_idname == "GeometryNodeTree") and is_group_valid(tree, context)