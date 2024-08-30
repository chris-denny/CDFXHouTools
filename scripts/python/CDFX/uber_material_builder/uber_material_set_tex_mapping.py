""" Sets the texture mapping method based on button pushed for all textures on the node."""


def set_all_tex_mapping(node, parm):
    parm_method = parm.name().split("_")[-1]
    set_tri = 0
    set_hex = 0
    match parm_method:
        case "UV":
            pass
        case "TRI":
            set_tri = 1
        case "HEX":
            set_hex = 1
        case "HEXTRI":
            set_tri = 1
            set_hex = 1
    for tex_parm in node.parms():
        if not ("detail" in tex_parm.name() or "set_all_tex" in tex_parm.name()):
            if tex_parm.name().endswith("TRI"):
                tex_parm.set(set_tri)
                tex_parm.pressButton()
            elif tex_parm.name().endswith("HEX"):
                tex_parm.set(set_hex)
                tex_parm.pressButton()
