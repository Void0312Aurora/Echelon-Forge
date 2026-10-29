#include "runtime/host/integration/runtime_kernel_candidate.h"

#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/string_view.h>
#include <nanobind/stl/optional.h>
#include <nanobind/stl/vector.h>

#include <string>
#include <utility>

namespace nb = nanobind;

namespace {

using runtime::host::integration::RuntimeCandidateObservationPacket;
using runtime::host::integration::RuntimeKernelCandidate;
using runtime::host::integration::RuntimeKernelSiblingBranch;
using runtime::host::integration::RuntimeKernelSnapshotFacts;

} // namespace

NB_MODULE(ef_runtime_candidate_py, m) {
    // Reuse the maintained setup DTO registration across extension modules.
    nb::module_::import_("ef_py");
    nb::class_<RuntimeKernelSnapshotFacts>(m, "RuntimeKernelSnapshotFacts")
        .def(nb::init<>())
        .def_rw("step", &RuntimeKernelSnapshotFacts::step)
        .def_rw("state_digest", &RuntimeKernelSnapshotFacts::state_digest)
        .def_rw("event_cursor", &RuntimeKernelSnapshotFacts::event_cursor)
        .def_rw("rng_digest", &RuntimeKernelSnapshotFacts::rng_digest)
        .def_rw("terminated", &RuntimeKernelSnapshotFacts::terminated);

    nb::class_<RuntimeCandidateObservationPacket>(m, "RuntimeCandidateObservationPacket")
        .def(nb::init<>())
        .def_rw("snapshot_version", &RuntimeCandidateObservationPacket::snapshot_version)
        .def_rw("barrier_id", &RuntimeCandidateObservationPacket::barrier_id)
        .def_rw("source_time_s", &RuntimeCandidateObservationPacket::source_time_s)
        .def_rw("provenance", &RuntimeCandidateObservationPacket::provenance)
        .def_rw("refs", &RuntimeCandidateObservationPacket::refs)
        .def_rw("agent_observations", &RuntimeCandidateObservationPacket::agent_observations)
        .def_rw("instrument_states", &RuntimeCandidateObservationPacket::instrument_states);

    nb::class_<RuntimeKernelSiblingBranch> branch(m, "RuntimeKernelSiblingBranch");
    branch.def("valid", &RuntimeKernelSiblingBranch::valid)
        .def("snapshot_facts", &RuntimeKernelSiblingBranch::snapshot_facts)
        .def(
            "checkpoint",
            [](const RuntimeKernelSiblingBranch &self) {
                auto checkpoint = self.checkpoint();
                return checkpoint.release();
            },
            nb::rv_policy::take_ownership)
        .def(
            "fork_native",
            [](const RuntimeKernelSiblingBranch &self, std::string intervention_sha256,
               std::uint64_t horizon) {
                return self.fork_native_branch(std::move(intervention_sha256), horizon).release();
            },
            nb::arg("intervention_sha256"), nb::arg("horizon"), nb::rv_policy::take_ownership)
        .def("step", &RuntimeKernelSiblingBranch::step, nb::arg("payload_sha256"))
        .def("step_pilot_actions", &RuntimeKernelSiblingBranch::step_pilot_actions)
        .def("observation", &RuntimeKernelSiblingBranch::observation)
        .def("read_observation_packet", &RuntimeKernelSiblingBranch::read_observation_packet)
        .def("resolve_entity", &RuntimeKernelSiblingBranch::resolve_entity);

    nb::class_<RuntimeKernelCandidate> candidate(m, "RuntimeKernelCandidate");
    candidate
        .def(nb::init<std::uint64_t, std::uint64_t, bool, std::uint32_t>(), nb::arg("host_high"),
             nb::arg("host_low"), nb::arg("shadow") = true, nb::arg("seed") = 42)
        .def("start", [](RuntimeKernelCandidate &self) { return static_cast<bool>(self.start()); })
        .def("shutdown",
             [](RuntimeKernelCandidate &self) {
                 return static_cast<bool>(self.shutdown(10, 1000).status);
             })
        .def("snapshot_facts", &RuntimeKernelCandidate::native_snapshot_facts)
        .def("set_time_step", [](RuntimeKernelCandidate &self,
                                 double dt) { return self.set_time_step(self.world_ref(), dt); })
        .def(
            "checkpoint_native",
            [](RuntimeKernelCandidate &self) { return self.native_checkpoint().release(); },
            nb::rv_policy::take_ownership)
        .def(
            "spawn_unit",
            [](RuntimeKernelCandidate &self, nb::object request) {
                // Resolve the existing ef_py DTO without a parallel setup format.
                const auto entity =
                    self.spawn_unit(self.world_ref(), nb::cast<WorldSpawnRequest>(request));
                return entity ? entity->entity_id : 0;
            },
            nb::arg("request"))
        .def("step_native", &RuntimeKernelCandidate::native_step, nb::arg("payload_sha256"))
        .def("step_pilot_actions", &RuntimeKernelCandidate::step_pilot_actions)
        .def("observation", &RuntimeKernelCandidate::observation)
        .def("read_observation_packet", &RuntimeKernelCandidate::read_observation_packet)
        .def("resolve_entity", &RuntimeKernelCandidate::resolve_entity)
        .def(
            "fork_native",
            [](RuntimeKernelCandidate &self, std::string intervention_sha256,
               std::uint64_t horizon) {
                auto branch = self.fork_native_branch(std::move(intervention_sha256), horizon);
                return branch.release();
            },
            nb::arg("intervention_sha256"), nb::arg("horizon"), nb::rv_policy::take_ownership);
}
