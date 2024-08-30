redshift_index_dict = {
    # Albedo
    ("albedo",          "constant", "detail"):      {"target_index": 1},
    ("albedo",          "attribute", "detail"):     {"target_index": 1},
    ("albedo",          "tex", "detail"):           {"target_index": 1},
    ("albedo",          "hex", "detail"):           {"target_index": 1},
    ("albedo",          "triplanar", "detail"):     {"target_index": 1},
    ("albedo",          "hextri", "detail"):        {"target_index": 1},
    ("albedo",          "detail_cc", "detail"):     {"target_index": 3},
    ("albedo",          "detailout", "detail"):     {"target_index": 3},
    # Metalness
    ("metalness",       "detail_cc", "detail"):     {"target_index": 1},
    ("metalness",       "detailout", "detail"):     {"target_index": 1},
    # Reflection
    ("reflection",      "constant", "detail"):      {"target_index": 1},
    ("reflection",      "attribute", "detail"):     {"target_index": 1},
    ("reflection",      "tex", "detail"):           {"target_index": 1},
    ("reflection",      "hex", "detail"):           {"target_index": 1},
    ("reflection",      "triplanar", "detail"):     {"target_index": 1},
    ("reflection",      "hextri", "detail"):        {"target_index": 1},
    ("reflection",      "detail_cc", "detail"):     {"target_index": 3},
    ("reflection",      "detailout", "detail"):     {"target_index": 3},
    # Roughness
    ("roughness",       "detail_cc", "detail"):     {"target_index": 1},
    ("roughness",       "detailout", "detail"):     {"target_index": 1},
    # Transmission
    ("transmission",    "constant", "detail"):      {"target_index": 1},
    ("transmission",    "attribute", "detail"):     {"target_index": 1},
    ("transmission",    "tex", "detail"):           {"target_index": 1},
    ("transmission",    "hex", "detail"):           {"target_index": 1},
    ("transmission",    "triplanar", "detail"):     {"target_index": 1},
    ("transmission",    "hextri", "detail"):        {"target_index": 1},
    ("transmission",    "detail_cc", "detail"):     {"target_index": 3},
    ("transmission",    "detailout", "detail"):     {"target_index": 3},
    # Subsurface color
    ("mscolor",         "constant", "detail"):      {"target_index": 1},
    ("mscolor",         "attribute", "detail"):     {"target_index": 1},
    ("mscolor",         "tex", "detail"):           {"target_index": 1},
    ("mscolor",         "hex", "detail"):           {"target_index": 1},
    ("mscolor",         "triplanar", "detail"):     {"target_index": 1},
    ("mscolor",         "hextri", "detail"):        {"target_index": 1},
    ("mscolor",         "detail_cc", "detail"):     {"target_index": 3},
    ("mscolor",         "detail_cc", "detail"):     {"target_index": 3},
    ("mscolor",         "detailout", "detail"):     {"target_index": 3},
    # Subsurface radius
    ("msradius",        "constant", "detail"):      {"target_index": 1},
    ("msradius",        "attribute", "detail"):     {"target_index": 1},
    ("msradius",        "tex", "detail"):           {"target_index": 1},
    ("msradius",        "hex", "detail"):           {"target_index": 1},
    ("msradius",        "triplanar", "detail"):     {"target_index": 1},
    ("msradius",        "hextri", "detail"):        {"target_index": 1},
    ("msradius",        "detail_cc", "detail"):     {"target_index": 3},
    ("msradius",        "detailout", "detail"):     {"target_index": 3},
    # Sheen 
    ("sheen",           "constant", "detail"):      {"target_index": 1},
    ("sheen",           "attribute", "detail"):     {"target_index": 1},
    ("sheen",           "tex", "detail"):           {"target_index": 1},
    ("sheen",           "hex", "detail"):           {"target_index": 1},
    ("sheen",           "triplanar", "detail"):     {"target_index": 1},
    ("sheen",           "hextri", "detail"):        {"target_index": 1},
    ("sheen",           "detail_cc", "detail"):     {"target_index": 3},
    ("sheen",           "detailout", "detail"):     {"target_index": 3},
    # Coat roughness
    ("coatroughness",   "detail_cc", "detail"):     {"target_index": 1},
    ("coatroughness",   "detailout", "detail"):     {"target_index": 1},
    # Coat bump
    ("coatbump",        "source", "shader"):        {"target_index": 31},
    ("coatbump",        "detail", "output"):        {"target_index": 1},
    ("coatbump",        "detail", "shader"):        {"target_index": 31},
    ("coatbump",        "output", "shader"):        {"target_index": 31},
    ("coatbump",        None, "shader"):            {"target_index": 31},
    # Emission color
    ("emcolor",         "constant", "detail"):      {"target_index": 1},
    ("emcolor",         "attribute", "detail"):     {"target_index": 1},
    ("emcolor",         "tex", "detail"):           {"target_index": 1},
    ("emcolor",         "hex", "detail"):           {"target_index": 1},
    ("emcolor",         "triplanar", "detail"):     {"target_index": 1},
    ("emcolor",         "hextri", "detail"):        {"target_index": 1},
    ("emcolor",         "detail_cc", "detail"):     {"target_index": 3},
    ("emcolor",         "detailout", "detail"):     {"target_index": 3},
    # Emission intensity
    ("emintensity",     "detail_cc", "detail"):     {"target_index": 1},
    ("emintensity",     "detailout", "detail"):     {"target_index": 1},
    # Opacity
    ("opacity",         "constant", "detail"):      {"target_index": 1},
    ("opacity",         "attribute", "detail"):     {"target_index": 1},
    ("opacity",         "tex", "detail"):           {"source_index": 3, "target_index": 1},
    ("opacity",         "tex", "output"):           {"source_index": 3},
    ("opacity",         "hex", "detail"):           {"source_index": 3, "target_index": 1},
    ("opacity",         "hex", "output"):           {"source_index": 3},
    ("opacity",         "triplanar", "detail"):     {"target_index": 1},
    ("opacity",         "hextri", "detail"):        {"source_index": 3, "target_index": 1},
    ("opacity",         "hextri", "output"):        {"source_index": 3},
    ("opacity",         "detailout", "detail"):     {"target_index": 3},
    ("opacity",         "detail_cc", "detail"):     {"target_index": 3},
    # Bump
    ("bump",            "source", "shader"):        {"target_index": 34},
    ("bump",            "detail", "output"):        {"target_index": 3},
    ("bump",            "detail", "shader"):        {"target_index": 34},
    ("bump",            "roundcorner", "output"):   {"target_index": 1},
    ("bump",            "roundcorner", "shader"):   {"target_index": 34},
    ("bump",            "output", "shader"):        {"target_index": 34},
    ("bump",            None, "shader"):            {"target_index": 34},
    # Displacement
    ("displacement",    "output", "material"):      {"target_index": 1},
    ("displacement",    None, "material"):          {"target_index": 1},
    # Detail out
    ("detail_a",        "output", "detailout"):     {"target_index": 1},
    ("detail_a",        None, "detailout"):         {"target_index": 1},
    ("detail_b",        "output", "detailout"):     {"target_index": 3},
    ("detail_b",        None, "detailout"):         {"target_index": 3},
    ("detail_c",        "output", "detailout"):     {"target_index": 5},
    ("detail_c",        None, "detailout"):         {"target_index": 5},
}