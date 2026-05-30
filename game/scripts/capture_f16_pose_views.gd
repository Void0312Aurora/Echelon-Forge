extends SceneTree

const F16ModelConfig = preload("res://scripts/world/f16_model_config.gd")

const OUTPUT_DIR := "/tmp/cmo_f16_pose_views"
const VIEW_SIZE := Vector2i(1400, 1000)

var _viewport: SubViewport
var _world_root: Node3D
var _camera: Camera3D
var _model: Node3D


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	DirAccess.make_dir_recursive_absolute(OUTPUT_DIR)
	_setup_viewport()
	_setup_world()
	await process_frame
	await process_frame
	await _capture_view("hero", Vector3(14.0, 6.5, 14.0), Vector3(0.0, 1.0, 0.0), 34.0)
	await _capture_view("front", Vector3(15.0, 3.6, 0.0), Vector3(0.0, 1.0, 0.0), 28.0)
	await _capture_view("side", Vector3(0.0, 3.4, 15.0), Vector3(0.0, 1.0, 0.0), 28.0)
	await _capture_view("top", Vector3(0.0, 18.0, 0.01), Vector3(1.0, 0.0, 0.0), 26.0)
	quit()


func _setup_viewport() -> void:
	_viewport = SubViewport.new()
	_viewport.name = "PhotoViewport"
	_viewport.size = VIEW_SIZE
	_viewport.msaa_3d = Viewport.MSAA_4X
	_viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(_viewport)


func _setup_world() -> void:
	_world_root = Node3D.new()
	_viewport.add_child(_world_root)

	var env := WorldEnvironment.new()
	var environment := Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = Color(0.83, 0.88, 0.94, 1.0)
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color(0.95, 0.97, 1.0, 1.0)
	environment.ambient_light_energy = 0.35
	env.environment = environment
	_world_root.add_child(env)

	var ground := MeshInstance3D.new()
	var ground_mesh := PlaneMesh.new()
	ground_mesh.size = Vector2(50.0, 50.0)
	ground.mesh = ground_mesh
	ground.material_override = _make_ground_material()
	_world_root.add_child(ground)

	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-46.0, 28.0, 0.0)
	sun.light_energy = 1.25
	sun.shadow_enabled = true
	_world_root.add_child(sun)

	var rim := OmniLight3D.new()
	rim.position = Vector3(-10.0, 6.0, -12.0)
	rim.light_energy = 420.0
	rim.omni_range = 80.0
	_world_root.add_child(rim)

	_model = _load_model()
	_model.position = Vector3(0.0, 0.0, 0.0)
	_world_root.add_child(_model)
	_add_debug_markers()

	_camera = Camera3D.new()
	_camera.name = "PhotoCamera"
	_camera.current = true
	_camera.near = 0.05
	_camera.far = 200.0
	_world_root.add_child(_camera)


func _load_model() -> Node3D:
	var scene: PackedScene = load(F16ModelConfig.SCENE_PATH)
	var instance: Node = scene.instantiate()
	if instance is Node3D:
		var model_3d: Node3D = instance
		model_3d.transform.basis = F16ModelConfig.model_basis()
		return model_3d
	return Node3D.new()


func _capture_view(name: String, camera_position: Vector3, up: Vector3, fov: float) -> void:
	_camera.position = camera_position
	_camera.fov = fov
	_camera.look_at(Vector3(0.0, 1.0, 0.0), up)
	await process_frame
	await process_frame
	var image: Image = _viewport.get_texture().get_image()
	var output_path := "%s/%s.png" % [OUTPUT_DIR, name]
	var err := image.save_png(output_path)
	print("CAPTURE ", name, " -> ", output_path, " err=", err)


func _make_ground_material() -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.albedo_color = Color(0.68, 0.72, 0.78, 1.0)
	material.roughness = 1.0
	return material


func _add_debug_markers() -> void:
	_add_anchor_marker(F16ModelConfig.NOSE_ANCHOR_NAME, Color(0.95, 0.32, 0.2, 1.0), 0.22)
	_add_anchor_marker(F16ModelConfig.TAIL_ANCHOR_NAME, Color(0.1, 0.1, 0.1, 1.0), 0.22)
	_add_anchor_marker(F16ModelConfig.LEFT_WING_ANCHOR_NAME, Color(0.2, 0.75, 0.98, 1.0), 0.18)
	_add_anchor_marker(F16ModelConfig.RIGHT_WING_ANCHOR_NAME, Color(0.12, 0.95, 0.32, 1.0), 0.18)
	_add_anchor_marker(F16ModelConfig.TOP_ANCHOR_NAME, Color(0.95, 0.9, 0.22, 1.0), 0.18)
	_add_anchor_marker(F16ModelConfig.BOTTOM_ANCHOR_NAME, Color(0.7, 0.3, 0.95, 1.0), 0.18)


func _add_anchor_marker(anchor_name: String, color: Color, radius: float) -> void:
	var anchor := _find_node_by_name(_model, anchor_name)
	if not (anchor is Node3D):
		return
	var marker := MeshInstance3D.new()
	var sphere := SphereMesh.new()
	sphere.radius = radius
	sphere.height = radius * 2.0
	marker.mesh = sphere
	marker.material_override = _make_marker_material(color)
	marker.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_world_root.add_child(marker)
	marker.global_position = (anchor as Node3D).global_position


func _make_marker_material(color: Color) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	material.emission_enabled = true
	material.emission = color * 0.65
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	return material


func _find_node_by_name(root_node: Node, expected_name: String) -> Node:
	if root_node.name == expected_name:
		return root_node
	for child in root_node.get_children():
		var found := _find_node_by_name(child, expected_name)
		if found != null:
			return found
	return null
