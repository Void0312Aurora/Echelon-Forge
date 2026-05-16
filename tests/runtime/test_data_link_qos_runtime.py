from __future__ import annotations

import json
import tempfile
import unittest

from python.testing.runtime import configure_sim_log_level, ensure_repo_imports, resolve_repo_path


configure_sim_log_level("error")
ensure_repo_imports()

import ef_py  # noqa: E402


_DB_PATH = resolve_repo_path("examples", "config", "database")


def _make_detection(
    target_id: int,
    *,
    range_m: float,
    bearing_deg: float = 0.0,
    elevation_deg: float = 0.0,
    closing_mps: float = 150.0,
) -> ef_py.Detection:
    det = ef_py.Detection()
    det.target_id = int(target_id)
    det.range = float(range_m)
    det.bearing = float(bearing_deg)
    det.elevation = float(elevation_deg)
    det.closing_speed = float(closing_mps)
    det.signal_strength = 1.0
    det.timestamp = 0.0
    return det


class DataLinkQosRuntimeTests(unittest.TestCase):
    def _kernel_with_overrides(self, overrides: dict[str, dict]) -> ef_py.SimulationKernel:
        kernel = ef_py.SimulationKernel()
        kernel.reset(7600 + len(overrides))
        self.assertTrue(kernel.load_database(_DB_PATH))
        with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as handle:
            json.dump({"units": list(overrides.values())}, handle)
            override_path = handle.name
        self.assertTrue(kernel.load_unit_definitions(override_path))
        return kernel

    def _make_budgeted_f16_override(
        self,
        name: str,
        report_budget: int,
        *,
        message_budget: int | None = None,
    ) -> dict:
        with open(
            resolve_repo_path("examples", "config", "database", "aircraft", "units", "f16c_block50.json"),
            "r",
            encoding="utf-8",
        ) as handle:
            unit = json.load(handle)
        unit["name"] = name
        unit["has_data_link"] = True
        unit["data_link_network_id"] = 1
        unit["data_link_max_reports_per_update"] = report_budget
        if message_budget is not None:
            unit["data_link_max_messages_per_update"] = message_budget
        return unit

    def test_datalink_broadcast_message_uses_budget_before_track_reports(self) -> None:
        sender_name = "F16_DL_Budget1_Sender"
        receiver_name = "F16_DL_Budget1_Receiver"
        kernel = self._kernel_with_overrides(
            {
                sender_name: self._make_budgeted_f16_override(sender_name, 1),
                receiver_name: self._make_budgeted_f16_override(receiver_name, 1),
            }
        )
        kernel.set_time_step(0.1)

        sender = int(kernel.spawn_unit(
            ef_py.Side.Blue,
            sender_name,
            0.0,
            0.0,
            3000.0,
            heading=0.0,
            pitch=0.0,
            roll=0.0,
            vx=0.0,
            vy=200.0,
            vz=0.0,
        ))
        receiver = int(kernel.spawn_unit(
            ef_py.Side.Blue,
            receiver_name,
            0.0,
            10_000.0,
            3000.0,
            heading=180.0,
            pitch=0.0,
            roll=0.0,
            vx=0.0,
            vy=-200.0,
            vz=0.0,
        ))
        foe = int(kernel.spawn_unit(
            ef_py.Side.Red,
            "F-16C_Block50",
            0.0,
            30_000.0,
            3000.0,
            heading=180.0,
            pitch=0.0,
            roll=0.0,
            vx=0.0,
            vy=-200.0,
            vz=0.0,
        ))

        kernel.set_contact_list(sender, [_make_detection(foe, range_m=30_000.0)])
        kernel.step()
        kernel.set_contact_list(sender, [_make_detection(foe, range_m=29_500.0)])
        kernel.step()

        kernel.send_message_command(
            sender,
            0,
            int(ef_py.CommMsgType.RequestSupport),
            77,
        )
        kernel.step()

        receiver_msgs = list(kernel.get_unit_messages(receiver))
        request_support_msgs = [
            msg for msg in receiver_msgs
            if int(getattr(msg, "type", 0)) == int(ef_py.CommMsgType.RequestSupport)
        ]
        self.assertEqual(len(request_support_msgs), 1)
        self.assertEqual(
            int(getattr(request_support_msgs[0], "type", 0)),
            int(ef_py.CommMsgType.RequestSupport),
        )
        self.assertEqual(int(getattr(request_support_msgs[0], "entity_ref", -1)), 77)

    def test_datalink_budget_limits_broadcast_fanout_per_update(self) -> None:
        sender_name = "F16_DL_Fanout1_Sender"
        recv1_name = "F16_DL_Fanout1_R1"
        recv2_name = "F16_DL_Fanout1_R2"
        kernel = self._kernel_with_overrides(
            {
                sender_name: self._make_budgeted_f16_override(sender_name, 1),
                recv1_name: self._make_budgeted_f16_override(recv1_name, 1),
                recv2_name: self._make_budgeted_f16_override(recv2_name, 1),
            }
        )
        kernel.set_time_step(0.1)

        sender = int(kernel.spawn_unit(
            ef_py.Side.Blue,
            sender_name,
            0.0,
            0.0,
            3000.0,
            heading=0.0,
            pitch=0.0,
            roll=0.0,
            vx=0.0,
            vy=200.0,
            vz=0.0,
        ))
        receiver1 = int(kernel.spawn_unit(
            ef_py.Side.Blue,
            recv1_name,
            -3_000.0,
            10_000.0,
            3000.0,
            heading=180.0,
            pitch=0.0,
            roll=0.0,
            vx=0.0,
            vy=-200.0,
            vz=0.0,
        ))
        receiver2 = int(kernel.spawn_unit(
            ef_py.Side.Blue,
            recv2_name,
            3_000.0,
            10_000.0,
            3000.0,
            heading=180.0,
            pitch=0.0,
            roll=0.0,
            vx=0.0,
            vy=-200.0,
            vz=0.0,
        ))

        kernel.send_message_command(
            sender,
            0,
            int(ef_py.CommMsgType.AssignTask),
            99,
        )
        kernel.step()

        first_counts = [
            len(list(kernel.get_unit_messages(receiver1))),
            len(list(kernel.get_unit_messages(receiver2))),
        ]
        self.assertEqual(sum(first_counts), 1)

        kernel.send_message_command(
            sender,
            0,
            int(ef_py.CommMsgType.AssignTask),
            99,
        )
        kernel.step()

        second_counts = [
            len(list(kernel.get_unit_messages(receiver1))),
            len(list(kernel.get_unit_messages(receiver2))),
        ]
        self.assertEqual(sum(second_counts), 2)

        sender_link_state = kernel.debug_get_data_link_state(sender)
        self.assertEqual([float(v) for v in sender_link_state[:6]], [1.0, 1.0, 0.0, 1.0, 0.0, 1.0])
        self.assertEqual([float(v) for v in sender_link_state[6:]], [0.0, 2.0, 0.0, 2.0])

    def test_datalink_message_budget_is_independent_from_track_report_budget(self) -> None:
        sender_name = "F16_DL_SplitBudget_Sender"
        receiver_name = "F16_DL_SplitBudget_Receiver"
        kernel = self._kernel_with_overrides(
            {
                sender_name: self._make_budgeted_f16_override(
                    sender_name,
                    0,
                    message_budget=1,
                ),
                receiver_name: self._make_budgeted_f16_override(
                    receiver_name,
                    1,
                    message_budget=1,
                ),
            }
        )
        kernel.set_time_step(0.1)

        sender = int(kernel.spawn_unit(
            ef_py.Side.Blue,
            sender_name,
            0.0,
            0.0,
            3000.0,
            heading=0.0,
            pitch=0.0,
            roll=0.0,
            vx=0.0,
            vy=200.0,
            vz=0.0,
        ))
        receiver = int(kernel.spawn_unit(
            ef_py.Side.Blue,
            receiver_name,
            0.0,
            10_000.0,
            3000.0,
            heading=180.0,
            pitch=0.0,
            roll=0.0,
            vx=0.0,
            vy=-200.0,
            vz=0.0,
        ))
        foe = int(kernel.spawn_unit(
            ef_py.Side.Red,
            "F-16C_Block50",
            0.0,
            30_000.0,
            3000.0,
            heading=180.0,
            pitch=0.0,
            roll=0.0,
            vx=0.0,
            vy=-200.0,
            vz=0.0,
        ))

        kernel.set_contact_list(sender, [_make_detection(foe, range_m=30_000.0)])
        kernel.step()
        kernel.set_contact_list(sender, [_make_detection(foe, range_m=29_500.0)])
        kernel.step()

        kernel.send_message_command(
            sender,
            0,
            int(ef_py.CommMsgType.RequestSupport),
            123,
        )
        kernel.step()

        receiver_msgs = list(kernel.get_unit_messages(receiver))
        request_support_msgs = [
            msg for msg in receiver_msgs
            if int(getattr(msg, "type", 0)) == int(ef_py.CommMsgType.RequestSupport)
        ]
        self.assertEqual(len(request_support_msgs), 1)
        self.assertEqual(int(getattr(request_support_msgs[0], "type", 0)), int(ef_py.CommMsgType.RequestSupport))

        sender_link_state = kernel.debug_get_data_link_state(sender)
        self.assertEqual([float(v) for v in sender_link_state[:6]], [0.0, 1.0, 0.0, 1.0, 1.0, 0.0])
        self.assertEqual([float(v) for v in sender_link_state[6:]], [0.0, 1.0, 1.0, 0.0])

    def test_datalink_report_budget_exposes_drop_counters(self) -> None:
        sender_name = "F16_DL_ReportBudget_Sender"
        recv1_name = "F16_DL_ReportBudget_R1"
        recv2_name = "F16_DL_ReportBudget_R2"
        kernel = self._kernel_with_overrides(
            {
                sender_name: self._make_budgeted_f16_override(
                    sender_name,
                    1,
                    message_budget=0,
                ),
                recv1_name: self._make_budgeted_f16_override(
                    recv1_name,
                    1,
                    message_budget=0,
                ),
                recv2_name: self._make_budgeted_f16_override(
                    recv2_name,
                    1,
                    message_budget=0,
                ),
            }
        )
        kernel.set_time_step(0.1)

        sender = int(kernel.spawn_unit(
            ef_py.Side.Blue,
            sender_name,
            0.0,
            0.0,
            3000.0,
            heading=0.0,
            pitch=0.0,
            roll=0.0,
            vx=0.0,
            vy=200.0,
            vz=0.0,
        ))
        receiver1 = int(kernel.spawn_unit(
            ef_py.Side.Blue,
            recv1_name,
            -3_000.0,
            10_000.0,
            3000.0,
            heading=180.0,
            pitch=0.0,
            roll=0.0,
            vx=0.0,
            vy=-200.0,
            vz=0.0,
        ))
        receiver2 = int(kernel.spawn_unit(
            ef_py.Side.Blue,
            recv2_name,
            3_000.0,
            10_000.0,
            3000.0,
            heading=180.0,
            pitch=0.0,
            roll=0.0,
            vx=0.0,
            vy=-200.0,
            vz=0.0,
        ))
        foe = int(kernel.spawn_unit(
            ef_py.Side.Red,
            "F-16C_Block50",
            0.0,
            30_000.0,
            3000.0,
            heading=180.0,
            pitch=0.0,
            roll=0.0,
            vx=0.0,
            vy=-200.0,
            vz=0.0,
        ))

        kernel.set_contact_list(sender, [_make_detection(foe, range_m=30_000.0)])
        kernel.step()
        kernel.set_contact_list(sender, [_make_detection(foe, range_m=29_500.0)])
        kernel.step()
        kernel.step()

        delivered_counts = [
            len(list(kernel.get_unit_messages(receiver1))),
            len(list(kernel.get_unit_messages(receiver2))),
        ]
        self.assertEqual(sum(delivered_counts), 1)

        sender_link_state = kernel.debug_get_data_link_state(sender)
        self.assertEqual([float(v) for v in sender_link_state[:6]], [1.0, 0.0, 1.0, 0.0, 1.0, 0.0])
        self.assertEqual([float(v) for v in sender_link_state[6:]], [1.0, 0.0, 1.0, 0.0])


if __name__ == "__main__":
    unittest.main()
