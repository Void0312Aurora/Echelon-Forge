extends SceneTree

const F16ModelConfig = preload("res://scripts/world/f16_model_config.gd")


func _init() -> void:
	var scene: PackedScene = load(F16ModelConfig.SCENE_PATH)
	if scene == null:
		_emit_and_quit({"pass": false, "issues": ["f16_scene_missing"]}, 1)
		return

	var root_3d := Node3D.new()
	root.add_child(root_3d)

	var model: Node = scene.instantiate()
	root_3d.add_child(model)
	if model is Node3D:
		var model_3d: Node3D = model
		model_3d.transform.basis = F16ModelConfig.model_basis()

	await process_frame
	await process_frame

	var bounds := _compute_bounds(root_3d)
	var nose_anchor := _find_node_by_name(root_3d, F16ModelConfig.NOSE_ANCHOR_NAME)
	var tail_anchor := _find_node_by_name(root_3d, F16ModelConfig.TAIL_ANCHOR_NAME)
	var left_anchor := _find_node_by_name(root_3d, F16ModelConfig.LEFT_WING_ANCHOR_NAME)
	var right_anchor := _find_node_by_name(root_3d, F16ModelConfig.RIGHT_WING_ANCHOR_NAME)

	var issues: Array[String] = []
	var nose_to_tail := Vector3.ZERO
	if nose_anchor is Node3D and tail_anchor is Node3D:
		nose_to_tail = (_anchor_point(nose_anchor) - _anchor_point(tail_anchor)).normalized()
		if nose_to_tail.dot(Vector3.FORWARD) < 0.85:
			issues.append("nose_tail_direction_misaligned")
	else:
		issues.append("nose_or_tail_anchor_missing")

	var left_to_right := Vector3.ZERO
	if left_anchor is Node3D and right_anchor is Node3D:
		left_to_right = (_anchor_point(right_anchor) - _anchor_point(left_anchor)).normalized()
		if absf(left_to_right.dot(Vector3.UP)) > 0.2:
			issues.append("wings_not_level")
		if absf(left_to_right.dot(Vector3.RIGHT)) < 0.85:
			issues.append("wing_axis_misaligned")
	else:
		issues.append("left_or_right_wing_anchor_missing")

	if bounds.size.x < 6.0 or bounds.size.y < 2.0 or bounds.size.z < 6.0:
		issues.append("bounds_too_small")

	var report := {
		"pass": issues.is_empty(),
		"issues": issues,
		"nose_to_tail": _vector3_dict(nose_to_tail),
		"left_to_right": _vector3_dict(left_to_right),
		"bounds": {
			"min": _vector3_dict(bounds.position),
			"size": _vector3_dict(bounds.size),
			"center": _vector3_dict(bounds.get_center()),
		},
	}
	_emit_and_quit(report, 0 if issues.is_empty() else 1)


func _emit_and_quit(report: Dictionary, code: int) -> void:
	print(JSON.stringify(report, "\t"))
	quit(code)


func _compute_bounds(root_node: Node3D) -> AABB:
	var found := false
	var merged := AABB()
	var stack: Array[Node] = [root_node]
	while not stack.is_empty():
		var node: Node = stack.pop_back()
		if node is MeshInstance3D:
			var mesh_node := node as MeshInstance3D
			var aabb: AABB = mesh_node.get_aabb()
			var corners: Array[Vector3] = [
				aabb.position,
				aabb.position + Vector3(aabb.size.x, 0.0, 0.0),
				aabb.position + Vector3(0.0, aabb.size.y, 0.0),
				aabb.position + Vector3(0.0, 0.0, aabb.size.z),
				aabb.position + Vector3(aabb.size.x, aabb.size.y, 0.0),
				aabb.position + Vector3(aabb.size.x, 0.0, aabb.size.z),
				aabb.position + Vector3(0.0, aabb.size.y, aabb.size.z),
				aabb.position + aabb.size,
			]
			var world_min: Vector3 = mesh_node.global_transform * corners[0]
			var world_max: Vector3 = world_min
			for corner in corners:
				var point: Vector3 = mesh_node.global_transform * corner
				world_min = world_min.min(point)
				world_max = world_max.max(point)
			var world_aabb := AABB(world_min, world_max - world_min)
			if not found:
				merged = world_aabb
				found = true
			else:
				merged = merged.merge(world_aabb)
		for child in node.get_children():
			stack.append(child)
	return merged


func _vector3_dict(value: Vector3) -> Dictionary:
	return {
		"x": value.x,
		"y": value.y,
		"z": value.z,
	}


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
