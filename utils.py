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


def is_group_valid(tree, context):
    try:
        return not (tree is None or tree.is_embedded_data)
    except AttributeError:
        return False


def active_group_poll(cls, context):
    if not context.active_node.select:
        return False

    tree = fetch_tree_of_active_node(context)
    return is_group_valid(tree, context)


def group_poll(cls, context):
    try:
        tree = context.space_data.edit_tree
        return is_group_valid(tree, context)
    except AttributeError:
        return False