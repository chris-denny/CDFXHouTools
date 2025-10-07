import hou #type: ignore
import os
import re

def version_numbered_string(parm, method, node):
    """ 
    Version a numbered string parameter on a Houdini node.
    
    Args:
        parm: Parameter name to modify
        method: Either "increment" or "decrement"
        node: The Houdini node
        
    Raises:
        ValueError: If method is invalid
        AttributeError: If parameter doesn't exist on node

    Example Callback Script:
        Increment:
            from CDFX.utils.output_utils import version_numbered_string;version_numbered_string(parm="version", method="increment", node=kwargs["node"])
        Decrement:
            from CDFX.utils.output_utils import version_numbered_string;version_numbered_string(parm="version", method="decrement", node=kwargs["node"])
    """

    if method not in ("increment", "decrement"):
        raise ValueError("Method must be either 'increment' or 'decrement'")

    parm_obj = node.parm(parm)
    if parm_obj is None:
        raise AttributeError(f"Parameter '{parm}' not found on node '{node.name()}'")
    
    input_string = parm_obj.eval()
    
    # Apply transformation
    if method == "increment":
        output_string = hou.text.incrementNumberedString(input_string)
    else: # method == "decrement"
        output_string = decrement_numbered_string(input_string)
    
    # Set new value
    if output_string != input_string:
        parm_obj.set(output_string)
        hou.ui.setStatusMessage(f"'{node.name()}' parameter '{parm}' versioned: {input_string} >>> {output_string}", hou.severityType.Message)
    else:
        hou.ui.setStatusMessage(f"'{node.name()}' parameter '{parm}' unchanged: {input_string}", hou.severityType.Message)

    # Trigger check directory parameter
    check_dir_parm_obj = node.parm("check_dir")
    if check_dir_parm_obj is not None:
        check_dir_parm_obj.pressButton()
    
        
def decrement_numbered_string(input_string):
    """
    Decrements the number in a string, preserving zero-padding.
    
    Args:
        input_string: String containing a trailing number
        
    Returns:
        String with decremented number, or original if no number found
    """

    # Find the trailing number in the string
    match = re.search(r'(\d+)$', input_string)
    
    if not match:
        # No number found at the end, return original string
        return input_string
    
    number_str = match.group(1)
    prefix = input_string[:match.start()]
    
    # Convert to integer and decrement (don't go below 1)
    number = max(1, int(number_str) - 1)
    
    # Return the decremented string with the same width as the original
    return prefix + str(number).zfill(len(number_str))


def check_directory(dir_parm, dir_msg_parm, node):
    """
    Check if a directory exists and if files exist in the directory.
    
    Args:
        dir_parm: Parameter name to modify, this should be the full path to the directory/file output.
        dir_msg_parm: Parameter name to modify, this should be the message to display to the user.
        node: The Houdini node
        
    Raises:
        AttributeError: If parameter doesn't exist on node

    Example Callback Script:from CDFX.utils.output_utils import check_directory;check_directory(dir_parm="RS_outputFileNamePrefix", dir_msg_parm="dir_msg", node=kwargs["node"])
        
    """
    
    dir_parm_obj = node.parm(dir_parm)
    if dir_parm_obj is None:
        raise AttributeError(f"Parameter '{dir_parm}' not found on node '{node.name()}'")
    
    dir_msg_parm_obj = node.parm(dir_msg_parm)
    if dir_msg_parm_obj is None:
        raise AttributeError(f"Parameter '{dir_msg_parm}' not found on node '{node.name()}'")
    
    dir = dir_parm_obj.evalAsString()
    dir = os.path.dirname(dir)
    folder_name = os.path.basename(dir)

    # Check if directory exists, and if files exist in the directory
    folder_name = os.path.basename(dir)
    if not os.path.exists(dir):
        dir_msg_parm_obj.set(f"Folder '{folder_name}' does not exist.")
    else:
        try:
            # Check if directory has any contents without listing everything
            has_contents = next(os.scandir(dir), None) is not None
            if not has_contents:
                dir_msg_parm_obj.set(f"Folder '{folder_name}' exists and is empty.")
            else:
                dir_msg_parm_obj.set(f"Folder '{folder_name}' exists and is not empty.")
        except PermissionError:
            dir_msg_parm_obj.set(f"Folder '{folder_name}' exists but cannot be accessed.")
