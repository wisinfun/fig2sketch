from .base import *
from converter import prototype, tree, artboard
from converter.positioning import Matrix
from sketchformat.layer_common import ClippingMaskMode, Rect
from sketchformat.style import *
import pytest
from unittest.mock import ANY

FIG_ARTBOARD = {
    **FIG_BASE,
    "type": "FRAME",
    "resizeToFit": False,
    "children": [],
}


@pytest.fixture
def no_prototyping(monkeypatch):
    monkeypatch.setattr(prototype, "prototyping_information", lambda _: {})


@pytest.mark.usefixtures("no_prototyping")
class TestArtboardBackgroud:
    def test_no_background(self):
        ab = tree.convert_node(FIG_ARTBOARD, "CANVAS")

        assert ab.hasBackgroundColor == False

    def test_disabled_background(self):
        ab = tree.convert_node(
            {
                **FIG_ARTBOARD,
                "fillPaints": [
                    {
                        "type": "SOLID",
                        "color": FIG_COLOR[0],
                        "opacity": 0.9,
                        "visible": False,
                    }
                ],
            },
            "CANVAS",
        )

        assert ab.hasBackgroundColor == False

    def test_simple_background(self):
        ab = tree.convert_node(
            {
                **FIG_ARTBOARD,
                "fillPaints": [
                    {
                        "type": "SOLID",
                        "color": FIG_COLOR[0],
                        "opacity": 0.9,
                        "visible": True,
                    }
                ],
            },
            "CANVAS",
        )

        assert ab.hasBackgroundColor == True
        assert ab.backgroundColor == SKETCH_COLOR[0]

    def test_gradient_background(self, warnings):
        ab = tree.convert_node(
            {
                **FIG_ARTBOARD,
                "fillPaints": [
                    {
                        "type": "GRADIENT_LINEAR",
                        "transform": Matrix([[0.7071, -0.7071, 0.6], [0.7071, 0.7071, -0.1]]),
                        "stops": [
                            {"color": FIG_COLOR[0], "position": 0},
                            {"color": FIG_COLOR[1], "position": 0.4},
                            {"color": FIG_COLOR[2], "position": 1},
                        ],
                        "visible": True,
                    }
                ],
            },
            "CANVAS",
        )

        assert ab.hasBackgroundColor == False
        assert len(ab.layers) == 1
        bg = ab.layers[0]
        assert len(bg.style.fills) == 1
        assert bg.style.fills[0].fillType == FillType.GRADIENT

        warnings.assert_any_call("ART003", ANY)


class TestGrid:
    def _grid(self, spacing, color):
        return {
            "type": "STRETCH",
            "axis": "X",
            "visible": True,
            "numSections": 5,
            "offset": 0.0,
            "sectionSize": spacing,
            "gutterSize": 20.0,
            "color": color,
            "pattern": "GRID",
        }

    def test_single_grid(self):
        grid = artboard.convert_grid(
            {**FIG_ARTBOARD, "layoutGrids": [self._grid(20, FIG_COLOR[0])]}
        )

        assert grid.isEnabled == True
        assert grid.gridSize == 20
        assert grid.thickGridTimes == 0

    def test_dual_multiple_grid(self):
        grid = artboard.convert_grid(
            {
                **FIG_ARTBOARD,
                "layoutGrids": [
                    self._grid(20, FIG_COLOR[0]),
                    self._grid(60, FIG_COLOR[0]),
                ],
            }
        )

        assert grid.isEnabled == True
        assert grid.gridSize == 20
        assert grid.thickGridTimes == 3

    def test_dual_nonmultiple_grid(self, warnings):
        grid = artboard.convert_grid(
            {
                **FIG_ARTBOARD,
                "layoutGrids": [
                    self._grid(15, FIG_COLOR[0]),
                    self._grid(50, FIG_COLOR[0]),
                ],
            }
        )

        assert grid.isEnabled == True
        assert grid.gridSize == 15
        assert grid.thickGridTimes == 0

        warnings.assert_any_call("GRD002", ANY)

    def test_triple_grid(self, warnings):
        grid = artboard.convert_grid(
            {
                **FIG_ARTBOARD,
                "layoutGrids": [
                    self._grid(15, FIG_COLOR[0]),
                    self._grid(30, FIG_COLOR[0]),
                    self._grid(45, FIG_COLOR[0]),
                ],
            }
        )

        assert grid.isEnabled == True
        assert grid.gridSize == 15
        assert grid.thickGridTimes == 2

        warnings.assert_any_call("GRD003", ANY)

    def test_triple_multiple_grid(self):
        grid = artboard.convert_grid(
            {
                **FIG_ARTBOARD,
                "layoutGrids": [
                    self._grid(15, FIG_COLOR[0]),
                    self._grid(25, FIG_COLOR[0]),
                    self._grid(45, FIG_COLOR[0]),
                ],
            }
        )

        assert grid.isEnabled == True
        assert grid.gridSize == 15
        assert grid.thickGridTimes == 3


class TestLayout:
    def _layout(self, axis="X", align="STRETCH", count=4, offset=0, spacing=20, gutter=10):
        return {
            "type": align,
            "axis": axis,
            "visible": True,
            "numSections": count,
            "offset": offset,
            "sectionSize": spacing,
            "gutterSize": gutter,
            "color": {"r": 0, "g": 0, "b": 0, "a": 0},
            "pattern": "STRIPES",
        }

    def test_4_columns(self):
        layout = artboard.convert_layout(
            {**FIG_ARTBOARD, "layoutGrids": [self._layout()]},
            Rect(x=0, y=0, width=110, height=0),
        )

        assert layout.isEnabled
        assert layout.drawVertical
        assert layout.totalWidth == 110
        assert layout.gutterWidth == 10
        assert layout.columnWidth == 20
        assert layout.numberOfColumns == 4

    def test_centered_columns(self):
        layout = artboard.convert_layout(
            {**FIG_ARTBOARD, "layoutGrids": [self._layout(align="CENTER")]},
            Rect(x=0, y=0, width=200, height=0),
        )

        assert layout.isEnabled
        assert layout.drawVertical
        assert layout.totalWidth == 110
        assert layout.gutterWidth == 10
        assert layout.columnWidth == 20
        assert layout.numberOfColumns == 4
        assert layout.horizontalOffset == 45

    def test_multiple_column_layouts(self, warnings):
        layout = artboard.convert_layout(
            {
                **FIG_ARTBOARD,
                "layoutGrids": [
                    self._layout(align="MIN", count=2147483647),
                    self._layout(),
                ],
            },
            Rect(x=0, y=0, width=200, height=0),
        )

        assert layout.isEnabled
        assert layout.drawVertical
        assert layout.totalWidth == 290
        assert layout.gutterWidth == 10
        assert layout.columnWidth == 20
        assert layout.numberOfColumns == 10
        assert layout.horizontalOffset == 0

        warnings.assert_any_call("GRD004", ANY)

    def test_row_layout(self):
        layout = artboard.convert_layout(
            {
                **FIG_ARTBOARD,
                "layoutGrids": [self._layout(axis="Y")],
            },
            Rect(x=0, y=0, width=200, height=110),
        )

        assert layout.isEnabled
        assert layout.drawHorizontal
        assert layout.totalWidth == 200
        assert layout.gutterHeight == 10
        assert layout.rowHeightMultiplication == 2

    def test_float_row_layout(self, warnings):
        layout = artboard.convert_layout(
            {
                **FIG_ARTBOARD,
                "layoutGrids": [self._layout(axis="Y", align="CENTER", spacing=27)],
            },
            Rect(x=0, y=0, width=200, height=110),
        )

        assert layout is None

        warnings.assert_any_call("GRD007", ANY)
        warnings.assert_any_call("GRD005", ANY)
        warnings.assert_any_call("GRD006", ANY)
