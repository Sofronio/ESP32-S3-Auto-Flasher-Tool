ESP32-S3 Auto Flasher - Multi Device Support
============================================

Overview
--------
A Python script for automatically flashing ESP32-S3 firmware to multiple devices. 
It detects CH34x USB-SERIAL adapters, identifies ESP32-S3 chips, and supports 
batch flashing operations.

Quick Start
-----------

*Install Python*
- Download Python from https://www.python.org/downloads/
- During installation, CHECK "Add Python to PATH"
- Verify installation:

~~~
python --version
~~~

*Open Command Prompt*
Multiple ways to open CMD:
- Press Win + R, type cmd, press Enter
- In File Explorer, go to script folder, type cmd in address bar, press Enter
- Right-click in script folder > "Open in Terminal"
- Right-click in empty space while holding Shift > "Open PowerShell window here" > type cmd

*Install Required Packages*
~~~
pip install esptool pyserial
~~~

*Prepare Firmware Files*
Place these 4 files in the same folder as the script:
- bootloader.bin
- partitions.bin
- firmware.bin
- littlefs.bin

*Run the Flasher*
~~~
# Basic usage (no erase)
python esp32_flasher.py

# With flash erase
python esp32_flasher.py --erase
~~~

Usage Guide
-----------

*Device Connection*
1. Connect ESP32-S3 via USB (CH340/CH343 adapter)
2. Enter download mode:
   - Hold BOOT button
   - Press RESET button once
   - Release BOOT button

*Script Operation*
~~~
ESP32-S3 Auto Flasher - Multi Device Support
============================================
Press Ctrl+C at any time to exit

Scanning for devices...
Found 2 CH34x device(s):
  1. COM3 - USB-SERIAL CH340
  2. COM5 - USB-SERIAL CH343

Testing for ESP32...
  COM3: ✓ ESP32-S3
  COM5: ✓ ESP32-S3

Found 2 ESP32 device(s):
  1. COM3 - ESP32-S3
  2. COM5 - ESP32-S3

  A. Flash ALL devices (2 devices)
  S. Scan again
  Q. Quit

Select option (1,2,3... / A / S / Q):
~~~

*Available Commands*
- 1, 2, 3...: Flash single device
- A: Flash ALL detected devices
- S: Rescan for devices
- Q: Quit program
- Ctrl+C: Exit immediately (anywhere)

*Flashing Process*
~~~
Flashing to: COM33
Device: USB-Enhanced_SERIAL CH343
Chip: ESP32-S3
============================================
Skipping flash erase (use --erase to enable)

Executing:
esptool --port COM33 --baud 921600 --before default-reset --after hard-reset write-flash --flash-mode dio --flash-freq 80m --flash-size 16MB 0x0000 bootloader.bin 0x8000 partitions.bin 0x10000 firmware.bin 0x670000 littlefs.bin

--------------------------------------------------
[esptool output...]
============================================
✅ Flash successful on COM33!
============================================

Press Enter to scan for more devices, or Ctrl+C to exit.
~~~

Command Line Options
--------------------

~~~
# Basic flash (no erase)
python esp32_flasher.py

# Flash with erase
python esp32_flasher.py --erase

# Help message
python esp32_flasher.py --help
~~~

Troubleshooting
---------------

*"python" not recognized*
- Reinstall Python with "Add to PATH" checked
- Or use full path: C:\Python312\python.exe esp32_flasher.py

*"pip" not recognized*
- Ensure Python is installed correctly
- Try: python -m pip install esptool pyserial

*No COM ports detected*
- Install CH340/CH343 drivers
- Check Device Manager for COM ports
- Ensure USB cable is data-capable

*ESP32 not detected*
- Enter download mode (BOOT + RESET)
- Check if drivers are installed
- Try different USB port

*Permission errors (Linux/Mac)*
~~~
# Add user to dialout group
sudo usermod -a -G dialout $USER

# Log out and back in, or run:
newgrp dialout
~~~

File Structure
--------------

~~~
esp32_flasher.py          # Main script
bootloader.bin           # Required
partitions.bin           # Required
firmware.bin             # Required
littlefs.bin             # Required
~~~

Production Workflow
-------------------

1. Prepare workstation with Python and dependencies
2. Place firmware files in folder
3. Connect first ESP32-S3 device
4. Run: python esp32_flasher.py --erase
5. Select 'A' to flash all detected devices
6. Replace device, press Enter to rescan
7. Repeat for each device
8. Press Ctrl+C when finished

Tips
----

- Use --erase for first-time flashing or when changing firmware
- Without --erase, flashing is much faster
- Script automatically detects CH34x adapters only
- Works with both CH340 and CH343 chips
- Supports ESP32-S3, ESP32-C3, ESP32-S2 identification

Emergency Exit
--------------

- Ctrl+C at any time to exit immediately
- No data will be saved, clean exit

---
Note: This tool is designed for production flashing of multiple ESP32-S3 devices with CH34x USB adapters.
