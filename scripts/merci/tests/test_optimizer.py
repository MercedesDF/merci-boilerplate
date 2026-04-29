#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from unittest.mock import patch, MagicMock
import importlib.util
import sys
from pathlib import Path

# Cargar dinámicamente merci-optimizer.py (manejo del guion en el nombre)
REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = REPO_ROOT / "scripts" / "merci" / "merci-optimizer.py"

spec = importlib.util.spec_from_file_location("merci_optimizer", SCRIPT_PATH)
merci_optimizer = importlib.util.module_from_spec(spec)
sys.modules["merci_optimizer"] = merci_optimizer
spec.loader.exec_module(merci_optimizer)

class TestMerciOptimizer(unittest.TestCase):
    @patch("merci_optimizer.Image.open")
    @patch("merci_optimizer.Path.mkdir")
    @patch("merci_optimizer.Path.glob")
    def test_optimize_images(self, mock_glob, mock_mkdir, mock_image_open):
        # 1. Simular que glob encuentra un archivo "test.png"
        mock_file = MagicMock()
        mock_file.name = "test.png"
        mock_file.stem = "test"
        mock_glob.side_effect = [[mock_file], [], []]  # Para las llamadas de .png, .jpg, .jpeg

        # 2. Simular el objeto Imagen de Pillow (2000x1000px)
        mock_img_instance = MagicMock()
        mock_img_instance.width = 2000
        mock_img_instance.height = 1000
        mock_img_instance.mode = "RGBA"
        
        mock_converted = MagicMock()
        mock_converted.width = 2000
        mock_converted.height = 1000
        mock_img_instance.convert.return_value = mock_converted
        
        mock_image_open.return_value.__enter__.return_value = mock_img_instance
        
        # Simular el redimensionado
        mock_resized = MagicMock()
        mock_converted.resize.return_value = mock_resized

        # 3. Ejecutar la función
        merci_optimizer.optimize_images()

        # 4. Verificaciones (Aserciones)
        mock_mkdir.assert_called_once_with(exist_ok=True)
        # Debe redimensionar 4 veces
        self.assertEqual(mock_converted.resize.call_count, 4)
        # Debe guardar 5 veces en total: 1 original + 4 redimensionadas
        self.assertEqual(mock_converted.save.call_count, 1)
        self.assertEqual(mock_resized.save.call_count, 4)
        
        # Comprobar el guardado base
        args_base, _ = mock_converted.save.call_args_list[0]
        self.assertTrue(str(args_base[0]).endswith("test.webp"))
        
        # Comprobar el guardado redimensionado
        args_res, _ = mock_resized.save.call_args_list[0]
        self.assertTrue(str(args_res[0]).endswith("test-1920w.webp"))