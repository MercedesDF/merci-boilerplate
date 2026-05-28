from pathlib import Path
import shutil

SCRATCH_DIR = Path("scratch/test_purge")
if SCRATCH_DIR.exists(): shutil.rmtree(SCRATCH_DIR)
shutil.copytree("assets", SCRATCH_DIR / "assets")

def purge_directory(path: Path, exclude: list = None):
    if not path.exists(): return
    if exclude is None: exclude = []
    
    for item in path.iterdir():
        if item.name in exclude: continue
        if item.is_dir(): shutil.rmtree(item)
        else: item.unlink()

img_dir = SCRATCH_DIR / "assets" / "images"
imagenes_a_conservar = ["favicon.ico", "favicon.png", "logo.png", "tu_logo.webp"]
purge_directory(img_dir, exclude=imagenes_a_conservar)

print("Exists tu_logo.webp before rename:", (img_dir / "tu_logo.webp").exists())
if (img_dir / "tu_logo.webp").exists():
    (img_dir / "tu_logo.webp").rename(img_dir / "logo.webp")

print("Files left:", list(img_dir.iterdir()))
