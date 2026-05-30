extends RefCounted

signal status_changed(status_text: String)
signal snapshot_received(snapshot: Dictionary)
signal map_setup_received(payload: Dictionary)
signal nav_setup_received(payload: Dictionary)
signal event_received(event_payload: Dictionary)

var _socket: WebSocketPeer
var _status_text: String = "disconnected"
var _target_url: String = "ws://127.0.0.1:8765/game"


func get_status_text() -> String:
	return _status_text


func get_target_url() -> String:
	return _target_url


func is_backend_connected() -> bool:
	return _socket != null and _socket.get_ready_state() == WebSocketPeer.STATE_OPEN


func connect_to_backend(url: String) -> bool:
	var trimmed := url.strip_edges()
	if trimmed.is_empty():
		return false

	disconnect_from_backend(false)
	_target_url = trimmed
	_socket = WebSocketPeer.new()
	var err := _socket.connect_to_url(trimmed)
	if err != OK:
		_socket = null
		_set_status("connect_failed(%s)" % error_string(err))
		return false

	_set_status("connecting")
	return true


func disconnect_from_backend(announce: bool = true) -> void:
	if _socket != null:
		if _socket.get_ready_state() == WebSocketPeer.STATE_OPEN:
			_socket.close()
		_socket = null
	if announce:
		_set_status("disconnected")


func poll() -> void:
	if _socket == null:
		return

	_socket.poll()
	var state := _socket.get_ready_state()
	match state:
		WebSocketPeer.STATE_CONNECTING:
			_set_status("connecting")
		WebSocketPeer.STATE_OPEN:
			_set_status("connected")
			while _socket.get_available_packet_count() > 0:
				var packet := _socket.get_packet()
				_handle_text_packet(packet.get_string_from_utf8())
		WebSocketPeer.STATE_CLOSING:
			_set_status("closing")
		WebSocketPeer.STATE_CLOSED:
			var close_code := _socket.get_close_code()
			var close_reason := _socket.get_close_reason()
			_socket = null
			_set_status("closed(%d:%s)" % [close_code, close_reason])


func send_json(payload: Dictionary) -> bool:
	if not is_backend_connected():
		return false

	var err := _socket.send_text(JSON.stringify(payload))
	if err != OK:
		event_received.emit(
			{
				"type": "state_event",
				"event": "send_error",
				"payload": {"error": error_string(err)}
			}
		)
		return false
	return true


func _handle_text_packet(text: String) -> void:
	var parsed = JSON.parse_string(text)
	if typeof(parsed) != TYPE_DICTIONARY:
		event_received.emit(
			{
				"type": "state_event",
				"event": "raw_text",
				"payload": {"text": text}
			}
		)
		return

	var packet: Dictionary = parsed
	var packet_type := str(packet.get("type", ""))
	match packet_type:
		"state_snapshot":
			snapshot_received.emit(packet)
		"map_setup":
			map_setup_received.emit(packet)
		"nav_setup":
			nav_setup_received.emit(packet)
		"state_event", "hello":
			event_received.emit(packet)
		_:
			event_received.emit(
				{
					"type": "state_event",
					"event": "unclassified_packet",
					"payload": packet
				}
			)


func _set_status(next_status: String) -> void:
	if _status_text == next_status:
		return
	_status_text = next_status
	status_changed.emit(_status_text)
