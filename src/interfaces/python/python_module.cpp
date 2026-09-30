#include "interfaces/python/binding_utils.h"

#include <string>

#include <spdlog/spdlog.h>

#ifdef EF_PYTHON_DIAGNOSTICS_MODULE
#define EF_PYTHON_MODULE_NAME ef_py_diagnostics
#else
#define EF_PYTHON_MODULE_NAME ef_py
#endif

NB_MODULE(EF_PYTHON_MODULE_NAME, m) {
    m.def(
        "set_log_level",
        [](const std::string &level) {
            if (level == "trace")
                spdlog::set_level(spdlog::level::trace);
            else if (level == "debug")
                spdlog::set_level(spdlog::level::debug);
            else if (level == "info")
                spdlog::set_level(spdlog::level::info);
            else if (level == "warn")
                spdlog::set_level(spdlog::level::warn);
            else if (level == "error")
                spdlog::set_level(spdlog::level::err);
            else if (level == "critical")
                spdlog::set_level(spdlog::level::critical);
            else if (level == "off")
                spdlog::set_level(spdlog::level::off);
        },
        "Set global log level (trace/debug/info/warn/error/critical/off)", nb::arg("level"));

#ifdef EF_PRODUCTION_FACADE_ONLY
    bind_command(m);
    bind_core_enums(m);
    bind_core_instruments(m);
    bind_core_unit_data(m);
    bind_core_observation(m);
    bind_episode(m);
    bind_gpu_facade_only(m);
    bind_runtime_facade_only(m);
#else
    bind_command(m);
    bind_core(m);
    bind_episode(m);
    bind_runtime(m);
    bind_gpu(m);
#endif
}
