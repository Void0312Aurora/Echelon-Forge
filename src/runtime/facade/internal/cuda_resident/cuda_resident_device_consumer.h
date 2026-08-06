#pragma once

#include "runtime/contracts/cuda_resident_device_consumer_contract.h"

namespace runtime::cuda_resident {

namespace testing {
class CudaResidentDeviceConsumerTestAccess;
}

// Private CR2 consumer seam. One owner thread may submit work; leases and
// receipts are independently copyable shared owners and may outlive the
// backend that produced them. This class is not exposed by RuntimeFacade.
class CudaResidentDeviceConsumer final {
  public:
    [[nodiscard]] device_consumer::SubmitResult
    submit(const device_consumer::ObservationLease &lease,
           const device_consumer::ConsumerRequest &request);
    [[nodiscard]] device_consumer::Status await(const device_consumer::ConsumerReceipt &receipt);
    [[nodiscard]] device_consumer::DiagnosticResult
    materialize_for_diagnostics(const device_consumer::ConsumerReceipt &receipt);

  private:
    friend class testing::CudaResidentDeviceConsumerTestAccess;

    struct Faults {
        bool fail_next_allocation = false;
        bool fail_next_launch = false;
        bool fail_next_event_record = false;
        bool fail_next_wait = false;
        bool fail_next_materialize = false;
    } faults_{};
};

namespace testing {

class CudaResidentDeviceConsumerTestAccess final {
  public:
    static void fail_next_allocation(CudaResidentDeviceConsumer &consumer) noexcept;
    static void fail_next_launch(CudaResidentDeviceConsumer &consumer) noexcept;
    static void fail_next_event_record(CudaResidentDeviceConsumer &consumer) noexcept;
    static void fail_next_wait(CudaResidentDeviceConsumer &consumer) noexcept;
    static void fail_next_materialize(CudaResidentDeviceConsumer &consumer) noexcept;
};

} // namespace testing

} // namespace runtime::cuda_resident
