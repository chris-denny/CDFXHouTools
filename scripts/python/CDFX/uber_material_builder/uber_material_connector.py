import hou # type: ignore
import sys
import time

from CDFX.uber_material_builder.node_dict import node_dict
from CDFX.uber_material_builder.usd_index_dict import usd_index_dict
from CDFX.uber_material_builder.karma_index_dict import karma_index_dict
from CDFX.uber_material_builder.redshift_index_dict import redshift_index_dict
from CDFX.uber_material_builder.render_engine_index_dict import render_engine_index_dict


class NodeConnector:
    """Manages connections between nodes in a Houdini scene."""

    def __init__(self, parent_node, child_node, renderer, renderer_index_dict, print_diagnostics, **kwargs):
        self.version = parent_node.type().nameComponents()[3]
        self.major_version = int(self.version.split(".")[0])
        self.minor_version = int(self.version.split(".")[1])
        self.node_dict = node_dict
        self.parent_node = parent_node
        self.child_node = child_node
        self.renderer = renderer
        self.renderer_index_dict = renderer_index_dict
        self.parameter_name = kwargs["parm_name"]
        self.property_name = ""
        self.kwargs = kwargs
        self.parm_value = kwargs["script_value"]
        self.suffix_key = ""
        self.source_node_index = 0
        self.target_node_index = 0
        self.detail_node = node_dict["detailout"]
        self.bumpdetail_node = node_dict["bumpdetailout"]
        self.dispdetail_node = node_dict["dispdetailout"]
        self.weights_node = node_dict["weights"]
        self.shader_output = self.parent_node.parm("solo_METH").eval()
        self.osltri_enabled = (self.parent_node.parm("enable_osltri").eval() == 1 if self.renderer == "redshift" else False)
        self.print_diagnostics = print_diagnostics

    def log(self, message):
        if self.print_diagnostics:
            if self.renderer != "usd":
                print(message)

    def get_node_property(self, property_suffix):
        property_name = f"{self.property_name}{self.node_dict[property_suffix]}"
        if not hasattr(self.parent_node, "parm"):
            return False

        parm = self.parent_node.parm(property_name)
        return parm.eval() if parm is not None else False

    def compile_rs_osl(self, node, output_check):
        """Compiles an OSL node if needed."""
        osl_node = self.child_node.node(node)
        type = ""
        try:
            type = osl_node.type().name()
        except AttributeError:
            self.log(f"!! Error:'{node}' not found as a child of '{self.child_node}'.")
            return
        if type == "redshift::rsOSL":
            parm = osl_node.parm("RS_osl_compile")
            already_compiled = output_check in osl_node.outputNames()
            if parm and not already_compiled:
                self.log(f"Compiling OSL node: '{node}'...")
                parm.pressButton()
            if already_compiled:
                if not parm:
                    msg = f"!! Error: parm not found on OSL node: '{node}'."
                else:
                    msg = f"OSL node: '{node}' is already compiled."
                self.log(msg)
    
    def check_node(self, node_name, node_type):
        """Checks if a node exists in the Houdini scene."""
        base_message = f"  Checking for {node_type} node: {node_name}"
        
        if node_name is None:
            self.log(f"{base_message} - Skipping check because node name is 'None'.")
            return True
        
        # Check if it exists
        test_item = self.child_node.item(node_name)
        if test_item is not None:
            if isinstance(test_item, hou.NetworkDot):
                self.log(f"{base_message} - Network dot found.")
                return True
            elif isinstance(test_item, hou.Node):
                self.log(f"{base_message} - Node found.")
                return True
        
        # If neither a node nor a network dot is found, display an error message
        print(f"{base_message} - !! Error: Not found as a child of '{self.parent_node}/{self.child_node}'.")
        return False

    def set_indices(self):
        source_suffix_key = next(
            (
                key
                for key, suffix in self.node_dict.items()
                if self.source_node_name and self.source_node_name.endswith(suffix)
            ),
            None,
        )
        target_suffix_key = next(
            (
                key
                for key, suffix in self.node_dict.items()
                if self.target_node_name and self.target_node_name.endswith(suffix)
            ),
            None,
        )

        try:
            if self.renderer == "usd":
                self.source_node_index = self.renderer_index_dict[self.property_name]["source_index"]
            else:
                self.source_node_index = self.renderer_index_dict[
                    (self.property_name, source_suffix_key, target_suffix_key)
                ]["source_index"]
        except KeyError:
            self.source_node_index = 0
        try:
            if self.renderer == "usd":
                self.target_node_index = self.renderer_index_dict[self.property_name]["target_index"]
            else:
                self.target_node_index = self.renderer_index_dict[
                    (self.property_name, source_suffix_key, target_suffix_key)
                ]["target_index"]
        except KeyError:
            self.target_node_index = 0

        self.log(
            f"  Source suffix key: '{source_suffix_key}' for source node: '{self.source_node_name}'\n"
            f"  Target suffix key: '{target_suffix_key}' for target node: '{self.target_node_name}'"
        )

    def connect_nodes(self, source_name, target_name, source_index_override=0, target_index_override=0):
        """Connects the source node to the target node if they both exist."""
        self.log(f"{'-' * 20}")
        self.log(f"Child Node: {self.child_node.name()}")
        self.log(f"Property Name: {self.property_name}")
        self.log(f"Source Name: {source_name}")
        self.log(f"Target Name: {target_name}")

        if not self.check_node(source_name, "Source") or not self.check_node(target_name, "Target"):
            self.log(f"    Skipping connection for {source_name} to {target_name} because one or both nodes do not exist.")
            return

        self.source_node_name = source_name
        self.target_node_name = target_name
        self.source_node = self.child_node.item(self.source_node_name)
        self.target_node = self.child_node.item(self.target_node_name)

        if source_index_override == 0 and target_index_override == 0:
            self.set_indices()
        else:
            self.source_node_index = source_index_override
            self.target_node_index = target_index_override
            self.log(f"    Using override indices - Source: {self.source_node_index}, Target: {self.target_node_index}")

        if isinstance(self.target_node, hou.NetworkDot):
            current_input_node = self.target_node.input()
            if current_input_node != self.source_node:
                self.target_node.setInput(self.source_node)
                self.log(f"    Connected '{source_name}' to network dot '{target_name}'.")
            else:
                self.log(f"    '{source_name}' already connected to network dot '{target_name}'.")
        else:        
            current_input_node = self.target_node.input(self.target_node_index)
            if current_input_node is None or current_input_node != self.source_node:
                self.target_node.setInput(
                    self.target_node_index, self.source_node, self.source_node_index
                )
                self.log(
                    f"    Connected '{self.source_node_name}' at index '{self.source_node_index}' to '{self.target_node_name}' at index '{self.target_node_index}'."
                )
            else:
                self.log(
                    f"    '{self.source_node_name}' already connected to '{self.target_node_name}' at index '{self.target_node_index}'."
                )

    def resolve_connections(self):
        """Resolves the connection between nodes based on the property name and method."""
        for key, suffix in self.node_dict.items():
            if not self.parameter_name.endswith(suffix):
                continue

            self.property_name = self.parameter_name[:-len(suffix)]
            self.suffix_key = key
            self.suffix = suffix

            try:
                self.property_method = self.parent_node.parm(
                    f"{self.property_name}{self.node_dict['method']}"
                ).evalAsString()
            except AttributeError:
                self.property_method = ""

            if self.property_method == self.node_dict["custom"]:
                return

            # Check property methods
            method_is_none = self.property_method == self.node_dict["none"]
            texture_enabled = self.property_method == self.node_dict["tex"]
            triplanar_enabled = self.get_node_property("triplanar")
            hex_enabled = self.get_node_property("hex")
            detail_enabled = self.get_node_property("detail")
            aces_enabled = self.get_node_property("aces")
            roundcorner_enabled = self.get_node_property("roundcorner")

            # Expanded strings for nodes
            expanded_property_method = f"{self.property_name}{self.property_method}"
            expanded_triplanar = f"{self.property_name}{self.node_dict['triplanar']}"
            expanded_osltriplanar = f"{self.property_name}{self.node_dict['osltri']}"
            expanded_hex = f"{self.property_name}{self.node_dict['hex']}"
            expanded_hextri = f"{self.property_name}{self.node_dict['hextri']}"
            expanded_detail = f"{self.property_name}{self.node_dict['detail']}"
            expanded_detail_cc = f"{self.property_name}{self.node_dict['detail_cc']}"
            expanded_roundcorner = f"{self.property_name}{self.node_dict['roundcorner']}"
            expanded_aces = f"{self.property_name}{self.node_dict['aces']}"
            expanded_source = f"{self.property_name}{self.node_dict['source']}"
            expanded_cleansource = f"{self.property_name}{self.node_dict['cleansource']}"
            expanded_output = f"{self.property_name}{self.node_dict['output']}"

            # Expanded strings for parameters and node names
            expanded_sprite = self.node_dict["sprite"]
            expanded_solo = self.node_dict["solo"]
            expanded_aovout = self.node_dict["aovout"]
            expanded_shader = self.node_dict["shader"]
            expanded_material = self.node_dict["material"]

            if self.renderer == "redshift":
                # Pre-emptively trigger RS_osl_compile for texture and detail nodes
                # This is needed when HDA is locked with editable contents
                if any([texture_enabled, aces_enabled, hex_enabled]):
                    if self.property_name in ["detail_a", "detail_b", "detail_c"]:
                        self.compile_rs_osl(f"{self.property_name}_hex_tile", "UV_Offset")
                        self.compile_rs_osl(f"{self.property_name}_tri_hex_tile", "UV_Offset")
                        self.compile_rs_osl(f"{self.property_name}_tri_osl", "UV_Offset")
                    else:
                        self.compile_rs_osl(expanded_aces, "outColor")
                        self.compile_rs_osl("hex_tile", "UV_Offset")
                        self.compile_rs_osl("tri_hex_tile", "UV_Offset")
                        self.compile_rs_osl("tri_osl", "UV_Offset")
                if self.suffix_key == "sprite" or self.suffix_key == "aovout":
                    if self.shader_output != "beauty":
                        self.parent_node.parm("solo_METH").set("beauty")
                    isSprite = self.parent_node.parm(expanded_sprite).eval()
                    isAOV = self.parent_node.parm(expanded_aovout).eval()
                    self.source_node_name = expanded_aovout if isAOV else expanded_shader
                    self.target_node_name = expanded_sprite if isSprite else expanded_material
                    self.connect_nodes(self.source_node_name, self.target_node_name)
                    if isSprite:
                        self.connect_nodes(expanded_sprite, expanded_material)
                    return
                
            if self.renderer == "karma":
                if self.suffix_key == "kmablend":
                    new_node_type = self.get_node_property("kmablend")
                    if self.check_node(expanded_detail, "Detail"):
                        self.log(f"Changing {expanded_detail} from '{self.child_node.node(expanded_detail).type().name()}' to '{new_node_type}'")
                        self.child_node.node(expanded_detail).changeNodeType(new_node_type)
                    return
                if self.suffix_key == "sprite":
                    if self.shader_output != "beauty":
                        self.parent_node.parm("solo_METH").set("beauty")
                        self.connect_nodes(expanded_shader, expanded_material)
                    return
                if self.suffix_key == "aovout":
                    isAOV = self.parent_node.parm(expanded_aovout).eval()
                    self.target_node = self.child_node.node(expanded_material)
                    mat_nodes = [node for node in self.child_node.children() if node.name().startswith("mat_") and node.type().name() == "kma_aov::2.0"]
                    if isAOV:
                        for node in mat_nodes:
                                if node not in self.target_node.inputs():
                                    self.log(f"Connecting {node.name()} to {self.target_node.name()}")
                                    self.target_node.setNextInput(node)
                                else:
                                    self.log(f"{node.name()} already connected to {self.target_node.name()}")
                        self.log(f"All AOV nodes connected to {self.target_node.name()}")
                    else:
                        while True:
                            connections = [conn for conn in self.target_node.inputConnections() 
                                    if conn.inputNode() in mat_nodes]
                            if not connections:
                                break
                            input_index = connections[0].inputIndex()
                            node = connections[0].inputNode()
                            self.target_node.setInput(input_index, None)
                            self.log(f"Disconnected {node} node from MATERIAL at input {input_index}")
                        self.log(f"No more AOV connections to disconnect for {self.child_node.name()}/{expanded_material}")
                    if self.shader_output != "beauty":
                        self.parent_node.parm("solo_METH").set("beauty")
                        self.connect_nodes(expanded_shader, expanded_material)
                    return
                
            if self.property_name == "solo":
                match self.property_method:
                    case "beauty":
                        self.connect_nodes(expanded_shader, expanded_material)
                        return
                    case "detail":
                        self.source_node_name = self.detail_node
                    case "bumpdetail":
                        self.source_node_name = self.bumpdetail_node
                    case "dispdetail":
                        self.source_node_name = self.dispdetail_node
                    case "weights":
                        self.source_node_name = self.weights_node
                    case "bump" | "coatbump":
                        self.source_node_name = self.property_method + self.node_dict["cleansource"]
                    case "displacement":
                        self.source_node_name = self.property_method + self.node_dict["source"]
                    case _:
                        self.source_node_name = self.property_method + self.node_dict["output"]
                if self.renderer =="karma":
                    self.connect_nodes(self.source_node_name, expanded_solo, target_index_override=1)
                else:
                    self.connect_nodes(self.source_node_name, expanded_solo)
                self.connect_nodes(expanded_solo, expanded_material)
                return

            if texture_enabled:
                if hex_enabled and triplanar_enabled:
                    expanded_property_method = expanded_hextri
                elif hex_enabled:
                    expanded_property_method = expanded_hex
                elif triplanar_enabled:
                    if self.osltri_enabled:
                        expanded_property_method = expanded_osltriplanar
                    else:
                        expanded_property_method = expanded_triplanar
            if method_is_none:
                expanded_property_method = None
            
            if self.suffix_key == "detail_cc":
                if self.property_name == "displacement":
                    self.source_node_name = expanded_detail_cc if self.parm_value == "on" else self.dispdetail_node
                    self.connect_nodes(self.source_node_name, expanded_detail)
                elif self.property_name == "bump":
                    self.source_node_name = expanded_detail_cc if self.parm_value == "on" else self.bumpdetail_node
                    self.connect_nodes(self.source_node_name, expanded_detail)
                elif self.property_name == "coatbump":
                    self.source_node_name = expanded_detail_cc if self.parm_value == "on" else self.bumpdetail_node
                    self.connect_nodes(self.source_node_name, expanded_detail)
                else: 
                    self.source_node_name = expanded_detail_cc if self.parm_value == "on" else self.detail_node
                    self.connect_nodes(self.source_node_name, expanded_detail)
            elif self.property_name in ["detail_a", "detail_b", "detail_c"]:
                if detail_enabled:
                    self.connect_nodes(expanded_property_method, expanded_detail)
                    self.connect_nodes(expanded_detail, expanded_output)
                else:
                    self.connect_nodes(expanded_property_method, expanded_output)
                if self.suffix_key == "output":
                    self.source_node_name = None if self.parm_value == "off" else expanded_output
                    self.connect_nodes(self.source_node_name, self.detail_node)
                    self.connect_nodes(self.source_node_name, self.bumpdetail_node)
                    self.connect_nodes(self.source_node_name, self.dispdetail_node)
            elif self.property_name in ["bump", "coatbump"]:
                self.connect_nodes(expanded_property_method, expanded_source)
                self.connect_nodes(expanded_property_method, expanded_cleansource)
                self.connect_nodes(expanded_source, expanded_output)
                if method_is_none:
                    if self.property_name == "bump" and roundcorner_enabled:
                        self.connect_nodes(expanded_roundcorner, expanded_shader)
                    elif detail_enabled:
                        self.connect_nodes(expanded_detail, expanded_shader)
                    else:
                        self.connect_nodes(None, expanded_shader)
                elif roundcorner_enabled and self.property_name == "bump":
                    self.connect_nodes(expanded_roundcorner, expanded_output)
                    self.connect_nodes(expanded_detail, expanded_output)
                    self.connect_nodes(expanded_output, expanded_shader)
                elif detail_enabled:
                    self.connect_nodes(expanded_detail, expanded_output)
                    self.connect_nodes(expanded_output, expanded_shader)
                else:
                    self.connect_nodes(expanded_source, expanded_shader)
            elif self.property_name == "displacement":
                self.connect_nodes(expanded_property_method, expanded_source)
                if self.renderer == "karma":
                    if method_is_none and not detail_enabled:
                        self.source_node_name = None
                    elif detail_enabled:
                        self.source_node_name = expanded_detail
                    else:
                        self.source_node_name = expanded_source
                    self.connect_nodes(self.source_node_name, expanded_output)
                elif self.renderer == "redshift":
                    if method_is_none and not detail_enabled:
                        self.source_node_name = None
                    else:
                        self.source_node_name = expanded_output
                    self.connect_nodes(self.source_node_name, expanded_material)
            else:
                if detail_enabled and aces_enabled:
                    self.connect_nodes(expanded_property_method, expanded_detail)
                    self.connect_nodes(expanded_detail, expanded_aces)
                    self.connect_nodes(expanded_aces, expanded_output)
                elif detail_enabled:
                    self.connect_nodes(expanded_property_method, expanded_detail)
                    self.connect_nodes(expanded_detail, expanded_output)
                    if self.child_node.node(expanded_aces) is not None:
                        self.connect_nodes(None, expanded_aces)
                elif aces_enabled:
                    self.connect_nodes(expanded_property_method, expanded_aces)
                    self.connect_nodes(expanded_aces, expanded_output)
                else:
                    if self.child_node.node(expanded_aces) is not None:
                        self.connect_nodes(None, expanded_aces)
                    self.connect_nodes(expanded_property_method, expanded_output)

    def resolve_usd_connections(self):
        """Resolves the connections between nodes for USD renderer."""
        for _, suffix in self.node_dict.items():
            if not self.parameter_name.endswith(suffix):
                continue

            self.property_name = self.parameter_name[:-len(suffix)]
            if self.property_name not in usd_index_dict.keys():
                return
            try:
                self.property_method = self.parent_node.parm(
                    f"{self.property_name}{self.node_dict['method']}"
                ).evalAsString()
            except AttributeError:
                return

            if self.property_method == self.node_dict["custom"]:
                self.log("Custom method not supported for USD renderer.")
                return

            method_is_none = self.property_method == self.node_dict["none"]

            self.source_node_name = None if method_is_none else f"{self.property_name}{self.property_method}"
            self.target_node_name = self.node_dict['shader']

            if self.child_node.node(self.source_node_name) or method_is_none:
                self.connect_nodes(self.source_node_name, self.target_node_name)


# Function to initiate node connection
def initiate_node_connections(**kwargs):
    """Initiate node connections based on the renderer."""
    parent_node = kwargs["node"]
    print_diagnostics = parent_node.parm("print_diagnostics").eval() == 1
    if print_diagnostics:
        print()
        print("#" * 40)
        print(f"Processing parameter '{kwargs['parm'].name()}' on node '{parent_node.path()}'")
        print(f"{kwargs}")
    enabled_render_engines = set()
    for renderer, _ in render_engine_index_dict.items():
        try:
            if parent_node.parm(f"rndr_{renderer}").eval() == 1:
                enabled_render_engines.add(renderer)
        except AttributeError:
            pass

    # Create a mapping from node suffix to renderer
    node_to_renderer = {suffix: renderer for renderer, suffix in render_engine_index_dict.items()}
    # Process only nodes that match the enabled renderers
    for node in parent_node.children():
        suffix = node.name().rsplit('_', 1)[-1]
        if not suffix:
            continue
        renderer = node_to_renderer.get(suffix)
        if renderer and renderer in enabled_render_engines:
            renderer_index_dict = globals()[f"{renderer}_index_dict"]
            node_connector = NodeConnector(
                parent_node=parent_node, child_node=node, renderer=renderer, renderer_index_dict=renderer_index_dict, print_diagnostics=print_diagnostics, **kwargs
            )
            start_time = time.time()
            node_connector.log(f"\nProcessing for renderer: {renderer.upper()}")
            if renderer == "usd":
                node_connector.resolve_usd_connections()
            else:
                node_connector.resolve_connections()
            end_time = time.time()
            node_connector.log(f"Time taken: {(end_time - start_time)*1000:.3f} milliseconds")
            node_connector.log(f"{'_' * 30}")
    if print_diagnostics:
        print("#" * 40)