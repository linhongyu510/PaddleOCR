"""Unit tests for the robustness benchmark's degradation and preprocessing functions.

These are pure image transforms, and the failure mode that matters is a silent
no-op: a degradation that returns something indistinguishable from its input would
make the benchmark report a reassuring number while testing nothing. Each test
therefore asserts the transform actually changed the image in the intended way.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

ROOT = Path(__file__).parents[2]
_spec = importlib.util.spec_from_file_location(
    "_robustness", ROOT / "benchmarks" / "run_robustness_benchmark.py"
)
assert _spec and _spec.loader
robustness = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(robustness)


@pytest.fixture
def sample() -> Image.Image:
    """A light page with dark text-like bars, so blur and lighting are measurable."""
    array = np.full((80, 200, 3), 250, dtype=np.uint8)
    array[20:30, 20:180] = 10
    array[50:60, 20:180] = 10
    return Image.fromarray(array)


def _edge_steepness(image: Image.Image) -> float:
    """Steepest horizontal step in the image; falls sharply when edges are smeared.

    Deliberately not the *mean* gradient: total variation across a step is conserved
    under blur (measured 480.0 both before and after a 15px smear), so a mean-gradient
    metric is blind to blur by construction.
    """
    grey = np.asarray(image.convert("L"), dtype=np.float32)
    return float(np.abs(np.diff(grey, axis=1)).max())


def test_motion_blur_reduces_edge_steepness(sample: Image.Image) -> None:
    blurred = robustness._motion_blur(sample, 15, 0.0)
    assert blurred.size == sample.size
    assert _edge_steepness(blurred) < _edge_steepness(sample) * 0.5


def test_motion_blur_is_directional(sample: Image.Image) -> None:
    """A horizontal smear must differ from a diagonal one, or angle is ignored."""
    horizontal = np.asarray(robustness._motion_blur(sample, 15, 0.0), dtype=np.int16)
    diagonal = np.asarray(robustness._motion_blur(sample, 15, 45.0), dtype=np.int16)
    assert np.abs(horizontal - diagonal).mean() > 1.0


def test_motion_blur_of_length_one_is_close_to_identity(sample: Image.Image) -> None:
    result = robustness._motion_blur(sample, 1, 0.0)
    assert (
        np.abs(np.asarray(result, dtype=np.int16) - np.asarray(sample, dtype=np.int16)).max() <= 1
    )


def test_motion_blur_does_not_mutate_its_input(sample: Image.Image) -> None:
    before = np.array(sample)
    robustness._motion_blur(sample, 9, 20.0)
    assert np.array_equal(np.array(sample), before)


def test_uneven_illumination_creates_a_horizontal_gradient(sample: Image.Image) -> None:
    lit = np.asarray(robustness._uneven_illumination(sample, 0.65).convert("L"), dtype=np.float32)
    left = lit[:, : lit.shape[1] // 4].mean()
    right = lit[:, -lit.shape[1] // 4 :].mean()
    # The far side must be materially darker, otherwise it is a global dim.
    assert left > right * 1.3


def test_shadow_darkens_only_part_of_the_frame(sample: Image.Image) -> None:
    shadowed = np.asarray(robustness._shadow(sample).convert("L"), dtype=np.float32)
    original = np.asarray(sample.convert("L"), dtype=np.float32)
    left = shadowed[:, :40].mean()
    right = shadowed[:, -40:].mean()
    assert left < right * 0.8
    # The unshadowed side should be essentially untouched.
    assert right > original[:, -40:].mean() * 0.9


def test_paper_texture_adds_noise_without_destroying_structure(sample: Image.Image) -> None:
    textured = robustness._paper_texture(sample, 12.0)
    delta = np.asarray(textured, dtype=np.float32) - np.asarray(sample, dtype=np.float32)
    assert delta.std() > 1.0
    # Text bars must remain far darker than the page.
    grey = np.asarray(textured.convert("L"), dtype=np.float32)
    assert grey[20:30, 20:180].mean() < grey[0:10, 0:10].mean() - 100


def test_paper_texture_is_deterministic(sample: Image.Image) -> None:
    """A fixed seed keeps benchmark runs comparable."""
    first = np.asarray(robustness._paper_texture(sample, 12.0))
    second = np.asarray(robustness._paper_texture(sample, 12.0))
    assert np.array_equal(first, second)


def test_perspective_preserves_size_but_moves_content(sample: Image.Image) -> None:
    skewed = robustness._perspective(sample, 0.16)
    assert skewed.size == sample.size
    difference = np.abs(
        np.asarray(skewed, dtype=np.int16) - np.asarray(sample, dtype=np.int16)
    ).mean()
    assert difference > 1.0


def test_illumination_flatten_removes_a_gradient(sample: Image.Image) -> None:
    """The local pipeline must actually equalise lighting, or its negative
    benchmark result would be meaningless."""
    lit = robustness._uneven_illumination(sample, 0.65)
    before = np.asarray(lit.convert("L"), dtype=np.float32)
    after = np.asarray(robustness._illumination_flatten(lit).convert("L"), dtype=np.float32)

    def imbalance(frame: np.ndarray) -> float:
        quarter = frame.shape[1] // 4
        return abs(frame[:, :quarter].mean() - frame[:, -quarter:].mean())

    assert imbalance(after) < imbalance(before) * 0.5


def test_every_registered_degradation_changes_the_image(sample: Image.Image) -> None:
    """A degradation that is a no-op would silently weaken the benchmark."""
    for tier, entries in robustness.DEGRADATIONS.items():
        for name, transform in entries.items():
            result = transform(sample)
            assert isinstance(result, Image.Image), f"{tier}/{name}"
            if result.size != sample.size:
                continue
            difference = np.abs(
                np.asarray(result.convert("RGB"), dtype=np.int16)
                - np.asarray(sample, dtype=np.int16)
            ).mean()
            assert difference > 0.05, f"{tier}/{name} barely changed the image"


def test_every_preprocessor_returns_a_usable_rgb_image(sample: Image.Image) -> None:
    for name, preprocessor in robustness.PREPROCESSORS.items():
        result = preprocessor(sample)
        assert isinstance(result, Image.Image), name
        assert result.convert("RGB").size[0] >= sample.size[0], name


def test_degradation_tiers_have_no_duplicate_names() -> None:
    """`--compare-preprocess` merges severe and capture into one dict."""
    seen: set[str] = set()
    for entries in robustness.DEGRADATIONS.values():
        overlap = seen & set(entries)
        assert not overlap, f"duplicate degradation names would be lost: {overlap}"
        seen |= set(entries)
