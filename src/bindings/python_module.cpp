#include <nanobind/nanobind.h>
#include <spdlog/spdlog.h>

namespace nb = nanobind;

void init_engine() {
    spdlog::info("CMO Engine initialized from Python!");
}

NB_MODULE(cmo_py, m) {
    m.def("init", &init_engine, "Initialize the CMO engine");
}
