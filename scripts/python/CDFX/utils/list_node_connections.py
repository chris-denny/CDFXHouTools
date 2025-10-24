import hou #type: ignore

def print_node_connections():
    # Get the currently selected node
    selected_nodes = hou.selectedNodes()

    if not selected_nodes:
        print(f"\nNo node selected.")
        return
    for node in selected_nodes:
        
        print(f"\nConnections for node '{node.name()}':")
        
        input_names = node.inputNames()
        input_labels = node.inputLabels()
        output_names = node.outputNames()
        output_labels = node.outputLabels()

        # Print inputs
        if input_names:
            print("  Inputs:")
            for name, label in zip(input_names, input_labels):
                input_index = node.inputIndex(name)
                input_node = node.input(input_index)
                if input_node:
                    connection_name = " <<< " + input_node.name()
                else:
                    connection_name = ""
                print(f"    {input_index}: {label} ({name}){connection_name}")
        else:
            print("  No Inputs.")
        
        # Print outputs
        if output_names:
            # Get all output connectors
            all_connectors = node.outputConnectors()
            print("  Outputs:")
            for name, label in zip(output_names, output_labels):
                output_index = node.outputIndex(name)
                connections = all_connectors[output_index]
                if connections:
                    # Get the connected nodes from this connector
                    connected_nodes = [conn.outputNode() for conn in connections]
                    connection_names = ", ".join([n.name() for n in connected_nodes])
                else:
                    connection_names = None
                print(f"    {output_index}: {label} ({name})")
                if connection_names: print(f"        >>> {connection_names}")
        else:
            print("  No Outputs.")
