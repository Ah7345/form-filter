#!/usr/bin/env python3
"""
Fixed Font Download Script for Arabic Fonts
This script properly downloads the required Arabic fonts for the PDF generation.
"""

import requests
import os
from pathlib import Path

def download_font(url, filename):
    """Download font file with proper headers"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, allow_redirects=True)
        response.raise_for_status()
        
        # Check if we got HTML instead of TTF
        if response.text.startswith('<!DOCTYPE') or response.text.startswith('<html'):
            print(f"❌ {filename}: Got HTML instead of TTF file")
            return False
            
        # Save the file
        with open(filename, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ {filename}: Downloaded successfully ({len(response.content)} bytes)")
        return True
        
    except Exception as e:
        print(f"❌ {filename}: Download failed - {str(e)}")
        return False

def main():
    """Main download function"""
    # Create fonts directory
    fonts_dir = Path("fonts")
    fonts_dir.mkdir(exist_ok=True)
    
    # Font URLs to try
    font_urls = [
        # Direct CDN links
        ("https://cdn.jsdelivr.net/npm/@fontsource/noto-naskh-arabic@5.0.0/files/noto-naskh-arabic-latin-400-normal.woff2", "fonts/NotoNaskhArabic-Regular.ttf"),
        ("https://cdn.jsdelivr.net/npm/@fontsource/noto-naskh-arabic@5.0.0/files/noto-naskh-arabic-latin-700-normal.woff2", "fonts/NotoNaskhArabic-Bold.ttf"),
        
        # Alternative sources
        ("https://fonts.cdnfonts.com/css/noto-naskh-arabic", "fonts/NotoNaskhArabic-Regular.ttf"),
        ("https://fonts.cdnfonts.com/css/noto-naskh-arabic", "fonts/NotoNaskhArabic-Bold.ttf"),
    ]
    
    print("🔍 محاولة تحميل الخطوط العربية...")
    
    success_count = 0
    for url, filename in font_urls:
        if download_font(url, filename):
            success_count += 1
            break  # Stop after first success
    
    if success_count == 0:
        print("\n❌ فشل في تحميل الخطوط من المصادر المتاحة")
        print("\n💡 الحلول البديلة:")
        print("1. قم بتحميل الخطوط يدوياً من Google Fonts")
        print("2. استخدم خطوط النظام المتاحة")
        print("3. قم بتثبيت الخطوط على مستوى النظام")
        
        # Create a fallback font file
        print("\n🔄 إنشاء ملف خط بديل...")
        create_fallback_font()
    else:
        print(f"\n✅ تم تحميل {success_count} خط بنجاح!")

def create_fallback_font():
    """Create a simple fallback font configuration"""
    fallback_config = """# Fallback Font Configuration
# Since we couldn't download the Arabic fonts, we'll use system fonts

# For macOS, try these fonts:
# - Arial Unicode MS
# - Arial
# - Helvetica

# For Windows, try these fonts:
# - Arial Unicode MS
# - Arial
# - Segoe UI

# For Linux, try these fonts:
# - DejaVu Sans
# - Liberation Sans
# - FreeSans
"""
    
    with open("fonts/FALLBACK_FONTS.txt", "w", encoding="utf-8") as f:
        f.write(fallback_config)
    
    print("✅ تم إنشاء ملف FALLBACK_FONTS.txt")

if __name__ == "__main__":
    main()
