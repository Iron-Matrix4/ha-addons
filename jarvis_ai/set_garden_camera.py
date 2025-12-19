#!/usr/bin/env python3
"""Quick script to set garden camera preference in Jarvis memory"""
import sys
sys.path.insert(0, '/app')

from memory import Memory

mem = Memory('/data/jarvis_memory.db')

# Set preferred garden camera
mem.set_preference('garden_camera_entity', 'camera.bray_garden_camera_medium_resolution_channel')

print("✓ Set garden_camera_entity preference")
print(f"  Value: {mem.get_preference('garden_camera_entity')}")

# Show all preferences
prefs = mem.get_all_preferences()
print(f"\nAll preferences ({len(prefs)}):")
for key, val in prefs.items():
    print(f"  - {key}: {val}")

mem.close()
