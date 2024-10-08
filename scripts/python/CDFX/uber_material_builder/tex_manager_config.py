tex_type_patterns = {
    "albedo": r"\b(albedo|diff?(?:use)?|base\W?colou?r)\b",
    "ambientocclusion": r"\b(ambient\W?occlusion|ao)\b",
    "metalness": r"\b(metal(?:l?ic|l?ness))\b",
    "roughness": r"\b(rough(?:ness)?)\b",
    "reflection": r"\b(refl(?:ection)?|spec(?:ular)?|specularedgecolor)\b",
    "transmission": r"\b(transm(?:ission|issive|ittance)?|refr(?:action|active|act)?)\b",
    "mscolor": r"\b(ms\W?color|sss\W?(?:colou?r)?|scatteringcolor|subsurf(?:ace)?\W?(?:colou?r)?|transl(?:ucency|ucence|ucent)?)\b",
    "msradius": r"\b(ms\W?radius|sss\W?radius|scatteringdistancescale|subsurf(?:ace)?\W?radius)\b",
    "sheen": r"\b(sheen\W?(?:colou?r)?)\b",
    "coatroughness": r"\b(coat\W?(?:rough(?:ness)?))\b",
    "coatbump": r"\b(coat\W?bump|coat\W?normal)\b",
    "emcolor": r"\b(em\W?color|em(?:is|it)(?:sive|sion|tance)?\W?(?:colou?r)?)\b",
    "emintensity": r"\b(em\W?intensity|em(?:is|it)(?:sive|sion|tance)?\W?intensity)\b",
    "opacity": r"\b(opac(?:ity)?|mask)\b",
    "bump": r"\b(bump|nor\W?gl|nor\W?dx|norm?(?:al)?)\b",
    "displacement": r"\b(disp(?:lacement)?|height)\b",
    "preview": r"\b(prev(?:iew)?|thumb(?:nail)?|render)\b",
}
extension_order_reference = {
    "color": ["jpg", "jpeg", "png", "exr", "tif", "tiff", "tga"],
    "other_data": ["exr", "jpg", "jpeg", "png", "tif", "tiff", "tga"],
    "vector": ["exr", "tif", "tiff", "jpg", "jpeg", "png", "tga"],
}
extension_order = {
    "albedo": extension_order_reference["color"],
    "metalness": extension_order_reference["other_data"],
    "roughness": extension_order_reference["other_data"],
    "reflection": extension_order_reference["color"],
    "transmission": extension_order_reference["color"],
    "mscolor": extension_order_reference["color"],
    "msradius": extension_order_reference["vector"],
    "sheen": extension_order_reference["color"],
    "coatroughness": extension_order_reference["other_data"],
    "coatbump": extension_order_reference["vector"],
    "emcolor": extension_order_reference["color"],
    "emintensity": extension_order_reference["other_data"],
    "opacity": extension_order_reference["other_data"],
    "bump": extension_order_reference["vector"],
    "displacement": extension_order_reference["vector"],
}
resolution_order = ["4k", "2k", "6k", "8k", "12k", "16k"]
preferred_keywords = {
    "albedo": ["albedo"],
    "metalness": [],
    "roughness": [],
    "reflection": [],
    "transmission": [],
    "mscolor": [],
    "msradius": [],
    "sheen": [],
    "coatroughness": [],
    "coatbump": [],
    "emcolor": [],
    "emintensity": [],
    "opacity": [],
    "bump": ["normal", "norm", "nor_gl", "norgl"],
    "displacement": ["16bit"],
}
excluded_keywords = {
    "albedo": [],
    "metalness": [],
    "roughness": [],
    "reflection": [],
    "transmission": [],
    "mscolor": [],
    "msradius": [],
    "sheen": [],
    "coatroughness": [],
    "coatbump": [],
    "emcolor": [],
    "emintensity": [],
    "opacity": [],
    "bump": [],
    "displacement": [],
}
