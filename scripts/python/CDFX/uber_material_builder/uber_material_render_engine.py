import hou # type: ignore
import sys
import time

from CDFX.uber_material_builder.render_engine_index_dict import render_engine_index_dict

def render_engine_connections(**kwargs):
    """Connect or disconnect render engine nodes based on the enabled render_engines."""
    def log(message):
        if print_diagnostics:
            print(message)

    parent_node = hou.pwd()
    print_diagnostics = parent_node.parm("print_diagnostics").eval() == 1
    collect_node = parent_node.node("COLLECT")
    
    if not collect_node:
        print("Warning: No COLLECT node found, cannot connect render engines.")
        return
    
    _, render_engine = kwargs.get("parm_name", "").split("_")
    render_engine_enabled = parent_node.parm(kwargs.get("parm_name", "")).eval() == 1
    render_engine_node = parent_node.node(f"shader_{render_engine_index_dict[render_engine]}")
    
    if not render_engine_node:
        print(f"Warning: No node found for render engine {render_engine}")
        return

    if render_engine_enabled:
        if render_engine_node in collect_node.inputs():
            log(f"Warning: {render_engine} node is already connected to COLLECT node")
            return
        
        output_names = [name for name in render_engine_node.outputNames()
                        if not (render_engine == "karma" and name.startswith("mat_"))]
        
        for output_name in output_names:
            log(f"Connecting {render_engine} node output {output_name} to COLLECT node")
            collect_node.setNextInput(render_engine_node, render_engine_node.outputIndex(output_name))
    else:
        while True:
            connections = [conn for conn in collect_node.inputConnections() 
                           if conn.inputNode() == render_engine_node]
            if not connections:
                log(f"No connections to disconnect for {render_engine} node")
                break
            
            input_index = connections[0].inputIndex()
            collect_node.setInput(input_index, None)
            log(f"Disconnected {render_engine} node from COLLECT at input {input_index}")

    log(f"Finished {'connecting' if render_engine_enabled else 'disconnecting'} {render_engine} node")
    log("#" * 20 )
