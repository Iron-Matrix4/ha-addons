import tools
import config

def test_pc_tools():
    print("Testing PC Tools...")
    # Test something safe like volume or calculator
    print(tools.open_application("calculator"))
    print(tools.set_volume_mute(True))
    print(tools.set_volume_mute(False))

def test_ha_tools():
    print("\nTesting HA Tools...")
    if not config.HA_TOKEN:
        print("Skipping HA test: No Token")
        return

    # Try to get state of a common entity (sun.sun is usually present)
    print(tools.get_ha_state("sun.sun"))

if __name__ == "__main__":
    test_pc_tools()
    test_ha_tools()
