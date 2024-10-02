import hou  # type: ignore
from pathlib import Path
import re
from CDFX.uber_material_builder.tex_manager_config import (
    tex_type_patterns,
    extension_order,
    resolution_order,
    preferred_keywords,
    excluded_keywords,
)


class TextureFile:
    def __init__(self, file_path, file_name,tex_type, resolution, file_ext):
        self.file_path = file_path
        self.file_name = file_name
        self.tex_type = tex_type
        self.resolution = resolution
        self.file_ext = file_ext

    def __str__(self):
        return f"  File: {self.file_path}, Type: {self.tex_type}, Resolution: {self.resolution}, Extension: {self.file_ext}"


class TexManager:
    def __init__(self, node):
        self.node = node
        self.print_diagnostics = self.node.parm("print_diagnostics").eval() == 1
        self.source_file = self.node.parm("tex_mngr_source")
        self.source_file_string = self.source_file.evalAsString().replace("\\", "/")
        self.source_file_unexpanded_string = self.source_file.unexpandedString().replace("\\", "/")
        self.source_file_unexpanded_directory = self.source_file_unexpanded_string.rsplit("/", 1)[0]
        try:
            self.source_file_expression = self.source_file.expression()
        except hou.OperationFailed:
            self.source_file_expression = None
        self.enabled_tex_types = self.node.parm("tex_mngr_enabled").evalAsString().split()
        self.tex_mngr_remove = self.node.parm("tex_mngr_remove").eval() == 1
        self.path = Path(self.source_file_string)
        self.directory = self.path.parent
        self.base_name = self.path.stem
        self.file_ext = self.path.suffix
        self.preferred_resolution = None
        # Regex patterns for texture types
        self.tex_type_patterns = tex_type_patterns
        self.resolution_pattern = r"(?<![a-zA-Z0-9])(\d{1,2}k)(?![a-zA-Z0-9])"
        self.udim_pattern = r"(?<!\d)(\d{4})(?!\d)"

    def log(self, message):
        if self.print_diagnostics:
            print(message)

    def find_related_textures(self):

        find_preferred_resolution = re.search(
            self.resolution_pattern, self.base_name, re.IGNORECASE
        )
        self.preferred_resolution = (
            find_preferred_resolution.group(1) if find_preferred_resolution else None
        )
        all_tex_types = "|".join(pattern for pattern in self.tex_type_patterns.values())
        tex_type_patterns_compiled = re.compile(rf"({all_tex_types})", re.IGNORECASE)
        resolution_pattern_compiled = re.compile(rf"({self.resolution_pattern})", re.IGNORECASE)

        # Filter out parts that match texture type patterns or resolution, and omit parts after them
        filtered_parts = []
        pattern_parts = re.split(r"[\W_]+", self.base_name)
        for part in pattern_parts:
            if tex_type_patterns_compiled.search(part) or resolution_pattern_compiled.search(part):
                break
            filtered_parts.append(part)

        # Create the dynamic pattern from filtered parts
        if filtered_parts:
            dynamic_pattern = r"".join([rf"({re.escape(part)})[\W_]*" for part in filtered_parts])
        else:
            dynamic_pattern = r""

        # Remove \b for file matching
        tex_type_group = r"|".join(
            f"(?P<{tex_type}>{pattern[2:-2]})"
            for tex_type, pattern in self.tex_type_patterns.items()
        )

        # Regex for texture type, resolution, and udim
        dynamic_pattern += (
            rf"(?:[\W_]*(?:{tex_type_group}|{self.resolution_pattern}|{self.udim_pattern}))*"
        )

        pattern = re.compile(dynamic_pattern, re.IGNORECASE)

        self.log(f"Filtered Words: {filtered_parts}")
        self.log(f"Dynamic Regex: {dynamic_pattern}")
        self.log(f"Preferred Resolution: {self.preferred_resolution}")

        related_files = {}
        processed_files = set()

        self.log(f"-" * 20)
        self.log(f"Related Textures:")

        def process_texture(file_name, is_file=True):
            match = pattern.search(file_name)
            if match or not filtered_parts:
                file_path = f"{self.source_file_unexpanded_directory}/{file_name}"

                tex_type = next(
                    (tex_type for tex_type in self.tex_type_patterns.keys() if match.group(tex_type)),
                    None
                )
                if tex_type is None:
                    return

                # Excluded keyword sorting
                for keyword in excluded_keywords.get(tex_type, []):
                    if keyword.lower() in file_name.lower():
                        self.log(f"  Excluding: {file_path} because it contains the excluded word '{keyword}'")
                        return
                    
                resolution_match = resolution_pattern_compiled.search(file_name)
                resolution = resolution_match.group(1) if resolution_match else None
                
                if is_file:
                    file_ext = Path(file_name).suffix
                    # Double-check if the file exists
                    if not Path(hou.expandString(file_path)).exists():
                        self.log(f"  Double-checking... Warning! File does not exist: {file_path}")
                        return
                    self.log(f"  Double-checking... Success! File exists: {file_path}")
                    # Replace <UDIM> after checking existence
                    file_name = re.sub(self.udim_pattern, "<UDIM>", file_name)
                    file_path = f"{self.source_file_unexpanded_directory}/{file_name}"
                else:
                    file_ext = None
                    file_path = f"{file_path}" if not file_path.startswith("op:`op") else f"{file_path}')`"
                    
                # Check if this file_path has already been processed
                if file_path in processed_files:
                    return

                processed_files.add(file_path)

                texture_file = TextureFile(file_path, file_name, tex_type, resolution, file_ext)
                if tex_type not in related_files:
                    related_files[tex_type] = []
                related_files[tex_type].append(texture_file)

        if not self.source_file_string.startswith("op:"):
            for file in self.directory.iterdir():
                if file.is_file():
                    process_texture(file.name)
        else:
            node = hou.node(self.source_file_string[3:])
            if node:
                self.source_file_unexpanded_directory = self.source_file_unexpanded_directory.replace("\"", "'")
                for child in node.parent().children():
                    process_texture(child.name(), is_file=False)
            else:
                print(f"Warning! Node not found: {self.source_file_string}")

        self.related_textures = related_files

        for _, texture_files in self.related_textures.items():
            for texture_file in texture_files:
                self.log(texture_file)
        self.log(f"-" * 20)

    def get_sort_key(self, texture, tex_type):
        # Resolution sorting (lower score is better)
        if texture.resolution:
            if (
                self.preferred_resolution
                and texture.resolution.lower() == self.preferred_resolution.lower()
            ):
                resolution_score = -1  # Prioritize exact match with preferred resolution
            else:
                resolution_score = resolution_order.index(texture.resolution.lower())
        elif texture.resolution == self.preferred_resolution:
            resolution_score = -1  # Prioritize exact match with preferred resolution when None
        else:
            resolution_score = len(resolution_order)  # Lowest priority if no resolution

        if texture.file_ext:
            # File extension sorting (lower index is better)
            ext = texture.file_ext.lstrip(".").lower()
            if ext in extension_order[tex_type]:
                extension_score = extension_order[tex_type].index(ext)
            else:
                extension_score = len(extension_order[tex_type])
        else:
            extension_score = len(extension_order[tex_type])

        # Preferred keyword sorting (True is better than False)
        has_preferred_keyword = any(
            keyword in texture.file_path.lower() for keyword in preferred_keywords.get(tex_type, [])
        )
        self.log(
            f"  File Path: {texture.file_path}, Preferred Keyword: {has_preferred_keyword}, Resolution Score: {resolution_score}, Extension Score: {extension_score}"
        )
        # Sorting order select_best_texture
        return (has_preferred_keyword, -resolution_score, -extension_score)

    def select_best_texture(self, tex_type):
        if tex_type not in self.related_textures:
            return None

        textures = self.related_textures[tex_type]

        # Sort textures by resolution, file extension preference, and preferred keywords
        textures.sort(key=lambda x: self.get_sort_key(x, tex_type), reverse=True)

        # Return the first (best) texture after sorting
        self.log(f"    Texture priority list for {tex_type}:")
        for i, texture in enumerate(textures):
            self.log(f"        {i+1}: {texture.file_path}")
        return textures[0] if textures else None

    def remove_texture(self, tex_type):
        filename_parm = self.node.parm(f"{tex_type}_filename")
        method_parm = self.node.parm(f"{tex_type}_METH")
        if filename_parm.evalAsString() != "":
            print(f"Removing {tex_type} texture")
            filename_parm.set("")
        if method_parm.evalAsString() == "_TEX":
            method = "_CONST" if tex_type not in ["bump", "coatbump", "displacement"] else "_NONE"
            print(f"Setting {tex_type} method to {method}")
            method_parm.set(method)
            method_parm.pressButton()

    def assign_textures(self):
        for tex_type in self.enabled_tex_types:
            filename_parm = self.node.parm(f"{tex_type}_filename")
            method_parm = self.node.parm(f"{tex_type}_METH")
            if tex_type in self.related_textures and filename_parm:
                best_texture = self.select_best_texture(tex_type)
                if best_texture:
                    resolved_texture = best_texture.file_path
                    print(f"Setting {tex_type} to {resolved_texture}")
                    filename_parm.set(resolved_texture)
                    method_parm.set("_TEX")
                    method_parm.pressButton()
                    if tex_type in ["bump", "coatbump"]:
                        self.log(f"Checking {tex_type} input type for {best_texture.file_name}")
                        if re.search(r"[\W_]bump[\W_]", best_texture.file_name, re.IGNORECASE):
                            self.log(f"Setting {tex_type} input type to height")
                            self.node.parm(f"{tex_type}_inputType").set("0")
                        else:
                            self.log(f"Setting {tex_type} input type to tangent-space normal")
                            self.node.parm(f"{tex_type}_inputType").set("1")

            elif self.tex_mngr_remove:
                self.remove_texture(tex_type)

    def resolve_tex(self):
        if self.source_file_string == "":
            print(f"No texture specified. Removing all textures on enabled properties.")
            for tex_type in self.enabled_tex_types:
                self.remove_texture(tex_type)
            return
        self.log(f"#" * 30)
        self.log(f"\nResolving textures for {self.source_file_string}")
        self.find_related_textures()
        if self.related_textures:
            self.assign_textures()
        else:
            print(f"No matching textures found for {self.source_file_string}")
        self.log(f"#" * 30)


def initiate_tex_manager(**kwargs):
    tex_manager = TexManager(kwargs["node"])
    tex_manager.resolve_tex()
