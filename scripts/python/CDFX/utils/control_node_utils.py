import hou #type:ignore

def attach_parameters(node, parm, control_node_name):
    """Create expression links between a node's parameters and a control node.
    
    Args:
        node: The node containing parameters to link
        parm: The parameter name to link
        control_node_name: Path to the control node
    """
    node_parm_tuple = node.parmTuple(parm)
    if node_parm_tuple is None:
        return

    # Get the control node
    control_node = node.node(control_node_name)
    if control_node is None:
        return
        
    for parm_item in node_parm_tuple:
        parm_name = parm_item.name()
        
        # Check if parameter exists on control node
        if control_node.parm(parm_name) is None:
            continue
            
        # Use chs() for string parameters, ch() for numeric parameters
        if parm_item.parmTemplate().type() == hou.parmTemplateType.String:
            parm_item.setExpression(f'chs("{control_node_name}/{parm_name}")')
        else:
            parm_item.setExpression(f'ch("{control_node_name}/{parm_name}")')


def detach_parameters(node, parm):
    """Remove expression links from a node's parameters.
    
    Args:
        node: The node containing parameters to unlink
        parm: The parameter name to unlink
    """
    node_parm_tuple = node.parmTuple(parm)
    if node_parm_tuple is None:
        return

    for parm_item in node_parm_tuple:
        parm_item.deleteAllKeyframes()

    

def get_new_parameters(node, full_update, enable_control_node):
    """Determine which parameters need to be attached or detached.
    
    Args:
        node: The Houdini node to process
        full_update: Whether to process all parameters or just changed ones
        enable_control_node: Whether control node functionality is enabled (1) or disabled (0)
        
    Returns:
        tuple: (parameters to add, parameters to remove)
    """

    # Get and clean parameter list
    parm_string = node.parm("attached_parms").evalAsString().strip()
    new_parameters = parm_string.split() if parm_string else []
    
    prev_parameters_cache = "attached_parms"
    # Get cached parameters or initialize empty list
    cached_parameters = node.cachedUserData(prev_parameters_cache) or []

    # Determine parameters to add based on mode
    added_parameters = []
    if enable_control_node == 1:
        if full_update:
            added_parameters = [p for p in new_parameters if node.parm(p) is not None]
        else:
            added_parameters = [p for p in new_parameters if p not in cached_parameters and node.parm(p) is not None]

    # Determine parameters to remove based on mode
    if full_update and enable_control_node == 0:
        # Add all previous and new parameters to removed parameters list
        all_params = set(cached_parameters + new_parameters)
        removed_parameters = [p for p in all_params if node.parm(p) is not None]
    else:
        removed_parameters = [p for p in cached_parameters if p not in new_parameters and node.parm(p) is not None]

    # Update the cached user data
    node.setCachedUserData(prev_parameters_cache, new_parameters)

    return added_parameters, removed_parameters

def link_parameters(node, control_node="ctl_node", full_update=False):
    """Main function to link or unlink parameters based on control node settings.
    
    Args:
        node: The Houdini node to process
        control_node: Parameter name containing the path to the control node
        full_update: Whether to process all parameters or just changed ones
    """
    # Get control node settings
    control_node_name = node.parm(control_node).evalAsString().strip()
    enable_control_node = node.parm("enable_ctl_node").evalAsInt()
    
    added_parameters, removed_parameters = get_new_parameters(node, full_update, enable_control_node)

    if not added_parameters and not removed_parameters:
        return

    # Early return if control node is disabled or not specified
    if enable_control_node == 0 and not full_update:
        return

    for added_parameter in added_parameters:
        attach_parameters(node, added_parameter, control_node_name)
    for removed_parameter in removed_parameters:
        detach_parameters(node, removed_parameter)


def menu_attach_parameters(node, parmtuple):
    """Add parameter to attached parameters list.
    
    Args:
        node: The node containing parameters to link
        parmtuple: The parameter tuple to link
    """
    attached_parms = node.parm("attached_parms")
    if attached_parms is None:
        return
        
    parm_string = attached_parms.evalAsString().strip()
    new_parameters = parm_string.split() if parm_string else []
    if parmtuple.name() not in new_parameters:
        new_parameters.append(parmtuple.name())
    attached_parms.set(" ".join(new_parameters))
    link_parameters(node)


def menu_detach_parameters(node, parmtuple):
    """Remove parameter from attached parameters list.
    
    Args:
        node: The node containing parameters to unlink
        parmtuple: The parameter tuple to unlink
    """
    attached_parms = node.parm("attached_parms")
    if attached_parms is None:
        return
        
    parm_string = attached_parms.evalAsString().strip()
    new_parameters = parm_string.split() if parm_string else []
    if parmtuple.name() in new_parameters:
        new_parameters.remove(parmtuple.name())
    attached_parms.set(" ".join(new_parameters))
    detach_parameters(node, parmtuple.name())
    node.setCachedUserData("attached_parms", new_parameters)


def menu_hardlink_parameters(node, parmtuple, control_node_parm="ctl_node"):
    """Remove parameter from attached parameters list and hardlink to control node.
    
    Args:
        node: The node containing parameters to link
        parmtuple: The parameter tuple to link
        control_node_name: Path to the control node
    """
    attached_parms = node.parm("attached_parms")
    if attached_parms is None:
        return
        
    parm_string = attached_parms.evalAsString().strip()
    new_parameters = parm_string.split() if parm_string else []
    if parmtuple.name() in new_parameters:
        new_parameters.remove(parmtuple.name())
    attached_parms.set(" ".join(new_parameters))
    link_parameters(node)
    
    # Get the control node
    control_node_name = node.parm(control_node_parm).evalAsString().strip()
    control_node = node.node(f"{control_node_name}")
    if control_node is None:
        return

    for parm_item in parmtuple:
        parm_name = parm_item.name()
        # Check if parameter exists on control node
        if control_node.parm(parm_name) is None:
            continue
        if parm_item.parmTemplate().type() == hou.parmTemplateType.String:
            parm_item.setExpression(f'chs(chsop("{control_node_parm}")/{parm_name})')
        else:
            parm_item.setExpression(f'ch(chsop("{control_node_parm}")/{parm_name})')