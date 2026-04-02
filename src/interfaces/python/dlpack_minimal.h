#pragma once

#include <cstdint>

// Minimal DLPack definitions for exporting CUDA float tensors via the Python
// __dlpack__ protocol. This intentionally covers only the subset required by
// the maintained GPU batch observation/visual bridges.

typedef enum {
    kDLCPU = 1,
    kDLCUDA = 2,
} DLDeviceType;

typedef struct {
    DLDeviceType device_type;
    int32_t device_id;
} DLDevice;

typedef struct {
    uint8_t code;
    uint8_t bits;
    uint16_t lanes;
} DLDataType;

typedef struct {
    void* data;
    DLDevice device;
    int32_t ndim;
    DLDataType dtype;
    int64_t* shape;
    int64_t* strides;
    uint64_t byte_offset;
} DLTensor;

typedef struct DLManagedTensor {
    DLTensor dl_tensor;
    void* manager_ctx;
    void (*deleter)(struct DLManagedTensor* self);
} DLManagedTensor;

static constexpr uint8_t kDLFloat = 2;
