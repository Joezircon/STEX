from stex.core.forge import ForgeEngine
import numpy as np


def test_empty_white_image_is_cut_ready():
    image = np.ones((100, 100, 3), dtype=np.uint8) * 255
    forge = ForgeEngine()
    report = forge.inspect_array(image)

    assert report.is_cut_ready
    assert report.white_island_count == 0


def test_white_island_inside_black_region_is_detected():
    image = np.ones((200, 200, 3), dtype=np.uint8) * 255

    # black cutout
    image[40:160, 40:160] = 0

    # unsupported white island
    image[90:110, 90:110] = 255

    forge = ForgeEngine(min_island_area=10)
    report = forge.inspect_array(image)

    assert not report.is_cut_ready
    assert report.white_island_count == 1
