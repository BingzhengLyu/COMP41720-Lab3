# Converting Lab Report to PDF

## Option 1: Using Pandoc (Recommended)

### Install Pandoc

**macOS:**
```bash
brew install pandoc
brew install basictex  # For LaTeX support
```

**Linux:**
```bash
sudo apt-get install pandoc texlive
```

**Windows:**
Download from: https://pandoc.org/installing.html

### Convert to PDF

```bash
cd "/Users/xwys/Autumn Semester 2/Distributed Systems/Lab 3"

# Basic conversion
pandoc LAB_REPORT.md -o LAB_REPORT.pdf

# With table of contents and section numbers
pandoc LAB_REPORT.md -o LAB_REPORT.pdf \
  --toc \
  --number-sections \
  --pdf-engine=xelatex

# With custom formatting
pandoc LAB_REPORT.md -o LAB_REPORT.pdf \
  --toc \
  --number-sections \
  --pdf-engine=xelatex \
  -V geometry:margin=1in \
  -V fontsize=11pt \
  -V documentclass=report
```

## Option 2: Using VS Code Extension

1. Install "Markdown PDF" extension in VS Code
2. Open `LAB_REPORT.md`
3. Right-click in editor
4. Select "Markdown PDF: Export (pdf)"

## Option 3: Using Online Converter

1. Go to https://www.markdowntopdf.com/
2. Upload `LAB_REPORT.md`
3. Download generated PDF

## Option 4: Using Python (markdown2pdf)

```bash
pip install markdown2pdf
markdown2pdf LAB_REPORT.md LAB_REPORT.pdf
```

## Option 5: Using Typora

1. Download Typora: https://typora.io/
2. Open `LAB_REPORT.md`
3. File → Export → PDF

## Recommended: Pandoc with Custom Template

This gives the best results:

```bash
pandoc LAB_REPORT.md -o LAB_REPORT.pdf \
  --from markdown \
  --template eisvogel \
  --listings \
  --toc \
  --number-sections \
  --pdf-engine=xelatex
```

To get the eisvogel template:
```bash
# Download template
wget https://raw.githubusercontent.com/Wandmalfarbe/pandoc-latex-template/master/eisvogel.tex

# Place in pandoc templates directory
mkdir -p ~/.pandoc/templates/
mv eisvogel.tex ~/.pandoc/templates/
```

## Verification

After conversion, check that:
- [ ] All sections are present
- [ ] Code blocks are properly formatted
- [ ] Tables are readable
- [ ] Images/diagrams are included (if any)
- [ ] Page numbers are correct
- [ ] Table of contents is accurate

## Tips for Best Results

1. **Headers**: Ensure consistent header hierarchy
2. **Code Blocks**: Use proper syntax highlighting
3. **Tables**: Keep tables simple and readable
4. **Line Length**: Break long lines for better formatting
5. **Special Characters**: Avoid special unicode characters

## Troubleshooting

### Issue: LaTeX Error

**Solution:**
```bash
# Install full LaTeX distribution
brew install --cask mactex  # macOS
```

### Issue: Missing Fonts

**Solution:**
```bash
# Install additional fonts
brew tap homebrew/cask-fonts
brew install --cask font-dejavu
```

### Issue: Large File Size

**Solution:**
```bash
# Compress PDF
gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 \
   -dPDFSETTINGS=/ebook -dNOPAUSE -dQUIET -dBATCH \
   -sOutputFile=LAB_REPORT_compressed.pdf LAB_REPORT.pdf
```

## Quick Command for macOS

```bash
cd "/Users/xwys/Autumn Semester 2/Distributed Systems/Lab 3"

# If pandoc is installed
pandoc LAB_REPORT.md -o LAB_REPORT.pdf --toc --number-sections

# If not, install first
brew install pandoc
brew install basictex
```

## Final Check Before Submission

```bash
# Verify PDF created
ls -lh LAB_REPORT.pdf

# Open to review
open LAB_REPORT.pdf  # macOS
xdg-open LAB_REPORT.pdf  # Linux
start LAB_REPORT.pdf  # Windows
```

---

**Note**: The LAB_REPORT.md is already formatted professionally. Any of these methods will produce a good PDF. Pandoc with `--toc --number-sections` is recommended for academic submissions.

