#include "interfaces/python/binding_utils.h"

#include <string>

#include <spdlog/spdlog.h>

NB_MODULE(ef_py, m) {
    m.def("set_log_level", [](const std::string& level) {
        if (level == "trace") spdlog::set_level(spdlog::level::trace);
        else if (level == "debug") spdlog::set_level(spdlog::level::debug);
        else if (level == "info") spdlog::set_level(spdlog::level::info);
        else if (level == "warn") spdlog::set_level(spdlog::level::warn);
        else if (level == "error") spdlog::set_level(spdlog::level::err);
        else if (level == "critical") spdlog::set_level(spdlog::level::critical);
        else if (level == "off") spdlog::set_level(spdlog::level::off);
    }, "Set global log level (trace/debug/info/warn/error/critical/off)", nb::arg("level"));

    bind_command(m);
    bind_core(m);
    bind_episode(m);
    bind_runtime(m);
    bind_gpu(m);
}
