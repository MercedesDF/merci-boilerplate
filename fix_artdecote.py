import os
import glob
import re

files = glob.glob("art-de-cote/*.md")

for filepath in files:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    if "subtema:" not in content:
        content = re.sub(r'tema: (.*)', r'tema: \1\nsubtema: "General"\ndestacado: "false"', content)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Updated {filepath}")
