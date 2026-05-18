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
    _LINK_STATE_KEYS = (
        "report_budget",
        "message_budget",
        "reports_sent_last",
        "messages_sent_last",
        "reports_dropped_last",
        "messages_dropped_last",
        "reports_sent_total",
        "messages_sent_total",
        "reports_dropped_total",
        "messages_dropped_total",
    )

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

    def _spawn_f16(
        self,
        kernel: ef_py.SimulationKernel,
        side: ef_py.Side,
        name: str,
        x: float,
        y: float,
        *,
        z: float = 3000.0,
        heading: float = 0.0,
        vx: float = 0.0,
        vy: float = 0.0,
        vz: float = 0.0,
    ) -> int:
        return int(kernel.spawn_unit(
            side,
            name,
            x,
            y,
            z,
            heading=heading,
            pitch=0.0,
            roll=0.0,
            vx=vx,
            vy=vy,
            vz=vz,
        ))

    def _get_data_link_state(self, kernel: ef_py.SimulationKernel, entity_id: int) -> dict[str, int]:
        values = [int(v) for v in kernel.debug_get_data_link_state(entity_id)]
        return dict(zip(self._LINK_STATE_KEYS, values, strict=True))

    def _prime_confirmed_tracks(
        self,
        kernel: ef_py.SimulationKernel,
        sender: int,
        first_step_detections: list[ef_py.Detection],
        second_step_detections: list[ef_py.Detection] | None = None,
    ) -> None:
        kernel.set_contact_list(sender, first_step_detections)
        kernel.step()
        kernel.set_contact_list(sender, second_step_detections or first_step_detections)
        kernel.step()

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
        self.assertEqual([float(v) for v in sender_link_state[6:]], [0.0, 1.0, 2.0, 0.0])

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
        self.assertEqual(sum(delivered_counts), 2)

        sender_link_state = kernel.debug_get_data_link_state(sender)
        self.assertEqual([float(v) for v in sender_link_state[:6]], [1.0, 0.0, 1.0, 0.0, 0.0, 0.0])
        self.assertEqual([float(v) for v in sender_link_state[6:]], [2.0, 0.0, 1.0, 0.0])

    def test_datalink_message_budget_scales_with_larger_broadcast_fanout(self) -> None:
        sender_name = "F16_DL_MsgScale_Sender"
        receiver_names = [f"F16_DL_MsgScale_R{i}" for i in range(5)]
        overrides = {
            sender_name: self._make_budgeted_f16_override(sender_name, 0, message_budget=2),
        }
        overrides.update({
            name: self._make_budgeted_f16_override(name, 0, message_budget=0)
            for name in receiver_names
        })

        kernel = self._kernel_with_overrides(overrides)
        kernel.set_time_step(0.1)

        sender = self._spawn_f16(kernel, ef_py.Side.Blue, sender_name, 0.0, 0.0)
        receiver_ids = [
            self._spawn_f16(kernel, ef_py.Side.Blue, name, -6_000.0 + (idx * 3_000.0), 10_000.0, heading=180.0)
            for idx, name in enumerate(receiver_names)
        ]

        kernel.send_message_command(
            sender,
            0,
            int(ef_py.CommMsgType.AssignTask),
            314,
        )
        kernel.step()

        sender_state = self._get_data_link_state(kernel, sender)
        self.assertEqual(sender_state["report_budget"], 0)
        self.assertEqual(sender_state["message_budget"], 2)
        self.assertEqual(sender_state["reports_sent_last"], 0)
        self.assertEqual(sender_state["reports_dropped_last"], 0)
        self.assertEqual(sender_state["messages_sent_last"], 2)
        self.assertEqual(sender_state["messages_dropped_last"], 3)
        self.assertEqual(sender_state["messages_sent_total"], 2)
        self.assertEqual(sender_state["messages_dropped_total"], 3)

        delivered_messages = sum(
            1
            for receiver_id in receiver_ids
            for msg in kernel.get_unit_messages(receiver_id)
            if int(getattr(msg, "type", 0)) == int(ef_py.CommMsgType.AssignTask)
        )
        self.assertEqual(delivered_messages, 2)

    def test_datalink_targeted_message_does_not_count_nonrecipients_as_budget_drops(self) -> None:
        sender_name = "F16_DL_TargetedScale_Sender"
        receiver_names = [f"F16_DL_TargetedScale_R{i}" for i in range(5)]
        overrides = {
            sender_name: self._make_budgeted_f16_override(sender_name, 0, message_budget=1),
        }
        overrides.update({
            name: self._make_budgeted_f16_override(name, 0, message_budget=0)
            for name in receiver_names
        })

        kernel = self._kernel_with_overrides(overrides)
        kernel.set_time_step(0.1)

        sender = self._spawn_f16(kernel, ef_py.Side.Blue, sender_name, 0.0, 0.0)
        receiver_ids = [
            self._spawn_f16(kernel, ef_py.Side.Blue, name, -6_000.0 + (idx * 3_000.0), 10_000.0, heading=180.0)
            for idx, name in enumerate(receiver_names)
        ]
        target_receiver = receiver_ids[3]

        kernel.send_message_command(
            sender,
            target_receiver,
            int(ef_py.CommMsgType.AssignTask),
            271,
        )
        kernel.step()

        sender_state = self._get_data_link_state(kernel, sender)
        self.assertEqual(sender_state["message_budget"], 1)
        self.assertEqual(sender_state["messages_sent_last"], 1)
        self.assertEqual(sender_state["messages_dropped_last"], 0)
        self.assertEqual(sender_state["messages_sent_total"], 1)
        self.assertEqual(sender_state["messages_dropped_total"], 0)

        per_receiver_counts = {
            receiver_id: sum(
                1
                for msg in kernel.get_unit_messages(receiver_id)
                if int(getattr(msg, "type", 0)) == int(ef_py.CommMsgType.AssignTask)
            )
            for receiver_id in receiver_ids
        }
        self.assertEqual(per_receiver_counts[target_receiver], 1)
        self.assertEqual(sum(per_receiver_counts.values()), 1)

    def test_datalink_report_budget_scales_with_track_receiver_matrix(self) -> None:
        sender_name = "F16_DL_ReportScale_Sender"
        receiver_names = [f"F16_DL_ReportScale_R{i}" for i in range(4)]
        overrides = {
            sender_name: self._make_budgeted_f16_override(sender_name, 5, message_budget=0),
        }
        overrides.update({
            name: self._make_budgeted_f16_override(name, 0, message_budget=0)
            for name in receiver_names
        })

        kernel = self._kernel_with_overrides(overrides)
        kernel.set_time_step(0.1)

        sender = self._spawn_f16(kernel, ef_py.Side.Blue, sender_name, 0.0, 0.0)
        receiver_ids = [
            self._spawn_f16(kernel, ef_py.Side.Blue, name, -4_500.0 + (idx * 3_000.0), 10_000.0, heading=180.0)
            for idx, name in enumerate(receiver_names)
        ]
        foe1 = self._spawn_f16(kernel, ef_py.Side.Red, "F-16C_Block50", 0.0, 30_000.0, heading=180.0)
        foe2 = self._spawn_f16(kernel, ef_py.Side.Red, "F-16C_Block50", 7_000.0, 34_000.0, heading=180.0)
        foe3 = self._spawn_f16(kernel, ef_py.Side.Red, "F-16C_Block50", -7_000.0, 36_000.0, heading=180.0)

        detection_batch = [
            _make_detection(foe1, range_m=30_000.0, bearing_deg=0.0, closing_mps=0.0),
            _make_detection(foe2, range_m=34_700.0, bearing_deg=11.5, closing_mps=0.0),
            _make_detection(foe3, range_m=36_700.0, bearing_deg=-11.0, closing_mps=0.0),
        ]
        self._prime_confirmed_tracks(kernel, sender, detection_batch)

        sender_tracks = list(kernel.get_track_debug_view(sender))
        confirmed_tracks = [track for track in sender_tracks if int(getattr(track, "status", 0)) == 1]
        self.assertGreaterEqual(len(confirmed_tracks), 3)

        kernel.step()

        sender_state = self._get_data_link_state(kernel, sender)
        self.assertEqual(sender_state["report_budget"], 5)
        self.assertEqual(sender_state["message_budget"], 0)
        self.assertEqual(sender_state["reports_sent_last"], 5)
        self.assertGreater(sender_state["reports_dropped_last"], 0)
        self.assertEqual(sender_state["reports_sent_total"], 10)
        self.assertEqual(sender_state["reports_dropped_total"], 9)
        self.assertEqual(sender_state["messages_sent_last"], 0)
        self.assertEqual(sender_state["messages_dropped_last"], 0)

        delivered_reports = sum(
            1
            for receiver_id in receiver_ids
            for msg in kernel.get_unit_messages(receiver_id)
            if int(getattr(msg, "type", 0)) == int(ef_py.CommMsgType.ReportTrack)
        )
        self.assertEqual(delivered_reports, 10)

    def test_datalink_report_budget_refills_each_update_under_continuous_churn(self) -> None:
        sender_name = "F16_DL_Churn_Sender"
        receiver_names = [f"F16_DL_Churn_R{i}" for i in range(3)]
        overrides = {
            sender_name: self._make_budgeted_f16_override(sender_name, 2, message_budget=0),
        }
        overrides.update({
            name: self._make_budgeted_f16_override(name, 0, message_budget=0)
            for name in receiver_names
        })

        kernel = self._kernel_with_overrides(overrides)
        kernel.set_time_step(0.1)

        sender = self._spawn_f16(kernel, ef_py.Side.Blue, sender_name, 0.0, 0.0)
        for idx, name in enumerate(receiver_names):
            self._spawn_f16(kernel, ef_py.Side.Blue, name, -3_000.0 + (idx * 3_000.0), 10_000.0, heading=180.0)
        foe = self._spawn_f16(kernel, ef_py.Side.Red, "F-16C_Block50", 0.0, 30_000.0, heading=180.0)

        stable_detection = [_make_detection(foe, range_m=30_000.0, bearing_deg=0.0, closing_mps=0.0)]
        self._prime_confirmed_tracks(kernel, sender, stable_detection)

        kernel.step()
        initial_state = self._get_data_link_state(kernel, sender)
        self.assertEqual(initial_state["reports_sent_last"], 1)
        self.assertEqual(initial_state["reports_dropped_last"], 0)
        self.assertEqual(initial_state["reports_sent_total"], 3)
        self.assertEqual(initial_state["reports_dropped_total"], 1)

        for update_idx, range_m in enumerate((29_100.0, 28_200.0), start=1):
            with self.subTest(update_idx=update_idx):
                kernel.set_contact_list(
                    sender,
                    [_make_detection(foe, range_m=range_m, bearing_deg=0.0, closing_mps=0.0)],
                )
                kernel.step()

                sender_state = self._get_data_link_state(kernel, sender)
                self.assertEqual(sender_state["reports_sent_last"], 2)
                self.assertEqual(sender_state["reports_dropped_last"], 1)
                self.assertEqual(sender_state["reports_sent_total"], 2 * update_idx + 3)
                self.assertEqual(sender_state["reports_dropped_total"], update_idx + 1)
                self.assertEqual(sender_state["messages_sent_last"], 0)
                self.assertEqual(sender_state["messages_dropped_last"], 0)

    def test_datalink_message_and_report_budgets_scale_independently_in_same_update(self) -> None:
        sender_name = "F16_DL_CombinedScale_Sender"
        receiver_names = [f"F16_DL_CombinedScale_R{i}" for i in range(3)]
        overrides = {
            sender_name: self._make_budgeted_f16_override(sender_name, 2, message_budget=1),
        }
        overrides.update({
            name: self._make_budgeted_f16_override(name, 0, message_budget=0)
            for name in receiver_names
        })

        kernel = self._kernel_with_overrides(overrides)
        kernel.set_time_step(0.1)

        sender = self._spawn_f16(kernel, ef_py.Side.Blue, sender_name, 0.0, 0.0)
        receiver_ids = [
            self._spawn_f16(kernel, ef_py.Side.Blue, name, -3_000.0 + (idx * 3_000.0), 10_000.0, heading=180.0)
            for idx, name in enumerate(receiver_names)
        ]
        foe1 = self._spawn_f16(kernel, ef_py.Side.Red, "F-16C_Block50", 0.0, 30_000.0, heading=180.0)
        foe2 = self._spawn_f16(kernel, ef_py.Side.Red, "F-16C_Block50", 8_000.0, 35_000.0, heading=180.0)

        self._prime_confirmed_tracks(
            kernel,
            sender,
            [
                _make_detection(foe1, range_m=30_000.0, bearing_deg=0.0, closing_mps=0.0),
                _make_detection(foe2, range_m=35_900.0, bearing_deg=12.5, closing_mps=0.0),
            ],
        )

        kernel.send_message_command(
            sender,
            0,
            int(ef_py.CommMsgType.RequestSupport),
            808,
        )
        kernel.step()

        sender_state = self._get_data_link_state(kernel, sender)
        self.assertEqual(sender_state["report_budget"], 2)
        self.assertEqual(sender_state["message_budget"], 1)
        self.assertEqual(sender_state["reports_sent_last"], 2)
        self.assertGreater(sender_state["reports_dropped_last"], 0)
        self.assertEqual(sender_state["messages_sent_last"], 1)
        self.assertGreater(sender_state["messages_dropped_last"], 0)
        self.assertEqual(sender_state["reports_sent_total"], 4)
        self.assertGreater(sender_state["reports_dropped_total"], 0)
        self.assertEqual(sender_state["messages_sent_total"], 1)
        self.assertGreater(sender_state["messages_dropped_total"], 0)

        delivered_reports = sum(
            1
            for receiver_id in receiver_ids
            for msg in kernel.get_unit_messages(receiver_id)
            if int(getattr(msg, "type", 0)) == int(ef_py.CommMsgType.ReportTrack)
        )
        delivered_messages = sum(
            1
            for receiver_id in receiver_ids
            for msg in kernel.get_unit_messages(receiver_id)
            if int(getattr(msg, "type", 0)) == int(ef_py.CommMsgType.RequestSupport)
        )
        self.assertEqual(delivered_reports, 4)
        self.assertEqual(delivered_messages, 1)

    def test_datalink_last_update_counters_reset_while_totals_persist_after_idle_frame(self) -> None:
        sender_name = "F16_DL_CounterReset_Sender"
        receiver_names = [f"F16_DL_CounterReset_R{i}" for i in range(3)]
        overrides = {
            sender_name: self._make_budgeted_f16_override(sender_name, 0, message_budget=2),
        }
        overrides.update({
            name: self._make_budgeted_f16_override(name, 0, message_budget=0)
            for name in receiver_names
        })

        kernel = self._kernel_with_overrides(overrides)
        kernel.set_time_step(0.1)

        sender = self._spawn_f16(kernel, ef_py.Side.Blue, sender_name, 0.0, 0.0)
        for idx, name in enumerate(receiver_names):
            self._spawn_f16(kernel, ef_py.Side.Blue, name, -3_000.0 + (idx * 3_000.0), 10_000.0, heading=180.0)

        kernel.send_message_command(
            sender,
            0,
            int(ef_py.CommMsgType.AssignTask),
            451,
        )
        kernel.step()

        active_state = self._get_data_link_state(kernel, sender)
        self.assertEqual(active_state["messages_sent_last"], 2)
        self.assertEqual(active_state["messages_dropped_last"], 1)
        self.assertEqual(active_state["messages_sent_total"], 2)
        self.assertEqual(active_state["messages_dropped_total"], 1)
        self.assertEqual(active_state["reports_sent_last"], 0)
        self.assertEqual(active_state["reports_dropped_last"], 0)

        kernel.step()

        idle_state = self._get_data_link_state(kernel, sender)
        self.assertEqual(idle_state["messages_sent_last"], 0)
        self.assertEqual(idle_state["messages_dropped_last"], 0)
        self.assertEqual(idle_state["messages_sent_total"], 2)
        self.assertEqual(idle_state["messages_dropped_total"], 1)
        self.assertEqual(idle_state["reports_sent_last"], 0)
        self.assertEqual(idle_state["reports_dropped_last"], 0)


if __name__ == "__main__":
    unittest.main()
