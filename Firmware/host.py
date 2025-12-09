# interactive_server.py -- Full-featured Macropad config manager
import serial
import json
import time
import os

# -----------------------
# Configuration
# -----------------------
SERIAL_PORT = "COM3"  # Replace with your RP2040 serial port
BAUD_RATE = 115200
RETRY_INTERVAL = 2.0

# Available keycodes for "press" and "send"
KEYCODES = [
    "A","B","C","D","E","F","G","H","I","J","K","L","M",
    "N","O","P","Q","R","S","T","U","V","W","X","Y","Z",
    "1","2","3","4","5","6","7","8","9","0",
    "ENTER","BACKSPACE","TAB","SPACE","ESCAPE",
    "UP_ARROW","DOWN_ARROW","LEFT_ARROW","RIGHT_ARROW",
    "CONTROL","SHIFT","ALT","GUI"
]

# -----------------------
# Helpers
# -----------------------
def open_serial():
    while True:
        try:
            ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
            print(f"Connected to {SERIAL_PORT}")
            return ser
        except serial.SerialException as e:
            print(f"Serial connection failed: {e}. Retrying in {RETRY_INTERVAL}s...")
            time.sleep(RETRY_INTERVAL)

def send_packet(ser, packet):
    try:
        json_str = json.dumps(packet)
        ser.write((json_str + "\n").encode('utf-8'))
        print("\nPacket sent successfully!")
    except Exception as e:
        print("Failed to send packet:", e)

def receive_response(ser):
    try:
        while ser.in_waiting:
            line = ser.readline().decode('utf-8').strip()
            if line:
                print("Macropad:", line)
    except Exception as e:
        print("Serial read error:", e)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def choose_key(prompt):
    while True:
        choice = input(prompt).strip()
        if choice.isdigit() and 1 <= int(choice) <= len(KEYCODES):
            return KEYCODES[int(choice)-1]
        elif choice.upper() in KEYCODES:
            return choice.upper()
        else:
            print("Invalid choice. Try again.")

def print_keycodes():
    print("\nAvailable keys:")
    for i, k in enumerate(KEYCODES, 1):
        print(f"{i}. {k}", end='  ')
        if i % 10 == 0:
            print()
    print()


# -----------------------
# Macro / Screen prompts
# -----------------------
def prompt_macro():
    name = input("Macro layer name: ").strip()
    number = input("Macro layer number (1-10): ").strip()
    keycodes = {}

    for btn in range(1, 6):
        print(f"\nConfiguring Button {btn}...")
        actions = []
        while True:
            print("\nAdd Action:")
            print("1. send keys")
            print("2. press key")
            print("3. write text")
            print("0. finish button")
            choice = input("Choice: ").strip()

            if choice == "0":
                break
            elif choice == "1":  # send keys
                print_keycodes()
                keys = []
                while True:
                    k = choose_key("Select key to send: ")
                    keys.append(k)
                    another = input("Add another key? (y/n): ").strip().lower()
                    if another != "y":
                        break
                actions.append({"action":"send", "keys":keys})
            elif choice == "2":  # press key
                print_keycodes()
                k = choose_key("Select key to press: ")
                actions.append({"action":"press","key":k})
            elif choice == "3":  # write
                txt = input("Enter text to write: ")
                actions.append({"action":"write","text":txt})
            else:
                print("Invalid choice.")
        if actions:
            keycodes[str(btn)] = actions

    packet = {"type":"macro","name":name,"number":int(number),"keycodes":keycodes}
    return packet

def prompt_screen():
    name = input("Screen layer name: ").strip()
    number = input("Screen layer number (1-10): ").strip()
    line1 = input("Line 1 text: ").strip()
    line2 = input("Line 2 text: ").strip()

    packet = {"type":"screen","name":name,"number":int(number),"screen":{"line1":line1,"line2":line2}}
    return packet

# -----------------------
# Main Loop
# -----------------------
def main():
    ser = open_serial()
    try:
        while True:
            receive_response(ser)
            print("\n--- Macropad Config Server ---")
            print("1. Update Macro Layer")
            print("2. Update Screen Layer")
            print("3. Exit")
            choice = input("Select an option: ").strip()

            if choice == "1":
                packet = prompt_macro()
                send_packet(ser, packet)
            elif choice == "2":
                packet = prompt_screen()
                send_packet(ser, packet)
            elif choice == "3":
                print("Exiting...")
                break
            else:
                print("Invalid choice, try again.")

            time.sleep(0.1)
            clear_screen()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        ser.close()

if __name__ == "__main__":
    main()
