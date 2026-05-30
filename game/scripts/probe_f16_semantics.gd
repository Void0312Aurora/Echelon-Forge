extends SceneTree

const F16ModelConfig = preload("res://scripts/world/f16_model_config.gd")


func _init() -> void:
	var scene: PackedScene = load(F16ModelConfig.SCENE_PATH)
	if scene == null:
		print(JSON.stringify({"error": "f16_scene_missing"}, "\t"))
		quit(1)
		return

	var root_3d := Node3D.new()
	root.add_child(root_3d)

	var instance: Node = scene.instantiate()
	root_3d.add_child(instance)
	if instance is Node3D:
		var model_3d: Node3D = instance
		if _apply_model_basis():
			model_3d.transform.basis = F16ModelConfig.model_basis()

	await process_frame
	await process_frame

	var report := {
		"bounds": _aabb_dict(_compute_bounds(root_3d)),
		"anchors": {
			"nose": _vector3_dict(_anchor_point(root_3d, F16ModelConfig.NOSE_ANCHOR_NAME)),
			"tail": _vector3_dict(_anchor_point(root_3d, F16ModelConfig.TAIL_ANCHOR_NAME)),
			"left": _vector3_dict(_anchor_point(root_3d, F16ModelConfig.LEFT_WING_ANCHOR_NAME)),
			"right": _vector3_dict(_anchor_point(root_3d, F16ModelConfig.RIGHT_WING_ANCHOR_NAME)),
		},
	}

	var anchors: Dictionary = report["anchors"]
	var nose := _dict_to_vector3(anchors.get("nose", {}))
	var tail := _dict_to_vector3(anchors.get("tail", {}))
	var left := _dict_to_vector3(anchors.get("left", {}))
	var right := _dict_to_vector3(anchors.get("right", {}))

	report["axes"] = {
		"forward": _vector3_dict((nose - tail).normalized()),
		"right": _vector3_dict((right - left).normalized()),
	}

	print(JSON.stringify(report, "\t"))
	quit()


func _apply_model_basis() -> bool:
	var raw_value := OS.get_environment("CMO_F16_APPLY_MODEL_BASIS").strip_edges().to_lower()
	return raw_value not in ["0", "false", "no", "off"]


func _anchor_point(root_node: Node, expected_name: String) -> Vector3:
	var anchor := _find_node_by_name(root_node, expected_name)
	if anchor is MeshInstance3D:
		var mesh_anchor := anchor as MeshInstance3D
		var aabb := mesh_anchor.get_aabb()
		return mesh_anchor.global_transform * aabb.get_center()
	if anchor is Node3D:
		return (anchor as Node3D).global_position
	return Vector3.ZERO


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


func _aabb_dict(aabb: AABB) -> Dictionary:
	return {
		"min": _vector3_dict(aabb.position),
		"size": _vector3_dict(aabb.size),
		"center": _vector3_dict(aabb.get_center()),
	}


func _vector3_dict(value: Vector3) -> Dictionary:
	return {
		"x": value.x,
		"y": value.y,
		"z": value.z,
	}


func _dict_to_vector3(value: Variant) -> Vector3:
	if typeof(value) != TYPE_DICTIONARY:
		return Vector3.ZERO
	var dict: Dictionary = value
	return Vector3(
		float(dict.get("x", 0.0)),
		float(dict.get("y", 0.0)),
		float(dict.get("z", 0.0))
	)


func _find_node_by_name(root_node: Node, expected_name: String) -> Node:
	if root_node.name == expected_name:
		return root_node
	for child in root_node.get_children():
		var found := _find_node_by_name(child, expected_name)
		if found != null:
			return found
	return null
