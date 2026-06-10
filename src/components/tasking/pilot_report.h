#pragma once

#include "components/domains/air/tasking/pilot_report_air.h"
#include "components/tasking/common/pilot_report_core.h"
#include "components/domains/ground/tasking/pilot_report_ground.h"
#include "components/domains/naval/tasking/pilot_report_naval.h"

struct PilotReport : PilotReportCore, PilotReportAir, PilotReportNaval, PilotReportGround {};

// Flat umbrella retained only as a compatibility/transport shell.
// Shared-core and domain slices remain the maintained owner surfaces.
using PilotReportCompatibilityTransportShell = PilotReport;
inline constexpr bool kPilotReportCompatibilityTransportShell = true;

static_assert(
    kPilotReportAirOwnedDomainSlice && kPilotReportNavalOwnedDomainSlice &&
        kPilotReportGroundOwnedDomainSlice,
    "PilotReport compatibility shells must project to explicit owner slices."
);

[[nodiscard]] inline const PilotReportCore&
pilot_report_shared_core(
    const PilotReportCompatibilityTransportShell& report
) noexcept {
    return report;
}

[[nodiscard]] inline PilotReportCore&
pilot_report_shared_core(PilotReportCompatibilityTransportShell& report) noexcept {
    return report;
}

[[nodiscard]] inline const PilotReportAir&
pilot_report_air_owner_slice(
    const PilotReportCompatibilityTransportShell& report
) noexcept {
    return report;
}

[[nodiscard]] inline PilotReportAir&
pilot_report_air_owner_slice(PilotReportCompatibilityTransportShell& report) noexcept {
    return report;
}

[[nodiscard]] inline const PilotReportNaval&
pilot_report_naval_owner_slice(
    const PilotReportCompatibilityTransportShell& report
) noexcept {
    return report;
}

[[nodiscard]] inline PilotReportNaval&
pilot_report_naval_owner_slice(
    PilotReportCompatibilityTransportShell& report
) noexcept {
    return report;
}

[[nodiscard]] inline const PilotReportGround&
pilot_report_ground_owner_slice(
    const PilotReportCompatibilityTransportShell& report
) noexcept {
    return report;
}

[[nodiscard]] inline PilotReportGround&
pilot_report_ground_owner_slice(
    PilotReportCompatibilityTransportShell& report
) noexcept {
    return report;
}

[[nodiscard]] inline PilotReportNaval::CommandAuthorityDirective
pilot_report_naval_command_authority(
    const PilotReportCompatibilityTransportShell& report
) noexcept {
    return pilot_report_naval_command_authority(pilot_report_naval_owner_slice(report));
}

[[nodiscard]] inline PilotReportGround::StaticStatusDirective
pilot_report_ground_static_status_directive(
    const PilotReportCompatibilityTransportShell& report
) noexcept {
    return pilot_report_ground_static_status_directive(
        pilot_report_ground_owner_slice(report)
    );
}
