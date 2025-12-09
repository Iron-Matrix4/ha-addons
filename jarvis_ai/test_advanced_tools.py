import tools
import time

def test_advanced_tools():
    print("--- Testing Advanced Tools ---")
    
    # 1. Weather
    print("\n[Weather]")
    print(tools.get_weather("London"))
    
    # 2. System Status
    print("\n[System]")
    print(tools.get_system_status())
    
    # 3. Search
    print("\n[Search]")
    print(tools.google_search("Python programming language"))
    
    # 4. Clipboard
    print("\n[Clipboard]")
    test_text = "Hello from Jarvis Test!"
    print(f"Writing: {test_text}")
    print(tools.write_to_clipboard(test_text))
    print(f"Reading: {tools.read_clipboard()}")
    
    # 5. Timer
    print("\n[Timer]")
    print(tools.set_timer(2))
    print("Waiting for timer...")
    time.sleep(3) # Wait for timer to finish printing

if __name__ == "__main__":
    test_advanced_tools()
