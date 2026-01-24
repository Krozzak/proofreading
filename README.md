# Printer Proofreading

A PDF comparison tool for validating printed materials against original designs using SSIM (Structural Similarity Index).

![Version](https://img.shields.io/badge/version-3.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## Overview

**Printer Proofreading** helps quality control teams compare original design PDFs with printer proofs to ensure print accuracy. The tool automatically detects content regions, ignoring margins and crop marks, to provide accurate similarity scores.

### Key Features

- **Smart Content Detection**: Automatically identifies the actual design content, ignoring margins, bleeds, and crop marks
- **Multi-page PDF Support**: Navigate and validate each page individually
- **Side-by-side Comparison**: View original and printer versions simultaneously
- **SSIM Scoring**: Objective similarity measurement with configurable thresholds
- **Manual Crop Adjustment**: Fine-tune detection when automatic detection is uncertain
- **Batch Processing**: Process entire folders of PDFs with 8-character code matching
- **Export Options**: CSV export and clipboard copy for reporting

## Screenshots

*Coming soon*

## Installation

### Prerequisites

- Python 3.8 or higher
- Windows (primary support), macOS/Linux (limited testing)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/printer-proofreading.git
cd printer-proofreading

# Install dependencies
pip install -r requirements.txt

# Run the application
cd PROOFREADING
python proofreading_v3.py
```

### Dependencies

```
Pillow>=9.0.0
PyMuPDF>=1.21.0
scikit-image>=0.19.0
numpy>=1.21.0
tkinterdnd2>=0.3.0
scipy>=1.7.0
```

## Usage

### 1. Select Folders

Launch the application and drag-and-drop (or click to browse) two folders:

- **DOSSIER DESIGN (ORIGINAL)**: Contains the original design PDFs
- **DOSSIER IMPRIMEUR**: Contains the printer proof PDFs

### 2. File Matching

Files are automatically matched using an **8-character prefix** system:

- `12345678_design_v1.pdf` matches `12345678_printer.pdf`
- Both files share the same litho code (first 8 characters)

### 3. Review and Validate

- Navigate between PDFs using "PDF Pr??c??dent" / "PDF Suivant"
- For multi-page PDFs, use "Page pr??c." / "Page suiv."
- Click "Approuver" or "Rejeter" for each page
- All pages must be validated before moving to the next PDF

### 4. Export Results

- **CSV Export**: File > Exporter en CSV
- **Clipboard**: Copy results directly to paste into Excel

## Features in Detail

### Content Detection (V3)

The tool uses a hybrid detection approach:

1. **Threshold-based detection**: Identifies non-white pixels to find content boundaries
2. **Edge detection (Canny)**: For white-on-white designs ("space savers")
3. **Fallback**: Uses full image when detection confidence is low

Visual indicators show detection confidence:

- Green outline: High confidence (>70%)
- Yellow outline: Medium confidence (50-70%)
- Gray button: Full image used (detection uncertain)

### Manual Crop Adjustment

When automatic detection fails:

1. Click "Ajuster zone..."
2. Select "Ajuster Original" or "Ajuster Imprimeur"
3. Draw a rectangle around the content area
4. The similarity score recalculates automatically

### Multi-page Support

- Page indicator shows current position (e.g., "Page 2/5")
- Validation status tracks pages: "2/5 pages valid??es"
- PDF marked "Approved" only when ALL pages are approved
- PDF marked "Rejected" if ANY page is rejected

### Similarity Threshold

- Default threshold: 85%
- Adjustable via slider (0-100%)
- Scores above threshold show green, below show red
- Can be disabled entirely for visual-only comparison

## Project Structure

```
PROOFREADING/
????????? proofreading_v3.py      # Main application (recommended)
????????? proofreading_v2.py      # Previous version
????????? proofreading.py         # Legacy version
????????? PROOFREADING_WEB/       # Flask web application
    ????????? app.py
    ????????? launcher.py
    ????????? build_portable.py
    ????????? templates/
    ????????? static/
```

## Building Executables

### Desktop Application (PyInstaller)

```bash
cd PROOFREADING
pyinstaller PrinterProofreading.spec
```

Output: `dist/PrinterProofreading.exe`

### Web Application (Portable)

```bash
cd PROOFREADING/PROOFREADING_WEB
python build_portable.py
```

Output: `dist/LorealProofreading/LorealProofreading.exe`

## Configuration

### Options Menu

- **Activer le score de similarit??**: Toggle similarity calculation on/off
- **D??tection auto du contenu**: Enable/disable automatic content detection
- **Afficher zone d??tect??e**: Show/hide the detection overlay rectangle

### Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Previous PDF | Left Arrow |
| Next PDF | Right Arrow |
| Approve | Enter |
| Reject | Backspace |

## Technical Details

### SSIM Calculation

```python
# Images are preprocessed before comparison:
# 1. Content region detected and cropped
# 2. Resized to 800x800 with aspect ratio preserved
# 3. Converted to grayscale
# 4. SSIM calculated using scikit-image
```

### PDF Rendering

- Uses PyMuPDF (fitz) for PDF to image conversion
- 2x resolution matrix for high-quality rendering
- Supports multi-page documents

## Troubleshooting

### Common Issues

**"Could not load PDF"**

- Ensure the file is a valid PDF
- Check file permissions
- Try opening the file in another PDF viewer

**Low similarity scores for identical content**

- Use manual crop adjustment to exclude margins
- Disable auto-detection if results are inconsistent
- Check that both PDFs have the same page count

**Application won't start**

- Verify Python version (3.8+)
- Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`
- Check for tkinterdnd2 compatibility issues

### Performance Tips

- Close other applications when processing large batches
- PDFs with many pages consume more memory
- Consider processing in smaller batches for 100+ files

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [PyMuPDF](https://pymupdf.readthedocs.io/) for PDF rendering
- [scikit-image](https://scikit-image.org/) for SSIM implementation
- [tkinterdnd2](https://github.com/pmgagne/tkinterdnd2) for drag-and-drop support

## Version History

### v3.0.0 (Current)

- Smart content detection (threshold + edge-based)
- Manual crop adjustment interface
- Multi-page PDF support with per-page validation
- Option to disable similarity scoring
- Improved UI with compact similarity bar

### v2.0.0

- Basic SSIM comparison
- Side-by-side view
- CSV export
- 8-character code matching

### v1.0.0

- Initial release
- Single-page comparison
- Basic validation workflow
