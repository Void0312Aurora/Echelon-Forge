from __future__ import annotations

from tests.architecture.runtime_facade.helpers import *
from tests.support.xmacro_text import expand_binding_field_incs
from tests.support.xmacro_text import expand_header_field_incs


def test_wp24_task_order_maintained_batch_contract_has_runtime_facade_binding_wiring_while_compatibility_shells_are_removed() -> None:
  contracts_text = (RUNTIME_CONTRACTS / "world_batch_contracts.h").read_text(encoding="utf-8")
  facade_header = (RUNTIME_FACADE / "runtime_facade.h").read_text(encoding="utf-8")
  # ObservationBatchRequest/TaskingBatchRequest/ObservationBatchPacket/
  # TaskingBatchPacket field blocks are schema-owned (I31): expand the
  # X-macro #include lines so this file's source-text section splits keep
  # matching the compiled struct/binding shape instead of the #include
  # line and the named-variable nb::class_<T> binding declaration style.
  facade_types = expand_header_field_incs(
    (RUNTIME_FACADE / "runtime_facade_types.h").read_text(encoding="utf-8")
  )
  facade_cpp = runtime_facade_source_text()
  bindings_runtime = expand_binding_field_incs(RUNTIME_BINDINGS.read_text(encoding="utf-8"))
  runtime_header = WORLD_BATCH_RUNTIME_H.read_text(encoding="utf-8")
  runtime_header_single_line = " ".join(runtime_header.split())
  facade_header_single_line = " ".join(facade_header.split())

  assert "struct TaskOrderMaintainedBatchContract {" in contracts_text
  assert "struct WorldTaskOrderMaintainedAssignment {" in contracts_text
  assert "struct WorldTaskOrderAssignment" not in contracts_text
  assert "WorldTaskOrderCompatibilityAssignment" not in contracts_text

  assert "void set_task_orders_maintained_batch(" in runtime_header
  assert (
    "std::vector<TaskOrderMaintainedBatchContract> get_task_orders_maintained_batch("
    in runtime_header_single_line
  )
  assert "void set_mission_commands_maintained_batch(" in runtime_header
  assert "std::vector<MissionCommandMaintainedBatchContract>" in runtime_header
  assert "get_mission_commands_maintained_batch(" in runtime_header
  assert "void set_leader_intents_maintained_batch(" in runtime_header
  assert "std::vector<LeaderIntentMaintainedBatchContract>" in runtime_header
  assert "get_leader_intents_maintained_batch(" in runtime_header
  assert "void set_pilot_reports_maintained_batch(" in runtime_header
  assert "std::vector<PilotReportMaintainedBatchContract>" in runtime_header
  assert "get_pilot_reports_maintained_batch(" in runtime_header
  assert "void set_task_orders_batch(" not in runtime_header
  assert "std::vector<TaskOrder> get_task_orders_batch(" not in runtime_header
  assert "void set_task_orders_compatibility_batch(" not in runtime_header
  assert "std::vector<TaskOrder> get_task_orders_compatibility_batch(" not in runtime_header

  assert "void set_task_orders_maintained_batch(" in facade_header
  assert (
    "std::vector<TaskOrderMaintainedBatchContract> get_task_orders_maintained_batch("
    in facade_header_single_line
  )
  assert "void set_mission_commands_maintained_batch(" in facade_header
  assert "get_mission_commands_maintained_batch(" in facade_header
  assert "void set_leader_intents_maintained_batch(" in facade_header
  assert "get_leader_intents_maintained_batch(" in facade_header
  assert "void set_pilot_reports_maintained_batch(" in facade_header
  assert "get_pilot_reports_maintained_batch(" in facade_header
  assert "void set_task_orders_batch(" not in facade_header
  assert "std::vector<TaskOrder> get_task_orders_batch(" not in facade_header
  assert "void set_task_orders_compatibility_batch(" not in facade_header
  assert "std::vector<TaskOrder> get_task_orders_compatibility_batch(" not in facade_header
  assert "void set_mission_commands_batch(" not in facade_header
  assert "std::vector<MissionCommand> get_mission_commands_batch(" not in facade_header
  assert "void set_leader_intents_batch(" not in facade_header
  assert "std::vector<LeaderIntent> get_leader_intents_batch(" not in facade_header
  assert "void set_pilot_reports_batch(" not in facade_header
  assert "std::vector<PilotReport> get_pilot_reports_batch(" not in facade_header

  observation_request_section = facade_types.split("struct ObservationBatchRequest", 1)[1].split("struct TaskingBatchRequest", 1)[0]
  tasking_request_section = facade_types.split("struct TaskingBatchRequest", 1)[1].split("struct EngagementBatchRequest", 1)[0]
  execution_request_section = facade_types.split("struct ExecutionBatchStepRequest", 1)[1].split("struct DeviceResidentOutputDescriptor", 1)[0]
  assert "bool include_task_orders = false;" not in observation_request_section
  assert "bool include_task_order_contracts = false;" not in observation_request_section
  assert "bool include_mission_commands = false;" not in observation_request_section
  assert "bool include_leader_intents = false;" not in observation_request_section
  assert "bool include_pilot_reports = false;" not in observation_request_section
  assert "bool include_mission_command_contracts = false;" not in observation_request_section
  assert "bool include_leader_intent_contracts = false;" not in observation_request_section
  assert "bool include_pilot_report_contracts = false;" not in observation_request_section
  assert "bool include_task_order_contracts = false;" in tasking_request_section
  assert "bool include_mission_command_contracts = false;" in tasking_request_section
  assert "bool include_leader_intent_contracts = false;" in tasking_request_section
  assert "bool include_pilot_report_contracts = false;" in tasking_request_section
  assert "bool include_mission_commands = false;" not in tasking_request_section
  assert "bool include_leader_intents = false;" not in tasking_request_section
  assert "bool include_pilot_reports = false;" not in tasking_request_section
  assert "bool include_task_orders = false;" not in execution_request_section
  assert "bool include_task_order_contracts = false;" not in execution_request_section
  assert "bool include_mission_commands = false;" not in execution_request_section
  assert "bool include_leader_intents = false;" not in execution_request_section
  assert "bool include_pilot_reports = false;" not in execution_request_section
  assert "bool include_mission_command_contracts = false;" not in execution_request_section
  assert "bool include_leader_intent_contracts = false;" not in execution_request_section
  assert "bool include_pilot_report_contracts = false;" not in execution_request_section

  observation_packet_section = facade_types.split("struct ObservationBatchPacket", 1)[1].split("struct EngagementEventPacket", 1)[0]
  tasking_packet_section = facade_types.split("struct TaskingBatchPacket", 1)[1].split("struct ExecutionBatchStepResult", 1)[0]
  assert "std::vector<TaskOrderMaintainedBatchContract> task_order_contracts;" not in observation_packet_section
  assert "std::vector<MissionCommand> mission_commands;" not in observation_packet_section
  assert "std::vector<LeaderIntent> leader_intents;" not in observation_packet_section
  assert "std::vector<PilotReport> pilot_reports;" not in observation_packet_section
  assert "std::vector<TaskOrder> task_orders;" not in observation_packet_section
  assert "std::vector<TaskOrderMaintainedBatchContract> task_order_contracts;" in tasking_packet_section
  assert "std::vector<MissionCommandMaintainedBatchContract> mission_command_contracts;" in tasking_packet_section
  assert "std::vector<LeaderIntentMaintainedBatchContract> leader_intent_contracts;" in tasking_packet_section
  assert "std::vector<PilotReportMaintainedBatchContract> pilot_report_contracts;" in tasking_packet_section
  assert "std::vector<MissionCommand> mission_commands;" not in tasking_packet_section
  assert "std::vector<LeaderIntent> leader_intents;" not in tasking_packet_section
  assert "std::vector<PilotReport> pilot_reports;" not in tasking_packet_section
  assert '"facade_tasking_packet"' in tasking_packet_section
  assert "kPolicySourceLabelFacadeObservationPacket" not in tasking_packet_section

  observation_request_helper_section = facade_cpp.split("observation_request_from_step_request", 1)[1].split("tasking_request_from_step_request", 1)[0]
  assert ".include_task_order_contracts = request.include_task_order_contracts," not in observation_request_helper_section
  assert "tasking_request_from_step_request" in facade_cpp
  tasking_request_helper_section = facade_cpp.split("tasking_request_from_step_request", 1)[1].split("next_snapshot_version", 1)[0]
  assert ".include_task_order_contracts = request.include_task_order_contracts," not in tasking_request_helper_section
  assert ".include_mission_commands = request.include_mission_commands," not in tasking_request_helper_section
  assert ".include_leader_intents = request.include_leader_intents," not in tasking_request_helper_section
  assert ".include_pilot_reports = request.include_pilot_reports," not in tasking_request_helper_section
  assert ".include_mission_command_contracts = request.include_mission_command_contracts," not in tasking_request_helper_section
  assert ".include_leader_intent_contracts = request.include_leader_intent_contracts," not in tasking_request_helper_section
  assert ".include_pilot_report_contracts = request.include_pilot_report_contracts," not in tasking_request_helper_section

  export_vector_overload_section = facade_cpp.split("RuntimeFacade::export_observation_packet(const std::vector<WorldEntityRef> &refs) const", 1)[1].split("RuntimeFacade::export_observation_packet(const ObservationBatchRequest &request) const", 1)[0]
  assert ".include_task_orders = true," not in export_vector_overload_section
  assert ".include_task_order_contracts = true," not in export_vector_overload_section

  build_observation_packet_section = facade_cpp.split("RuntimeFacade::build_observation_packet", 1)[1].split("RuntimeFacade::build_tasking_packet", 1)[0]
  assert "if (request.include_task_order_contracts)" not in build_observation_packet_section
  assert "packet.task_order_contracts = runtime_->get_task_orders_maintained_batch(request.refs);" not in build_observation_packet_section
  assert "packet.mission_commands = runtime_->get_mission_commands_batch(request.refs);" not in build_observation_packet_section
  assert "if (request.include_task_orders)" not in build_observation_packet_section
  assert "runtime_->get_task_orders_batch(" not in build_observation_packet_section
  assert "runtime_->get_task_orders_compatibility_batch(request.refs);" not in build_observation_packet_section
  build_tasking_packet_section = facade_cpp.split("RuntimeFacade::build_tasking_packet", 1)[1]
  assert "if (request.include_task_order_contracts)" in build_tasking_packet_section
  assert "if (request.include_mission_command_contracts)" in build_tasking_packet_section
  assert "if (request.include_leader_intent_contracts)" in build_tasking_packet_section
  assert "if (request.include_pilot_report_contracts)" in build_tasking_packet_section
  assert "if (request.include_mission_commands)" not in build_tasking_packet_section
  assert "if (request.include_leader_intents)" not in build_tasking_packet_section
  assert "if (request.include_pilot_reports)" not in build_tasking_packet_section
  assert "packet.task_order_contracts = runtime_->get_task_orders_maintained_batch(request.refs);" in build_tasking_packet_section
  assert "packet.mission_command_contracts =" in build_tasking_packet_section
  assert "runtime_->get_mission_commands_maintained_batch(request.refs);" in build_tasking_packet_section
  assert "packet.leader_intent_contracts =" in build_tasking_packet_section
  assert "runtime_->get_leader_intents_maintained_batch(request.refs);" in build_tasking_packet_section
  assert "packet.pilot_report_contracts =" in build_tasking_packet_section
  assert "runtime_->get_pilot_reports_maintained_batch(request.refs);" in build_tasking_packet_section
  assert "packet.mission_commands = runtime_->get_mission_commands_batch(request.refs);" not in build_tasking_packet_section
  assert "packet.leader_intents = runtime_->get_leader_intents_batch(request.refs);" not in build_tasking_packet_section
  assert "packet.pilot_reports = runtime_->get_pilot_reports_batch(request.refs);" not in build_tasking_packet_section

  assert '.def_rw("order", &WorldTaskOrderAssignment::order);' not in bindings_runtime
  assert '"set_task_orders_batch"' not in bindings_runtime
  assert '"get_task_orders_batch"' not in bindings_runtime
  assert '"set_task_orders_compatibility_batch"' not in bindings_runtime
  assert '"get_task_orders_compatibility_batch"' not in bindings_runtime
  facade_binding_section = bindings_runtime.split('nb::class_<RuntimeFacade>(m, "RuntimeFacade")', 1)[1]
  assert '"set_mission_commands_batch"' not in facade_binding_section
  assert '"get_mission_commands_batch"' not in facade_binding_section
  assert '"set_leader_intents_batch"' not in facade_binding_section
  assert '"get_leader_intents_batch"' not in facade_binding_section
  assert '"set_pilot_reports_batch"' not in facade_binding_section
  assert '"get_pilot_reports_batch"' not in facade_binding_section
  assert '"WorldTaskOrderAssignment"' not in bindings_runtime
  assert '"WorldTaskOrderCompatibilityAssignment"' not in bindings_runtime
  # ObservationBatchRequest/TaskingBatchRequest/ObservationBatchPacket/
  # TaskingBatchPacket are schema-owned as of I31 and now declare their
  # nb::class_<T> via a named local variable (matching the established
  # I26 macro-binding style) instead of an inline fluent
  # nb::class_<T>(m, "T") chain, so these section markers only match on
  # the type-only prefix that both binding styles share.
  observation_request_binding_section = bindings_runtime.split('nb::class_<ObservationBatchRequest>', 1)[1].split('nb::class_<TaskingBatchRequest>', 1)[0]
  tasking_request_binding_section = bindings_runtime.split('nb::class_<TaskingBatchRequest>', 1)[1].split('nb::class_<EngagementBatchRequest>(m, "EngagementBatchRequest")', 1)[0]
  observation_packet_binding_section = bindings_runtime.split('nb::class_<ObservationBatchPacket>', 1)[1].split('nb::class_<TaskingBatchPacket>', 1)[0]
  tasking_packet_binding_section = bindings_runtime.split('nb::class_<TaskingBatchPacket>', 1)[1].split('nb::class_<EngagementEventPacket>(m, "EngagementEventPacket")', 1)[0]
  assert '"include_task_order_contracts"' not in observation_request_binding_section
  assert '"include_task_order_contracts"' in tasking_request_binding_section
  assert '"include_mission_command_contracts"' in tasking_request_binding_section
  assert '"include_leader_intent_contracts"' in tasking_request_binding_section
  assert '"include_pilot_report_contracts"' in tasking_request_binding_section
  assert '"include_mission_commands"' not in tasking_request_binding_section
  assert '"include_leader_intents"' not in tasking_request_binding_section
  assert '"include_pilot_reports"' not in tasking_request_binding_section
  assert '"task_order_contracts"' not in observation_packet_binding_section
  assert '"task_order_contracts"' in tasking_packet_binding_section
  assert '"mission_command_contracts"' in tasking_packet_binding_section
  assert '"leader_intent_contracts"' in tasking_packet_binding_section
  assert '"pilot_report_contracts"' in tasking_packet_binding_section
  assert '"mission_commands"' not in tasking_packet_binding_section
  assert '"leader_intents"' not in tasking_packet_binding_section
  assert '"pilot_reports"' not in tasking_packet_binding_section
  assert '"include_task_orders"' not in bindings_runtime
  assert '"task_orders"' not in bindings_runtime
  assert '"include_mission_commands"' not in bindings_runtime
  assert '"include_leader_intents"' not in bindings_runtime
  assert '"include_pilot_reports"' not in bindings_runtime
  assert '"TaskingBatchRequest"' in bindings_runtime
  assert '"TaskingBatchPacket"' in bindings_runtime
  assert '"export_tasking_packet"' in bindings_runtime
  assert 'nb::class_<TaskOrderMaintainedBatchContract>(m, "TaskOrderMaintainedBatchContract")' in bindings_runtime
  assert 'nb::class_<MissionCommandMaintainedBatchContract>(' in bindings_runtime
  assert 'nb::class_<LeaderIntentMaintainedBatchContract>(' in bindings_runtime
  assert 'nb::class_<PilotReportMaintainedBatchContract>(' in bindings_runtime
  assert 'nb::class_<WorldMissionCommandMaintainedAssignment>(' in bindings_runtime
  assert 'nb::class_<WorldTaskOrderMaintainedAssignment>(' in bindings_runtime
  assert 'nb::class_<WorldLeaderIntentMaintainedAssignment>(' in bindings_runtime
  assert 'nb::class_<WorldPilotReportMaintainedAssignment>(' in bindings_runtime
  assert '"set_mission_commands_maintained_batch"' in bindings_runtime
  assert '"get_mission_commands_maintained_batch"' in bindings_runtime
  assert '"set_task_orders_maintained_batch"' in bindings_runtime
  assert '"get_task_orders_maintained_batch"' in bindings_runtime
  assert '"set_leader_intents_maintained_batch"' in bindings_runtime
  assert '"get_leader_intents_maintained_batch"' in bindings_runtime
  assert '"set_pilot_reports_maintained_batch"' in bindings_runtime
  assert '"get_pilot_reports_maintained_batch"' in bindings_runtime

def test_wp24_python_maintained_observation_consumers_do_not_read_compatibility_task_orders() -> None:
  multi_agent_runtime = (
    REPO_ROOT / "python" / "rl" / "runtime" / "multi_agent_runtime.py"
  ).read_text(encoding="utf-8")
  world_batch_vec_env = world_batch_vec_env_source_text()
  cooperative_vec_env = (
    REPO_ROOT / "python" / "rl" / "runtime" / "cooperative_world_batch_vec_env.py"
  ).read_text(encoding="utf-8")

  export_packet_section = multi_agent_runtime.split("def export_packet(", 1)[1].split("def export_tasking_packet(", 1)[0]
  assert "include_mission_commands" not in export_packet_section
  assert "include_task_order_contracts" not in export_packet_section
  assert "include_mission_command_contracts: bool = True" in multi_agent_runtime
  assert "include_task_order_contracts: bool = False" in multi_agent_runtime
  assert "include_leader_intent_contracts: bool = False" in multi_agent_runtime
  assert "include_pilot_report_contracts: bool = False" in multi_agent_runtime
  assert "request.include_mission_command_contracts" in multi_agent_runtime
  assert "request.include_leader_intent_contracts" in multi_agent_runtime
  assert "request.include_pilot_report_contracts" in multi_agent_runtime
  assert "request.include_task_orders = False" not in multi_agent_runtime
  assert "ef_py.TaskingBatchRequest" in multi_agent_runtime
  assert "return self.runtime.export_tasking_packet(request)" in multi_agent_runtime
  assert "_ObservationPacketCompat" not in multi_agent_runtime
  assert "_TaskingPacketCompat" not in multi_agent_runtime
  assert "get_agent_observations_batch" not in multi_agent_runtime
  assert "get_instrument_states_batch" not in multi_agent_runtime
  assert "get_mission_commands_maintained_batch" not in multi_agent_runtime
  assert ".task_orders" not in multi_agent_runtime

  for source in (world_batch_vec_env, cooperative_vec_env):
    assert "include_task_orders=False" not in source
    assert ".task_orders" not in source

def test_wp24_python_command_chain_business_writes_use_maintained_contracts() -> None:
  adapter = (
    REPO_ROOT / "python" / "rl" / "runtime" / "world_batch" / "adapter.py"
  ).read_text(encoding="utf-8")
  command_chain_cache = (
    REPO_ROOT / "python" / "rl" / "runtime" / "world_batch" / "command_chain_cache.py"
  ).read_text(encoding="utf-8")
  world_batch_vec_env = world_batch_vec_env_source_text()
  cooperative_vec_env = (
    REPO_ROOT / "python" / "rl" / "runtime" / "cooperative_world_batch_vec_env.py"
  ).read_text(encoding="utf-8")
  multi_agent_runtime = (
    REPO_ROOT / "python" / "rl" / "runtime" / "multi_agent_runtime.py"
  ).read_text(encoding="utf-8")

  for source in (adapter, world_batch_vec_env, cooperative_vec_env):
    assert "WorldMissionCommandMaintainedAssignment" in source
    assert "WorldLeaderIntentMaintainedAssignment" in source
    assert "WorldPilotReportMaintainedAssignment" in source
    assert "set_mission_commands_maintained_batch" in source
    assert "set_leader_intents_maintained_batch" in source
    assert "set_pilot_reports_maintained_batch" in source

  for forbidden in (
    "WorldMissionCommandAssignment()",
    "WorldLeaderIntentAssignment()",
    "WorldPilotReportAssignment()",
    "set_mission_commands_batch(",
    "set_leader_intents_batch(",
    "set_pilot_reports_batch(",
    "project_world_leader_intent_assignment_transport",
    "project_world_pilot_report_assignment_transport",
  ):
    assert forbidden not in adapter
    assert forbidden not in world_batch_vec_env
    assert forbidden not in cooperative_vec_env

  for required in (
    "mission_command_maintained_batch_contract",
    "leader_intent_maintained_batch_contract",
    "pilot_report_maintained_batch_contract",
    "project_world_mission_command_maintained_assignment",
    "project_world_leader_intent_maintained_assignment",
    "project_world_pilot_report_maintained_assignment",
  ):
    assert required in command_chain_cache

  assert "export_tasking_packet(request)" in multi_agent_runtime
  assert "get_mission_commands_maintained_batch" not in multi_agent_runtime
  assert "get_mission_commands_batch" not in multi_agent_runtime
  assert "mission_commands=[]" not in multi_agent_runtime
  assert 'getattr(tasking_packet, "mission_commands"' not in multi_agent_runtime
