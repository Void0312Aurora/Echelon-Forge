# Keep Flecs' JSON state-transfer numbers round-trippable for native restore.
# The pinned amalgamation defaults to ten decimal places, which changes real
# simulation doubles when the owner adapter decodes the snapshot with exact
# double precision. Its JSON tokenizer also splits signed exponents and does
# not bound numeric tokens. Patch only the formatter and JSON number reader.

if (NOT DEFINED FLECS_SOURCE_FILE)
    message(FATAL_ERROR "FLECS_SOURCE_FILE must be defined")
endif()
if (NOT EXISTS "${FLECS_SOURCE_FILE}")
    message(FATAL_ERROR "Flecs source not found: ${FLECS_SOURCE_FILE}")
endif()

file(READ "${FLECS_SOURCE_FILE}" _flecs_source)

function(_flecs_replace_once _original _replacement _label)
    string(FIND "${_flecs_source}" "${_replacement}" _applied)
    string(REPLACE "${_original}" "" _without_original "${_flecs_source}")
    string(LENGTH "${_flecs_source}" _source_length)
    string(LENGTH "${_without_original}" _without_length)
    string(LENGTH "${_original}" _original_length)
    math(EXPR _removed_length "${_source_length} - ${_without_length}")
    if (_removed_length EQUAL 0 AND NOT _applied EQUAL -1)
        return()
    endif()
    if (NOT _removed_length EQUAL _original_length OR NOT _applied EQUAL -1)
        message(FATAL_ERROR
            "Flecs exact JSON precision patch requires exactly one pinned ${_label}; "
            "inspect the upstream source before changing the patch.")
    endif()
    string(REPLACE "${_original}" "${_replacement}" _updated "${_flecs_source}")
    set(_flecs_source "${_updated}" PARENT_SCOPE)
endfunction()

set(_flecs_original_float_call "flecs_strbuf_ftoa(b, flt, 10, nan_delim);")
set(_flecs_previous_float_call [=[if (nan_delim && (ecs_os_isnan(flt) || ecs_os_isinf(flt))) {
        ecs_strbuf_appendch(b, nan_delim);
        ecs_strbuf_append(b, "%s", ecs_os_isnan(flt) ? "NaN" : (flt < 0 ? "-Inf" : "Inf"));
        ecs_strbuf_appendch(b, nan_delim);
    } else {
        ecs_strbuf_append(b, "%.*g", 17, flt);
    }]=])
string(REPLACE "ecs_strbuf_append(b, \"%.*g\", 17, flt);"
               "ecs_strbuf_append(b, flt == 0 ? \"%.1f\" : \"%.17g\", flt);"
               _flecs_exact_float_call "${_flecs_previous_float_call}")
# Upgrade the known earlier formatter patch in an existing generated source.
string(REPLACE "${_flecs_previous_float_call}" "${_flecs_exact_float_call}"
       _flecs_source "${_flecs_source}")
_flecs_replace_once("${_flecs_original_float_call}" "${_flecs_exact_float_call}" "formatter call")

set(_flecs_number_reader [=[const char *result = json;
        if (*result == '-') {
            result ++;
        }
        if (*result == '0') {
            result ++;
        } else if (*result >= '1' && *result <= '9') {
            do { result ++; } while (isdigit((unsigned char)*result));
        } else {
            token_kind[0] = JsonInvalid;
            return NULL;
        }
        if (*result == '.') {
            result ++;
            if (!isdigit((unsigned char)*result)) {
                token_kind[0] = JsonInvalid;
                return NULL;
            }
            do { result ++; } while (isdigit((unsigned char)*result));
        }
        if (*result == 'e' || *result == 'E') {
            result ++;
            if (*result == '+' || *result == '-') {
                result ++;
            }
            if (!isdigit((unsigned char)*result)) {
                token_kind[0] = JsonInvalid;
                return NULL;
            }
            do { result ++; } while (isdigit((unsigned char)*result));
        }
        if ((result - json >= ECS_MAX_TOKEN_SIZE) ||
            (*result && !isspace((unsigned char)*result) &&
             *result != ',' && *result != '}' && *result != ']')) {
            token_kind[0] = JsonInvalid;
            return NULL;
        }
        ecs_size_t number_length = (ecs_size_t)(result - json);
        ecs_os_memcpy(token, json, number_length);
        token[number_length] = '\0';]=])
_flecs_replace_once("const char *result = flecs_parse_digit(json, token);"
                    "${_flecs_number_reader}" "JSON number reader")
_flecs_replace_once("if (!strchr(token, '.')) {"
                    "if (!strchr(token, '.') && !strchr(token, 'e') && !strchr(token, 'E')) {"
                    "JSON large integer check")

file(WRITE "${FLECS_SOURCE_FILE}" "${_flecs_source}")
message(STATUS "Flecs exact JSON precision patch: applied")
