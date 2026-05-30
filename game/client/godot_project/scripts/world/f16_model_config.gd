extends RefCounted

const SCENE_PATH := "res://assets/models/f16.glb"
const MODEL_BASIS_X := Vector3(0.0, 0.0, 1.0)
const MODEL_BASIS_Y := Vector3(0.0, 1.0, 0.0)
const MODEL_BASIS_Z := Vector3(-1.0, 0.0, 0.0)
const NOSE_ANCHOR_NAME := "Link16Antennas"
const TAIL_ANCHOR_NAME := "InternalFlame"
const LEFT_WING_ANCHOR_NAME := "LWStation3"
const RIGHT_WING_ANCHOR_NAME := "RWStation3"


static func model_basis() -> Basis:
	return Basis(MODEL_BASIS_X, MODEL_BASIS_Y, MODEL_BASIS_Z).orthonormalized()
