#pragma once

#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>
#include <nanobind/stl/array.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/tuple.h>
#include <nanobind/stl/vector.h>

#include <cstddef>
#include <cstdint>
#include <utility>
#include <vector>

namespace nb = nanobind;

void bind_core(nb::module_& m);
void bind_command(nb::module_& m);
void bind_episode(nb::module_& m);
void bind_runtime(nb::module_& m);
void bind_gpu(nb::module_& m);

template <typename Shape>
auto visual_tensor_to_numpy(std::vector<float>&& data, size_t ndim, const size_t* shape) {
    auto* output = new std::vector<float>(std::move(data));
    nb::capsule owner(output, [](void* ptr) noexcept {
        delete static_cast<std::vector<float>*>(ptr);
    });
    return nb::ndarray<nb::numpy, const float, Shape>(output->data(), ndim, shape, owner);
}

template <typename Shape>
auto uint32_tensor_to_numpy(std::vector<std::uint32_t>&& data, size_t ndim, const size_t* shape) {
    auto* output = new std::vector<std::uint32_t>(std::move(data));
    nb::capsule owner(output, [](void* ptr) noexcept {
        delete static_cast<std::vector<std::uint32_t>*>(ptr);
    });
    return nb::ndarray<nb::numpy, const std::uint32_t, Shape>(output->data(), ndim, shape, owner);
}
