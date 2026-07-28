from __future__ import annotations

import importlib
import socket
import threading
import unittest

from python.runtime_bootstrap import ensure_repo_imports


HOST_FRAME_PAYLOAD = (
  '[1,"Altis",12.5,0.2,36.0,[1000.0,2000.0,5.0],[0.0,0.0,0.0],'
  "[0.0,1.0,0.0],[0.0,0.0,1.0]]"
)


class ArmaProxyBackendStubTests(unittest.TestCase):
  @classmethod
  def setUpClass(cls) -> None:
    ensure_repo_imports()
    cls.stub_mod = importlib.import_module("tools.diagnostics.arma_proxy_backend_stub")

  def test_host_frame_parser_reads_expected_fields(self) -> None:
    frame = self.stub_mod.HostFrame.from_sqf_payload(HOST_FRAME_PAYLOAD)

    self.assertEqual(frame.protocol_version, 1)
    self.assertEqual(frame.world_name, "Altis")
    self.assertAlmostEqual(frame.delta_time_s, 0.2)
    self.assertEqual(frame.position_asl, (1000.0, 2000.0, 5.0))
    self.assertEqual(frame.direction, (0.0, 1.0, 0.0))

  def test_stub_generates_proxy_state_from_begin_session_and_host_frame(self) -> None:
    config = self.stub_mod.StubConfig(
      start_position_asl=(0.0, 0.0, 1200.0),
      speed_mps=250.0,
      turn_rate_deg_s=0.0,
      climb_rate_mps=0.0,
      bootstrap_from_host=True,
    )
    stub = self.stub_mod.ArmaProxyBackendStub(config)

    self.assertEqual(
      stub.handle_line("begin_session\talpha\tAltis\tB_Plane_Fighter_01_F"),
      "ack\tbegin_session",
    )
    response = stub.handle_line(
      f"host_frame\talpha\tmission|tick\t{HOST_FRAME_PAYLOAD}"
    )
    self.assertTrue(response.startswith("proxy_state\t"))

    payload = response.split("\t", 1)[1]
    proxy_state = self.stub_mod.parse_sqf_simple_array(payload)
    self.assertEqual(int(proxy_state[0]), 1)
    self.assertAlmostEqual(float(proxy_state[1][0]), 1000.0)
    self.assertAlmostEqual(float(proxy_state[1][1]), 2050.0)
    self.assertAlmostEqual(float(proxy_state[1][2]), 1200.0)
    self.assertEqual(int(proxy_state[8]), self.stub_mod.ENGINE_ON_FLAG)

  def test_stub_rejects_unknown_session(self) -> None:
    stub = self.stub_mod.ArmaProxyBackendStub()
    response = stub.handle_line(f"host_frame\tmissing\tctx\t{HOST_FRAME_PAYLOAD}")
    self.assertEqual(response, "err\thost_frame\tunknown_session")

  def test_tcp_server_handles_line_protocol_smoke(self) -> None:
    stub = self.stub_mod.ArmaProxyBackendStub(
      self.stub_mod.StubConfig(port=0, speed_mps=150.0)
    )

    with self.stub_mod.ArmaProxyBackendTcpServer(("127.0.0.1", 0), stub) as server:
      thread = threading.Thread(
        target=server.serve_forever,
        kwargs={"poll_interval": 0.05},
        daemon=True,
      )
      thread.start()
      host, port = server.server_address[:2]
      try:
        with socket.create_connection((host, port), timeout=1.0) as sock:
          stream = sock.makefile("rwb")
          stream.write(b"begin_session\talpha\tAltis\tB_Plane_Fighter_01_F\n")
          stream.flush()
          self.assertEqual(
            stream.readline().decode("utf-8").strip(),
            "ack\tbegin_session",
          )

          stream.write(
            f"host_frame\talpha\tmission|tick\t{HOST_FRAME_PAYLOAD}\n".encode(
              "utf-8"
            )
          )
          stream.flush()
          self.assertTrue(
            stream.readline().decode("utf-8").strip().startswith(
              "proxy_state\t"
            )
          )

          stream.write(b"shutdown\talpha\n")
          stream.flush()
          self.assertEqual(
            stream.readline().decode("utf-8").strip(),
            "ack\tshutdown",
          )
      finally:
        server.shutdown()
        thread.join(timeout=1.0)
      self.assertFalse(thread.is_alive())


if __name__ == "__main__":
  unittest.main()
