class MultiCameraTracker:
    def __init__(self):
        from deep_sort_realtime.deepsort_tracker import DeepSort

        self.trackers = {}
        self._tracker_type = DeepSort

    def update(self, detections, camera_id, frame=None):
        if frame is None:
            return detections

        tracker = self.trackers.setdefault(
            camera_id,
            self._tracker_type(max_age=30, n_init=2, nms_max_overlap=1.0),
        )
        raw_detections = []
        for detection in detections:
            x1, y1, x2, y2 = detection.bbox
            raw_detections.append(
                ([x1, y1, x2 - x1, y2 - y1], detection.confidence, detection.vehicle_type)
            )

        tracks = tracker.update_tracks(raw_detections, frame=frame)
        return [
            {
                "track_id": track.track_id,
                "camera_id": camera_id,
                "bbox": track.to_ltrb(),
                "confirmed": track.is_confirmed(),
            }
            for track in tracks
            if track.is_confirmed()
        ]
