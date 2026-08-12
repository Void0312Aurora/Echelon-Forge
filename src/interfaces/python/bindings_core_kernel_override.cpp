#include "interfaces/python/bindings_core_detail.h"

#include <stdexcept>

#include "components/basic/common.h"
#include "components/combat/common/missile_guidance_mechanism_profile.h"
#include "components/combat/common/weapon_common.h"
#include "components/systems/sensor.h"

void bind_simulation_kernel_diagnostics_override_surface(nb::class_<SimulationKernel> &kernel) {
    kernel
        .def("set_contact_list", &SimulationKernel::set_contact_list,
             "Override the ContactList for a unit or missile", nb::arg("entity_id"),
             nb::arg("detections"))
        .def(
            "debug_set_unit_truth_state",
            [](SimulationKernel &self, uint64_t entity_id, double x_m, double y_m, double z_m,
               double heading_deg, double pitch_deg, double roll_deg, double vx_mps, double vy_mps,
               double vz_mps) {
                auto e = diagnostics_legacy_binding_entity_quarantine_lookup(self, entity_id);
                if (!e.is_valid()) {
                    throw std::invalid_argument("Invalid entity ID for debug_set_unit_truth_state");
                }
                // Diagnostics-only truth override for deterministic runtime tests. Keep this
                // quarantined from the maintained command surface: scripted scenarios use it to
                // remove unrelated platform-control drift while validating weapons behavior.
                e.set<Transform>({x_m, y_m, z_m, heading_deg, pitch_deg, roll_deg});
                e.set<Velocity>({vx_mps, vy_mps, vz_mps});
            },
            "Debug diagnostics-only override of entity transform and velocity truth state",
            nb::arg("entity_id"), nb::arg("x_m"), nb::arg("y_m"), nb::arg("z_m"),
            nb::arg("heading_deg"), nb::arg("pitch_deg"), nb::arg("roll_deg"), nb::arg("vx_mps"),
            nb::arg("vy_mps"), nb::arg("vz_mps"))
        .def(
            "set_missile_guidance_mechanism_profile",
            [](SimulationKernel &self, uint64_t entity_id, int capture_mode, int pn_mode,
               int lead_mode, int kinematics_source, int apn_mode) {
                auto e = diagnostics_legacy_binding_entity_quarantine_lookup(self, entity_id);
                const Missile *missile = e.is_valid() ? e.get<Missile>() : nullptr;
                if (!missile) {
                    throw std::invalid_argument(
                        "Invalid missile entity for set_missile_guidance_mechanism_profile");
                }
                if (missile->last_guidance_time >= 0.0) {
                    throw std::invalid_argument("Missile guidance mechanism profile must be set "
                                                "before the first guidance update");
                }
                if (capture_mode < MissileGuidanceMechanismProfile::kCaptureOff ||
                    capture_mode > MissileGuidanceMechanismProfile::kCaptureOn) {
                    throw std::invalid_argument("capture_mode must be 0 or 1");
                }
                if (pn_mode < MissileGuidanceMechanismProfile::kPnLegacyBodyRates ||
                    pn_mode > MissileGuidanceMechanismProfile::kPnWorldTrackAnalytic) {
                    throw std::invalid_argument("pn_mode must be in [0, 3]");
                }
                if (lead_mode < MissileGuidanceMechanismProfile::kLeadOff ||
                    lead_mode > MissileGuidanceMechanismProfile::kLeadQuadratic) {
                    throw std::invalid_argument("lead_mode must be in [0, 2]");
                }
                if (kinematics_source < MissileGuidanceMechanismProfile::kKinematicsTrack ||
                    kinematics_source >
                        MissileGuidanceMechanismProfile::kKinematicsTruthConstantVelocity) {
                    throw std::invalid_argument("kinematics_source must be 0 or 1");
                }
                if (apn_mode < MissileGuidanceMechanismProfile::kApnOff ||
                    apn_mode > MissileGuidanceMechanismProfile::kApnOn) {
                    throw std::invalid_argument("apn_mode must be 0 or 1");
                }
                MissileGuidanceMechanismProfile profile;
                profile.active = true;
                profile.capture_mode = capture_mode;
                profile.pn_mode = pn_mode;
                profile.lead_mode = lead_mode;
                profile.kinematics_source = kinematics_source;
                profile.apn_mode = apn_mode;
                e.set<MissileGuidanceMechanismProfile>(profile);
            },
            "Attach a diagnostics-only exact guidance mechanism profile before first update",
            nb::arg("entity_id"), nb::arg("capture_mode"), nb::arg("pn_mode"), nb::arg("lead_mode"),
            nb::arg("kinematics_source"), nb::arg("apn_mode"))
        .def("set_missile_tuning", &SimulationKernel::set_missile_tuning,
             "Override missile parameters for diagnostics", nb::arg("tuning"))
        .def("get_missile_tuning", &SimulationKernel::get_missile_tuning, nb::rv_policy::copy,
             "Get current missile tuning snapshot");
}
