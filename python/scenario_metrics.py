import json
import os


class ScenarioLogger:
    def __init__(self, path, metadata):
        self.path = path
        self._handle = None

        if not path:
            return

        dir_name = os.path.dirname(path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        self._handle = open(path, "w", encoding="utf-8")
        self._write({"type": "meta", "data": metadata})

    def _write(self, record):
        if not self._handle:
            return
        self._handle.write(json.dumps(record, ensure_ascii=True))
        self._handle.write("\n")

    def log_tick(self, tick_index, sim_time, entities, detections):
        serialized = {}
        for name, contacts in detections.items():
            serialized[name] = [
                {
                    "target_id": det.target_id,
                    "range": det.range,
                    "bearing": det.bearing,
                    "timestamp": det.timestamp,
                }
                for det in contacts
            ]

        record = {
            "type": "tick",
            "tick": tick_index,
            "sim_time": sim_time,
            "entities": entities,
            "detections": serialized,
        }
        self._write(record)

    def close(self):
        if self._handle:
            self._handle.close()
            self._handle = None


class ScenarioMetrics:
    def __init__(self, entity_names):
        self.entity_names = list(entity_names)
        self.min_range = None
        self.first_detection_time = None
        self.detection_count = 0
        self.destroyed = {}

    def update(self, sim_time, positions, detections, healths):
        # Min range across all pairs
        names = self.entity_names
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a = positions[names[i]]
                b = positions[names[j]]
                dx = a[0] - b[0]
                dy = a[1] - b[1]
                dz = a[2] - b[2]
                dist = (dx * dx + dy * dy + dz * dz) ** 0.5
                if self.min_range is None or dist < self.min_range:
                    self.min_range = dist

        tick_detections = 0
        for name, contacts in detections.items():
            if contacts:
                tick_detections += len(contacts)
                if self.first_detection_time is None:
                    self.first_detection_time = sim_time

        self.detection_count += tick_detections

        for name, hp in healths.items():
            if hp[0] <= 0 and name not in self.destroyed:
                self.destroyed[name] = sim_time

    def summary(self):
        return {
            "min_range": self.min_range,
            "first_detection_time": self.first_detection_time,
            "detection_count": self.detection_count,
            "destroyed": self.destroyed,
        }
