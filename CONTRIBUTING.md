# Contributing to Printer Proofreading

Thank you for your interest in contributing to Printer Proofreading! This document provides guidelines and information for contributors.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## How to Contribute

### Reporting Bugs

1. **Check existing issues** to avoid duplicates
2. **Create a new issue** with:
   - Clear, descriptive title
   - Steps to reproduce the bug
   - Expected vs actual behavior
   - Your environment (OS, Python version)
   - Screenshots if applicable
   - Sample files (if possible, anonymized)

### Suggesting Features

1. **Check existing feature requests**
2. **Create a new issue** with:
   - Clear description of the feature
   - Use case / problem it solves
   - Proposed implementation (optional)
   - Mockups if applicable

### Submitting Code

#### Setup Development Environment

```bash
# Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/printer-proofreading.git
cd printer-proofreading

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest black flake8
```

#### Development Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow the existing code style
   - Add comments for complex logic
   - Update documentation if needed

3. **Test your changes**
   ```bash
   # Run the application
   cd PROOFREADING
   python proofreading_v3.py

   # Test with various PDF files
   # Verify multi-page support
   # Check edge cases
   ```

4. **Format your code**
   ```bash
   black PROOFREADING/proofreading_v3.py
   flake8 PROOFREADING/proofreading_v3.py
   ```

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add description of your feature"
   ```

6. **Push and create a Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

### Commit Message Format

Use conventional commits format:

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

Examples:
```
feat(detection): add edge-based content detection for white designs
fix(pdf): handle corrupted PDF files gracefully
docs(readme): update installation instructions
```

## Code Style Guidelines

### Python

- Follow PEP 8
- Use type hints where helpful
- Maximum line length: 100 characters
- Use descriptive variable names
- Add docstrings for public methods

```python
def calculate_similarity(self, img1: Image, img2: Image) -> float:
    """
    Calculate SSIM similarity between two images.

    Args:
        img1: Original design image
        img2: Printer proof image

    Returns:
        Similarity score between 0.0 and 1.0

    Raises:
        ValueError: If images are None or empty
    """
```

### GUI Code

- Use descriptive widget names (`self.approve_button`, not `self.btn1`)
- Group related UI elements in frames
- Use constants for colors and fonts
- Support keyboard navigation where possible

### Comments

- Comment the "why", not the "what"
- Keep comments up to date with code changes
- Use TODO comments for future work: `# TODO: implement batch mode`

## Testing

### Manual Testing Checklist

Before submitting a PR, verify:

- [ ] Application starts without errors
- [ ] Folder selection works (drag-drop and browse)
- [ ] PDF files load correctly
- [ ] Multi-page PDFs navigate properly
- [ ] Content detection shows overlay
- [ ] Manual crop adjustment works
- [ ] Validation updates the list correctly
- [ ] CSV export contains correct data
- [ ] All pages must be validated before moving to next PDF

### Test Files

If your change affects PDF handling or comparison:
1. Test with single-page PDFs
2. Test with multi-page PDFs (2-5 pages)
3. Test with mismatched page counts
4. Test with "Original only" and "Printer only" scenarios
5. Test with white-on-white designs

## Documentation

- Update README.md for user-facing changes
- Update docs/DOCUMENTATION.md for technical changes
- Add inline documentation for new functions
- Include examples where helpful

## Questions?

Feel free to:
- Open an issue for questions
- Start a discussion in GitHub Discussions
- Reach out to maintainers

## Recognition

Contributors will be recognized in:
- The project README
- Release notes
- Our appreciation!

Thank you for contributing!
