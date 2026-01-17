#pragma once

#include <string>
#include <unordered_map>

#include "content/unit_definition.h"

#include <vector>

bool load_unit_definitions_json(const std::string& path,
                                std::vector<UnitDefinition>& out_definitions,
                                std::string* error);
