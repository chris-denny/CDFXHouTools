""" Destroys unconnected nodes in the Uber Material Builder. """
from CDFX.uber_material_builder.render_engine_index_dict import render_engine_index_dict

def destroy_unconnected_nodes(parent_node):
    def log(message):
        if print_diagnostics:
            print(message)

    try:
        print_diagnostics = parent_node.parm("print_diagnostics").eval() == 1
    except AttributeError:
        print_diagnostics = False

    excluded_nodes = {
        "COLLECT",
        "SHADER",
        "MATERIAL",
        "SOLO",
        "StoreColorToAOV",
        "StoreColorToAOV1",
        "StoreColorToAOV2",
        "AOVOUT",
        "suboutput",
    }
    exclusion_words = {"keep", "mat_", "_reference", "_clnsrc"}
    collect_node = parent_node.node("COLLECT")
    connected_nodes = set(collect_node.inputAncestors())

    destroyed_nodes = 0
    destroyed_render_engines = set()
    print(f"Shrinking {parent_node.name()}...")
    # First pass: destroy nodes that are not connected to the COLLECT node
    for node in parent_node.children():
        if node.name() in excluded_nodes:
            log(f"Excluding node: {node.name()}")
            continue
        if any(exclusion_word in node.name().lower() for exclusion_word in exclusion_words):
            log(f"Excluding node: {node.name()}")
            continue
        if node not in connected_nodes:
            log(f"Destroying node: {node.name()}")
            destroyed_render_engines.add(node.name())
            node.destroy()
    # Second pass: destroy nodes that are not connected within each renderers node
    for node in parent_node.children():
        if node.name() != "COLLECT":
            material_node = node.node("MATERIAL")
            connected_nodes = set(material_node.inputAncestors())
            for child_node in node.children():
                child_name = child_node.name()
                if child_node in connected_nodes or child_name in excluded_nodes:
                    log(f"Excluding node: {child_name}")
                    continue
                if any(exclusion_word in child_name.lower() for exclusion_word in exclusion_words):
                    if "_clnsrc" in child_name.lower():
                        if not child_node.inputConnections():
                            log(f"Destroying node: {child_name}")
                            destroyed_nodes += 1
                            child_node.destroy()
                            continue
                    log(f"Excluding node: {child_name}")
                    continue
                log(f"Destroying node: {child_name}")
                destroyed_nodes += 1
                child_node.destroy()

    print(f"  Removed: {list(destroyed_render_engines) if len(destroyed_render_engines) > 0 else 'No'} render engine nodes, "
          f"{destroyed_nodes} child nodes.")
