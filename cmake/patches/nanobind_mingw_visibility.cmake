# Backport of nanobind upstream commit bcd936089989f11a0f76f28face7d8ca780ef137
# ("Fix visibility for GCC on Windows (mingw64)", first released in v2.0.0)
# onto the pinned v1.9.2.
#
# On Windows NB_EXPORT expands to __declspec(dllexport), which implies default
# visibility.  v1.9.2 unconditionally attaches
# __attribute__((visibility("hidden"))) to the nanobind namespace whenever
# __GNUC__ is defined -- including under MinGW GCC -- and GCC rejects the
# contradiction:
#
#   error: 'dllexport' implies default visibility, but 'class
#   nanobind::python_error' has already been declared with a different
#   visibility
#
# Upstream restricts the attribute to non-Windows GCC targets.  Of bcd9360's
# three nb_defs.h hunks, only the NB_NAMESPACE guard is backported here: the
# NB_EXPORT hunk is a revert of PR #440, and the pinned v1.9.2 predates #440
# so it already carries that post-image; the NB_EXPORT_SHARED hunk's pre-image
# IS still present in v1.9.2 but is deliberately not backported -- it only
# attaches hidden visibility to non-exported statics in static-lib builds and
# cannot produce the dllexport/visibility contradiction this patch fixes.  A
# future v2.0.0 migration audit must therefore not treat "bcd9360 included
# upstream" as proof this file and upstream are otherwise identical.
#
# This runs as a FetchContent PATCH_COMMAND, so it must be idempotent: patched
# sources survive in the build tree across reconfigures.

if (NOT DEFINED NANOBIND_DEFS_HEADER)
    message(FATAL_ERROR "NANOBIND_DEFS_HEADER must be defined")
endif()

if (NOT EXISTS "${NANOBIND_DEFS_HEADER}")
    message(FATAL_ERROR "nanobind header not found: ${NANOBIND_DEFS_HEADER}")
endif()

file(READ "${NANOBIND_DEFS_HEADER}" _nb_defs)

set(_nb_patched_guard "#if defined(__GNUC__) && !defined(_WIN32)\n#  define NB_NAMESPACE nanobind __attribute__((visibility(\"hidden\")))")

if (_nb_defs MATCHES "#if defined\\(__GNUC__\\) && !defined\\(_WIN32\\)\n#  define NB_NAMESPACE")
    message(STATUS "nanobind MinGW visibility patch: already applied")
    return()
endif()

set(_nb_original_guard "#if defined(__GNUC__)\n#  define NB_NAMESPACE nanobind __attribute__((visibility(\"hidden\")))")

string(FIND "${_nb_defs}" "${_nb_original_guard}" _nb_match)
if (_nb_match EQUAL -1)
    message(FATAL_ERROR
        "nanobind MinGW visibility patch does not apply to "
        "${NANOBIND_DEFS_HEADER}. The pinned nanobind version likely changed; "
        "re-check whether upstream commit bcd9360 is already included and drop "
        "this patch if so.")
endif()

string(REPLACE "${_nb_original_guard}" "${_nb_patched_guard}" _nb_defs "${_nb_defs}")
file(WRITE "${NANOBIND_DEFS_HEADER}" "${_nb_defs}")
message(STATUS "nanobind MinGW visibility patch: applied (upstream bcd9360)")
