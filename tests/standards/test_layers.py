"""Tests para standards/layers.py — setup_layers y LAYERS dict."""

import pytest
import ezdxf

from cad_copilot.standards.layers import setup_layers, LAYERS


class TestLayerDict:
    def test_layer_count(self):
        assert len(LAYERS) == 17

    def test_required_layers_present(self):
        required = ["A-WALL", "A-DOOR", "A-GLAZ", "A-ANNO-DIMS", "A-ANNO-TEXT", "A-ANNO-TTLB"]
        for layer in required:
            assert layer in LAYERS, f"Layer faltante: {layer}"

    def test_wall_layer_color(self):
        assert LAYERS["A-WALL"]["color"] == 7

    def test_door_layer_color(self):
        assert LAYERS["A-DOOR"]["color"] == 2

    def test_glaz_layer_color(self):
        assert LAYERS["A-GLAZ"]["color"] == 3

    def test_all_layers_have_required_keys(self):
        for name, props in LAYERS.items():
            assert "color" in props, f"Layer {name} sin color"
            assert "lineweight" in props, f"Layer {name} sin lineweight"
            assert "linetype" in props, f"Layer {name} sin linetype"


class TestSetupLayers:
    def test_creates_all_layers(self):
        doc = ezdxf.new("R2013", setup=True)
        setup_layers(doc)
        for name in LAYERS:
            assert name in doc.layers, f"Layer no creado: {name}"

    def test_wall_layer_exists(self):
        doc = ezdxf.new("R2013", setup=True)
        setup_layers(doc)
        assert "A-WALL" in doc.layers

    def test_wall_patt_layer_exists(self):
        doc = ezdxf.new("R2013", setup=True)
        setup_layers(doc)
        assert "A-WALL-PATT" in doc.layers

    def test_idempotent_no_error_on_double_call(self):
        """Llamar setup_layers dos veces no lanza error (guard por nombre)."""
        doc = ezdxf.new("R2013", setup=True)
        setup_layers(doc)
        setup_layers(doc)  # no debe fallar
        assert "A-WALL" in doc.layers

    def test_layer_color_set_correctly(self):
        doc = ezdxf.new("R2013", setup=True)
        setup_layers(doc)
        layer = doc.layers.get("A-WALL")
        assert layer.dxf.color == 7

    def test_door_layer_color_set(self):
        doc = ezdxf.new("R2013", setup=True)
        setup_layers(doc)
        layer = doc.layers.get("A-DOOR")
        assert layer.dxf.color == 2
