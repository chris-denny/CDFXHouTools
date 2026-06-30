import hou  # type: ignore

VALID_UBER_MATERIAL_TYPES = {
    "CDFX::Uber_Material_Builder_Redshift",
    "CDFX::Uber_Material_Builder_Karma",
    "CDFX::Uber_Material_Builder",
}


def is_uber_material_builder(node):
    """Check if a node's type matches one of the Uber Material Builder HDAs,
    regardless of version (e.g. ignores the trailing ::1.13)."""
    type_name = node.type().name()
    base_name = type_name.rsplit("::", 1)[0]
    return base_name in VALID_UBER_MATERIAL_TYPES


def get_descendants_excluding_locked_hda(node):
    """Get all descendant nodes, excluding anything inside a locked HDA."""
    all_children = node.allSubChildren()
    result = []
    for child in all_children:
        ancestor = child.parent()
        inside_locked_hda = False
        while ancestor and ancestor != node.parent():
            if ancestor.isLockedHDA():
                inside_locked_hda = True
                break
            ancestor = ancestor.parent()
        if not inside_locked_hda:
            result.append(child)
    return result


def count_unconnected(node):
    """
    Two-pass connectivity check, mirroring destroy_unconnected_nodes logic:
      Pass 1: top-level children connected to COLLECT.
      Pass 2: for each CONNECTED render-engine subnet, children connected to its own MATERIAL node.
              If the subnet itself isn't connected to COLLECT, all of its descendants
              count as unconnected (no point checking local wiring in a dead subnet).

    Returns (total_count, connected_count, unconnected_count), or None if no
    COLLECT node exists on this material.
    """
    collect_node = node.node("COLLECT")
    if collect_node is None:
        return None

    total = 0
    connected = 0

    top_level_connected = set(collect_node.inputAncestors())
    top_level_connected.add(collect_node)

    for child in node.children():
        if child.isLockedHDA():
            continue

        total += 1
        child_is_connected = child in top_level_connected
        if child_is_connected:
            connected += 1

        if child.name() == "COLLECT":
            continue

        if not child_is_connected:
            # Entire render-engine subnet is disconnected - all its descendants
            # are dead weight, don't bother checking local wiring
            for grandchild in get_descendants_excluding_locked_hda(child):
                total += 1
            continue

        # Pass 2: subnet IS connected, so check nested connectivity within it
        material_node = child.node("MATERIAL")
        if material_node is None:
            for grandchild in get_descendants_excluding_locked_hda(child):
                total += 1
            continue

        nested_connected = set(material_node.inputAncestors())
        nested_connected.add(material_node)

        for grandchild in child.children():
            total += 1
            if grandchild in nested_connected:
                connected += 1

    unconnected = total - connected
    return total, connected, unconnected


def print_unoptimized_mats(possible_threshold=45, threshold=55):
    print("_" * 32)

    selected_nodes = hou.selectedNodes()
    scanning_scene = False

    if not selected_nodes:
        mat_context = hou.node("/mat")
        if mat_context is None:
            print(f"No nodes selected and /mat context not found.")
            return
        selected_nodes = mat_context.children()
        if not selected_nodes:
            print(f"No nodes selected and /mat context is empty.")
            return
        print(f"No nodes selected, scanning all materials in /mat.")
        scanning_scene = True

    unoptimized = []
    possibly_unoptimized = []
    any_uber_mat_found = False

    for node in selected_nodes:
        if node.isLockedHDA():
            continue

        if not is_uber_material_builder(node):
            continue

        result = count_unconnected(node)
        if result is None:
            continue

        any_uber_mat_found = True
        total, connected, unconnected = result

        if total == 0:
            continue

        unconnected_pct = (unconnected / total) * 100

        if unconnected_pct >= threshold:
            unoptimized.append((node, total, connected, unconnected, unconnected_pct))
        elif unconnected_pct >= possible_threshold:
            possibly_unoptimized.append((node, total, connected, unconnected, unconnected_pct))


    if not any_uber_mat_found:
        if scanning_scene:
            print("Error: No Uber Materials in scene.")
        else:
            print("Error: No Uber Materials selected.")
        return

    print(f"Unoptimized Materials:")
    if not unoptimized:
        print("  None found.")
    else:
        for node, total, connected, unconnected, pct in sorted(unoptimized, key=lambda x: x[4], reverse=True):
            print(f"  {node.path()} - {pct:.0f}% unconnected ({unconnected}/{total} nodes)")

    print(f"\nPossibly Unoptimized Materials:")
    if not possibly_unoptimized:
        print("  None found.")
    else:
        for node, total, connected, unconnected, pct in sorted(possibly_unoptimized, key=lambda x: x[4], reverse=True):
            print(f"  {node.path()} - {pct:.0f}% unconnected ({unconnected}/{total} nodes)")

    if unoptimized:
        hou.clearAllSelected()
        for node, total, connected, unconnected, pct in unoptimized:
            node.setSelected(True)
        print("\nUnoptimized Materials have been selected.")
    
    print("_" * 32)

if __name__ == "__main__":
    pass