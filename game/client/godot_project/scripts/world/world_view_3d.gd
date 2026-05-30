extends SubViewportContainer

const F16ModelConfig = preload("res://scripts/world/f16_model_config.gd")
const F16_SCENE_PATH := "res://assets/models/f16.glb"
const DEFAULT_GROUND_SIZE_M := 60000.0
const CAMERA_TRAIL_DISTANCE_M := 128.0
const CAMERA_SIDE_OFFSET_M := 24.0
const CAMERA_HEIGHT_M := 42.0
const CAMERA_GROUND_HEIGHT_BOOST_M := 18.0
const CAMERA_GROUND_SIDE_BOOST_M := 12.0
const CAMERA_GROUND_TRAIL_BOOST_M := 26.0
const CAMERA_GROUND_CLOSE_TRAIL_M := 38.0
const CAMERA_GROUND_CLOSE_SIDE_M := 18.0
const CAMERA_GROUND_CLOSE_HEIGHT_M := 14.0
const CAMERA_GROUND_CLOSE_LOOK_AHEAD_M := 34.0
const CAMERA_LOOK_AHEAD_M := 90.0
const CAMERA_LOOK_HEIGHT_M := 11.0
const CAMERA_SMOOTHNESS := 5.5
const MARKER_RING_SEGMENTS := 48

var _f16_scene: PackedScene = null
var _unit_nodes: Dictionary = {}
var _tracked_unit_id: String = ""
var _tracked_unit_payload: Dictionary = {}
var _fallback_focus: Vector3 = Vector3.ZERO
var _fallback_extent_m: float = 2500.0
var _camera_target_position: Vector3 = Vector3(0.0, 180.0, 240.0)
var _camera_look_target: Vector3 = Vector3.ZERO

@onready var _viewport: SubViewport = $WorldViewport
@onready var _ground: MeshInstance3D = $WorldViewport/WorldRoot/Ground
@onready var _zones_root: Node3D = $WorldViewport/WorldRoot/ZonesRoot
@onready var _nav_root: Node3D = $WorldViewport/WorldRoot/NavRoot
@onready var _route_line: MeshInstance3D = $WorldViewport/WorldRoot/NavRoot/RouteLine
@onready var _units_root: Node3D = $WorldViewport/WorldRoot/UnitsRoot
@onready var _camera_rig: Node3D = $WorldViewport/WorldRoot/CameraRig
@onready var _camera: Camera3D = $WorldViewport/WorldRoot/CameraRig/Camera3D


func _ready() -> void:
	_f16_scene = _load_f16_scene()
	_configure_ground(DEFAULT_GROUND_SIZE_M)
	set_process(true)


func _process(delta: float) -> void:
	_update_camera(delta)


func apply_map_setup(payload: Dictionary) -> void:
	_clear_children(_zones_root)

	var zone_centers: Array[Vector3] = []
	var max_extent_m: float = 0.0
	var zones_variant: Variant = payload.get("zones", [])
	if typeof(zones_variant) == TYPE_ARRAY:
		var zones: Array = zones_variant
		for zone_variant in zones:
			if typeof(zone_variant) != TYPE_DICTIONARY:
				continue
			var zone: Dictionary = zone_variant
			var world_center: Vector3 = _add_zone(zone)
			zone_centers.append(world_center)
			max_extent_m = max(
				max_extent_m,
				max(
					absf(world_center.x) + _float_from_dict(zone, "width", 1.0) * 0.5,
					absf(world_center.z) + _float_from_dict(zone, "length", 1.0) * 0.5
				)
			)

	if not zone_centers.is_empty():
		_fallback_focus = _average_points(zone_centers)
		_fallback_extent_m = max(1800.0, max_extent_m)
		_configure_ground(max(DEFAULT_GROUND_SIZE_M, _fallback_extent_m * 3.0))


func apply_nav_setup(payload: Dictionary) -> void:
	for child in _nav_root.get_children():
		if child == _route_line:
			continue
		child.queue_free()

	var route_points: Array[Vector3] = []
	var max_extent_m: float = _fallback_extent_m
	var markers_variant: Variant = payload.get("markers", [])
	if typeof(markers_variant) == TYPE_ARRAY:
		var markers: Array = markers_variant
		for marker_variant in markers:
			if typeof(marker_variant) != TYPE_DICTIONARY:
				continue
			var marker: Dictionary = marker_variant
			var marker_position: Vector3 = _add_nav_marker(marker)
			route_points.append(marker_position)
			max_extent_m = max(max_extent_m, max(absf(marker_position.x), absf(marker_position.z)) + 1500.0)

	_update_route_line(route_points)
	if not route_points.is_empty():
		_fallback_focus = _average_points(route_points)
		_fallback_focus.y = 0.0
		_fallback_extent_m = max(max_extent_m, 2500.0)
		_configure_ground(max(DEFAULT_GROUND_SIZE_M, _fallback_extent_m * 3.0))


func apply_snapshot(snapshot: Dictionary) -> void:
	var player_slot: String = str(snapshot.get("player_slot", ""))
	var units_variant: Variant = snapshot.get("units", [])
	if typeof(units_variant) == TYPE_ARRAY:
		_update_units(units_variant, player_slot)


func _load_f16_scene() -> PackedScene:
	if not ResourceLoader.exists(F16_SCENE_PATH):
		return null
	var loaded: Resource = load(F16_SCENE_PATH)
	if loaded is PackedScene:
		return loaded
	return null


func _configure_ground(size_m: float) -> void:
	var plane := PlaneMesh.new()
	plane.size = Vector2(max(size_m, 10.0), max(size_m, 10.0))
	_ground.mesh = plane
	_ground.material_override = _make_ground_material()
	_ground.position = Vector3(0.0, -0.02, 0.0)
	_ground.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF


func _add_zone(zone: Dictionary) -> Vector3:
	var world_center: Vector3 = _sim_to_world(
		_float_from_dict(zone, "x"),
		_float_from_dict(zone, "y"),
		0.0
	)
	var width_m: float = max(1.0, _float_from_dict(zone, "width", 1.0))
	var length_m: float = max(1.0, _float_from_dict(zone, "length", 1.0))
	var heading_deg: float = _float_from_dict(zone, "heading")
	var surface: String = str(zone.get("surface", "")).strip_edges()

	var plane := PlaneMesh.new()
	plane.size = Vector2(width_m, length_m)

	var mesh_instance := MeshInstance3D.new()
	mesh_instance.name = "%s_Zone" % str(zone.get("name", "Zone"))
	mesh_instance.mesh = plane
	mesh_instance.material_override = _make_zone_material(surface)
	mesh_instance.position = world_center + Vector3(0.0, _zone_height_offset(surface), 0.0)
	mesh_instance.rotation_degrees = Vector3(0.0, -heading_deg, 0.0)
	mesh_instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_zones_root.add_child(mesh_instance)

	var outline := MeshInstance3D.new()
	outline.mesh = _make_rectangle_outline(width_m, length_m, Color("f2d479"))
	outline.position = mesh_instance.position + Vector3(0.0, 0.05, 0.0)
	outline.rotation = mesh_instance.rotation
	outline.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_zones_root.add_child(outline)

	return world_center


func _add_nav_marker(marker: Dictionary) -> Vector3:
	var position: Vector3 = _sim_to_world(
		_float_from_dict(marker, "x"),
		_float_from_dict(marker, "y"),
		_float_from_dict(marker, "z", _float_from_dict(marker, "altitude_m"))
	)
	var radius_m: float = max(60.0, _float_from_dict(marker, "radius_m", 1000.0))
	var mode: String = str(marker.get("waypoint_mode", "flyby")).to_lower()
	var marker_color: Color = Color("f6d85f")
	if mode == "flyover":
		marker_color = Color("ff9955")

	var marker_root := Node3D.new()
	marker_root.name = "Waypoint_%s" % str(marker.get("index", "0"))
	marker_root.position = position
	_nav_root.add_child(marker_root)

	var stem := MeshInstance3D.new()
	var stem_mesh := BoxMesh.new()
	stem_mesh.size = Vector3(8.0, max(4.0, position.y), 8.0)
	stem.mesh = stem_mesh
	stem.material_override = _make_flat_material(marker_color.darkened(0.25))
	stem.position = Vector3(0.0, -position.y * 0.5, 0.0)
	stem.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	marker_root.add_child(stem)

	var sphere := MeshInstance3D.new()
	var sphere_mesh := SphereMesh.new()
	sphere_mesh.radius = max(55.0, min(130.0, radius_m * 0.06))
	sphere_mesh.height = sphere_mesh.radius * 2.0
	sphere.mesh = sphere_mesh
	sphere.material_override = _make_flat_material(marker_color)
	sphere.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	marker_root.add_child(sphere)

	var ring := MeshInstance3D.new()
	ring.mesh = _make_ring_outline(radius_m, marker_color)
	ring.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	marker_root.add_child(ring)

	return position


func _update_route_line(points: Array[Vector3]) -> void:
	if points.size() < 2:
		_route_line.mesh = null
		return

	var mesh := ImmediateMesh.new()
	mesh.surface_begin(Mesh.PRIMITIVE_LINE_STRIP, _make_flat_material(Color("67d7ff")))
	for point in points:
		mesh.surface_add_vertex(point + Vector3(0.0, 4.0, 0.0))
	mesh.surface_end()
	_route_line.mesh = mesh
	_route_line.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF


func _update_units(units: Array, player_slot: String) -> void:
	var seen_ids: Dictionary = {}
	var tracked_candidate: String = player_slot
	var tracked_payload: Dictionary = {}

	for index in range(units.size()):
		var unit_variant: Variant = units[index]
		if typeof(unit_variant) != TYPE_DICTIONARY:
			continue

		var unit: Dictionary = unit_variant
		var fallback_id: String = "unit_%d" % index
		var unit_id: String = str(unit.get("id", unit.get("name", fallback_id)))
		var unit_node: Node3D = _ensure_unit_node(unit_id, unit)
		_update_unit_transform(unit_node, unit)
		seen_ids[unit_id] = true
		if bool(unit.get("player", false)) or unit_id == player_slot:
			tracked_candidate = unit_id
			tracked_payload = unit

	var stale_ids: Array[String] = []
	for unit_id_variant in _unit_nodes.keys():
		var existing_id: String = str(unit_id_variant)
		if not seen_ids.has(existing_id):
			stale_ids.append(existing_id)

	for stale_id in stale_ids:
		var stale_variant: Variant = _unit_nodes.get(stale_id)
		if stale_variant is Node3D:
			var stale_node: Node3D = stale_variant
			stale_node.queue_free()
		_unit_nodes.erase(stale_id)

	if not tracked_candidate.is_empty():
		_tracked_unit_id = tracked_candidate
		_tracked_unit_payload = tracked_payload


func _ensure_unit_node(unit_id: String, unit: Dictionary) -> Node3D:
	var existing_variant: Variant = _unit_nodes.get(unit_id)
	if existing_variant is Node3D:
		return existing_variant

	var unit_root := Node3D.new()
	unit_root.name = unit_id

	var visual_root := Node3D.new()
	visual_root.name = "VisualRoot"
	unit_root.add_child(visual_root)
	visual_root.add_child(_make_visual_for_unit(unit))

	_units_root.add_child(unit_root)
	_unit_nodes[unit_id] = unit_root
	return unit_root


func _make_visual_for_unit(unit: Dictionary) -> Node3D:
	var unit_type: String = str(unit.get("type", "Unit"))
	if _unit_is_aircraft(unit_type):
		return _make_aircraft_visual(bool(unit.get("player", false)))
	return _make_facility_visual(unit)


func _make_aircraft_visual(is_player: bool) -> Node3D:
	var visual_root := Node3D.new()
	visual_root.name = "AircraftVisual"

	if _f16_scene != null:
		var model_instance: Node = _f16_scene.instantiate()
		visual_root.add_child(model_instance)
		if model_instance is Node3D:
			var model_3d: Node3D = model_instance
			model_3d.transform.basis = F16ModelConfig.model_basis()
	else:
		var hull := MeshInstance3D.new()
		var hull_mesh := BoxMesh.new()
		hull_mesh.size = Vector3(2.6, 0.8, 8.8)
		hull.mesh = hull_mesh
		hull.material_override = _make_flat_material(Color("8eb6d8") if is_player else Color("7c8896"))
		visual_root.add_child(hull)

		var nose := MeshInstance3D.new()
		var nose_mesh := CylinderMesh.new()
		nose_mesh.top_radius = 0.0
		nose_mesh.bottom_radius = 0.9
		nose_mesh.height = 3.0
		nose.mesh = nose_mesh
		nose.rotation_degrees = Vector3(90.0, 0.0, 0.0)
		nose.position = Vector3(0.0, 0.0, -5.6)
		nose.material_override = hull.material_override
		visual_root.add_child(nose)

		var wings := MeshInstance3D.new()
		var wings_mesh := BoxMesh.new()
		wings_mesh.size = Vector3(8.0, 0.22, 2.6)
		wings.mesh = wings_mesh
		wings.position = Vector3(0.0, 0.1, -0.4)
		wings.material_override = hull.material_override
		visual_root.add_child(wings)

	var highlight := MeshInstance3D.new()
	var highlight_mesh := SphereMesh.new()
	highlight_mesh.radius = 1.2 if is_player else 0.9
	highlight_mesh.height = highlight_mesh.radius * 2.0
	highlight.mesh = highlight_mesh
	highlight.position = Vector3(0.0, 2.3, 0.0)
	highlight.material_override = _make_flat_material(Color("6fe8ff") if is_player else Color("f6a85f"))
	highlight.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	visual_root.add_child(highlight)

	return visual_root


func _make_facility_visual(unit: Dictionary) -> Node3D:
	var visual_root := Node3D.new()
	visual_root.name = "FacilityVisual"

	var body := MeshInstance3D.new()
	var body_mesh := BoxMesh.new()
	body_mesh.size = Vector3(18.0, 24.0, 18.0)
	body.mesh = body_mesh
	body.position = Vector3(0.0, 12.0, 0.0)
	body.material_override = _make_flat_material(_color_for_side(str(unit.get("side", "Neutral"))).darkened(0.35))
	visual_root.add_child(body)

	var cap := MeshInstance3D.new()
	var cap_mesh := CylinderMesh.new()
	cap_mesh.top_radius = 7.0
	cap_mesh.bottom_radius = 9.5
	cap_mesh.height = 9.0
	cap.mesh = cap_mesh
	cap.position = Vector3(0.0, 28.5, 0.0)
	cap.material_override = _make_flat_material(Color("bcd6e6"))
	visual_root.add_child(cap)

	var beacon := MeshInstance3D.new()
	var beacon_mesh := SphereMesh.new()
	beacon_mesh.radius = 2.8
	beacon_mesh.height = 5.6
	beacon.mesh = beacon_mesh
	beacon.position = Vector3(0.0, 35.0, 0.0)
	beacon.material_override = _make_flat_material(Color("ffba63"))
	beacon.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	visual_root.add_child(beacon)

	return visual_root


func _update_unit_transform(unit_node: Node3D, unit: Dictionary) -> void:
	var world_position: Vector3 = _sim_to_world(
		_float_from_dict(unit, "x"),
		_float_from_dict(unit, "y"),
		_float_from_dict(unit, "z")
	)
	unit_node.position = world_position

	var yaw_rad: float = deg_to_rad(-_float_from_dict(unit, "heading"))
	var pitch_rad: float = deg_to_rad(_float_from_dict(unit, "pitch"))
	var roll_rad: float = deg_to_rad(-_float_from_dict(unit, "roll"))

	var q_yaw := Quaternion(Vector3.UP, yaw_rad)
	var q_pitch := Quaternion(Vector3.RIGHT, pitch_rad)
	var q_roll := Quaternion(Vector3.BACK, roll_rad)
	unit_node.quaternion = q_yaw * q_pitch * q_roll


func _update_camera(delta: float) -> void:
	var desired_eye: Vector3 = _fallback_focus + Vector3(0.0, max(220.0, _fallback_extent_m * 0.45), max(320.0, _fallback_extent_m * 0.7))
	var desired_look: Vector3 = _fallback_focus

	var tracked_variant: Variant = _unit_nodes.get(_tracked_unit_id)
	if tracked_variant is Node3D:
		var tracked_node: Node3D = tracked_variant
		var aircraft_position: Vector3 = tracked_node.global_position
		var forward: Vector3 = -tracked_node.global_transform.basis.z
		forward.y = 0.0
		if forward.length_squared() < 0.001:
			forward = Vector3.FORWARD
		else:
			forward = forward.normalized()
		var right: Vector3 = forward.cross(Vector3.UP).normalized()
		var near_ground_factor: float = clampf(1.0 - (aircraft_position.y / 140.0), 0.0, 1.0)
		var tracked_ias: float = _float_from_dict(_tracked_unit_payload, "ias")
		var ground_close_mode := aircraft_position.y < 12.0 and tracked_ias < 45.0
		var trail_distance: float = CAMERA_TRAIL_DISTANCE_M + CAMERA_GROUND_TRAIL_BOOST_M * near_ground_factor
		var side_offset: float = CAMERA_SIDE_OFFSET_M + CAMERA_GROUND_SIDE_BOOST_M * near_ground_factor
		var height_offset: float = CAMERA_HEIGHT_M + CAMERA_GROUND_HEIGHT_BOOST_M * near_ground_factor
		var look_ahead_distance: float = CAMERA_LOOK_AHEAD_M
		var look_height: float = CAMERA_LOOK_HEIGHT_M
		if ground_close_mode:
			trail_distance = CAMERA_GROUND_CLOSE_TRAIL_M
			side_offset = CAMERA_GROUND_CLOSE_SIDE_M
			height_offset = CAMERA_GROUND_CLOSE_HEIGHT_M
			look_ahead_distance = CAMERA_GROUND_CLOSE_LOOK_AHEAD_M
			look_height = 6.0
		desired_eye = (
			aircraft_position
			- forward * trail_distance
			+ right * side_offset
			+ Vector3.UP * height_offset
		)
		desired_look = (
			aircraft_position
			+ forward * look_ahead_distance
			+ Vector3.UP * look_height
		)

	_camera_target_position = _camera_target_position.lerp(desired_eye, clampf(delta * CAMERA_SMOOTHNESS, 0.0, 1.0))
	_camera_look_target = _camera_look_target.lerp(desired_look, clampf(delta * CAMERA_SMOOTHNESS, 0.0, 1.0))
	_camera_rig.global_position = _camera_target_position
	if _camera.global_position.distance_to(_camera_look_target) > 0.1:
		_camera.look_at(_camera_look_target, Vector3.UP)


func capture_debug_state() -> Dictionary:
	var viewport_size: Vector2i = _viewport.size if _viewport != null else Vector2i.ZERO
	var report := {
		"tracked_unit_id": _tracked_unit_id,
		"fallback_focus": _vector3_dict(_fallback_focus),
		"fallback_extent_m": _fallback_extent_m,
		"viewport_size": _vector2i_dict(viewport_size),
		"camera_position": _vector3_dict(_camera.global_position),
		"camera_target_position": _vector3_dict(_camera_target_position),
		"camera_look_target": _vector3_dict(_camera_look_target),
		"unit_count": _unit_nodes.size(),
		"player_unit_found": false,
		"player_visible": false,
		"player_behind_camera": null,
		"player_in_viewport_rect": null,
		"player_screen_position": null,
		"player_distance_m": null,
		"player_visual_kind": "",
		"player_uses_imported_model": false,
		"player_pose_debug": {},
	}

	var tracked_variant: Variant = _unit_nodes.get(_tracked_unit_id)
	if tracked_variant is Node3D:
		var tracked_node: Node3D = tracked_variant
		report["player_unit_found"] = true
		report["player_distance_m"] = _camera.global_position.distance_to(tracked_node.global_position)
		var projected: Vector2 = _camera.unproject_position(tracked_node.global_position)
		var behind_camera := _camera.is_position_behind(tracked_node.global_position)
		var in_viewport_rect := (
			projected.x >= 0.0
			and projected.y >= 0.0
			and projected.x <= float(viewport_size.x)
			and projected.y <= float(viewport_size.y)
		)
		report["player_screen_position"] = _vector2_dict(projected)
		report["player_behind_camera"] = behind_camera
		report["player_in_viewport_rect"] = in_viewport_rect
		report["player_visible"] = (not behind_camera) and in_viewport_rect

		var visual_info := _describe_visual_kind(tracked_node)
		report["player_visual_kind"] = visual_info.get("kind", "")
		report["player_uses_imported_model"] = bool(visual_info.get("uses_imported_model", false))
		report["player_pose_debug"] = _capture_player_pose_debug(tracked_node)

	return report


func save_debug_screenshot(path: String) -> bool:
	if _viewport == null:
		return false
	var trimmed_path := path.strip_edges()
	if trimmed_path.is_empty():
		return false
	var image: Image = _viewport.get_texture().get_image()
	if image == null or image.is_empty():
		return false
	var err := image.save_png(trimmed_path)
	return err == OK


func _describe_visual_kind(unit_node: Node3D) -> Dictionary:
	var visual_root := unit_node.get_node_or_null("VisualRoot")
	if visual_root == null:
		return {"kind": "missing_visual_root", "uses_imported_model": false}

	for child in visual_root.get_children():
		if child is Node3D and child.name == "AircraftVisual":
			for grandchild in child.get_children():
				if grandchild is Node3D and str(grandchild.name).to_lower().contains("f16"):
					return {"kind": "imported_f16", "uses_imported_model": true}
			return {"kind": "fallback_aircraft", "uses_imported_model": false}
		if child is Node3D and child.name == "FacilityVisual":
			return {"kind": "facility", "uses_imported_model": false}

	return {"kind": "unknown", "uses_imported_model": false}


func _capture_player_pose_debug(unit_node: Node3D) -> Dictionary:
	var visual_root := unit_node.get_node_or_null("VisualRoot")
	if visual_root == null:
		return {"present": false, "reason": "visual_root_missing"}

	var aircraft_visual := _find_child_by_name(visual_root, "AircraftVisual")
	if aircraft_visual == null:
		return {"present": false}

	var imported_model: Node3D = null
	for child in aircraft_visual.get_children():
		if child is Node3D and str(child.name).to_lower().contains("f16"):
			imported_model = child
			break
	if imported_model == null:
		return {"present": false, "reason": "imported_model_missing"}

	var nose_anchor := _find_node_by_name(imported_model, F16ModelConfig.NOSE_ANCHOR_NAME)
	var tail_anchor := _find_node_by_name(imported_model, F16ModelConfig.TAIL_ANCHOR_NAME)
	var left_anchor := _find_node_by_name(imported_model, F16ModelConfig.LEFT_WING_ANCHOR_NAME)
	var right_anchor := _find_node_by_name(imported_model, F16ModelConfig.RIGHT_WING_ANCHOR_NAME)

	var forward := Vector3.ZERO
	if nose_anchor != null and tail_anchor != null:
		forward = (_anchor_point(nose_anchor) - _anchor_point(tail_anchor)).normalized()

	var wing_axis := Vector3.ZERO
	if left_anchor != null and right_anchor != null:
		wing_axis = (_anchor_point(right_anchor) - _anchor_point(left_anchor)).normalized()

	return {
		"present": true,
		"forward": _vector3_dict(forward),
		"wing_axis": _vector3_dict(wing_axis),
		"nose_anchor_found": nose_anchor != null,
		"tail_anchor_found": tail_anchor != null,
		"left_anchor_found": left_anchor != null,
		"right_anchor_found": right_anchor != null,
	}


func _sim_to_world(x_m: float, y_m: float, z_m: float) -> Vector3:
	return Vector3(x_m, z_m, -y_m)


func _clear_children(node: Node) -> void:
	for child in node.get_children():
		child.queue_free()


func _average_points(points: Array[Vector3]) -> Vector3:
	if points.is_empty():
		return Vector3.ZERO
	var total := Vector3.ZERO
	for point in points:
		total += point
	return total / float(points.size())


func _make_ground_material() -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.albedo_color = Color("162536")
	material.roughness = 1.0
	material.metallic = 0.0
	return material


func _make_zone_material(surface: String) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.albedo_color = _zone_color(surface)
	material.roughness = 0.95
	material.metallic = 0.05
	material.cull_mode = BaseMaterial3D.CULL_DISABLED
	return material


func _make_flat_material(color: Color) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.cull_mode = BaseMaterial3D.CULL_DISABLED
	return material


func _make_rectangle_outline(width_m: float, length_m: float, color: Color) -> ImmediateMesh:
	var mesh := ImmediateMesh.new()
	var half_width: float = width_m * 0.5
	var half_length: float = length_m * 0.5
	mesh.surface_begin(Mesh.PRIMITIVE_LINE_STRIP, _make_flat_material(color))
	mesh.surface_add_vertex(Vector3(-half_width, 0.0, -half_length))
	mesh.surface_add_vertex(Vector3(half_width, 0.0, -half_length))
	mesh.surface_add_vertex(Vector3(half_width, 0.0, half_length))
	mesh.surface_add_vertex(Vector3(-half_width, 0.0, half_length))
	mesh.surface_add_vertex(Vector3(-half_width, 0.0, -half_length))
	mesh.surface_end()
	return mesh


func _make_ring_outline(radius_m: float, color: Color) -> ImmediateMesh:
	var mesh := ImmediateMesh.new()
	var clamped_radius: float = max(radius_m, 10.0)
	mesh.surface_begin(Mesh.PRIMITIVE_LINE_STRIP, _make_flat_material(color))
	for index in range(MARKER_RING_SEGMENTS + 1):
		var t: float = float(index) / float(MARKER_RING_SEGMENTS)
		var angle: float = TAU * t
		mesh.surface_add_vertex(Vector3(cos(angle) * clamped_radius, 0.0, sin(angle) * clamped_radius))
	mesh.surface_end()
	return mesh


func _zone_color(surface: String) -> Color:
	match surface:
		"Concrete":
			return Color("5d646f")
		"Asphalt":
			return Color("434a54")
		"SoftDirt":
			return Color("7f5a3a")
		_:
			return Color("4c5d68")


func _zone_height_offset(surface: String) -> float:
	match surface:
		"Concrete":
			return 0.04
		"Asphalt":
			return 0.03
		_:
			return 0.02


func _unit_is_aircraft(unit_type: String) -> bool:
	return _looks_like_aircraft(unit_type, unit_type)


func _color_for_side(side: String) -> Color:
	match side.to_lower():
		"blue":
			return Color("5da9ff")
		"red":
			return Color("ff6f61")
		"green":
			return Color("73d88f")
		_:
			return Color("b1b9c4")


func _looks_like_aircraft(raw_type: String, unit_name: String) -> bool:
	var type_upper := str(raw_type).to_upper()
	var name_upper := str(unit_name).to_upper()
	return (
		"F-16" in type_upper
		or "F16" in type_upper
		or "AIRCRAFT" in type_upper
		or "FIGHTER" in type_upper
		or "F-16" in name_upper
		or "F16" in name_upper
		or "AIRCRAFT" in name_upper
	)


func _anchor_point(node: Node) -> Vector3:
	if node is MeshInstance3D:
		var mesh_node := node as MeshInstance3D
		var aabb := mesh_node.get_aabb()
		return mesh_node.global_transform * aabb.get_center()
	if node is Node3D:
		return (node as Node3D).global_position
	return Vector3.ZERO


func _find_node_by_name(root_node: Node, expected_name: String) -> Node:
	if root_node.name == expected_name:
		return root_node
	for child in root_node.get_children():
		var found := _find_node_by_name(child, expected_name)
		if found != null:
			return found
	return null


func _find_child_by_name(root_node: Node, expected_name: String) -> Node:
	for child in root_node.get_children():
		if str(child.name) == expected_name:
			return child
	return null


func _float_from_dict(source: Dictionary, key: String, default_value: float = 0.0) -> float:
	var value: Variant = source.get(key, default_value)
	if value == null:
		return default_value
	if value is float or value is int:
		return float(value)
	return default_value


func _vector2_dict(value: Vector2) -> Dictionary:
	return {
		"x": value.x,
		"y": value.y,
	}


func _vector2i_dict(value: Vector2i) -> Dictionary:
	return {
		"x": value.x,
		"y": value.y,
	}


func _vector3_dict(value: Vector3) -> Dictionary:
	return {
		"x": value.x,
		"y": value.y,
		"z": value.z,
	}
