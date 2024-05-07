import RPi.GPIO as GPIO
from signal import signal, SIGTERM, SIGHUP, pause
from rpi_lcd import LCD
from bluepy.btle import Peripheral, Scanner, DefaultDelegate
import time
import sys

# Define GPIO pins
buzzer_pin = 27  # Adjust pin number to your setup
led_pin = 17     # Adjust pin number to your setup

# Initialize GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(buzzer_pin, GPIO.OUT)
GPIO.setup(led_pin, GPIO.OUT)
GPIO.output(led_pin, GPIO.LOW)
GPIO.output(buzzer_pin, GPIO.LOW)

# Initialize LCD
lcd = LCD()

# Initialize PWM for the buzzer
pwmBuzzer = GPIO.PWM(buzzer_pin, 1)  # Initialize PWM on buzzer_pin at very low frequency
pwmBuzzer.start(50)  # Start PWM with 50% duty cycle
# Define note frequencies (in Hz)
NOTE_C4 = 262

def safe_exit(signum, frame):
    lcd.clear()
    GPIO.cleanup()
    sys.exit(1)

signal(SIGTERM, safe_exit)
signal(SIGHUP, safe_exit)

class NotificationDelegate(DefaultDelegate):
    def __init__(self):
        super().__init__()

    def handleNotification(self, cHandle, data):
        print("Raw received data:", data)  # Print raw data
        try:
            distance, force_read = map(int, data.decode().split(','))
            handle_data(distance, force_read)
        except ValueError as e:
            print("Error processing the data:", e)


def handle_data(distance, force_read):
    if distance < 30:
        # Calculate beep count based on distance (minimum of twice per second)
        beep_count = max(2, 30 - distance)  # Increase beeps as object gets closer

        # Set the frequency to NOTE_C4 (defined elsewhere)
        pwmBuzzer.ChangeFrequency(NOTE_C4)
        
        # Calculate on-time for each beep within the second
        total_duration = 1.0  # total time in seconds
        on_time = total_duration / beep_count
        
        # Active beeping loop for continuous sound
        start_time = time.time()
        while time.time() - start_time < total_duration:
            pwmBuzzer.ChangeDutyCycle(80)  # Turn on the buzzer
            time.sleep(on_time)            # Time for beep on
            pwmBuzzer.ChangeDutyCycle(0)   # Turn off the buzzer briefly
            time.sleep(0.02)               # Very brief off time to distinguish beeps
        
        pwmBuzzer.ChangeDutyCycle(0)  # Ensure buzzer is off after the loop


        if force_read >= 30:
            GPIO.output(led_pin, GPIO.LOW)
            lcd.text(f'{distance} cm', 1)
            lcd.text("", 2)
        else:
            GPIO.output(led_pin, GPIO.HIGH)
            pwmBuzzer.ChangeDutyCycle(80)
            lcd.text("Car's boot has", 1)
            lcd.text("been touched", 2)
            time.sleep(1)
            lcd.text("Please move your", 1)
            lcd.text("car forward!", 2)
            time.sleep(1)
    else:
        # Deactivate the buzzer
        GPIO.output(buzzer_pin, GPIO.LOW)
        lcd.text("Drive Safe", 1)
        lcd.text("     ^v^  ", 2)
        time.sleep(1)
        lcd.clear()

def scan_and_connect():
    scanner = Scanner()
    devices = scanner.scan(10.0)  # Scan for 10 seconds

    target_device = None
    target_name = "ParkingSensor"

    for dev in devices:
        for (adtype, desc, value) in dev.getScanData():
            if desc == "Complete Local Name" and value == target_name:
                target_device = dev.addr
                break

    if target_device:
        print(f"Found target device {target_device}, attempting to connect...")
        peripheral = Peripheral(target_device)
        peripheral.setDelegate(NotificationDelegate())

        try:
            service_uuid = "12345678-1234-5678-1234-56789abcdef0"
            char_uuid = "abcdef12-3456-7890-1234-567890abcdef"
            service = peripheral.getServiceByUUID(service_uuid)
            char = service.getCharacteristics(char_uuid)[0]

            # Setup to receive notifications
            setup_data = b"\x01\x00"
            notify_handle = char.getHandle() + 1
            peripheral.writeCharacteristic(notify_handle, setup_data, withResponse=True)

            # Wait for notifications
            while True:
                if peripheral.waitForNotifications(1.0):
                    continue  # wait for further notifications
                print("Waiting for notifications...")

        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            peripheral.disconnect()

if __name__ == "__main__":
    scan_and_connect()
