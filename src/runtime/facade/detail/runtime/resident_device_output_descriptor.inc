// X-macro list of DeviceResidentOutputDescriptor fields.
//
// Consumers define EF_RESIDENT_DEVICE_OUTPUT_DESCRIPTOR_FIELD(type, name,
// default_value) before including this file; the macro is #undef'd here
// after expansion.

EF_RESIDENT_DEVICE_OUTPUT_DESCRIPTOR_FIELD(std::vector<std::uint64_t>, output_shape, {})
EF_RESIDENT_DEVICE_OUTPUT_DESCRIPTOR_FIELD(std::string, dtype, {})
EF_RESIDENT_DEVICE_OUTPUT_DESCRIPTOR_FIELD(std::size_t, element_count, 0)
EF_RESIDENT_DEVICE_OUTPUT_DESCRIPTOR_FIELD(std::uint64_t, source_snapshot, 0)
EF_RESIDENT_DEVICE_OUTPUT_DESCRIPTOR_FIELD(std::string, sync_or_export_barrier, {})
EF_RESIDENT_DEVICE_OUTPUT_DESCRIPTOR_FIELD(std::string, host_visible_availability, "unavailable")
EF_RESIDENT_DEVICE_OUTPUT_DESCRIPTOR_FIELD(std::string, diagnostics_label, "diagnostics_only")
EF_RESIDENT_DEVICE_OUTPUT_DESCRIPTOR_FIELD(std::vector<std::string>, consumer_constraints, {})

#undef EF_RESIDENT_DEVICE_OUTPUT_DESCRIPTOR_FIELD
