extends Control

const GameBackendClient = preload("res://scripts/net/game_backend_client.gd")
const WorldViewScene = preload("res://scenes/world/WorldView3D.tscn")
const SIDEBAR_WIDTH := 420.0
const MAX_EVENT_LINES := 14
const INPUT_SEND_INTERVAL_S := 0.05
const THROTTLE_STEP_PER_SEC := 0.55
const AXIS_MAGNITUDE := 0.85
const DEFAULT_LOCAL_SESSION_MODE := "prototype_takeoff_patrol_rtb"
const DEFAULT_LOCAL_SCENARIO := "scenarios/combined/cooperative_takeoff_to_cruise_paramroute_navv2_train_v1.json"
const MAX_TASK_CHIPS := 6
const AUTOMATION_CAPTURE_DELAY_S := 2.0

var backend_client
var last_snapshot: Dictionary = {}
var event_lines: Array[String] = []
var input_send_accum_s := 0.0
var throttle_command := 0.82
var gear_command_down := true
var master_arm_enabled := false
var last_terminal_payload: Dictionary = {}

var backend_url_edit: LineEdit
var player_role_option: OptionButton
var connection_value: Label
var session_value: Label
var mission_value: Label
var player_value: Label
var authority_value: Label
var render_status_label: Label
var event_log: RichTextLabel
var input_state_label: Label
var mission_task_value: Label
var mission_phase_value: Label
var mission_command_value: Label
var mission_waypoint_value: Label
var lead_command_box: HBoxContainer
var lead_command_status_label: Label
var mission_sequence_box: HBoxContainer
var mission_history_log: RichTextLabel
var reward_summary_label: Label
var terminal_status_label: Label
var restart_button: Button
var world_view: Node
var automation_enabled := false
var automation_capture_requested := false
var automation_capture_delay_s := AUTOMATION_CAPTURE_DELAY_S
var automation_report_path := ""
var automation_fail_on_missing_player := true
var automation_expected_role := "Lead"
var automation_backend_url := ""
var automation_screenshot_path := ""
var automation_world_screenshot_path := ""


func _ready() -> void:
	_configure_automation_from_environment()
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_build_ui()
	_build_backend_bridge()
	_refresh_status_panel()
	_append_event("Game branch client bootstrapped. Waiting for backend.")


func _process(delta: float) -> void:
	if backend_client != null:
		backend_client.poll()
	_update_local_input_state(delta)
	_process_automation(delta)


func _build_backend_bridge() -> void:
	backend_client = GameBackendClient.new()
	backend_client.status_changed.connect(_on_backend_status_changed)
	backend_client.snapshot_received.connect(_on_snapshot_received)
	backend_client.map_setup_received.connect(_on_map_setup_received)
	backend_client.nav_setup_received.connect(_on_nav_setup_received)
	backend_client.event_received.connect(_on_event_received)
	var target_url: String = automation_backend_url if not automation_backend_url.is_empty() else backend_client.get_target_url()
	backend_url_edit.text = target_url
	backend_client.connect_to_backend(target_url)


func _build_ui() -> void:
	var background := ColorRect.new()
	background.color = Color("08111d")
	background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(background)

	var safe_area := MarginContainer.new()
	safe_area.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	safe_area.add_theme_constant_override("margin_left", 28)
	safe_area.add_theme_constant_override("margin_top", 28)
	safe_area.add_theme_constant_override("margin_right", 28)
	safe_area.add_theme_constant_override("margin_bottom", 28)
	add_child(safe_area)

	var layout := HBoxContainer.new()
	layout.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	layout.size_flags_vertical = Control.SIZE_EXPAND_FILL
	layout.add_theme_constant_override("separation", 24)
	safe_area.add_child(layout)

	var sidebar := PanelContainer.new()
	sidebar.custom_minimum_size = Vector2(SIDEBAR_WIDTH, 0.0)
	sidebar.size_flags_vertical = Control.SIZE_EXPAND_FILL
	sidebar.add_theme_stylebox_override("panel", _panel_style(Color("102033"), Color("2d4f73")))
	layout.add_child(sidebar)

	var sidebar_margin := MarginContainer.new()
	sidebar_margin.add_theme_constant_override("margin_left", 20)
	sidebar_margin.add_theme_constant_override("margin_top", 18)
	sidebar_margin.add_theme_constant_override("margin_right", 20)
	sidebar_margin.add_theme_constant_override("margin_bottom", 18)
	sidebar.add_child(sidebar_margin)

	var sidebar_vbox := VBoxContainer.new()
	sidebar_vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sidebar_vbox.size_flags_vertical = Control.SIZE_EXPAND_FILL
	sidebar_vbox.add_theme_constant_override("separation", 14)
	sidebar_margin.add_child(sidebar_vbox)

	var title_label := _make_label("CMO GAME BRANCH", 28, Color("f4f7fb"))
	sidebar_vbox.add_child(title_label)

	var subtitle_label := _make_label(
		"Godot client shell for the isolated playable line. The backend remains authoritative.",
		14,
		Color("8eb4d7")
	)
	subtitle_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	sidebar_vbox.add_child(subtitle_label)

	sidebar_vbox.add_child(_make_label("Backend URL", 13, Color("70a6d8")))

	backend_url_edit = LineEdit.new()
	backend_url_edit.placeholder_text = "ws://127.0.0.1:8765/game"
	sidebar_vbox.add_child(backend_url_edit)

	sidebar_vbox.add_child(_make_label("Player Aircraft", 13, Color("70a6d8")))
	player_role_option = OptionButton.new()
	player_role_option.add_item("Lead")
	player_role_option.add_item("Wing")
	player_role_option.select(0)
	sidebar_vbox.add_child(player_role_option)

	var buttons := GridContainer.new()
	buttons.columns = 2
	buttons.add_theme_constant_override("h_separation", 10)
	buttons.add_theme_constant_override("v_separation", 10)
	sidebar_vbox.add_child(buttons)

	var connect_button := _make_button("Connect")
	connect_button.pressed.connect(_on_connect_pressed)
	buttons.add_child(connect_button)

	var disconnect_button := _make_button("Disconnect")
	disconnect_button.pressed.connect(_on_disconnect_pressed)
	buttons.add_child(disconnect_button)

	var start_local_button := _make_button("Start Local Session")
	start_local_button.pressed.connect(_on_start_local_pressed)
	buttons.add_child(start_local_button)

	restart_button = _make_button("Restart Mission")
	restart_button.disabled = true
	restart_button.pressed.connect(_on_restart_local_pressed)
	buttons.add_child(restart_button)

	var load_mission_button := _make_button("Load Prototype Mission")
	load_mission_button.pressed.connect(_on_load_prototype_pressed)
	buttons.add_child(load_mission_button)

	sidebar_vbox.add_child(_make_label("Session Status", 16, Color("f4f7fb")))

	var status_grid := GridContainer.new()
	status_grid.columns = 2
	status_grid.add_theme_constant_override("h_separation", 18)
	status_grid.add_theme_constant_override("v_separation", 8)
	sidebar_vbox.add_child(status_grid)

	status_grid.add_child(_make_label("Connection", 13, Color("6f91b0")))
	connection_value = _make_value_label("--")
	status_grid.add_child(connection_value)

	status_grid.add_child(_make_label("Session", 13, Color("6f91b0")))
	session_value = _make_value_label("(none)")
	status_grid.add_child(session_value)

	status_grid.add_child(_make_label("Mission", 13, Color("6f91b0")))
	mission_value = _make_value_label("(none)")
	status_grid.add_child(mission_value)

	status_grid.add_child(_make_label("Player Slot", 13, Color("6f91b0")))
	player_value = _make_value_label("(none)")
	status_grid.add_child(player_value)

	status_grid.add_child(_make_label("Authority", 13, Color("6f91b0")))
	authority_value = _make_value_label("(none)")
	status_grid.add_child(authority_value)

	sidebar_vbox.add_child(_make_label("Mission Flow", 16, Color("f4f7fb")))

	var mission_grid := GridContainer.new()
	mission_grid.columns = 2
	mission_grid.add_theme_constant_override("h_separation", 18)
	mission_grid.add_theme_constant_override("v_separation", 8)
	sidebar_vbox.add_child(mission_grid)

	mission_grid.add_child(_make_label("C2 Task", 13, Color("6f91b0")))
	mission_task_value = _make_value_label("--")
	mission_grid.add_child(mission_task_value)

	mission_grid.add_child(_make_label("Phase", 13, Color("6f91b0")))
	mission_phase_value = _make_value_label("--")
	mission_grid.add_child(mission_phase_value)

	mission_grid.add_child(_make_label("Command", 13, Color("6f91b0")))
	mission_command_value = _make_value_label("--")
	mission_grid.add_child(mission_command_value)

	mission_grid.add_child(_make_label("Waypoint", 13, Color("6f91b0")))
	mission_waypoint_value = _make_value_label("--")
	mission_grid.add_child(mission_waypoint_value)

	sidebar_vbox.add_child(_make_label("Lead Commands", 13, Color("70a6d8")))
	lead_command_box = HBoxContainer.new()
	lead_command_box.alignment = BoxContainer.ALIGNMENT_BEGIN
	lead_command_box.add_theme_constant_override("separation", 8)
	sidebar_vbox.add_child(lead_command_box)

	lead_command_status_label = _make_label("Lead command channel: unavailable", 12, Color("8eb4d7"))
	lead_command_status_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	sidebar_vbox.add_child(lead_command_status_label)

	sidebar_vbox.add_child(_make_label("Task Sequence", 13, Color("70a6d8")))
	mission_sequence_box = HBoxContainer.new()
	mission_sequence_box.alignment = BoxContainer.ALIGNMENT_BEGIN
	mission_sequence_box.add_theme_constant_override("separation", 8)
	sidebar_vbox.add_child(mission_sequence_box)

	sidebar_vbox.add_child(_make_label("Transition Log", 13, Color("70a6d8")))
	mission_history_log = RichTextLabel.new()
	mission_history_log.custom_minimum_size = Vector2(0.0, 124.0)
	mission_history_log.bbcode_enabled = false
	mission_history_log.scroll_following = true
	mission_history_log.add_theme_color_override("default_color", Color("d7e3f0"))
	mission_history_log.add_theme_font_size_override("normal_font_size", 12)
	sidebar_vbox.add_child(mission_history_log)

	sidebar_vbox.add_child(_make_label("Terminal", 16, Color("f4f7fb")))
	terminal_status_label = _make_label("Terminal: running", 13, Color("d7e8f8"))
	terminal_status_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	sidebar_vbox.add_child(terminal_status_label)

	reward_summary_label = _make_label("Reward: waiting", 13, Color("d7e8f8"))
	reward_summary_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	sidebar_vbox.add_child(reward_summary_label)

	sidebar_vbox.add_child(_make_label("Event Log", 16, Color("f4f7fb")))

	event_log = RichTextLabel.new()
	event_log.custom_minimum_size = Vector2(0.0, 260.0)
	event_log.size_flags_vertical = Control.SIZE_EXPAND_FILL
	event_log.bbcode_enabled = false
	event_log.scroll_following = true
	event_log.add_theme_color_override("default_color", Color("dbe7f3"))
	event_log.add_theme_font_size_override("normal_font_size", 13)
	sidebar_vbox.add_child(event_log)

	sidebar_vbox.add_child(_make_label("Controls", 16, Color("f4f7fb")))
	var controls_hint := _make_label(
		"Throttle W/S | Pitch Up/Down | Roll Left/Right | Yaw A/D | G gear | M master arm | Space brake | Enter fire",
		13,
		Color("7ea5c7")
	)
	controls_hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	sidebar_vbox.add_child(controls_hint)

	input_state_label = _make_label("Input: waiting", 13, Color("d7e8f8"))
	input_state_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	sidebar_vbox.add_child(input_state_label)

	var viewport_panel := PanelContainer.new()
	viewport_panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	viewport_panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
	viewport_panel.add_theme_stylebox_override("panel", _panel_style(Color("0d1828"), Color("385a7a")))
	layout.add_child(viewport_panel)

	var viewport_margin := MarginContainer.new()
	viewport_margin.add_theme_constant_override("margin_left", 22)
	viewport_margin.add_theme_constant_override("margin_top", 22)
	viewport_margin.add_theme_constant_override("margin_right", 22)
	viewport_margin.add_theme_constant_override("margin_bottom", 22)
	viewport_panel.add_child(viewport_margin)

	var viewport_vbox := VBoxContainer.new()
	viewport_vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	viewport_vbox.size_flags_vertical = Control.SIZE_EXPAND_FILL
	viewport_vbox.add_theme_constant_override("separation", 18)
	viewport_margin.add_child(viewport_vbox)

	var view_title := _make_label("Operations Deck", 24, Color("f4f7fb"))
	viewport_vbox.add_child(view_title)

	var view_subtitle := _make_label(
		"Scenario JSON zones, nav route markers, and F-16 visuals are rendered here from the authoritative backend payloads.",
		14,
		Color("82a9ca")
	)
	view_subtitle.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	viewport_vbox.add_child(view_subtitle)

	render_status_label = _make_label(
		"No authoritative backend snapshot yet.",
		16,
		Color("eaf4ff")
	)
	render_status_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	viewport_vbox.add_child(render_status_label)

	var world_frame := PanelContainer.new()
	world_frame.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	world_frame.size_flags_vertical = Control.SIZE_EXPAND_FILL
	world_frame.add_theme_stylebox_override("panel", _panel_style(Color("0b121c"), Color("244461")))
	viewport_vbox.add_child(world_frame)

	world_view = WorldViewScene.instantiate()
	if world_view is Control:
		var world_view_control: Control = world_view
		world_view_control.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		world_view_control.size_flags_vertical = Control.SIZE_EXPAND_FILL
	world_frame.add_child(world_view)


func _on_connect_pressed() -> void:
	var url := backend_url_edit.text.strip_edges()
	if url.is_empty():
		_append_event("Backend URL cannot be empty.")
		return

	if backend_client.connect_to_backend(url):
		_append_event("Connecting to %s" % url)
	else:
		_append_event("Connection request failed before socket open.")
	_refresh_status_panel()


func _on_disconnect_pressed() -> void:
	backend_client.disconnect_from_backend()
	_append_event("Disconnect requested.")
	_refresh_status_panel()


func _on_start_local_pressed() -> void:
	var payload := {
		"type": "game_command",
		"command": "start_local_session",
		"payload": {
			"mode": DEFAULT_LOCAL_SESSION_MODE,
			"scenario": DEFAULT_LOCAL_SCENARIO,
			"player_role": _selected_player_role()
		}
	}
	if backend_client.send_json(payload):
		_append_event("Requested local prototype session as %s." % _selected_player_role())
	else:
		_append_event("No connected backend; local session request was not sent.")


func _on_load_prototype_pressed() -> void:
	var payload := {
		"type": "game_command",
		"command": "load_mission_profile",
		"payload": {
			"profile": DEFAULT_LOCAL_SESSION_MODE
		}
	}
	if backend_client.send_json(payload):
		_append_event("Requested prototype mission profile.")
	else:
		_append_event("No connected backend; prototype mission request was not sent.")


func _on_restart_local_pressed() -> void:
	var payload := {
		"type": "game_command",
		"command": "restart_local_session",
		"payload": {
			"player_role": _selected_player_role()
		}
	}
	if backend_client.send_json(payload):
		_append_event("Requested local mission restart as %s." % _selected_player_role())
		last_terminal_payload = {}
		_refresh_status_panel()
	else:
		_append_event("No connected backend; restart request was not sent.")


func _on_backend_status_changed(status_text: String) -> void:
	_append_event("Backend status changed to %s" % status_text)
	if status_text == "connected":
		_request_local_session_start()
	_refresh_status_panel()


func _on_snapshot_received(snapshot: Dictionary) -> void:
	last_snapshot = snapshot
	if bool(snapshot.get("termination", {}).get("terminated", false)) or bool(snapshot.get("termination", {}).get("truncated", false)):
		last_terminal_payload = {
			"reason": str(snapshot.get("termination", {}).get("reason", "terminated")),
			"success": bool(snapshot.get("termination", {}).get("success", false)),
			"reward_total": float(snapshot.get("reward", {}).get("total", 0.0)),
			"reward_summary": snapshot.get("reward", {}).get("summary", []),
			"mission_status": snapshot.get("mission_status", {}),
			"restart_available": true
		}
	_apply_to_world_view("apply_snapshot", snapshot)
	_refresh_status_panel()


func _on_map_setup_received(payload: Dictionary) -> void:
	var zones_variant: Variant = payload.get("zones", [])
	var zone_count: int = zones_variant.size() if typeof(zones_variant) == TYPE_ARRAY else 0
	_append_event("map_setup received (%d zones)" % zone_count)
	_apply_to_world_view("apply_map_setup", payload)


func _on_nav_setup_received(payload: Dictionary) -> void:
	var markers_variant: Variant = payload.get("markers", [])
	var marker_count: int = markers_variant.size() if typeof(markers_variant) == TYPE_ARRAY else 0
	_append_event("nav_setup received (%d markers)" % marker_count)
	_apply_to_world_view("apply_nav_setup", payload)


func _on_event_received(event_payload: Dictionary) -> void:
	var event_name := str(event_payload.get("event", event_payload.get("type", "message")))
	var payload: Variant = event_payload.get("payload", {})
	if event_name == "session_terminal" and typeof(payload) == TYPE_DICTIONARY:
		last_terminal_payload = payload
	if event_name == "lead_command_applied" and typeof(payload) == TYPE_DICTIONARY:
		var label := str(payload.get("label", payload.get("command", "lead_command")))
		_append_event("Lead command applied: %s" % label)
		_refresh_status_panel()
		return
	if (event_name == "lead_command_rejected" or event_name == "lead_command_failed") and typeof(payload) == TYPE_DICTIONARY:
		_append_event("%s %s" % [event_name, JSON.stringify(payload)])
		_refresh_status_panel()
		return
	if typeof(payload) == TYPE_DICTIONARY and not payload.is_empty():
		_append_event("%s %s" % [event_name, JSON.stringify(payload)])
	else:
		_append_event(event_name)
	_refresh_status_panel()


func _issue_lead_command(command_id: String) -> void:
	var payload := {
		"type": "game_command",
		"command": "issue_lead_command",
		"payload": {
			"lead_command": command_id
		}
	}
	if backend_client.send_json(payload):
		_append_event("Requested lead command %s." % command_id)
	else:
		_append_event("No connected backend; lead command was not sent.")


func _refresh_status_panel() -> void:
	if connection_value != null:
		connection_value.text = backend_client.get_status_text() if backend_client != null else "--"

	if session_value != null:
		session_value.text = str(last_snapshot.get("session_id", "(none)"))

	if mission_value != null:
		mission_value.text = str(last_snapshot.get("mission_label", "(none)"))

	if player_value != null:
		var player_entity := str(last_snapshot.get("player_entity_name", ""))
		var role_label := str(last_snapshot.get("player_role_label", ""))
		var player_slot := str(last_snapshot.get("player_slot", "(none)"))
		if not player_entity.is_empty() or not role_label.is_empty():
			player_value.text = "%s | %s | %s" % [
				role_label if not role_label.is_empty() else "--",
				player_entity if not player_entity.is_empty() else "Ownship",
				player_slot
			]
		else:
			player_value.text = player_slot

	if authority_value != null:
		var lead_authority := bool(last_snapshot.get("lead_authority", false))
		var role_label_for_authority := str(last_snapshot.get("player_role_label", ""))
		authority_value.text = "Lead C2" if lead_authority else (
			"Wing execution" if role_label_for_authority == "Wing" else "Aircraft control"
		)

	_refresh_mission_flow_panel()
	_refresh_terminal_panel()

	if render_status_label != null:
		if last_snapshot.is_empty():
			render_status_label.text = "No authoritative backend snapshot yet."
		else:
			var sim_time := float(last_snapshot.get("sim_time_s", 0.0))
			var ownship: Variant = last_snapshot.get("ownship", {})
			var ownship_name := "Ownship"
			var altitude_text := "--"
			var speed_text := "--"
			if typeof(ownship) == TYPE_DICTIONARY:
				ownship_name = str(ownship.get("name", ownship_name))
				if ownship.has("alt_m"):
					altitude_text = "%.1f m" % float(ownship.get("alt_m", 0.0))
				if ownship.has("ias_mps"):
					speed_text = "%.1f m/s" % float(ownship.get("ias_mps", 0.0))
			var role_label_render := str(last_snapshot.get("player_role_label", ""))
			render_status_label.text = "%s%s | T+%.1fs | ALT %s | IAS %s" % [
				("%s " % role_label_render) if not role_label_render.is_empty() else "",
				ownship_name,
				sim_time,
				altitude_text,
				speed_text
			]

	if input_state_label != null:
		var snapshot_control: Variant = last_snapshot.get("control_state", {})
		var source := str(last_snapshot.get("control_source", "local"))
		if typeof(snapshot_control) == TYPE_DICTIONARY and not snapshot_control.is_empty():
			var role_text := str(last_snapshot.get("player_role_label", "Aircraft"))
			var ownship_name := str(last_snapshot.get("player_entity_name", "Ownship"))
			input_state_label.text = (
				"Input (%s | %s %s): pitch %.2f | roll %.2f | yaw %.2f | throttle %.2f | gear %s | brake %s | arm %s | fire %s"
				% [
					source,
					role_text,
					ownship_name,
					float(snapshot_control.get("pitch", 0.0)),
					float(snapshot_control.get("roll", 0.0)),
					float(snapshot_control.get("yaw", 0.0)),
					float(snapshot_control.get("throttle", 0.0)),
					"down" if bool(snapshot_control.get("gear", true)) else "up",
					"on" if bool(snapshot_control.get("brake", false)) else "off",
					"on" if bool(snapshot_control.get("master_arm", false)) else "off",
					"on" if bool(snapshot_control.get("fire_weapon", false)) else "off"
				]
			)
		else:
			input_state_label.text = "Input: waiting for first backend control snapshot"

	if restart_button != null:
		var can_restart := false
		if not last_snapshot.is_empty():
			var termination: Variant = last_snapshot.get("termination", {})
			if typeof(termination) == TYPE_DICTIONARY:
				can_restart = bool(termination.get("terminated", false)) or bool(termination.get("truncated", false))
		if typeof(last_terminal_payload) == TYPE_DICTIONARY and not last_terminal_payload.is_empty():
			can_restart = can_restart or bool(last_terminal_payload.get("restart_available", false))
		restart_button.disabled = not can_restart

	_refresh_lead_command_panel()


func _request_local_session_start() -> void:
	if automation_enabled and player_role_option != null:
		for idx in range(player_role_option.item_count):
			if player_role_option.get_item_text(idx) == automation_expected_role:
				player_role_option.select(idx)
				break
	var payload := {
		"type": "game_command",
		"command": "start_local_session",
		"payload": {
			"mode": DEFAULT_LOCAL_SESSION_MODE,
			"scenario": DEFAULT_LOCAL_SCENARIO,
			"player_role": _selected_player_role()
		}
	}
	if backend_client.send_json(payload):
		_append_event("Requested automatic local session start as %s." % _selected_player_role())
		last_terminal_payload = {}


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		match event.keycode:
			KEY_G:
				gear_command_down = not gear_command_down
				_append_event("Gear command -> %s" % ("down" if gear_command_down else "up"))
			KEY_M:
				master_arm_enabled = not master_arm_enabled
				_append_event("Master arm -> %s" % ("on" if master_arm_enabled else "off"))


func _update_local_input_state(delta: float) -> void:
	if backend_client == null:
		return
	if not backend_client.is_backend_connected():
		return

	if Input.is_key_pressed(KEY_W):
		throttle_command = clampf(throttle_command + THROTTLE_STEP_PER_SEC * delta, 0.0, 1.0)
	if Input.is_key_pressed(KEY_S):
		throttle_command = clampf(throttle_command - THROTTLE_STEP_PER_SEC * delta, 0.0, 1.0)

	input_send_accum_s += delta
	if input_send_accum_s < INPUT_SEND_INTERVAL_S:
		return
	input_send_accum_s = 0.0
	_send_current_input_snapshot()


func _send_current_input_snapshot() -> void:
	var pitch := 0.0
	var roll := 0.0
	var yaw := 0.0

	if Input.is_key_pressed(KEY_UP):
		pitch += AXIS_MAGNITUDE
	if Input.is_key_pressed(KEY_DOWN):
		pitch -= AXIS_MAGNITUDE
	if Input.is_key_pressed(KEY_LEFT):
		roll -= AXIS_MAGNITUDE
	if Input.is_key_pressed(KEY_RIGHT):
		roll += AXIS_MAGNITUDE
	if Input.is_key_pressed(KEY_A):
		yaw -= AXIS_MAGNITUDE
	if Input.is_key_pressed(KEY_D):
		yaw += AXIS_MAGNITUDE

	var payload := {
		"type": "client_input",
		"player_slot": "player_1",
		"tick": Time.get_ticks_msec(),
		"axes": {
			"pitch": pitch,
			"roll": roll,
			"yaw": yaw,
			"throttle": throttle_command
		},
		"toggles": {
			"gear": gear_command_down,
			"brake": Input.is_key_pressed(KEY_SPACE),
			"master_arm": master_arm_enabled,
			"fire_weapon": Input.is_key_pressed(KEY_ENTER),
			"fire_gun": Input.is_key_pressed(KEY_SHIFT)
		}
	}
	backend_client.send_json(payload)


func _append_event(text: String) -> void:
	var stamped := "[%s] %s" % [Time.get_time_string_from_system(), text]
	event_lines.append(stamped)
	while event_lines.size() > MAX_EVENT_LINES:
		event_lines.remove_at(0)

	if event_log == null:
		return

	event_log.clear()
	for line in event_lines:
		event_log.append_text(line + "\n")


func _refresh_mission_flow_panel() -> void:
	var mission_status: Variant = last_snapshot.get("mission_status", {})
	if typeof(mission_status) != TYPE_DICTIONARY:
		if mission_task_value != null:
			mission_task_value.text = "--"
		if mission_phase_value != null:
			mission_phase_value.text = "--"
		if mission_command_value != null:
			mission_command_value.text = "--"
		if mission_waypoint_value != null:
			mission_waypoint_value.text = "--"
		_render_task_sequence([], -1)
		_render_transition_history([])
		return

	if mission_task_value != null:
		mission_task_value.text = str(mission_status.get("c2_task_label", mission_status.get("c2_task", "--")))
	if mission_phase_value != null:
		var phase_text := str(mission_status.get("phase_label", mission_status.get("phase_name", "--")))
		var role_text := str(mission_status.get("player_role_label", ""))
		if not role_text.is_empty():
			mission_phase_value.text = "%s | %s" % [phase_text, role_text]
		else:
			mission_phase_value.text = phase_text
	if mission_command_value != null:
		var command_name := str(mission_status.get("command_name", "--"))
		var command_code := int(mission_status.get("command_code", 0))
		mission_command_value.text = "%s (%d)" % [command_name, command_code]
	if mission_waypoint_value != null:
		var waypoint_total := int(mission_status.get("waypoint_total", 0))
		if waypoint_total > 0:
			mission_waypoint_value.text = "%d/%d" % [
				int(mission_status.get("active_waypoint", 0)),
				waypoint_total
			]
		else:
			mission_waypoint_value.text = "--"

	var sequence_variant: Variant = mission_status.get("task_sequence", [])
	var sequence_index := int(mission_status.get("task_sequence_index", -1))
	if typeof(sequence_variant) == TYPE_ARRAY:
		_render_task_sequence(sequence_variant, sequence_index)
	else:
		_render_task_sequence([], sequence_index)

	var history_variant: Variant = mission_status.get("history", [])
	if typeof(history_variant) == TYPE_ARRAY:
		_render_transition_history(history_variant)
	else:
		_render_transition_history([])


func _refresh_lead_command_panel() -> void:
	if lead_command_box == null:
		return

	for child in lead_command_box.get_children():
		child.queue_free()

	var mission_status: Variant = last_snapshot.get("mission_status", {})
	var lead_available := false
	var command_options: Array = []
	var last_command: Dictionary = {}
	if typeof(mission_status) == TYPE_DICTIONARY:
		lead_available = bool(mission_status.get("lead_commands_available", false))
		var options_variant: Variant = mission_status.get("lead_command_options", [])
		if typeof(options_variant) == TYPE_ARRAY:
			command_options = options_variant
		var last_variant: Variant = mission_status.get("last_lead_command", {})
		if typeof(last_variant) == TYPE_DICTIONARY:
			last_command = last_variant

	if lead_available:
		for option_variant in command_options:
			if typeof(option_variant) != TYPE_DICTIONARY:
				continue
			var option: Dictionary = option_variant
			var command_id := str(option.get("id", ""))
			if command_id.is_empty():
				continue
			var button := _make_button(str(option.get("label", command_id)))
			button.custom_minimum_size = Vector2(0.0, 36.0)
			var enabled := bool(option.get("enabled", true))
			button.disabled = not enabled
			if enabled:
				button.pressed.connect(_issue_lead_command.bind(command_id))
			lead_command_box.add_child(button)
	else:
		var locked_label := _make_label("Lead slot required", 12, Color("7ea5c7"))
		lead_command_box.add_child(locked_label)

	if lead_command_status_label != null:
		if lead_available:
			var unavailable_reasons: Array[String] = []
			for option_variant in command_options:
				if typeof(option_variant) != TYPE_DICTIONARY:
					continue
				var option: Dictionary = option_variant
				if not bool(option.get("enabled", true)):
					var reason := str(option.get("reason", ""))
					if not reason.is_empty():
						unavailable_reasons.append(reason)
			if not last_command.is_empty():
				var label := str(last_command.get("label", last_command.get("command", "--")))
				var current: Variant = last_command.get("current", {})
				var current_text := ""
				if typeof(current) == TYPE_DICTIONARY:
					current_text = "%s / %s" % [
						str(current.get("c2_task", "--")),
						str(current.get("command_name", "--"))
					]
				lead_command_status_label.text = "Lead command channel: active | last %s -> %s" % [
					label,
					current_text if not current_text.is_empty() else "--"
				]
			else:
				lead_command_status_label.text = "Lead command channel: active | no manual command issued"
			if not unavailable_reasons.is_empty():
				lead_command_status_label.text += " | " + " ".join(unavailable_reasons)
		else:
			lead_command_status_label.text = "Lead command channel: unavailable for Wing slot"


func _render_task_sequence(sequence: Array, active_index: int) -> void:
	if mission_sequence_box == null:
		return
	for child in mission_sequence_box.get_children():
		child.queue_free()

	var shown := mini(sequence.size(), MAX_TASK_CHIPS)
	for idx in range(shown):
		var task_name := str(sequence[idx])
		var chip := Label.new()
		chip.text = task_name.trim_prefix("TASK_").replace("_", " ")
		chip.add_theme_font_size_override("font_size", 11)
		chip.add_theme_color_override("font_color", Color("f4f7fb"))
		chip.add_theme_stylebox_override("normal", _task_chip_style(idx, active_index))
		mission_sequence_box.add_child(chip)


func _render_transition_history(history: Array) -> void:
	if mission_history_log == null:
		return
	mission_history_log.clear()
	for idx in range(history.size() - 1, -1, -1):
		var entry_variant: Variant = history[idx]
		if typeof(entry_variant) != TYPE_DICTIONARY:
			continue
		var entry: Dictionary = entry_variant
		var time_text := "%.1fs" % float(entry.get("time_s", 0.0))
		var task_label := str(entry.get("c2_task_label", entry.get("c2_task", "--")))
		var phase_label := str(entry.get("phase_label", entry.get("phase_name", "--")))
		var wp_text := str(entry.get("waypoint_text", "--"))
		var line := "%s  %s / %s" % [time_text, task_label, phase_label]
		if wp_text != "--":
			line += " | WP %s" % wp_text
		mission_history_log.append_text(line + "\n")


func _refresh_terminal_panel() -> void:
	var termination_variant: Variant = last_snapshot.get("termination", {})
	var reward_variant: Variant = last_snapshot.get("reward", {})

	var state_text := "Terminal: running"
	var state_color := Color("89d7a1")
	var reward_text := "Reward: waiting"

	if typeof(termination_variant) == TYPE_DICTIONARY:
		var terminated := bool(termination_variant.get("terminated", false))
		var truncated := bool(termination_variant.get("truncated", false))
		if terminated or truncated:
			var success := bool(termination_variant.get("success", false))
			var reason := str(termination_variant.get("reason", "terminated"))
			var role_label := str(last_snapshot.get("player_role_label", ""))
			var entity_name := str(last_snapshot.get("player_entity_name", ""))
			state_text = "Terminal: %s | %s" % [
				"SUCCESS" if success else "FAILED",
				reason
			]
			if not role_label.is_empty() or not entity_name.is_empty():
				state_text += " | %s %s" % [role_label, entity_name]
			state_color = Color("7fe6b7") if success else Color("ff8d7a")
		elif typeof(last_terminal_payload) == TYPE_DICTIONARY and not last_terminal_payload.is_empty():
			var success_event := bool(last_terminal_payload.get("success", false))
			var reason_event := str(last_terminal_payload.get("reason", "terminated"))
			var role_label_event := str(last_terminal_payload.get("player_role_label", ""))
			var entity_name_event := str(last_terminal_payload.get("player_entity_name", ""))
			state_text = "Terminal: %s | %s" % [
				"SUCCESS" if success_event else "FAILED",
				reason_event
			]
			if not role_label_event.is_empty() or not entity_name_event.is_empty():
				state_text += " | %s %s" % [role_label_event, entity_name_event]
			state_color = Color("7fe6b7") if success_event else Color("ff8d7a")

	if terminal_status_label != null:
		terminal_status_label.text = state_text
		terminal_status_label.add_theme_color_override("font_color", state_color)

	var reward_summary_variant: Variant = {}
	if typeof(reward_variant) == TYPE_DICTIONARY:
		var reward_total := float(reward_variant.get("total", 0.0))
		var summary_list: Variant = reward_variant.get("summary", [])
		reward_text = "Reward total: %.2f" % reward_total
		if typeof(summary_list) == TYPE_ARRAY and not summary_list.is_empty():
			reward_text += " | " + _format_reward_summary(summary_list)
	elif typeof(last_terminal_payload) == TYPE_DICTIONARY and not last_terminal_payload.is_empty():
		reward_text = "Reward total: %.2f" % float(last_terminal_payload.get("reward_total", 0.0))
		var event_summary: Variant = last_terminal_payload.get("reward_summary", [])
		if typeof(event_summary) == TYPE_ARRAY and not event_summary.is_empty():
			reward_text += " | " + _format_reward_summary(event_summary)

	if reward_summary_label != null:
		reward_summary_label.text = reward_text


func _format_reward_summary(summary_list: Array) -> String:
	var parts: Array[String] = []
	for item_variant in summary_list:
		if typeof(item_variant) != TYPE_DICTIONARY:
			continue
		var item: Dictionary = item_variant
		parts.append("%s=%.2f" % [
			str(item.get("name", "--")),
			float(item.get("value", 0.0))
		])
	return ", ".join(parts)


func _selected_player_role() -> String:
	if player_role_option == null:
		return "Lead"
	return player_role_option.get_item_text(player_role_option.selected)


func _apply_to_world_view(method_name: String, payload: Dictionary) -> void:
	if world_view == null:
		return
	if world_view.has_method(method_name):
		world_view.call(method_name, payload)


func _configure_automation_from_environment() -> void:
	automation_enabled = OS.has_environment("CMO_GAME_AUTOMATION")
	if not automation_enabled:
		return

	automation_report_path = OS.get_environment("CMO_GAME_AUTOMATION_REPORT").strip_edges()
	var delay_text := OS.get_environment("CMO_GAME_AUTOMATION_DELAY").strip_edges()
	if not delay_text.is_empty():
		automation_capture_delay_s = max(0.2, delay_text.to_float())
	var role_text := OS.get_environment("CMO_GAME_AUTOMATION_ROLE").strip_edges()
	if not role_text.is_empty():
		automation_expected_role = role_text
	automation_backend_url = OS.get_environment("CMO_GAME_AUTOMATION_BACKEND_URL").strip_edges()
	automation_screenshot_path = OS.get_environment("CMO_GAME_AUTOMATION_SCREENSHOT").strip_edges()
	automation_world_screenshot_path = OS.get_environment("CMO_GAME_AUTOMATION_WORLD_SCREENSHOT").strip_edges()
	var fail_text := OS.get_environment("CMO_GAME_AUTOMATION_FAIL_ON_MISSING_PLAYER").strip_edges().to_lower()
	if fail_text in ["0", "false", "no"]:
		automation_fail_on_missing_player = false


func _process_automation(delta: float) -> void:
	if not automation_enabled:
		return
	if not backend_client.is_backend_connected():
		return
	if last_snapshot.is_empty():
		return

	if not automation_capture_requested:
		automation_capture_requested = true
		automation_capture_delay_s = max(0.2, automation_capture_delay_s)
		return

	automation_capture_delay_s -= delta
	if automation_capture_delay_s > 0.0:
		return

	automation_enabled = false
	_capture_automation_screenshots()
	var report := _build_automation_report()
	_write_automation_report(report)
	var ok := bool(report.get("pass", false))
	get_tree().quit(0 if ok else 1)


func _build_automation_report() -> Dictionary:
	var report := {
		"pass": true,
		"timestamp_unix_s": Time.get_unix_time_from_system(),
		"player_role_expected": automation_expected_role,
		"player_role_actual": str(last_snapshot.get("player_role_label", "")),
		"player_entity_name": str(last_snapshot.get("player_entity_name", "")),
		"sim_time_s": float(last_snapshot.get("sim_time_s", 0.0)),
		"termination": last_snapshot.get("termination", {}),
		"render_status_text": render_status_label.text if render_status_label != null else "",
		"world_debug": {},
		"issues": [],
	}

	if world_view != null and world_view.has_method("capture_debug_state"):
		report["world_debug"] = world_view.call("capture_debug_state")

	var issues: Array[String] = []
	var world_debug: Variant = report.get("world_debug", {})
	if typeof(world_debug) == TYPE_DICTIONARY:
		var debug_dict: Dictionary = world_debug
		if automation_fail_on_missing_player and not bool(debug_dict.get("player_unit_found", false)):
			issues.append("player_unit_missing")
		if automation_fail_on_missing_player and not bool(debug_dict.get("player_visible", false)):
			issues.append("player_not_visible")
		if not bool(debug_dict.get("player_uses_imported_model", false)):
			issues.append("imported_f16_not_in_use")
	else:
		issues.append("world_debug_missing")

	if str(report.get("player_role_actual", "")) != automation_expected_role:
		issues.append("player_role_mismatch")

	report["issues"] = issues
	report["pass"] = issues.is_empty()
	return report


func _write_automation_report(report: Dictionary) -> void:
	var payload := JSON.stringify(report, "\t")
	if automation_report_path.is_empty():
		print(payload)
		return

	var file := FileAccess.open(automation_report_path, FileAccess.WRITE)
	if file == null:
		push_error("Failed to open automation report path: %s" % automation_report_path)
		print(payload)
		return
	file.store_string(payload + "\n")
	file.close()


func _capture_automation_screenshots() -> void:
	if not automation_screenshot_path.is_empty():
		var image: Image = get_viewport().get_texture().get_image()
		if image != null and not image.is_empty():
			image.save_png(automation_screenshot_path)

	if not automation_world_screenshot_path.is_empty() and world_view != null and world_view.has_method("save_debug_screenshot"):
		world_view.call("save_debug_screenshot", automation_world_screenshot_path)


func _make_label(text: String, font_size: int, color: Color) -> Label:
	var label := Label.new()
	label.text = text
	label.add_theme_font_size_override("font_size", font_size)
	label.add_theme_color_override("font_color", color)
	return label


func _make_value_label(text: String) -> Label:
	var label := _make_label(text, 14, Color("f4f7fb"))
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	return label


func _make_button(text: String) -> Button:
	var button := Button.new()
	button.text = text
	button.custom_minimum_size = Vector2(0.0, 42.0)
	button.add_theme_font_size_override("font_size", 13)
	button.add_theme_color_override("font_color", Color("f4f7fb"))
	var normal_style := _panel_style(Color("17314d"), Color("4b7397"))
	var hover_style := _panel_style(Color("22476f"), Color("7ec8ff"))
	var pressed_style := _panel_style(Color("2d5b89"), Color("9fdcff"))
	button.add_theme_stylebox_override("normal", normal_style)
	button.add_theme_stylebox_override("hover", hover_style)
	button.add_theme_stylebox_override("pressed", pressed_style)
	return button


func _task_chip_style(idx: int, active_index: int) -> StyleBoxFlat:
	if idx < active_index:
		return _panel_style(Color("1d4e3c"), Color("7fe6b7"))
	if idx == active_index:
		return _panel_style(Color("27527b"), Color("8fd4ff"))
	return _panel_style(Color("1c2530"), Color("526779"))


func _panel_style(background_color: Color, border_color: Color) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = background_color
	style.border_color = border_color
	style.set_border_width_all(2)
	style.set_corner_radius_all(14)
	return style
