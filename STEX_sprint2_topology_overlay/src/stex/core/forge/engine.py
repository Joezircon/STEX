from __future__ import annotations

import cv2
import numpy as np
from PIL import Image

from .models import ForgeProblem, ForgeReport


class ForgeEngine:
    """
    Forge is the manufacturability engine inside STEX.

    Current API:
    - inspect_file()
    - inspect_array()
    - detect unsupported white islands
    """

    def __init__(self, threshold: int = 180, min_island_area: int = 40):
        self.threshold = threshold
        self.min_island_area = min_island_area

    def inspect_file(self, image_path: str) -> ForgeReport:
        image = Image.open(image_path).convert("RGB")
        arr = np.array(image)
        return self.inspect_array(arr)

    def inspect_array(self, rgb_array: np.ndarray) -> ForgeReport:
        height, width = rgb_array.shape[:2]

        gray = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2GRAY)
        white_mask = gray >= self.threshold

        outside_connected_white = self._flood_from_edges(white_mask)
        island_mask = white_mask & (~outside_connected_white)

        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            island_mask.astype(np.uint8),
            connectivity=8,
        )

        problems: list[ForgeProblem] = []
        island_number = 0

        for label in range(1, num_labels):
            area = int(stats[label, cv2.CC_STAT_AREA])
            if area < self.min_island_area:
                continue

            island_number += 1

            x = int(stats[label, cv2.CC_STAT_LEFT])
            y = int(stats[label, cv2.CC_STAT_TOP])
            w = int(stats[label, cv2.CC_STAT_WIDTH])
            h = int(stats[label, cv2.CC_STAT_HEIGHT])
            cx, cy = centroids[label]

            problems.append(
                ForgeProblem(
                    problem_type="white_island",
                    severity="critical",
                    label=f"White Island {island_number}",
                    message="Unsupported white material would fall out after cutting.",
                    bbox=(x, y, w, h),
                    centroid=(int(cx), int(cy)),
                    area_px=area,
                    metadata={"component_label": int(label)},
                )
            )

        return ForgeReport(width, height, problems)

    def _flood_from_edges(self, white_mask: np.ndarray) -> np.ndarray:
        height, width = white_mask.shape
        flood = white_mask.astype(np.uint8) * 255
        mask = np.zeros((height + 2, width + 2), dtype=np.uint8)

        for x in range(width):
            if flood[0, x] == 255:
                cv2.floodFill(flood, mask, (x, 0), 128)
            if flood[height - 1, x] == 255:
                cv2.floodFill(flood, mask, (x, height - 1), 128)

        for y in range(height):
            if flood[y, 0] == 255:
                cv2.floodFill(flood, mask, (0, y), 128)
            if flood[y, width - 1] == 255:
                cv2.floodFill(flood, mask, (width - 1, y), 128)

        return flood == 128
