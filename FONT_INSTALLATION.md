# 🎨 Arabic Font Installation Guide

This guide explains how to install the required Arabic fonts for proper PDF generation with Arabic text support.

## 🚨 Why Fonts Are Needed

Without proper Arabic fonts, the generated PDFs will show Arabic text as boxes (■■■■) instead of readable text.

## 📥 Method 1: Automatic Download (Recommended)

Run the font download script:

```bash
python download_fonts.py
```

## 📥 Method 2: Manual Download from Google Fonts

### Step 1: Visit Google Fonts
Go to: https://fonts.google.com/noto/specimen/Noto+Naskh+Arabic

### Step 2: Download Font Family
1. Click "Download family"
2. Extract the ZIP file
3. Look for the TTF files

### Step 3: Place Fonts in Project
1. Copy the TTF files to the `fonts/` directory
2. Rename them to:
   - `NotoNaskhArabic-Regular.ttf`
   - `NotoNaskhArabic-Bold.ttf`

## 📥 Method 3: System Font Installation

### macOS
1. Download the fonts from Google Fonts
2. Double-click each TTF file
3. Click "Install Font"
4. The app will automatically detect them

### Windows
1. Download the fonts from Google Fonts
2. Right-click each TTF file
3. Select "Install"
4. The app will automatically detect them

### Linux
1. Download the fonts from Google Fonts
2. Copy TTF files to `~/.local/share/fonts/`
3. Run `fc-cache -fv`
4. The app will automatically detect them

## 🔍 Verify Font Installation

After installing fonts, restart the Streamlit app. You should see:

```
✅ تم تسجيل الخطوط العربية بنجاح!
```

Instead of:

```
⚠️ استخدام خط النظام: Helvetica
```

## 🛠️ Troubleshooting

### Font Files Not Found
```
❌ خطأ في تسجيل الخطوط العربية: [Errno 2] No such file or directory
```

**Solution**: Ensure fonts are in the `fonts/` directory

### Invalid Font Files
```
❌ خطأ في تسجيل الخطوط العربية: Not a recognized TrueType font
```

**Solution**: Re-download fonts from Google Fonts

### Font Registration Fails
```
❌ خطأ في تسجيل الخطوط العربية: Permission denied
```

**Solution**: Check file permissions and ensure fonts are readable

## 📁 Directory Structure

Your project should look like this:

```
tem/
├── fonts/
│   ├── NotoNaskhArabic-Regular.ttf  ← Required
│   └── NotoNaskhArabic-Bold.ttf     ← Required
├── app.py
├── download_fonts.py
└── FONT_INSTALLATION.md
```

## 🎯 Expected Results

### With Arabic Fonts:
- ✅ Arabic text renders properly in PDFs
- ✅ No boxes (■■■■) in generated PDFs
- ✅ Professional appearance
- ✅ Full RTL support

### Without Arabic Fonts:
- ⚠️ Arabic text shows as boxes
- ⚠️ Limited Arabic support
- ⚠️ Fallback to system fonts

## 🆘 Still Having Issues?

1. **Check font file size**: Should be > 100KB
2. **Verify file format**: Must be TrueType (.ttf)
3. **Check permissions**: Files should be readable
4. **Restart app**: After installing fonts
5. **Clear cache**: Delete `__pycache__/` directories

## 🔗 Alternative Font Sources

If Google Fonts doesn't work:

- **GitHub**: https://github.com/google/fonts
- **Font Squirrel**: https://www.fontsquirrel.com/
- **DaFont**: https://www.dafont.com/

## 📞 Support

For additional help:
1. Check the troubleshooting section above
2. Verify font files are properly installed
3. Ensure the app has read access to the fonts directory
