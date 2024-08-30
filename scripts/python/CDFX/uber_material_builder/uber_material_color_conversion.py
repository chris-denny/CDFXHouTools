from CDFX.utils.color_conversion import convert_color, convert_srgb_to_linear, convert_linear_to_srgb

def color_conversion(**kwargs) -> None:
    """Perform color space conversion on a node's parameters"""
    # Get current node
    node = kwargs["node"]
    property_name, _, method = kwargs.get("parm_name", "").rpartition("_")
    property_name_base = f"{property_name}_val"
    
    # Create color dictionary from node parameters
    color = {
        f"{property_name_base}{channel}": node.parm(f"{property_name_base}{channel}").eval()
        for channel in "rgb"
    }
    # Assuming property_name_base is "albedo_val", the `color` dictionary would be:
    # {
    #     "albedo_valr": node.parm("albedo_valr").eval(),
    #     "albedo_valg": node.parm("albedo_valg").eval(),
    #     "albedo_valb": node.parm("albedo_valb").eval()
    # }

    # Get conversion function from method name
    conversion_func = {
        "srgbtolinear": convert_srgb_to_linear,
        "lineartosrgb": convert_linear_to_srgb
    }[method]
    
    # Apply conversion function to color dictionary
    color = convert_color(color, conversion_func)

    # Set the new color values on the node
    for name, value in color.items():
        node.parm(name).set(value)