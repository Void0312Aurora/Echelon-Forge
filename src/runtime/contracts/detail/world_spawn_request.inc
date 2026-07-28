// X-macro list of WorldSpawnRequest fields.
//
// Consumers define EF_WORLD_SPAWN_REQUEST_FIELD(type, name, default_value)
// before including this file; the macro is #undef'd here after expansion.

EF_WORLD_SPAWN_REQUEST_FIELD(std::uint64_t, world_index, 0)
EF_WORLD_SPAWN_REQUEST_FIELD(Side, side, Side::Neutral)
EF_WORLD_SPAWN_REQUEST_FIELD(std::string, type_name, {})
EF_WORLD_SPAWN_REQUEST_FIELD(std::string, entity_name, {})
EF_WORLD_SPAWN_REQUEST_FIELD(bool, is_agent, false)
EF_WORLD_SPAWN_REQUEST_FIELD(double, x, 0.0)
EF_WORLD_SPAWN_REQUEST_FIELD(double, y, 0.0)
EF_WORLD_SPAWN_REQUEST_FIELD(double, z, 0.0)
EF_WORLD_SPAWN_REQUEST_FIELD(double, heading, 0.0)
EF_WORLD_SPAWN_REQUEST_FIELD(double, pitch, 0.0)
EF_WORLD_SPAWN_REQUEST_FIELD(double, roll, 0.0)
EF_WORLD_SPAWN_REQUEST_FIELD(double, vx, 0.0)
EF_WORLD_SPAWN_REQUEST_FIELD(double, vy, 0.0)
EF_WORLD_SPAWN_REQUEST_FIELD(double, vz, 0.0)
EF_WORLD_SPAWN_REQUEST_FIELD(bool, ammo_override_enabled, false)
EF_WORLD_SPAWN_REQUEST_FIELD(int, missiles_remaining, 0)
EF_WORLD_SPAWN_REQUEST_FIELD(int, max_missiles, 0)
EF_WORLD_SPAWN_REQUEST_FIELD(bool, weapon_cooldown_override_enabled, false)
EF_WORLD_SPAWN_REQUEST_FIELD(double, weapon_cooldown_s, 2.0)
EF_WORLD_SPAWN_REQUEST_FIELD(double, weapon_last_fire_time, -1.0)

#undef EF_WORLD_SPAWN_REQUEST_FIELD
