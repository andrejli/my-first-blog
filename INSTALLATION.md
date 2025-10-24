# Installation Instructions for Different Python Environments

## 🐧 Debian 13 / Python 3.13 Installation

For Debian 13 users experiencing issues with `markdown-math` package compatibility:

```bash
# Use the Python 3.13 compatible requirements
pip install -r requirements-python313.txt

# Or install manually without markdown-math:
pip install Django>=5.2.0 Pillow>=10.0.0 django-crispy-forms>=2.0
pip install markdown>=3.6.0 pygments>=2.17.0 pymdown-extensions>=10.7.0
```

## 🚀 Quick Fix for Existing Issues

If you're getting `markdown-math` installation errors:

```bash
# Remove the problematic package from pip cache
pip cache purge

# Install without markdown-math (it's not actually used)
pip install -r requirements-python313.txt
```

## 📋 Platform-Specific Instructions

### **Debian 13 / Ubuntu 24+ (Python 3.13)**
```bash
pip install -r requirements-python313.txt
```

### **CentOS / RHEL / Fedora (Python 3.9-3.12)**
```bash
pip install -r requirements-legacy.txt
```

### **Windows / macOS (Any Python 3.9+)**
```bash
pip install -r requirements.txt
```

## 🔧 Math Equation Support

**Important:** Math equations are handled by **MathJax** in the frontend, not by the `markdown-math` Python package.

The system supports LaTeX math syntax:
- Inline math: `$E = mc^2$`
- Display math: `$$\int_{0}^{\infty} e^{-x} dx = 1$$`

This works in all environments without needing the `markdown-math` package.

## 🐛 Troubleshooting

### Error: "No module named 'markdown-math'"
**Solution:** Use `requirements-python313.txt` which doesn't include this package.

### Error: "Failed building wheel for markdown-math"
**Solution:** The package isn't needed. Use the updated requirements files.

### Math equations not rendering
**Check:** Ensure MathJax is loaded in your browser (check browser console for errors).

## 📦 Package Differences

| Package | Legacy | Python 3.13 | Used For |
|---------|--------|--------------|----------|
| markdown-math | ❌ Optional | ❌ Removed | Server-side math (not used) |
| MathJax | ✅ Frontend | ✅ Frontend | Client-side math rendering |
| markdown | ✅ 3.5.0+ | ✅ 3.6.0+ | Core markdown processing |
| pygments | ✅ 2.16.0+ | ✅ 2.17.0+ | Syntax highlighting |

## 🎯 Recommended Installation

**For new installations:**
```bash
# Clone the repository
git clone <repository-url>
cd my-first-blog

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies based on your Python version
pip install -r requirements-python313.txt  # Python 3.13+
# or
pip install -r requirements.txt           # Python 3.9-3.12

# Run Django setup
python manage.py migrate
python manage.py collectstatic
python manage.py runserver
```

Math equations will work automatically via MathJax in the browser! 🎉