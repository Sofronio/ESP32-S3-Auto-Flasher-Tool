import os
import subprocess
import sys
import argparse
import signal

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\nProgram terminated by user.")
    sys.exit(0)

def list_com_ports_with_pyserial():
    """
    List all available COM ports using pyserial.
    Returns list of tuples: (port_name, port_description)
    """
    try:
        import serial.tools.list_ports
        ports = []
        
        available_ports = list(serial.tools.list_ports.comports())
        
        for port_info in available_ports:
            port_name = port_info.device.upper()
            port_description = port_info.description.upper() if port_info.description else ""
            ports.append((port_name, port_description))
        
        return ports
    except ImportError:
        print("Error: pyserial not installed.")
        print("Please install it first: pip install pyserial")
        sys.exit(1)

def is_ch34x_port(port_description):
    """
    Check if port description matches CH34x pattern.
    Looks for USB, SERIAL, and CH in description.
    """
    if not port_description:
        return False
    
    desc_upper = port_description.upper()
    
    has_usb = "USB" in desc_upper
    has_serial = "SERIAL" in desc_upper
    has_ch = "CH" in desc_upper
    
    return has_usb and has_serial and has_ch

def test_esp32_on_port(port_name):
    """
    Test if an ESP32 is connected to the specified port.
    Returns (is_esp32, chip_info) tuple.
    """
    try:
        # Try with hyphen format first
        result = subprocess.run(
            ['esptool', '--port', port_name, 'chip-id'],
            capture_output=True,
            text=True,
            timeout=2
        )
        
        if result.returncode == 0 and 'ESP32' in result.stdout:
            output = result.stdout
            chip_info = "ESP32"
            if 'ESP32-S3' in output:
                chip_info = "ESP32-S3"
            elif 'ESP32-C3' in output:
                chip_info = "ESP32-C3"
            elif 'ESP32-S2' in output:
                chip_info = "ESP32-S2"
            return True, chip_info
        
        # Fallback to underscore format
        result = subprocess.run(
            ['esptool', '--port', port_name, 'chip_id'],
            capture_output=True,
            text=True,
            timeout=2
        )
        
        if result.returncode == 0 and 'ESP32' in result.stdout:
            output = result.stdout
            chip_info = "ESP32"
            if 'ESP32-S3' in output:
                chip_info = "ESP32-S3"
            return True, chip_info
        
        return False, ""
        
    except subprocess.TimeoutExpired:
        return False, "Timeout"
    except Exception as e:
        return False, f"Error: {str(e)[:30]}"

def erase_flash_if_needed(port_name, erase_flash):
    """Erase flash if requested"""
    if not erase_flash:
        print("Skipping flash erase (use --erase to enable)")
        return True
    
    print("Erasing flash...")
    try:
        erase_cmd = f'esptool --port {port_name} --baud 921600 erase-flash'
        subprocess.run(erase_cmd, shell=True, check=True, timeout=10)
        print("✓ Erase completed, waiting for device reset...")
        import time
        time.sleep(2)
        return True
    except subprocess.TimeoutExpired:
        print("⚠️ Erase timeout, continuing anyway...")
        return True
    except Exception as e:
        print(f"✗ Erase failed: {e}")
        return False

def flash_to_port(port_name, port_desc, chip_info="", erase_flash=False):
    """Flash firmware to a specific port"""
    print(f"\n{'='*60}")
    print(f"Flashing to: {port_name}")
    if port_desc:
        print(f"Device: {port_desc}")
    if chip_info:
        print(f"Chip: {chip_info}")
    print(f"{'='*60}")
    
    # Erase if needed
    if not erase_flash_if_needed(port_name, erase_flash):
        print("Skipping flash due to erase failure")
        return False
    
    # Flash command
    cmd = f'esptool --port {port_name} --baud 921600 --before default-reset --after hard-reset write-flash --flash-mode dio --flash-freq 80m --flash-size 16MB 0x0000 bootloader.bin 0x8000 partitions.bin 0x10000 firmware.bin 0x670000 littlefs.bin'
    
    print(f"\nExecuting:\n{cmd}")
    print("\n" + "-" * 50)
    
    # Execute flash command
    try:
        subprocess.run(cmd, shell=True, check=True, timeout=60)
        print("\n" + "=" * 50)
        print(f"✅ Flash successful on {port_name}!")
        print("=" * 50)
        return True
    except subprocess.TimeoutExpired:
        print("\n⚠️ Flash timeout, but may still be in progress...")
        return False
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Flash failed on {port_name}: {e}")
        return False
    except KeyboardInterrupt:
        print(f"\nFlash interrupted on {port_name}")
        return False

def main_flash_loop(erase_flash=False):
    """Main loop for flashing multiple devices"""
    print("ESP32-S3 Auto Flasher - Multi Device Support")
    print("=" * 60)
    print("Press Ctrl+C at any time to exit\n")
    
    # Check firmware files
    required_files = ["bootloader.bin", "partitions.bin", "firmware.bin", "littlefs.bin"]
    for f in required_files:
        if not os.path.exists(f):
            print(f"Error: Missing file '{f}'")
            return
    
    while True:
        print("\n" + "=" * 60)
        print("Scanning for devices...")
        
        # Get available COM ports
        ports_info = list_com_ports_with_pyserial()
        
        if not ports_info:
            print("No COM ports detected! Connect a device and press Enter to retry.")
            input("Or press Ctrl+C to exit...")
            continue
        
        # Filter for CH34x devices
        ch34x_ports = [(port, desc) for port, desc in ports_info if is_ch34x_port(desc)]
        
        if not ch34x_ports:
            print("No CH34x USB-SERIAL devices found.")
            print(f"Available ports: {', '.join([p[0] for p in ports_info])}")
            print("\nPress Enter to scan again, or Ctrl+C to exit.")
            input()
            continue
        
        print(f"\nFound {len(ch34x_ports)} CH34x device(s):")
        for i, (port, desc) in enumerate(ch34x_ports, 1):
            print(f"  {i}. {port} - {desc}")
        
        # Test for ESP32
        print("\nTesting for ESP32...")
        esp32_devices = []
        
        for port, desc in ch34x_ports:
            print(f"  {port}: ", end="", flush=True)
            is_esp32, chip_info = test_esp32_on_port(port)
            
            if is_esp32:
                print(f"✓ {chip_info}")
                esp32_devices.append((port, desc, chip_info))
            else:
                print("✗ Not ESP32")
        
        if not esp32_devices:
            print("\nNo ESP32 devices found on CH34x ports.")
            print("Make sure device is in download mode (hold BOOT, press RESET)")
            print("\nPress Enter to scan again, or Ctrl+C to exit.")
            input()
            continue
        
        # Handle device selection
        print(f"\nFound {len(esp32_devices)} ESP32 device(s):")
        for i, (port, desc, chip_info) in enumerate(esp32_devices, 1):
            print(f"  {i}. {port} - {chip_info}")
        
        print(f"\n  A. Flash ALL devices ({len(esp32_devices)} devices)")
        print("  S. Scan again")
        print("  Q. Quit")
        
        while True:
            choice = input("\nSelect option (1,2,3... / A / S / Q): ").strip().upper()
            
            if choice == 'Q':
                print("\nExiting program.")
                return
            elif choice == 'S':
                break  # Break to outer loop to scan again
            elif choice == 'A':
                # Flash all devices
                success_count = 0
                for port, desc, chip_info in esp32_devices:
                    if flash_to_port(port, desc, chip_info, erase_flash):
                        success_count += 1
                
                print(f"\nCompleted: {success_count}/{len(esp32_devices)} devices flashed successfully.")
                print("\nPress Enter to scan for more devices, or Ctrl+C to exit.")
                input()
                break  # Back to scanning
            elif choice.isdigit() and 1 <= int(choice) <= len(esp32_devices):
                # Flash single device
                port, desc, chip_info = esp32_devices[int(choice) - 1]
                flash_to_port(port, desc, chip_info, erase_flash)
                
                print("\nPress Enter to scan for more devices, or Ctrl+C to exit.")
                input()
                break  # Back to scanning
            else:
                print(f"Invalid choice. Enter 1-{len(esp32_devices)}, A, S, or Q")

def main():
    # Set up Ctrl+C handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="ESP32-S3 Auto Flasher - Multi Device Support")
    parser.add_argument(
        "--erase",
        action="store_true",
        help="Erase flash before writing (default: skip erase)"
    )
    
    args = parser.parse_args()
    
    # Check if pyserial is available
    try:
        import serial.tools.list_ports
    except ImportError:
        print("pyserial is required but not installed.")
        print("Please install it: pip install pyserial")
        sys.exit(1)
    
    # Run the main flash loop
    main_flash_loop(erase_flash=args.erase)

if __name__ == "__main__":
    main()