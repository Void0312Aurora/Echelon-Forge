#pragma once

#include "components/tasking/air/pilot_report_air.h"
#include "components/tasking/common/pilot_report_core.h"
#include "components/tasking/naval/pilot_report_naval.h"

struct PilotReport : PilotReportCore, PilotReportAir, PilotReportNaval {};
