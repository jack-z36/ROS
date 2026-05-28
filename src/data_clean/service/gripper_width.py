"""ArUco-based gripper width extraction for MCAP image streams."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from repo.config.mcap_process_config import GripperStreamConfig


class GripperDetectionError(RuntimeError):
    """Raised when a gripper stream cannot produce any valid width samples."""


@dataclass(frozen=True)
class GripperExtractionResult:
    values: list[float]
    frame_count: int
    direct_detection_frames: int
    missing_frames: int
    interpolated_frames: int


def _build_detector_parameters():
    if hasattr(cv2.aruco, "DetectorParameters"):
        return cv2.aruco.DetectorParameters()
    return cv2.aruco.DetectorParameters_create()


class GripperWidthAccumulator:
    """Incrementally reproduces the documented gripper-width extraction pipeline."""

    def __init__(self, stream_config: GripperStreamConfig):
        self.stream_config = stream_config
        self.frame_count = 0
        self.detected_distances: list[int] = []
        self.detected_indices: list[int] = []
        try:
            dictionary_id = getattr(cv2.aruco, stream_config.aruco_dict)
        except AttributeError as exc:
            raise GripperDetectionError(f'unsupported ArUco dictionary "{stream_config.aruco_dict}"') from exc
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(dictionary_id)
        self.parameters = _build_detector_parameters()

    def consume(self, image: np.ndarray) -> None:
        self.frame_count += 1
        frame_index = self.frame_count

        gray = self._to_gray(image)
        corners, ids, _ = cv2.aruco.detectMarkers(gray, self.aruco_dict, parameters=self.parameters)
        if ids is None:
            return

        marker_centers = []
        for idx, marker_id in enumerate(ids.flatten()):
            if marker_id in (self.stream_config.marker_id_0, self.stream_config.marker_id_1):
                marker_corners = corners[idx][0]
                center = np.mean(marker_corners, axis=0)
                marker_centers.append(center)

        if len(marker_centers) >= 2:
            distance = float(np.linalg.norm(marker_centers[0] - marker_centers[1]))
        elif len(marker_centers) == 1:
            distance = float(abs(gray.shape[1] / 2 - marker_centers[0][0]) * 2)
        else:
            return

        mapped_distance = self._map_pixel_distance(distance)
        self.detected_distances.append(mapped_distance)
        self.detected_indices.append(frame_index)

    def finalize(self) -> GripperExtractionResult:
        if self.frame_count == 0:
            raise GripperDetectionError(f'gripper stream "{self.stream_config.image_topic}" has no image frames')
        if not self.detected_distances:
            raise GripperDetectionError(
                f'gripper stream "{self.stream_config.image_topic}" could not detect any valid markers'
            )

        completed = self._interpolate_distances()
        normalized = [value / self.stream_config.gripper_max for value in completed]
        missing_frames = self.frame_count - len(self.detected_indices)
        return GripperExtractionResult(
            values=normalized,
            frame_count=self.frame_count,
            direct_detection_frames=len(self.detected_indices),
            missing_frames=missing_frames,
            interpolated_frames=missing_frames,
        )

    def _map_pixel_distance(self, distance: float) -> int:
        normalized = (
            (distance - self.stream_config.marker_min)
            / (self.stream_config.marker_max - self.stream_config.marker_min)
            * self.stream_config.gripper_max
        )
        clipped = np.clip(normalized, 0, self.stream_config.gripper_max)
        return int(clipped)

    def _interpolate_distances(self) -> list[int]:
        if len(self.detected_distances) == 1:
            return [self.detected_distances[0]] * self.frame_count

        result = [None] * self.frame_count
        for index, value in zip(self.detected_indices, self.detected_distances):
            result[index - 1] = value

        first_index = self.detected_indices[0] - 1
        for i in range(first_index):
            result[i] = self.detected_distances[0]

        for (start_index, start_value), (end_index, end_value) in zip(
            zip(self.detected_indices[:-1], self.detected_distances[:-1]),
            zip(self.detected_indices[1:], self.detected_distances[1:]),
        ):
            result[start_index - 1] = start_value
            gap = end_index - start_index
            if gap > 1:
                for k in range(1, gap):
                    interpolated = int(k * (end_value - start_value) / gap + start_value)
                    result[start_index - 1 + k] = interpolated
            result[end_index - 1] = end_value

        last_index = self.detected_indices[-1] - 1
        for i in range(last_index + 1, self.frame_count):
            result[i] = self.detected_distances[-1]

        return [int(value) for value in result]

    @staticmethod
    def _to_gray(image: np.ndarray) -> np.ndarray:
        if image.ndim == 2:
            return np.ascontiguousarray(image, dtype=np.uint8)
        if image.ndim != 3:
            raise GripperDetectionError(f"unsupported image rank for gripper detection: {image.ndim}")
        gray = cv2.cvtColor(np.ascontiguousarray(image, dtype=np.uint8), cv2.COLOR_BGR2GRAY)
        return np.ascontiguousarray(gray, dtype=np.uint8)
