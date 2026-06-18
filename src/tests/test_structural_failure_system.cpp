#include "components/basic/common.h"
#include "components/combat/common/damage_common.h"
#include "components/combat/health.h"
#include "components/combat/structural_failure.h"
#include "core/engine/simulation_kernel_engagement_event_store.h"
#include "core/interfaces/engagement_event_recorder.h"
#include "systems/combat/structural_consequence_system.h"
#include "systems/combat/structural_failure_system.h"

#include <doctest/doctest.h>
#include <flecs.h>

#include <string>
#include <utility>
#include <vector>

namespace {

void set_component_damage(ComponentDamageState &damage, const std::string &name, double integrity,
                          const std::string &mode, double mode_severity = -1.0) {
    damage.component_integrity[name] = integrity;
    damage.component_primary_failure_mode[name] = mode;
    if (mode_severity >= 0.0) {
        damage.component_failure_mode_severity[name][mode] = mode_severity;
    }
}

struct CapturingStructuralRecorder final : IEngagementEventRecorder {
    std::vector<StructuralBreakupEvent> structural_events;
    std::vector<PlatformConsequenceEvent> platform_consequence_events;

    EngagementDamageStateSnapshot capture_engagement_damage_state(std::uint64_t) const override {
        return {};
    }

    std::uint64_t record_effects_damage_event(EngagementEffectsDamageEventRecord) override {
        return 0;
    }

    std::uint64_t record_nearest_approach_event(EngagementNearestApproachEventRecord) override {
        return 0;
    }

    std::uint64_t record_fuze_evaluation_event(EngagementFuzeEvaluationEventRecord) override {
        return 0;
    }

    std::uint64_t record_warhead_mechanism_event(EngagementWarheadMechanismEventRecord) override {
        return 0;
    }

    std::uint64_t record_spatial_coverage_event(EngagementSpatialCoverageEventRecord) override {
        return 0;
    }

    std::uint64_t record_component_load_event(EngagementComponentLoadEventRecord) override {
        return 0;
    }

    std::uint64_t record_component_damage_event(EngagementComponentDamageEventRecord) override {
        return 0;
    }

    std::uint64_t
    record_structural_breakup_event(EngagementStructuralBreakupEventRecord record) override {
        structural_events.push_back(std::move(record.event));
        return static_cast<std::uint64_t>(structural_events.size());
    }

    std::uint64_t
    record_platform_consequence_event(EngagementPlatformConsequenceEventRecord record) override {
        platform_consequence_events.push_back(std::move(record.event));
        return static_cast<std::uint64_t>(platform_consequence_events.size());
    }
};

struct StructuralStepResult {
    StructuralBreakupState state{};
    std::vector<StructuralBreakupEvent> events;
};

StructuralStepResult run_single_aircraft_structural_step(const ComponentDamageState &damage) {
    flecs::world world;
    world.component<ComponentDamageState>();
    world.component<StructuralBreakupState>();
    world.component<KeyEntity>();
    CapturingStructuralRecorder recorder;
    world.set<EngagementEventRecorderRef>({&recorder});
    register_structural_failure_system(world);

    auto aircraft =
        world.entity().set<KeyEntity>({UnitType::Aircraft}).set<ComponentDamageState>(damage);

    world.progress(1.0 / 60.0);

    StructuralStepResult result{};
    if (const StructuralBreakupState *state = aircraft.get<StructuralBreakupState>()) {
        result.state = *state;
    }
    result.events = recorder.structural_events;
    return result;
}

} // namespace

TEST_SUITE("structural_failure_state") {

    TEST_CASE("functional component failure does not trigger structural breakup") {
        ComponentDamageState damage{};
        set_component_damage(damage, "center_fuselage_fuel_cell", 0.10, "fuel_leak");

        const StructuralBreakupState state =
            structural_failure::evaluate_structural_breakup_state(damage);

        CHECK(state.breakup_state == StructuralBreakupPhase::Intact);
        CHECK(state.active_break_modes == 0u);
        CHECK_FALSE(state.airframe_breakup);
    }

    TEST_CASE("functional cumulative wing damage does not trigger structural breakup") {
        ComponentDamageState damage{};
        set_component_damage(damage, "wing_spar_center_left_inner_wing_segment", 1.00, "none");
        set_component_damage(damage, "left_aileron_actuator", 0.70, "hydraulic_pressure_loss");
        set_component_damage(damage, "left_wing_fuel_cell", 0.70, "fuel_leak");

        const StructuralBreakupState state =
            structural_failure::evaluate_structural_breakup_state(damage);

        CHECK(state.breakup_state == StructuralBreakupPhase::Intact);
        CHECK_FALSE(structural_breakup_has_mode(state, StructuralBreakMode::WingLoss));
        CHECK_FALSE(structural_breakup_has_group(state, StructuralBreakGroup::WingLeft));
    }

    TEST_CASE("default shared wing spar activates both wing groups as one family") {
        ComponentDamageState damage{};
        set_component_damage(damage, "wing_spar_center", 0.20, "puncture");

        const StructuralBreakupState state =
            structural_failure::evaluate_structural_breakup_state(damage);

        CHECK(state.breakup_state == StructuralBreakupPhase::PartialDetachment);
        CHECK(structural_breakup_has_mode(state, StructuralBreakMode::WingLoss));
        CHECK(structural_breakup_has_group(state, StructuralBreakGroup::WingLeft));
        CHECK(structural_breakup_has_group(state, StructuralBreakGroup::WingRight));
        CHECK(state.detached_part_count == 2u);
        CHECK_FALSE(state.airframe_breakup);
    }

    TEST_CASE("three structural families produce full breakup and multi-axis mode") {
        ComponentDamageState damage{};
        set_component_damage(damage, "wing_spar_center", 0.20, "puncture");
        set_component_damage(damage, "engine_core", 0.10, "structural_weakening");
        set_component_damage(damage, "center_fuselage_fuel_cell", 0.20, "blast_deformation");

        const StructuralBreakupState state =
            structural_failure::evaluate_structural_breakup_state(damage);

        CHECK(state.breakup_state == StructuralBreakupPhase::FullBreakup);
        CHECK(structural_breakup_has_mode(state, StructuralBreakMode::WingLoss));
        CHECK(structural_breakup_has_mode(state, StructuralBreakMode::EngineDetach));
        CHECK(structural_breakup_has_mode(state, StructuralBreakMode::FuselageRupture));
        CHECK(structural_breakup_has_mode(state, StructuralBreakMode::MultiAxis));
        CHECK(state.airframe_breakup);
    }

    TEST_CASE("TG-P7 split receivers select split mapping without parent components") {
        ComponentDamageState damage{};
        set_component_damage(damage, "wing_spar_center_left_inner_wing_segment", 0.20, "cut");
        set_component_damage(damage, "engine_core_afterburner_segment", 0.10,
                             "structural_weakening");
        set_component_damage(damage, "engine_core_hot_section_segment", 0.10,
                             "structural_weakening");

        const StructuralBreakupState state =
            structural_failure::evaluate_structural_breakup_state(damage);

        CHECK(state.breakup_state == StructuralBreakupPhase::PartialBreakup);
        CHECK(structural_breakup_has_group(state, StructuralBreakGroup::WingLeft));
        CHECK_FALSE(structural_breakup_has_group(state, StructuralBreakGroup::WingRight));
        CHECK(structural_breakup_has_mode(state, StructuralBreakMode::WingLoss));
        CHECK(structural_breakup_has_mode(state, StructuralBreakMode::EngineDetach));
    }

    TEST_CASE("TG-P7 near-field cumulative wing damage produces wing_loss") {
        ComponentDamageState damage{};
        set_component_damage(damage, "wing_spar_center_left_inner_wing_segment", 1.00, "none");
        set_component_damage(damage, "left_aileron_actuator", 0.94, "cut");
        set_component_damage(damage, "left_wing_fuel_cell", 0.915, "cut");

        const StructuralBreakupState state =
            structural_failure::evaluate_structural_breakup_state(damage);

        CHECK(state.breakup_state == StructuralBreakupPhase::PartialDetachment);
        CHECK(structural_breakup_has_mode(state, StructuralBreakMode::WingLoss));
        CHECK(structural_breakup_has_group(state, StructuralBreakGroup::WingLeft));
        CHECK_FALSE(structural_breakup_has_group(state, StructuralBreakGroup::WingRight));
        CHECK_FALSE(state.airframe_breakup);
    }

    TEST_CASE("TG-P7 rod cut severity produces wing_loss despite high component integrity") {
        ComponentDamageState damage{};
        set_component_damage(damage, "wing_spar_center_left_inner_wing_segment", 1.00, "none");
        set_component_damage(damage, "left_aileron_actuator", 0.986, "cut", 0.31);
        set_component_damage(damage, "left_wing_fuel_cell", 0.992, "cut", 0.27);

        const StructuralBreakupState state =
            structural_failure::evaluate_structural_breakup_state(damage);

        CHECK(state.breakup_state == StructuralBreakupPhase::PartialDetachment);
        CHECK(structural_breakup_has_mode(state, StructuralBreakMode::WingLoss));
        CHECK(structural_breakup_has_group(state, StructuralBreakGroup::WingLeft));
        CHECK_FALSE(structural_breakup_has_group(state, StructuralBreakGroup::WingRight));
        CHECK_FALSE(state.airframe_breakup);
    }

    TEST_CASE("breakup state is irreversible when component damage later disappears") {
        ComponentDamageState severe_damage{};
        set_component_damage(severe_damage, "wing_spar_center", 0.20, "puncture");
        set_component_damage(severe_damage, "engine_core", 0.10, "structural_weakening");
        set_component_damage(severe_damage, "center_fuselage_fuel_cell", 0.20, "blast_deformation");

        const StructuralBreakupState full =
            structural_failure::evaluate_structural_breakup_state(severe_damage);

        ComponentDamageState restored_damage{};
        set_component_damage(restored_damage, "wing_spar_center", 1.0, "puncture");
        set_component_damage(restored_damage, "engine_core", 1.0, "structural_weakening");
        set_component_damage(restored_damage, "center_fuselage_fuel_cell", 1.0,
                             "blast_deformation");

        const StructuralBreakupState restored =
            structural_failure::evaluate_structural_breakup_state(restored_damage, full);

        CHECK(restored.breakup_state == StructuralBreakupPhase::FullBreakup);
        CHECK(structural_breakup_has_mode(restored, StructuralBreakMode::MultiAxis));
        CHECK(restored.airframe_breakup);
    }

    TEST_CASE("ECS system attaches and updates StructuralBreakupState on aircraft only") {
        flecs::world world;
        world.component<ComponentDamageState>();
        world.component<StructuralBreakupState>();
        world.component<KeyEntity>();
        register_structural_failure_system(world);

        ComponentDamageState aircraft_damage{};
        set_component_damage(aircraft_damage, "rudder_actuator", 0.10, "cut");
        auto aircraft = world.entity()
                            .set<KeyEntity>({UnitType::Aircraft})
                            .set<ComponentDamageState>(aircraft_damage);

        ComponentDamageState missile_damage{};
        set_component_damage(missile_damage, "rudder_actuator", 0.10, "cut");
        auto missile = world.entity()
                           .set<KeyEntity>({UnitType::Missile})
                           .set<ComponentDamageState>(missile_damage);

        world.progress(1.0 / 60.0);

        const StructuralBreakupState *aircraft_state = aircraft.get<StructuralBreakupState>();
        REQUIRE(aircraft_state != nullptr);
        CHECK(aircraft_state->breakup_state == StructuralBreakupPhase::PartialDetachment);
        CHECK(structural_breakup_has_mode(*aircraft_state, StructuralBreakMode::TailLoss));
        CHECK(missile.get<StructuralBreakupState>() == nullptr);
    }

} // TEST_SUITE

TEST_SUITE("structural_consequence") {

    TEST_CASE("no-breakup state produces zero consequence deltas") {
        StructuralBreakupState breakup{};
        AircraftDamageState aircraft{};
        PlatformDamageState platform{};
        Health health{100.0, 100.0};

        structural_consequence::apply_structural_breakup_consequence(breakup, aircraft, platform,
                                                                     health);

        CHECK(aircraft.structural_integrity == doctest::Approx(1.0));
        CHECK(aircraft.flight_control_integrity == doctest::Approx(1.0));
        CHECK(aircraft.propulsion_integrity == doctest::Approx(1.0));
        CHECK_FALSE(aircraft.forced_landing_required);
        CHECK(platform.mobility_capability == doctest::Approx(1.0));
        CHECK(platform.loss_state == PlatformLossState::CombatCapable);
        CHECK_FALSE(health.mobility_kill);
    }

    TEST_CASE("wing-loss consequence projects to maintained aircraft and platform state") {
        StructuralBreakupState breakup{};
        breakup.breakup_state = StructuralBreakupPhase::PartialDetachment;
        breakup.active_break_modes = structural_break_mode_mask(StructuralBreakMode::WingLoss);
        breakup.active_structural_groups =
            structural_break_group_mask(StructuralBreakGroup::WingLeft);
        breakup.detached_part_count = 1u;

        AircraftDamageState aircraft{};
        PlatformDamageState platform{};
        Health health{100.0, 100.0};

        structural_consequence::apply_structural_breakup_consequence(breakup, aircraft, platform,
                                                                     health);

        CHECK(aircraft.structural_integrity == doctest::Approx(0.35));
        CHECK(aircraft.roll_control_integrity == doctest::Approx(0.18));
        CHECK(aircraft.control_asymmetry == doctest::Approx(0.78));
        CHECK(aircraft.forced_landing_required);
        CHECK(aircraft.flight_control_kill);
        CHECK(platform.mobility_capability == doctest::Approx(0.0));
        CHECK(platform.loss_state == PlatformLossState::MobilityKill);
        CHECK(health.mobility_kill);
    }

    TEST_CASE("tail-loss consequence projects pitch yaw and mobility limits") {
        StructuralBreakupState breakup{};
        breakup.breakup_state = StructuralBreakupPhase::PartialDetachment;
        breakup.active_break_modes = structural_break_mode_mask(StructuralBreakMode::TailLoss);
        breakup.active_structural_groups =
            structural_break_group_mask(StructuralBreakGroup::TailLeft);
        breakup.detached_part_count = 1u;

        AircraftDamageState aircraft{};
        PlatformDamageState platform{};
        Health health{100.0, 100.0};

        structural_consequence::apply_structural_breakup_consequence(breakup, aircraft, platform,
                                                                     health);

        CHECK(aircraft.flight_control_integrity == doctest::Approx(0.60));
        CHECK(aircraft.pitch_control_integrity == doctest::Approx(0.45));
        CHECK(aircraft.yaw_control_integrity == doctest::Approx(0.50));
        CHECK(aircraft.forced_landing_required);
        CHECK(platform.mobility_capability == doctest::Approx(0.25));
        CHECK(platform.loss_state == PlatformLossState::MobilityKill);
    }

    TEST_CASE("engine-detach consequence projects propulsion and fuel hazards") {
        StructuralBreakupState breakup{};
        breakup.breakup_state = StructuralBreakupPhase::PartialDetachment;
        breakup.active_break_modes = structural_break_mode_mask(StructuralBreakMode::EngineDetach);
        breakup.active_structural_groups =
            structural_break_group_mask(StructuralBreakGroup::EngineRight);
        breakup.detached_part_count = 1u;

        AircraftDamageState aircraft{};
        PlatformDamageState platform{};
        Health health{100.0, 100.0};

        structural_consequence::apply_structural_breakup_consequence(breakup, aircraft, platform,
                                                                     health);

        CHECK(aircraft.propulsion_integrity == doctest::Approx(0.30));
        CHECK(aircraft.fuel_system_integrity == doctest::Approx(0.72));
        CHECK(aircraft.fuel_leak_severity == doctest::Approx(0.30));
        CHECK(aircraft.ignition_source_severity == doctest::Approx(0.20));
        CHECK(platform.mobility_capability == doctest::Approx(0.25));
        CHECK(platform.loss_state == PlatformLossState::MobilityKill);
    }

    TEST_CASE("fuselage-rupture consequence projects structural fire and crew hazards") {
        StructuralBreakupState breakup{};
        breakup.breakup_state = StructuralBreakupPhase::PartialDetachment;
        breakup.active_break_modes =
            structural_break_mode_mask(StructuralBreakMode::FuselageRupture);
        breakup.active_structural_groups =
            structural_break_group_mask(StructuralBreakGroup::Fuselage);
        breakup.detached_part_count = 1u;

        AircraftDamageState aircraft{};
        PlatformDamageState platform{};
        Health health{100.0, 100.0};

        structural_consequence::apply_structural_breakup_consequence(breakup, aircraft, platform,
                                                                     health);

        CHECK(aircraft.structural_integrity == doctest::Approx(0.50));
        CHECK(aircraft.fuel_leak_severity == doctest::Approx(0.45));
        CHECK(aircraft.fire_severity == doctest::Approx(0.15));
        CHECK(aircraft.fuselage_fire_zone_severity == doctest::Approx(0.20));
        CHECK(platform.mission_capability == doctest::Approx(0.35));
        CHECK(platform.survivability_margin == doctest::Approx(0.50));
        CHECK(platform.loss_state == PlatformLossState::MobilityKill);
    }

    TEST_CASE("multi-axis airframe breakup uses maintained lost state without entity lifecycle") {
        StructuralBreakupState breakup{};
        breakup.breakup_state = StructuralBreakupPhase::FullBreakup;
        breakup.active_break_modes =
            structural_break_mode_mask(StructuralBreakMode::WingLoss) |
            structural_break_mode_mask(StructuralBreakMode::EngineDetach) |
            structural_break_mode_mask(StructuralBreakMode::FuselageRupture) |
            structural_break_mode_mask(StructuralBreakMode::MultiAxis);
        breakup.active_structural_groups =
            structural_break_group_mask(StructuralBreakGroup::WingLeft) |
            structural_break_group_mask(StructuralBreakGroup::EngineRight) |
            structural_break_group_mask(StructuralBreakGroup::Fuselage);
        breakup.detached_part_count = 3u;
        breakup.airframe_breakup = true;

        AircraftDamageState aircraft{};
        PlatformDamageState platform{};
        Health health{100.0, 100.0};

        structural_consequence::apply_structural_breakup_consequence(breakup, aircraft, platform,
                                                                     health);

        CHECK(aircraft.structural_integrity == doctest::Approx(0.20));
        CHECK(aircraft.flight_control_kill);
        CHECK(aircraft.forced_landing_required);
        CHECK(platform.mobility_capability == doctest::Approx(0.0));
        CHECK(platform.survivability_margin == doctest::Approx(0.0));
        CHECK(platform.loss_state == PlatformLossState::Lost);
        CHECK(health.mobility_kill);
    }

    TEST_CASE("irreversible structural state does not accumulate duplicate deltas") {
        StructuralBreakupState breakup{};
        breakup.breakup_state = StructuralBreakupPhase::PartialDetachment;
        breakup.active_break_modes = structural_break_mode_mask(StructuralBreakMode::EngineDetach);
        breakup.active_structural_groups =
            structural_break_group_mask(StructuralBreakGroup::EngineRight);
        breakup.detached_part_count = 1u;

        AircraftDamageState aircraft{};
        PlatformDamageState platform{};
        Health health{100.0, 100.0};

        structural_consequence::apply_structural_breakup_consequence(breakup, aircraft, platform,
                                                                     health);
        const double propulsion_after_first = aircraft.propulsion_integrity;
        const double fuel_leak_after_first = aircraft.fuel_leak_severity;
        const double mobility_after_first = platform.mobility_capability;

        structural_consequence::apply_structural_breakup_consequence(breakup, aircraft, platform,
                                                                     health);

        CHECK(aircraft.propulsion_integrity == doctest::Approx(propulsion_after_first));
        CHECK(aircraft.fuel_leak_severity == doctest::Approx(fuel_leak_after_first));
        CHECK(platform.mobility_capability == doctest::Approx(mobility_after_first));
    }

    TEST_CASE("ECS bridge consumes structural breakup after structural failure update") {
        flecs::world world;
        world.component<ComponentDamageState>();
        world.component<StructuralBreakupState>();
        world.component<KeyEntity>();
        world.component<Health>();
        world.component<PlatformDamageState>();
        world.component<AircraftDamageState>();
        register_structural_failure_system(world);
        register_structural_consequence_system(world);

        ComponentDamageState damage{};
        set_component_damage(damage, "wing_spar_center", 0.20, "puncture");
        set_component_damage(damage, "engine_core", 0.10, "structural_weakening");
        set_component_damage(damage, "center_fuselage_fuel_cell", 0.20, "blast_deformation");
        auto aircraft = world.entity()
                            .set<KeyEntity>({UnitType::Aircraft})
                            .set<ComponentDamageState>(damage)
                            .set<Health>({100.0, 100.0})
                            .set<PlatformDamageState>(PlatformDamageState{})
                            .set<AircraftDamageState>(AircraftDamageState{});

        world.progress(1.0 / 60.0);

        const StructuralBreakupState *breakup = aircraft.get<StructuralBreakupState>();
        REQUIRE(breakup != nullptr);
        CHECK(breakup->airframe_breakup);

        const AircraftDamageState *aircraft_damage = aircraft.get<AircraftDamageState>();
        REQUIRE(aircraft_damage != nullptr);
        CHECK(aircraft_damage->structural_integrity == doctest::Approx(0.20));
        CHECK(aircraft_damage->forced_landing_required);

        const PlatformDamageState *platform = aircraft.get<PlatformDamageState>();
        REQUIRE(platform != nullptr);
        CHECK(platform->loss_state == PlatformLossState::Lost);
        CHECK(platform->survivability_margin == doctest::Approx(0.0));
        CHECK(aircraft.is_alive());
    }

    TEST_CASE("ECS bridge records chain-linked platform consequence event") {
        flecs::world world;
        world.component<ComponentDamageState>();
        world.component<StructuralBreakupState>();
        world.component<KeyEntity>();
        world.component<Health>();
        world.component<PlatformDamageState>();
        world.component<AircraftDamageState>();
        SimulationKernelEngagementEventStore store(world);
        world.set<EngagementEventRecorderRef>({&store});
        register_structural_failure_system(world);
        register_structural_consequence_system(world);

        ComponentDamageState damage{};
        set_component_damage(damage, "engine_core", 0.10, "structural_weakening");
        auto aircraft = world.entity()
                            .set<KeyEntity>({UnitType::Aircraft})
                            .set<ComponentDamageState>(damage)
                            .set<Health>({100.0, 100.0})
                            .set<PlatformDamageState>(PlatformDamageState{})
                            .set<AircraftDamageState>(AircraftDamageState{});

        world.progress(1.0 / 60.0);

        const StructuralBreakupState *breakup = aircraft.get<StructuralBreakupState>();
        REQUIRE(breakup != nullptr);
        CHECK(breakup->last_breakup_event_id != 0);

        const RecentEngagementEvents recent = store.export_recent_events_sorted();
        REQUIRE(recent.structural_breakup_events.size() == 1);
        REQUIRE(recent.platform_consequence_events.size() == 1);
        const StructuralBreakupEvent &structural = recent.structural_breakup_events[0];
        const PlatformConsequenceEvent &consequence = recent.platform_consequence_events[0];

        CHECK(consequence.header.stage == "platform_consequence");
        CHECK(consequence.header.parent_event_id == structural.header.event_id);
        CHECK(consequence.header.chain_id == structural.header.chain_id);
        CHECK(consequence.header.producer_node_id == "damage_system.structural_consequence");
        CHECK(consequence.header.consumer_visibility == "diagnostics_only");
        CHECK(consequence.mobility_capability_before == doctest::Approx(1.0));
        CHECK(consequence.mobility_capability_after == doctest::Approx(0.25));
        CHECK(consequence.loss_state_from == "combat_capable");
        CHECK(consequence.loss_state_to == "mobility_kill");
        CHECK(consequence.forced_landing);
        CHECK(consequence.engine_delta == doctest::Approx(-0.70));
        CHECK(consequence.fuel_leak_delta == doctest::Approx(0.30));
        CHECK(aircraft.is_alive());

        world.progress(1.0 / 60.0);

        const RecentEngagementEvents after_second_tick = store.export_recent_events_sorted();
        CHECK(after_second_tick.structural_breakup_events.size() == 1);
        CHECK(after_second_tick.platform_consequence_events.size() == 1);
    }

} // TEST_SUITE

TEST_SUITE("structural_failure_break_modes") {

    TEST_CASE("controlled wing spar failure produces wing_loss events") {
        ComponentDamageState damage{};
        set_component_damage(damage, "wing_spar_center", 0.20, "puncture");

        const StructuralStepResult result = run_single_aircraft_structural_step(damage);

        CHECK(result.state.breakup_state == StructuralBreakupPhase::PartialDetachment);
        CHECK(structural_breakup_has_mode(result.state, StructuralBreakMode::WingLoss));
        CHECK_FALSE(result.state.airframe_breakup);
        REQUIRE(result.events.size() == 2);
        CHECK(result.events[0].break_mode == "wing_loss");
        CHECK(result.events[0].detached_part_ref == "left_wing");
        CHECK(result.events[1].break_mode == "wing_loss");
        CHECK(result.events[1].detached_part_ref == "right_wing");
    }

    TEST_CASE("near-field cumulative wing damage writes wing_loss event") {
        ComponentDamageState damage{};
        set_component_damage(damage, "wing_spar_center_left_inner_wing_segment", 1.00, "none");
        set_component_damage(damage, "left_aileron_actuator", 0.94, "cut");
        set_component_damage(damage, "left_wing_fuel_cell", 0.915, "cut");

        const StructuralStepResult result = run_single_aircraft_structural_step(damage);

        CHECK(result.state.breakup_state == StructuralBreakupPhase::PartialDetachment);
        CHECK(structural_breakup_has_group(result.state, StructuralBreakGroup::WingLeft));
        CHECK_FALSE(structural_breakup_has_group(result.state, StructuralBreakGroup::WingRight));
        REQUIRE(result.events.size() == 1);
        CHECK(result.events[0].break_mode == "wing_loss");
        CHECK(result.events[0].detached_part_ref == "left_wing");
    }

    TEST_CASE("controlled stabilator failure produces tail_loss event") {
        ComponentDamageState damage{};
        set_component_damage(damage, "left_horizontal_tail_actuator_or_surface_component", 0.10,
                             "cut");

        const StructuralStepResult result = run_single_aircraft_structural_step(damage);

        CHECK(result.state.breakup_state == StructuralBreakupPhase::PartialDetachment);
        CHECK(structural_breakup_has_mode(result.state, StructuralBreakMode::TailLoss));
        CHECK_FALSE(result.state.airframe_breakup);
        REQUIRE(result.events.size() == 1);
        CHECK(result.events[0].breakup_state == "partial_detachment");
        CHECK(result.events[0].break_mode == "tail_loss");
        CHECK(result.events[0].detached_part_ref == "left_stabilator");
        CHECK(result.events[0].detached_part_count == 1);
    }

    TEST_CASE("controlled engine core failure produces engine_detach event") {
        ComponentDamageState damage{};
        set_component_damage(damage, "engine_core", 0.10, "structural_weakening");

        const StructuralStepResult result = run_single_aircraft_structural_step(damage);

        CHECK(result.state.breakup_state == StructuralBreakupPhase::PartialDetachment);
        CHECK(structural_breakup_has_mode(result.state, StructuralBreakMode::EngineDetach));
        CHECK_FALSE(result.state.airframe_breakup);
        REQUIRE(result.events.size() == 1);
        CHECK(result.events[0].breakup_state == "partial_detachment");
        CHECK(result.events[0].break_mode == "engine_detach");
        CHECK(result.events[0].detached_part_ref == "engine_core");
        CHECK(result.events[0].detached_part_count == 1);
    }

    TEST_CASE("controlled fuselage carrythrough failure produces fuselage_rupture event") {
        ComponentDamageState damage{};
        set_component_damage(damage, "wing_spar_center_carrythrough_segment", 0.10, "cut");

        const StructuralStepResult result = run_single_aircraft_structural_step(damage);

        CHECK(result.state.breakup_state == StructuralBreakupPhase::PartialDetachment);
        CHECK(structural_breakup_has_mode(result.state, StructuralBreakMode::FuselageRupture));
        CHECK_FALSE(result.state.airframe_breakup);
        REQUIRE(result.events.size() == 1);
        CHECK(result.events[0].breakup_state == "partial_detachment");
        CHECK(result.events[0].break_mode == "fuselage_rupture");
        CHECK(result.events[0].detached_part_ref == "center_fuselage");
        CHECK(result.events[0].detached_part_count == 1);
    }

    TEST_CASE("three structural families produce multi_axis full_breakup event") {
        ComponentDamageState damage{};
        set_component_damage(damage, "wing_spar_center", 0.20, "puncture");
        set_component_damage(damage, "engine_core", 0.10, "structural_weakening");
        set_component_damage(damage, "center_fuselage_fuel_cell", 0.20, "blast_deformation");

        const StructuralStepResult result = run_single_aircraft_structural_step(damage);

        CHECK(result.state.breakup_state == StructuralBreakupPhase::FullBreakup);
        CHECK(structural_breakup_has_mode(result.state, StructuralBreakMode::MultiAxis));
        CHECK(result.state.airframe_breakup);
        REQUIRE(result.events.size() == 5);
        const StructuralBreakupEvent &multi_axis = result.events.back();
        CHECK(multi_axis.breakup_state == "full_breakup");
        CHECK(multi_axis.break_mode == "multi_axis");
        CHECK(multi_axis.detached_part_ref == "multi_axis");
        CHECK(multi_axis.airframe_breakup);
    }

    TEST_CASE("no-damage baseline produces zero structural breakup events") {
        const StructuralStepResult result =
            run_single_aircraft_structural_step(ComponentDamageState{});

        CHECK(result.state.breakup_state == StructuralBreakupPhase::Intact);
        CHECK(result.state.active_break_modes == 0u);
        CHECK(result.events.empty());
    }

    TEST_CASE("wing_loss remains irreversible after component integrity is restored") {
        flecs::world world;
        world.component<ComponentDamageState>();
        world.component<StructuralBreakupState>();
        world.component<KeyEntity>();
        CapturingStructuralRecorder recorder;
        world.set<EngagementEventRecorderRef>({&recorder});
        register_structural_failure_system(world);

        ComponentDamageState damaged{};
        set_component_damage(damaged, "wing_spar_center", 0.20, "puncture");
        auto aircraft =
            world.entity().set<KeyEntity>({UnitType::Aircraft}).set<ComponentDamageState>(damaged);

        world.progress(1.0 / 60.0);
        REQUIRE(recorder.structural_events.size() == 2);

        ComponentDamageState restored{};
        set_component_damage(restored, "wing_spar_center", 1.0, "puncture");
        aircraft.set<ComponentDamageState>(restored);

        world.progress(1.0 / 60.0);

        const StructuralBreakupState *state = aircraft.get<StructuralBreakupState>();
        REQUIRE(state != nullptr);
        CHECK(state->breakup_state == StructuralBreakupPhase::PartialDetachment);
        CHECK(structural_breakup_has_mode(*state, StructuralBreakMode::WingLoss));
        CHECK(structural_breakup_has_group(*state, StructuralBreakGroup::WingLeft));
        CHECK(structural_breakup_has_group(*state, StructuralBreakGroup::WingRight));
        CHECK(recorder.structural_events.size() == 2);
    }

} // TEST_SUITE

TEST_SUITE("structural_failure_events") {

    TEST_CASE("ECS system writes structural breakup events only for new group transitions") {
        flecs::world world;
        world.component<ComponentDamageState>();
        world.component<StructuralBreakupState>();
        world.component<KeyEntity>();
        CapturingStructuralRecorder recorder;
        world.set<EngagementEventRecorderRef>({&recorder});
        register_structural_failure_system(world);

        ComponentDamageState damage{};
        set_component_damage(damage, "wing_spar_center", 0.20, "puncture");
        auto aircraft =
            world.entity().set<KeyEntity>({UnitType::Aircraft}).set<ComponentDamageState>(damage);

        world.progress(1.0 / 60.0);
        REQUIRE(recorder.structural_events.size() == 2);
        CHECK(recorder.structural_events[0].breakup_state == "partial_detachment");
        CHECK(recorder.structural_events[0].break_mode == "wing_loss");
        CHECK(recorder.structural_events[0].detached_part_ref == "left_wing");
        CHECK(recorder.structural_events[0].detached_part_count == 2);
        CHECK(recorder.structural_events[1].break_mode == "wing_loss");
        CHECK(recorder.structural_events[1].detached_part_ref == "right_wing");
        CHECK(recorder.structural_events[1].detached_part_count == 2);
        CHECK(aircraft.get<StructuralBreakupState>() != nullptr);

        world.progress(1.0 / 60.0);
        CHECK(recorder.structural_events.size() == 2);

        ComponentDamageState damage_with_engine = damage;
        set_component_damage(damage_with_engine, "engine_core", 0.10, "structural_weakening");
        aircraft.set<ComponentDamageState>(damage_with_engine);

        world.progress(1.0 / 60.0);
        REQUIRE(recorder.structural_events.size() == 3);
        CHECK(recorder.structural_events[2].break_mode == "engine_detach");
        CHECK(recorder.structural_events[2].detached_part_ref == "engine_core");
        CHECK(recorder.structural_events[2].detached_part_count == 3);

        world.progress(1.0 / 60.0);
        CHECK(recorder.structural_events.size() == 3);
    }

    TEST_CASE("undamaged aircraft writes no structural breakup events") {
        flecs::world world;
        world.component<ComponentDamageState>();
        world.component<StructuralBreakupState>();
        world.component<KeyEntity>();
        CapturingStructuralRecorder recorder;
        world.set<EngagementEventRecorderRef>({&recorder});
        register_structural_failure_system(world);

        auto aircraft = world.entity()
                            .set<KeyEntity>({UnitType::Aircraft})
                            .set<ComponentDamageState>(ComponentDamageState{});

        world.progress(1.0 / 60.0);

        CHECK(recorder.structural_events.empty());
        const StructuralBreakupState *state = aircraft.get<StructuralBreakupState>();
        REQUIRE(state != nullptr);
        CHECK(state->breakup_state == StructuralBreakupPhase::Intact);
    }

    TEST_CASE("multi-axis transition writes synthetic structural breakup event") {
        flecs::world world;
        world.component<ComponentDamageState>();
        world.component<StructuralBreakupState>();
        world.component<KeyEntity>();
        CapturingStructuralRecorder recorder;
        world.set<EngagementEventRecorderRef>({&recorder});
        register_structural_failure_system(world);

        ComponentDamageState damage{};
        set_component_damage(damage, "wing_spar_center", 0.20, "puncture");
        set_component_damage(damage, "engine_core", 0.10, "structural_weakening");
        set_component_damage(damage, "center_fuselage_fuel_cell", 0.20, "blast_deformation");
        world.entity().set<KeyEntity>({UnitType::Aircraft}).set<ComponentDamageState>(damage);

        world.progress(1.0 / 60.0);

        REQUIRE(recorder.structural_events.size() == 5);
        const StructuralBreakupEvent &multi_axis = recorder.structural_events.back();
        CHECK(multi_axis.breakup_state == "full_breakup");
        CHECK(multi_axis.break_mode == "multi_axis");
        CHECK(multi_axis.airframe_breakup);
    }

    TEST_CASE("event store assigns structural breakup cause from recent component damage") {
        flecs::world world;
        SimulationKernelEngagementEventStore store(world);
        constexpr std::uint64_t target_id = 42;

        ComponentDamageEvent damage_event{};
        damage_event.header.source_time_s = 1.0;
        damage_event.component_name = "engine_core";
        damage_event.component_system = "engine";
        damage_event.failure_mode = "structural_weakening";
        const std::uint64_t component_event_id = store.record_component_damage_event({
            .target_id = target_id,
            .event = damage_event,
        });

        StructuralBreakupEvent breakup_event{};
        breakup_event.header.source_time_s = 1.1;
        breakup_event.breakup_state = "partial_detachment";
        breakup_event.break_mode = "engine_detach";
        breakup_event.detached_part_ref = "engine_core";
        const std::uint64_t breakup_event_id = store.record_structural_breakup_event({
            .target_id = target_id,
            .contributing_component_names = {"engine_core"},
            .event = breakup_event,
        });

        const RecentEngagementEvents recent = store.export_recent_events_sorted();
        REQUIRE(recent.structural_breakup_events.size() == 1);
        const StructuralBreakupEvent &recorded = recent.structural_breakup_events[0];
        REQUIRE(recent.component_damage_events.size() == 1);
        const ComponentDamageEvent &recorded_damage = recent.component_damage_events[0];
        CHECK(recorded.cause_event_id == component_event_id);
        CHECK(recorded.header.parent_event_id == component_event_id);
        CHECK(recorded.header.chain_id == recorded_damage.header.chain_id);
        CHECK(recorded.header.chain_id != breakup_event_id);
        CHECK(recorded.header.stage == "structural_breakup");
        CHECK(recorded.header.producer_node_id == "damage_system.structural_failure");
    }

} // TEST_SUITE
