# CDFXHouTools
A growing collection of python scripts, shelf tools, and HDAs designed to streamline and enhance workflows for Houdini artists.

HDAs are in the Houdini Indie (.hdalc) format.

Have you found this useful? *Feel free to [buy me a coffee](https://buymeacoffee.com/chrisdenny)!*
___
## Installation
This repo is structured as a Houdini package.
Place this repo and the CDFXHouTools.json in your Houdini packages folder like so:
```
-- $HOME/houdiniXX.X
   -- packages
      -- CDFXHouTools (this repo)
      -- CDFXHouTools.json
```

The packages folder location is dependent on your OS. See SideFX documentation [here](https://www.sidefx.com/docs/houdini/ref/plugins.html#using_packages) for more information.

#### Compatibility
These tools have been created with cross-platform capability in mind, if you experience any issues please let me know.
Tested with Houdini 20.0 and 20.5.
___

## CDFX Uber Material Builder
The Uber Material Builder streamlines the material creation process, allowing artists to quickly prototype and iterate on complex shader designs while maintaining flexibility and control over the final result.
### Features:
- **Dynamic node connections, avoiding calls to unused nodes at render time**\
   The shader network is initially created with various texturing and mapping options, but only the selection is wired via scripting. Once shader look-dev is finished, unconnected nodes can be destroyed to reduce clutter and minimize the project's file size.
- **Unified UI**\
   Everything needed to control the look of the shader is top-level, making changes faster and exposes properties for better readability.
- **Automated Texture Manager**\
   By selecting a single reference file, all matching files are found and applied to their appropriate PBR property. Expressions and env variables are retained in the directory path. The "op:\`opfullpath('/img/copnet/texture')\`" method is supported. A `<UDIM>` token is added if 4 digits are found at the end of the filename. Image sequences are not supported. Preferences for file types and resolution (if a resolution is not found in the reference file), and preferred keywords can be customized via the `tex_manager_config.py` file.
- **Solo Shader Output**\
   Specify singular properties to output to the shader, allowing for easy debugging. Think your roughness isn't quite right? Just solo it like those C4D folks!
- **Easy Imperfection and Detail Creation**\
   Add and stack imperfection and detail maps to improve the materials realism, with individual controls for each material property. Controls are top-level so iteration is fast.
- **UV Mapping, Triplanar, Hex-Tiling, Hex-Tiled Triplanar**\
   Use a variety of mapping techniques, each with transform controls.
- **Transform Jitter**\
   When using a triplanar mapping method, add randomization to scale, offset, or rotation based on a point or vertex attribute.
- **Simultaneous Redshift and Karma Creation**\
   Redshift and Karma networks are modified simulatenously and are wired into a Collect node, allowing you to switch between rendering with Redshift or Karma on the fly; there's no need to change the material assignment. While it's not a perfect 1:1 match between the two, it's close enough to experiment with and reduces conversion time if you change render engines.
- **Support for both ROP and Solaris context for Redshift**
- **(Mostly) Compatible with Redshift RT**\
   Because the shader network only wires nodes that are needed, most materials work fine in RT mode.
- **OpenGL and USD Previews**\
   OpenGL tags are linked to the materials attributes, and a USD preview surface shader is simultaneously built to enable more accurate viewport previews in both OBJ and Solaris contexts. Vulkan experimentation will occur in the future.
- **Built-in Linear and sRGB Color Space Converter**
- **Future Expandability**\
   The core logic and configuration was built to be easy to expand and change. Adding additional render engines or texturing methods is straight-forward.
- **Recreate Self**\
   Delete unconnected nodes by mistake? Want to version up the HDA? The "Recreate Self" feature will transfer over all of your changes to a new node so you can continue with all of the original options restored. Any custom child nodes with "keep" in the name are copied over and are connected.

### Notes:
- Render engine specific versions are included, use the Karma variant if you don't have Redshift.
- I recommended you set "REDSHIFT_DISABLE_AUTOTEXTURESCOLORSPACE" to "1" via either houdini.env or packages to prevent Redshift from changing the color space on rs texture nodes.
- For Redshift, the OSL implementation of triplanar and hex-tiled triplanar adds 20-30s of compile time at the start of each new 'session'. Because of this, by default the uber material uses the default Redshift triplanar node. When set to hex-tiled triplanar, using OSL is forced.
___

## HDAs
Accessible via the "CDFX" tab menu.

### Boolean Advanced
Context: *SOP*\
A multi-threaded implementation of the boolean sop which includes numerous quality-of-life additions. Cutter position randomization, group and attribute transfer, and UV creation are to name a few. When an object fails to resolve the cut-faces, which is often occurs with CAD-based objects, it automatically switches to a more robust, but slower, VDB-based implementation.

### Checkpoint
Context: *SOP*\
Creates a simple file cache of the input geometry. A file path based on the node and parent nodes name is built, and adds frame numbering if necessary. For compute-heavy tasks, a topnet is built-in which divides the number of frames equally into the number of desired concurrent tasks. For more complex file-caches with wedging and such, Labs File Cache is preferred.

### Detect Animation
Context: *SOP*\
Detects if any of the provided attributes change value within the frame range, and are added to a group if so. Samples/second are used to reduce calculation time. This tool is primarily used to split apart animated parts from static parts to efficiently create Redshift proxy files (or likewise) further down the pipeline. When live calculation is unchecked, the selection is 'baked' via simple group nodes to avoid any unnecessary recomputing. This tool may not work as expected on geometry with changing point or poly counts.

### Guided Transform
Context: *SOP*\
In addition to transforming the selected geometry, this node creates guidelines representing the vector at which the object is translated, scaled, rotated, or sheared. When an object isn't perfectly aligned with the world, the guidelines help to dial in the transform's "pivot translate" and "pivot rotate" values. "Blend" parameters add another layer of animation control.

### Isolation
Context: *SOP*\
Filters downstream geometry based on primitive or point attributes/groups, allowing selective hiding, transparency, or colorization of filtered primitives. This streamlines the process of working with complex objects by temporarily obsuring elements that have already been configured or grouped by downstream nodes. 

### Material Assigner
Context: *SOP*\
Retains the same functionality of the base Houdini Material SOP node, but adds the ability to assign random materials from a list for surface randomization.

### Redshift Proxy Object
Context: *OBJ*\
Eases and enhances the method of creating Redshift proxy files for geometry. The file path is built based on the node name and adds frame numbering if necessary. "Enable Proxy File" and the internal routing of geo is controlled via a script and expressions, so "Render Proxy to Disk" works even when a proxy file is already being used. "Original Geometry" is added as an option for display mode. 

### Rest
Context: *SOP*\
In addition to the default Rest SOP controls, the ability to use vertex normals for rest normals is added.

### Unique Paths
Context: *SOP*\
Creates unique `path` and `name` attributes on primitives based on a connectivity attribute. This ensures no duplicate paths or names, which often occurs when working with CAD models. "Cusp" further splits geometry apart; I often use names like `splitPath` and `splitName` to differentiate these. This is handy for material assignment, as a single CAD part may have different surfaces and finishes. The process is multi-threaded so it remains as fast as possible, even on objects that have tens of thousands of pieces.

## MaterialX Nodes
In order to reduce the number of node descendents in Solaris, the following single-node MaterialX HDAs have been created. To view their original internal structure, use the "Nodes" variant found in the "Nodes" submenu.

### MtlX Transform Jitter
Context: *VOP*\
Generate randomized scale, offset, and rotation outputs based on `geomprop` values. Outputs can be used as inputs on the MtlX Triplanar and Transform Position nodes.

### MtlX Transform Position
Context: *VOP*\
Manipulate the scale, rotation, and translation of the incoming geometry, in that order, and output it's new position. 

### MtlX Triplanar
Context: *VOP*\
A custom triplanar implementation that enables proper xyz-axis specific rotations, edge and blend noise, and axis-mirroring fixes to match other common triplanar methods. Outputs include UVs and weights for use with the MtlX Triplanar Textures node.

### MtlX Triplanar Textures
Context: *VOP*\
A reduced version of the MtlX Triplanar node that supports hex-tiling. UVs and weights output from a MtlX Triplanar node must be used. Due to the complexity of the UVs and weights creation, it's better to use the MaterialX node Triplanar implmentation instead of re-creating it internally.

### MtlX UV Transform
Context: *VOP*\
Scale, rotate, and translate incoming UV data.

___

## Toolbar

### Recreate Nodes
Recreates selected nodes in the Houdini scene while keeping their connections and spare parameters. It retains child nodes with "keep" in their names. This method creates a new version of the top-level node instead of just duplicating it. This is useful when an HDA has been updated, allowing you to work with the latest version while preserving the original node's connections and settings.

### List Node Inputs and Outputs
Lists a selected nodes input and output connections names and indexes.

### Zip Backups
This tool is designed to efficiently manage and reduce the file space needed for backup files, but can be used for any file types that benefit from compression. By utilizing the `recursive_zip.py` script, a specified directory is recursively searched for folders that match a given name. Once identified, it creates a compressed `.zip` file of their contents, significantly reducing the overall file size—often by nearly a factor of 10 for `.hip/lc/nc` files.

#### How It Works
1. **Recursive Search**: The script traverses the specified directory and its subdirectories to locate folders that match the user's criteria.
2. **Backup Creation**: For each matching folder, the script generates a timestamped `.zip` file containing all the files within that folder, while ignoring system and hidden files. Folders within retain a relative path.
3. **Logging**: A log file in CSV format is created within each backup folder, documenting the files included in the backup, their sizes, and what zip file contains the file.
4. **User Interaction**: You can run the backup process in an unattended mode, allowing for automation without manual confirmation, or you can opt for a more interactive experience (recommended) where you confirm actions before proceeding.
5. **File Deletion Option**: After zipping, you have the option to delete the original files, further saving space. :warning: Due to how python deletes files, deletion is not un-doable. Files are not sent to trash.

___

## OCIO Config
The /ocio/config.ocio file is a modified version of the Houdini 20 Studio OCIO. Extensive regex file_rules define colorspaces for most PBR properties. 
___

## License and Notice:
This software is licensed under the GNU General Public License v3.0 (GPL-3.0). You can find the full text of the license in the LICENSE file in this repository.
This software is provided AS-IS, with absolutely no warranty or guarantee of any kind, express or implied. We disclaim any liability for damages resulting from using this software.
