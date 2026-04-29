#!/usr/bin/env python3
import unittest
from unittest.mock import patch
from pathlib import Path
import sys
import importlib.util

# 1. Definimos la ruta exacta al script que tiene guiones en su nombre.
MODULE_PATH = Path(__file__).resolve().parents[1] / "merci-sitemap.py"

# 2. Usamos importlib para cargar el archivo dinámicamente asignándole un nombre seguro ('merci_sitemap').
# Esto sortea la limitación de Python que impide importar archivos con guiones medios.
spec = importlib.util.spec_from_file_location("merci_sitemap", str(MODULE_PATH))
merci_sitemap = importlib.util.module_from_spec(spec)
sys.modules["merci_sitemap"] = merci_sitemap
spec.loader.exec_module(merci_sitemap)

class TestSitemap(unittest.TestCase):
    @patch("merci_sitemap.SITEMAP_PATH")
    def test_update_lastmod_success(self, mock_path):
        content = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            '   <url><lastmod>2000-01-01</lastmod></url>\n'
            '</urlset>'
        )
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = content
        
        # Llamamos a la función usando el módulo que acabamos de inyectar
        merci_sitemap.update_lastmod()
        
        called_with = mock_path.write_text.call_args[0][0]
        self.assertNotIn("2000-01-01", called_with)
        self.assertIn("<lastmod>", called_with)

if __name__ == "__main__":
    unittest.main()