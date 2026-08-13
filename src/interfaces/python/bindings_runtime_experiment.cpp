#include "interfaces/python/bindings_runtime_detail.h"

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

#include "runtime/facade/runtime_facade.h"

void bind_runtime_experiment(nb::module_ &m) {
    nb::class_<RuntimeWorldLayoutRequest> runtime_world_layout_request_class(
        m, "RuntimeWorldLayoutRequest");
    runtime_world_layout_request_class.def(nb::init<>());
#define EF_RUNTIME_WORLD_LAYOUT_REQUEST_FIELD(type, name, default_value)                           \
    runtime_world_layout_request_class.def_rw(#name, &RuntimeWorldLayoutRequest::name);
#include "runtime/facade/detail/runtime/runtime_world_layout_request.inc"

    nb::class_<RuntimeWorldLayoutResult> runtime_world_layout_result_class(
        m, "RuntimeWorldLayoutResult");
    runtime_world_layout_result_class.def(nb::init<>());
#define EF_RUNTIME_WORLD_LAYOUT_RESULT_FIELD(type, name, default_value)                            \
    runtime_world_layout_result_class.def_rw(#name, &RuntimeWorldLayoutResult::name);
#include "runtime/facade/detail/runtime/runtime_world_layout_result.inc"
}
