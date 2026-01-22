# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Printer Proofreading** is a PDF comparison tool for validating printed materials against original designs. The repository contains three distinct implementations:

1. **PROOFREADING_WEB** - Flask web application with portable executable support
2. **STANDALONE_EXE** - Tkinter desktop application
3. **Legacy versions** - Earlier iterations (proofreading.py, proofreading_v2.py)

All implementations use SSIM (Structural Similarity Index) to compare PDF documents by converting them to images and calculating similarity scores.

## Project Structure

```
PROOFREADING/
├── proofreading.py              # Legacy version
├── proofreading_v2.py           # Improved legacy version
├── PrinterProofreading.spec     # PyInstaller spec for legacy
├── STANDALONE_EXE/              # Tkinter desktop application
│   ├── printer_proofreading.py  # Main application
│   └── requirements.txt
└── PROOFREADING_WEB/            # Flask web application
    ├── app.py                   # Development Flask server
    ├── launcher.py              # Portable executable launcher
    ├── build_portable.py        # Build script
    ├── requirements.txt
    ├── templates/               # HTML templates
    └── static/                  # CSS/JS/uploads
```

## Core Architecture

### File Matching Logic
All versions use an 8-character prefix matching system:
- Extract first 8 characters from filenames
- Match "Original/Design" files with "Imprimeur/Printer" files
- Example: `12345678_design.pdf` matches `12345678_print.pdf`
- **IMPORTANT**: Process ALL files from BOTH folders, not just matched pairs
  - First: Match all Original files with their Printer counterparts
  - Then: Add any Printer files that have no Original match
  - This ensures no files are missed in the comparison

### Image Comparison Pipeline
1. **PDF → Image**: Convert first page using PyMuPDF (fitz) at 2x resolution
2. **Preprocessing**:
   - Resize to common dimensions (800x800 max)
   - Convert to grayscale
   - Optional: Crop margins (STANDALONE_EXE only, default 5%)
3. **Similarity Calculation**: Use scikit-image SSIM on grayscale arrays
4. **Scoring**: Convert SSIM index to 0-100 percentage scale

### Key Dependencies
- **PyMuPDF (fitz)**: PDF rendering
- **Pillow (PIL)**: Image manipulation
- **scikit-image**: SSIM calculation
- **NumPy**: Array operations
- **Flask**: Web interface (PROOFREADING_WEB only)
- **tkinterdnd2**: Drag-and-drop (STANDALONE_EXE only)
- **NOTE**: `cv2` (opencv-python) and `imagehash` were removed as they were not used

## Development Commands

### PROOFREADING_WEB (Flask Web App)

**Install dependencies:**
```bash
cd PROOFREADING/PROOFREADING_WEB
pip install -r requirements.txt
```

**Run development server:**
```bash
python app.py
```
Server starts on http://127.0.0.1:5000

**Build portable executable:**
```bash
python build_portable.py
```
Creates `dist/LorealProofreading/LorealProofreading.exe` with bundled templates and static files.

**Run portable launcher (development):**
```bash
python launcher.py
```
Finds free port, starts server, opens browser automatically.

### STANDALONE_EXE (Tkinter Desktop)

**Install dependencies:**
```bash
cd PROOFREADING/STANDALONE_EXE
pip install -r requirements.txt
```

**Run application:**
```bash
python printer_proofreading.py
```

**Build executable:**
```bash
cd PROOFREADING
pyinstaller PrinterProofreading.spec
```
Creates `dist/PrinterProofreading.exe` (single-file, no console, with icon).

### Legacy Versions

**Run legacy Tkinter app:**
```bash
cd PROOFREADING
python proofreading_v2.py
```

## Key Implementation Details

### PROOFREADING_WEB Specifics
- **Upload handling**: Supports both ZIP files and individual PDFs
- **Filename preservation**: Original filenames are preserved (no secure_filename sanitization) to maintain code matching integrity
- **Temporary storage**: Uses `static/uploads/` (dev) or `%USERPROFILE%\ProofreadingUploads` (portable)
- **Auto-approval threshold**: Configurable (default 95%), files above threshold auto-approved
- **Export format**: CSV with filename, code, score, status columns
- **Port handling**: launcher.py automatically finds free port to avoid conflicts
- **Interface**: Side-by-side image comparison with navigation buttons (similar to Tkinter version)
- **Complete file processing**: Handles both matched pairs AND unmatched files from either folder

### STANDALONE_EXE Specifics
- **Drag-and-drop**: Uses tkinterdnd2 for folder selection
- **Crop mode**: Optional margin removal (default 5%) to ignore borders/bleeds
- **Adjustable threshold**: User can set similarity threshold (default 85%)
- **Manual review**: Side-by-side comparison with approve/reject workflow
- **CSV export**: Includes timestamp and user decisions

### Comparison Algorithm Tuning
- **Resolution**: 2x scale factor on PDF rendering balances quality vs performance
- **Thumbnail size**: 800x800 max prevents memory issues on large PDFs
- **SSIM parameters**: Uses default scikit-image settings, data_range auto-calculated
- **Score range**: Clamped 0-100 for display, but internal SSIM can be negative

## Common Patterns

### PDF Processing
```python
doc = fitz.open(pdf_path)
page = doc.load_page(0)  # First page only
pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x resolution
img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
doc.close()
```

### SSIM Comparison
```python
# Convert to grayscale, normalize
gray1 = np.mean(arr1, axis=2).astype(np.float32)
gray2 = np.mean(arr2, axis=2).astype(np.float32)

# Calculate SSIM
similarity_index = ssim(gray1, gray2, data_range=gray2.max() - gray2.min())
score = max(0, min(100, similarity_index * 100))  # Clamp to 0-100
```

### File Code Extraction
```python
def extract_code(filename):
    base_name = os.path.basename(filename)
    return base_name[:8] if len(base_name) >= 8 else base_name
```

## Building for Production

### Web Application Bundle
The `build_portable.py` script uses PyInstaller to create a self-contained executable:
- Bundles Flask, templates, static files
- Uses `--onedir` mode for easier updates
- Includes all hidden imports for Flask ecosystem
- Creates portable package that doesn't require Python installation

### Desktop Application Bundle
The `PrinterProofreading.spec` configures PyInstaller:
- Single-file executable (`--onefile` equivalent)
- No console window (`console=False`)
- UPX compression enabled
- Custom icon support

## Important Notes

### Platform Compatibility
- **Windows-focused**: Path handling and executable generation assume Windows
- **Font paths**: Hardcoded `arial.ttf` may fail on non-Windows systems
- **File paths**: Use `os.path.join()` and `os.path.expanduser()` for portability

### Performance Considerations
- **Memory**: Large PDFs at 2x resolution can consume significant memory
- **Processing time**: SSIM calculation is CPU-intensive, scales with image size
- **File limits**: Web app has 500MB upload limit configured

### Security Notes
- **Secret key**: Web app uses hardcoded secret key (should be environment variable in production)
- **File uploads**: Original filenames are preserved for matching; subdirectories are created as needed
- **Temporary files**: Not automatically cleaned up, requires manual deletion

## Recent Fixes (January 2026)

### Fixed Issues
1. **Filename Sanitization Bug**: Removed `secure_filename()` that was modifying file names and breaking the 8-character code matching
   - Files are now saved with their original names to preserve matching codes
   - Subdirectories are created as needed to support file.webkitRelativePath structure

2. **Incomplete File Processing**: Added logic to process ALL files from both folders
   - Previously only processed Original folder files
   - Now also processes Printer-only files that have no Original match
   - Prevents files from being silently ignored

3. **Web Interface**: Redesigned to match Tkinter desktop interface
   - Side-by-side image comparison (Original on left, Printer on right)
   - Navigation buttons (Previous/Next)
   - Validation buttons (Approve/Reject) with auto-navigation
   - Similarity bar with threshold line
   - Results table below for quick navigation

4. **Removed Unused Dependencies**: Cleaned up imports
   - Removed `imagehash` (was imported but never used)
   - Removed `cv2` / `opencv-python` (was imported but never used)

## Version Information
- **STANDALONE_EXE**: v1.0.0 (hardcoded in printer_proofreading.py)
- **PROOFREADING_WEB**: No explicit version tracking
