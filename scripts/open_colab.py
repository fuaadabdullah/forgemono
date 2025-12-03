#!/usr/bin/env python3
"""
Open Google Colab in browser

Simple script to open Google Colab for uploading notebooks.
"""

import webbrowser


def main():
    colab_url = "https://colab.research.google.com/"
    print(f"🌐 Opening Google Colab: {colab_url}")

    try:
        webbrowser.open(colab_url)
        print("✅ Browser opened successfully")
        print("\\n📋 Next steps:")
        print("1. Click 'File' → 'Upload notebook'")
        print("2. Select: notebooks/colab_llamacpp_setup.ipynb")
        print("3. Run all cells to start your llama.cpp server")
    except Exception as e:
        print(f"❌ Could not open browser: {e}")
        print(f"📋 Manually visit: {colab_url}")


if __name__ == "__main__":
    main()
