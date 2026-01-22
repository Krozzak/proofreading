import PyInstaller.__main__
import os

# Configuration
app_name = "LorealProofreading"
script_name = "launcher.py"

# Build
PyInstaller.__main__.run([
    script_name,
    '--name=' + app_name,
    '--onedir',  # Un dossier au lieu d'un seul exe
    '--windowed',  # Sans console (optionnel)
    '--add-data=templates;templates',
    '--add-data=static;static',
    '--hidden-import=flask',
    '--hidden-import=werkzeug',
    '--hidden-import=jinja2',
    '--hidden-import=fitz',
    '--hidden-import=PIL',
    '--hidden-import=numpy',
    '--hidden-import=skimage',
    '--hidden-import=skimage.metrics',
    '--hidden-import=skimage.metrics._structural_similarity',
    '--hidden-import=scipy',
    '--hidden-import=scipy.ndimage',
    '--collect-submodules=skimage',
    '--collect-submodules=scipy',
    '--collect-data=skimage',
    '--clean',
    '--noconfirm',
])

print("\n✓ Build terminé !")
print(f"✓ Exécutable dans: dist\\{app_name}\\{app_name}.exe")