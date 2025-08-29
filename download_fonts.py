#!/usr/bin/env python3
"""
Font Download Script for Arabic Fonts
This script helps download the required Arabic fonts for the PDF generation.
"""

import os
import urllib.request
import urllib.error

def download_font(url, filename):
    """Download a font file from URL"""
    try:
        print(f"📥 Downloading {filename}...")
        urllib.request.urlretrieve(url, filename)
        
        # Check if file is valid
        if os.path.getsize(filename) > 100000:  # Should be > 100KB for TTF
            print(f"✅ Successfully downloaded {filename}")
            return True
        else:
            print(f"❌ File {filename} seems too small, may be corrupted")
            return False
    except Exception as e:
        print(f"❌ Error downloading {filename}: {e}")
        return False

def main():
    """Main function to download fonts"""
    print("🎨 Arabic Font Downloader")
    print("=" * 40)
    
    # Create fonts directory if it doesn't exist
    if not os.path.exists('fonts'):
        os.makedirs('fonts')
        print("📁 Created fonts directory")
    
    # Font URLs (multiple sources to try)
    font_sources = [
        {
            'name': 'NotoNaskhArabic-Regular.ttf',
            'urls': [
                'https://github.com/google/fonts/raw/main/ofl/notonaskharabic/NotoNaskhArabic-Regular.ttf',
                'https://fonts.gstatic.com/s/notonaskharabic/v1/ieVc2YdFI3GCY6SyQyWKkkxMtdjA.ttf',
                'https://raw.githubusercontent.com/google/fonts/main/ofl/notonaskharabic/NotoNaskhArabic-Regular.ttf'
            ]
        },
        {
            'name': 'NotoNaskhArabic-Bold.ttf',
            'urls': [
                'https://github.com/google/fonts/raw/main/ofl/notonaskharabic/NotoNaskhArabic-Bold.ttf',
                'https://fonts.gstatic.com/s/notonaskharabic/v1/ieVc2YdFI3GCY6SyQyWKkkxMtdjA.ttf',
                'https://raw.githubusercontent.com/google/fonts/main/ofl/notonaskharabic/NotoNaskhArabic-Bold.ttf'
            ]
        }
    ]
    
    success_count = 0
    
    for font in font_sources:
        filename = os.path.join('fonts', font['name'])
        downloaded = False
        
        for url in font['urls']:
            if download_font(url, filename):
                downloaded = True
                success_count += 1
                break
        
        if not downloaded:
            print(f"❌ Failed to download {font['name']} from all sources")
    
    print("\n" + "=" * 40)
    if success_count == 2:
        print("🎉 All fonts downloaded successfully!")
        print("🚀 You can now run the Streamlit app with full Arabic support.")
    else:
        print(f"⚠️ Only {success_count}/2 fonts downloaded successfully.")
        print("💡 The app will use fallback fonts with limited Arabic support.")
    
    print("\n📋 Manual Installation Instructions:")
    print("1. Visit: https://fonts.google.com/noto/specimen/Noto+Naskh+Arabic")
    print("2. Download the font family")
    print("3. Extract and place the TTF files in the fonts/ directory")
    print("4. Rename them to:")
    print("   - NotoNaskhArabic-Regular.ttf")
    print("   - NotoNaskhArabic-Bold.ttf")

if __name__ == "__main__":
    main()
