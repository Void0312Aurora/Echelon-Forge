#pragma once

#include <string>
#include <unordered_map>

#include "content/unit_definition.h"

bool load_unit_definitions_json(const std::string& path,
                                std::unordered_map<UnitType, UnitDefinition, UnitTypeHash>& out_definitions,
                                std::string* error);
