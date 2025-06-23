#!/usr/bin/env python3
"""
Test script to verify the enhanced memory file listing functionality
"""

import sys
from pathlib import Path
from datetime import datetime

# Add the project's root directory to the Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

def test_list_memory_files():
    """Test the list_memory_files function"""
    
    print("🧪 Testing Memory File Listing Functionality")
    print("=" * 50)
    
    # Import the function from streamlit app
    from streamlit_app import list_memory_files
    
    # Test the function
    memory_files = list_memory_files()
    
    print(f"📁 Found {len(memory_files)} memory files:")
    print()
    
    if memory_files:
        for i, file_info in enumerate(memory_files, 1):
            print(f"{i}. **{file_info['name']}**")
            print(f"   📍 Path: {file_info['path']}")
            print(f"   📏 Size: {file_info['size']}")
            print(f"   📊 Index: {file_info['index_size']}")
            
            # Show modification date
            mod_date = datetime.fromtimestamp(file_info['modified']).strftime('%Y-%m-%d %H:%M')
            print(f"   🕒 Modified: {mod_date}")
            print()
    else:
        print("❌ No memory files found!")
        print("💡 Try uploading a PDF file first to create memory files.")
    
    # Test file validation
    print("🔍 Testing file validation:")
    memory_dir = Path("data/memory")
    if memory_dir.exists():
        print(f"✅ Memory directory exists: {memory_dir}")
        
        # Check for video files
        video_files = list(memory_dir.glob("*"))
        video_files = [f for f in video_files if f.suffix.lower() in ['.mp4', '.mkv', '.avi']]
        print(f"📹 Found {len(video_files)} video files:")
        
        for video_file in video_files:
            index_file = video_file.with_name(f"{video_file.stem}_index.json")
            status = "✅" if index_file.exists() else "❌"
            print(f"   {status} {video_file.name} -> {index_file.name}")
    else:
        print(f"❌ Memory directory not found: {memory_dir}")
    
    print("\n🎉 Test completed!")

if __name__ == "__main__":
    test_list_memory_files() 