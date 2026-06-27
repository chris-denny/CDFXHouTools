import hou #type:ignore

def get_folder_hierarchy(node):
    # Dictionary to store parameters by folder path
    parms_by_folder = {}
    # List to track folder order
    folder_order = []
    
    # Function to recursively traverse the parameter template group
    def traverse_template_group(template, folder_path=""):
        if isinstance(template, hou.ParmTemplateGroup):
            # Process all entries in the group
            for entry in template.entries():
                traverse_template_group(entry, folder_path)
        
        elif isinstance(template, hou.FolderParmTemplate):
            # It's a folder, process its contents with updated path
            new_path = folder_path
            if new_path:
                new_path += ">" + template.label()
            else:
                new_path = template.label()
                
            # Add to folder order if not already there
            if new_path not in folder_order and new_path != "ROOT":
                folder_order.append(new_path)
                
            # Check if this is a multiparm folder
            if template.folderType() == hou.folderType.MultiparmBlock:
                # It's a multiparm folder
                try:
                    # Get the multiparm parameter (usually has same name as the folder)
                    multiparm_name = template.name()
                    multiparm = node.parm(multiparm_name)
                    
                    if multiparm and not multiparm.isHidden():
                        # Add the multiparm control parameter itself
                        if folder_path not in parms_by_folder:
                            parms_by_folder[folder_path] = []
                        
                        parms_by_folder[folder_path].append((multiparm_name, template.label()))
                        
                        # Get the number of instances
                        num_instances = multiparm.eval()
                        
                        # Get all child templates from the multiparm
                        child_templates = template.parmTemplates()
                        
                        # For each instance, create a subfolder
                        for i in range(1, num_instances + 1):
                            instance_folder = f"{new_path} [{i}]"
                            if instance_folder not in folder_order:
                                folder_order.append(instance_folder)
                            
                            # For each child template, find the corresponding instance parameter
                            for child_template in child_templates:
                                # Skip buttons
                                if isinstance(child_template, hou.ButtonParmTemplate):
                                    continue
                                    
                                # Get the pattern name with # placeholder
                                pattern_name = child_template.name()
                                
                                # Replace # with the instance number
                                instance_name = pattern_name.replace("#", str(i))
                                
                                # Try to get the parameter
                                try:
                                    instance_parm = node.parm(instance_name)
                                    if instance_parm and not instance_parm.isHidden():
                                        # Get a nice label for the parameter
                                        instance_label = child_template.label() or instance_name
                                        
                                        # Add to the instance folder
                                        if instance_folder not in parms_by_folder:
                                            parms_by_folder[instance_folder] = []
                                        
                                        parms_by_folder[instance_folder].append((instance_name, instance_label))
                                except:
                                    # Parameter might not exist, skip it
                                    pass
                except:
                    # If we can't process the multiparm, continue with normal folder processing
                    for entry in template.parmTemplates():
                        traverse_template_group(entry, new_path)
            else:
                # Regular folder, process its contents
                for entry in template.parmTemplates():
                    traverse_template_group(entry, new_path)
        
        elif not isinstance(template, hou.ButtonParmTemplate) and not template.isHidden():
            # It's a regular parameter (not a button and not hidden)
            # Store it with its folder path
            folder_key = folder_path if folder_path else "ROOT"
            
            # Add to folder order if not already there
            if folder_key not in folder_order and folder_key != "ROOT":
                folder_order.append(folder_key)
            
            # Find the actual parameter instance
            try:
                parm_name = template.name()
                
                # Check if this is a parameter tuple (like color parameters)
                if isinstance(template, hou.ParmTemplate) and template.numComponents() > 1:
                    # It's a parameter tuple, add the tuple name itself
                    parmtuple = node.parmTuple(parm_name)
                    
                    if parmtuple and not parmtuple.isHidden():
                        name = parmtuple.name()
                        label = template.label() or name
                        
                        if folder_key not in parms_by_folder:
                            parms_by_folder[folder_key] = []
                        
                        parms_by_folder[folder_key].append((name, label))
                else:
                    # Regular single parameter
                    parm = node.parm(parm_name)
                    
                    if parm and not parm.isHidden():
                        name = parm.name()
                        label = parm.description() or template.label() or name
                        
                        if folder_key not in parms_by_folder:
                            parms_by_folder[folder_key] = []
                        
                        parms_by_folder[folder_key].append((name, label))
            except:
                # Skip parameters that don't exist on the node
                pass
    
    # Start traversing from the root template group
    traverse_template_group(node.parmTemplateGroup())
    
    return parms_by_folder, folder_order

def create_hierarchical_menu(node):
    # Get parameters organized by folder and folder order
    parms_by_folder, folder_order = get_folder_hierarchy(node)
    
    # Build the final menu
    menu = []
    
    # First add root parameters
    if "ROOT" in parms_by_folder:
        for name, label in parms_by_folder["ROOT"]:
            menu.append(name)
            menu.append(label)
    
    # Process all folders in order
    for folder_path in folder_order:
        # Get the folder name (last part after >)
        if ">" in folder_path:
            folder_parts = folder_path.split(">")
            folder_name = folder_parts[-1]
            # Calculate depth based on number of parts
            depth = len(folder_parts) - 1
        else:
            folder_name = folder_path
            depth = 0
            
        # Calculate indentation based on folder depth
        indent = "    " * depth  # Four spaces per level
        
        # Add folder entry
        if folder_name != " ":
            menu.append(f"__FOLDER__{folder_path}")
            menu.append(f"{indent}> {folder_name}")
        
        # Add parameters for this folder with indentation
        if folder_path in parms_by_folder:
            # Parameters get one more level of indentation
            param_indent = "    " * (depth + 1)
            
            for name, label in parms_by_folder[folder_path]:
                menu.append(name)
                menu.append(f"{param_indent}{label} ({name})")
    
    return menu