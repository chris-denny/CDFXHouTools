""" Recreates the current node in the Houdini scene. """

import hou # type: ignore
import os


class NodeRecreator:
    def __init__(self, node, node_destroy_check, grab_latest, keep_children, use_new_parm_defaults, print_diagnostics):
        self.node = node
        self.new_node = None
        self.parent_node = self.node.parent()
        self.node_name = self.node.name()
        self.node_position = self.node.position()
        self.node_destroy_check = node_destroy_check
        self.success = 1
        self.grab_latest = grab_latest
        self.keep_children = keep_children
        self.use_new_parm_defaults = use_new_parm_defaults
        self.print_diagnostics = print_diagnostics
        self.temp_dir = hou.getenv("HOUDINI_TEMP_DIR")
        self.temp_file = os.path.join(self.temp_dir, "CDFX_recreate_self.cpio")

    def log(self, message=""):
        if self.print_diagnostics:
            print(message)

    def transfer_connections(self, old_node, new_node, keep_children=[]):
        for conn in old_node.inputConnections():
            input_node = new_node.parent().item(conn.inputItem().name())
            if input_node:
                self.log(f"  Input connection: {conn}")
                if not (old_node in keep_children and conn.inputItem() in keep_children):
                    new_node.setInput(conn.inputIndex(), input_node, conn.outputIndex())
                else:
                    self.log(f"  Skipping connection between copied nodes: {conn}")
            else:
                print(
                    f"Failed to transfer input connection from '{conn.inputItem().name()}' to '{new_node.name()}'. "
                    "A custom node may have not copied over."
                )
                self.success = 0

        for conn in old_node.outputConnections():
            output_node = new_node.parent().item(conn.outputItem().name())
            if output_node:
                self.log(f"  Transferring connection: {conn}")
                if not (old_node in keep_children and conn.outputItem() in keep_children):
                    output_node.setInput(conn.inputIndex(), new_node, conn.outputIndex())
                else:
                    self.log(f"  Skipping connection between copied nodes: {conn}")
            else:
                print(
                    f"Failed to transfer output connection from '{new_node.name()}' to '{conn.outputItem().name()}'. "
                    "A custom node may have not been copied over."
                )
                self.success = 0

    def copy_children(self, old_parent_node, new_parent_node, copied_nodes=None):
        if copied_nodes is None:
            copied_nodes = set()

        if old_parent_node.isLockedHDA():
            # self.log(f"Ignoring children from locked asset '{old_parent_node.name()}', skipping.")
            return

        children = set(old_parent_node.children())
        try:
            network_dots = set(old_parent_node.networkDots())
        except hou.OperationFailed:
            network_dots = set()

        all_items = children.union(network_dots)
        if all_items:
            keep_items = set()
            other_children = set()

            for item in all_items:
                if isinstance(item, hou.Node) and "keep" in item.name().lower():
                    keep_items.add(item)
                elif isinstance(item, hou.NetworkDot):
                    input_node = item.input()
                    output_nodes = set(item.outputs())
                    if (input_node and "keep" in input_node.name().lower()) or \
                       any("keep" in node.name().lower() for node in output_nodes):
                        keep_items.add(item)
                elif isinstance(item, hou.Node):
                    other_children.add(item)

            if keep_items:
                self.log(f"Items to keep from '{old_parent_node.name()}': {[item.name() for item in keep_items]}")
                self.log(f"  Copying items: {[item.name() for item in keep_items]} to {new_parent_node.name()}")

                # Batch save and load
                old_parent_node.saveItemsToFile(list(keep_items), self.temp_file)
                new_parent_node.loadItemsFromFile(self.temp_file)

                # Find the newly pasted items
                new_items = [new_parent_node.node(item.name()) for item in keep_items if isinstance(item, hou.Node)]
                new_items += [dot for dot in new_parent_node.networkDots() if dot.name() in [item.name() for item in keep_items if isinstance(item, hou.NetworkDot)]]

                for old_item, new_item in zip(keep_items, new_items):
                    if isinstance(old_item, hou.Node) and new_item:
                        self.transfer_connections(old_item, new_item, keep_items)
                        copied_nodes.add(old_item)

            if other_children:
                for child in other_children - copied_nodes:
                    old_child_node = old_parent_node.node(child.name())
                    new_child_node = new_parent_node.node(child.name())
                    if old_child_node and new_child_node:
                        copied_nodes.add(child)
                        self.copy_children(old_child_node, new_child_node, copied_nodes)

    def copy_parameters(self):
        self.log(f"Copying parameters{ ' ' if self.use_new_parm_defaults else ' (including those still at default values) '}to new node.")
        excluded_parms = ["tex_mngr_msg"]
        self.log(f"Excluding parameters: {excluded_parms}")
        for parm in [parm for parm in self.node.parms() if parm.name() not in excluded_parms]:
            new_parm = self.new_node.parm(parm.name())
            if new_parm:
                try:
                    if not parm.isAtDefault(compare_expressions=True) or not self.use_new_parm_defaults:
                        new_parm.deleteAllKeyframes()
                        new_parm.setFromParm(parm)
                        # self.log(f"Parameter '{parm.name()}': {parm.eval()} -> '{new_parm.name()}': {new_parm.eval()}.")
                except AttributeError:
                    self.log(f"Failed to copy parameter '{parm.name()}'")
                    self.success = 0
            else:
                try:
                    # Create the parameter on the new node if it doesn't exist
                    parm_template = parm.parmTemplate()
                    if str(parm_template.type()) not in ["parmTemplateType.FolderSet",
                                                        "parmTemplateType.Folder",
                                                        "parmTemplateType.Separator"]:
                        self.new_node.addSpareParmTuple(parm_template)
                        new_parm = self.new_node.parm(parm.name())
                        new_parm.setFromParm(parm)
                        self.log(f"Parameter '{parm.name()}' created and set on the new node. Value is {parm.eval()}.")
                        
                        # Check the parameter name, and if it matches certain names, copy the value over to the parameter name
                        # Only used for versioning 1.10 to 1.11
                        # new_parm_val = new_parm.eval()
                        # if new_parm_val != 0 or new_parm_val != 1:
                        #     match new_parm.name():
                        #         case "detail_a_inmin":
                        #             self.new_node.parm("detail_a_remap1pos").set(new_parm_val)
                        #             self.log(
                        #                 f"Parameter '{parm.name()}' copied to 'detail_a_remap1pos'"
                        #             )
                        #         case "detail_a_inmax":
                        #             self.new_node.parm("detail_a_remap2pos").set(new_parm_val)
                        #             self.log(f"Parameter '{parm.name()}' copied to 'detail_a_remap2pos'")
                        #         case "detail_b_inmin":
                        #             self.new_node.parm("detail_b_remap1pos").set(new_parm_val)
                        #             self.log(f"Parameter '{parm.name()}' copied to 'detail_b_remap1pos'")
                        #         case "detail_b_inmax":
                        #             self.new_node.parm("detail_b_remap2pos").set(new_parm_val)
                        #             self.log(f"Parameter '{parm.name()}' copied to 'detail_b_remap2pos'")
                        #         case "detail_c_inmin":
                        #             self.new_node.parm("detail_c_remap1pos").set(new_parm_val)
                        #             self.log(f"Parameter '{parm.name()}' copied to 'detail_c_remap1pos'")
                        #         case "detail_c_inmax":
                        #             self.new_node.parm("detail_c_remap2pos").set(new_parm_val)
                        #             self.log(f"Parameter '{parm.name()}' copied to 'detail_c_remap2pos'")

                        # # Only used for versioning 1.11 to 1.12
                        # new_parm_val = new_parm.eval()
                        # match new_parm.name():
                        #     case "detail_a_noise_coord_scale_global":
                        #         self.new_node.parm("detail_a_tri_overall_scale").set(new_parm_val)
                        #         self.log(f"Parameter '{parm.name()}' copied to 'detail_a_tri_overall_scale'")
                        #     case "detail_b_noise_coord_scale_global":
                        #         self.new_node.parm("detail_b_tri_overall_scale").set(new_parm_val)
                        #         self.log(f"Parameter '{parm.name()}' copied to 'detail_b_tri_overall_scale'")
                        #     case "detail_c_noise_coord_scale_global":
                        #         self.new_node.parm("detail_c_tri_overall_scale").set(new_parm_val)
                        #         self.log(f"Parameter '{parm.name()}' copied to 'detail_c_tri_overall_scale'")
                    else:
                        self.log(f"Parameter '{parm.name()}' is a folder, skipping.")
                    
                except AttributeError:
                    self.log(f"Failed to create and set parameter '{parm.name()}'")
                    self.success = 0
        if self.success == 1:
            self.log(f"All parameters successfully copied from old node.")

        # Check that all parameters match
        for parm in [parm for parm in self.node.parms() if not parm.isAtDefault(compare_expressions=True) or not self.use_new_parm_defaults]:
            if parm.name() not in excluded_parms:
                new_parm = self.new_node.parm(parm.name())
                if new_parm and new_parm.rawValue() != parm.rawValue():
                    print(f"Warning: Parameter {parm.name()} does not match")
                    self.success = 0
        # # Temporary uniform scale for textures, added in version 1.12
        # for property in ["detail_a_tri", "detail_b_tri", "detail_c_tri", "textures_tri"]:
        #     scale = (self.new_node.parm(f"{property}_scale1").eval(),
        #              self.new_node.parm(f"{property}_scale2").eval(),
        #              self.new_node.parm(f"{property}_scale3").eval())
        #     if scale[0] == scale[1] == scale[2] and scale[0] != 0:
        #         self.new_node.parm(f"{property}_overall_scale").set(scale[0])
        #         self.new_node.parm(f"{property}_scale1").set(1.0)
        #         self.new_node.parm(f"{property}_scale2").set(1.0)
        #         self.new_node.parm(f"{property}_scale3").set(1.0)

    def recreate(self):
        # Create a new node of the same type
        node_version = (
            self.node.type().name()
            if not self.grab_latest
            else self.node.type().namespaceOrder()[0]
        )
        self.new_node = self.parent_node.createNode(node_version)

        self.log()
        self.log(f"{'#' * 30}")
        self.log(f"Recreating node: {self.node_name}")
        self.log(f"New node type: {self.new_node.type()}")
        self.log(f"Old node type: {self.node.type()}")
        self.log(f"Namespace Order: {self.node.type().namespaceOrder()}")
        self.log(f"Destroy old node: {self.node_destroy_check}")
        self.log(f"Grab latest version: {self.grab_latest}")
        self.log(f"Keep children with 'keep' in name: {self.keep_children}")

        # Copy the parameters and compare their values
        self.log(f"{'-' * 20}")
        self.copy_parameters()
        self.log(f"{'-' * 20}")

        # Set node properties
        self.new_node.setColor(self.node.color())
        self.new_node.setComment(self.node.comment())
        self.new_node.setPosition(self.node_position)

        if self.success == 1:
            try:
                self.new_node.parm("trigger_all_parms").pressButton()
            except AttributeError:
                pass

            if self.keep_children:
                # Check if any node with 'keep' in the ancestors list exists
                if not any("keep" in child.name().lower() for child in self.node.allSubChildren(recurse_in_locked_nodes=False)):
                    self.log(f"Found no nodes with 'keep' in the name, skipping 'keep children' process.")
                else:
                    self.copy_children(self.node, self.new_node)
            else:
                print("Warning: Not copying 'keep' children.")
            self.log(f"{'-' * 20}")

        # Check if success is still true
        if self.success == 1:
            # Transfer connections
            self.transfer_connections(self.node, self.new_node)
            # Delete the current node
            if self.node_destroy_check:
                self.node.destroy()
            else:
                self.new_node.move((self.node.size().x() * 1.5, 0))

            # Rename the new node to the old node's name and reposition
            self.new_node.setName(self.node_name, unique_name=True)
            self.new_node.setSelected(on=True)
            print(
                f"Successfully recreated {self.node_name}. "
                f"{'New node name: ' + self.new_node.name() if not self.node_destroy_check else ''}"
            )
        else:
            # response = hou.ui.displayMessage(
            #     f"Failed to recreate exact match of {self.node_name}. Do you want to keep the new node?",
            #     buttons=("Yes", "No"),
            #     default_choice=1,
            #     close_choice=1,
            # )
            response = 0
            if response == 1:  # No
                self.new_node.destroy()
            else:
                # Transfer connections
                self.transfer_connections(self.node, self.new_node)
                # Rename the new node to the old node's name and reposition
                self.new_node.setName(self.node_name, unique_name=True)
                self.new_node.setSelected(on=True)
                self.new_node.move((self.node.size().x() * 1.5, 0))
                print(
                    f"Recreated {self.node_name} with errors. "
                    f"New node name: {self.new_node.name()}"
                )
        self.log(f"{'#' * 30}")


# Example usage:
# node_recreator = NodeRecreator(node=my_node)
# node_recreator.recreate()
def recreate_self(
    node, node_destroy_check=False, grab_latest=True, keep_children=True, use_new_parm_defaults=True, print_diagnostics=False
):
    node_recreator = NodeRecreator(
        node, node_destroy_check, grab_latest, keep_children, use_new_parm_defaults, print_diagnostics
    )
    node_recreator.recreate()
