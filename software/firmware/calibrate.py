from time import sleep
from europi import oled, b1, b2, ain, cv1, usb_connected
from europi_script import EuroPiScript
from os import stat, mkdir


class Calibrate(EuroPiScript):
    @classmethod
    def display_name(cls):
        """Push this script to the end of the menu."""
        return "~Calibrate"

    def main(self):
        def sample():
            readings = []
            for reading in range(256):
                readings.append(ain.pin.read_u16())
            return round(sum(readings) / 256)

        def wait_for_voltage(voltage):
            wait_for_b1(0)
            if voltage != 0:
                oled.centre_text(f"Plug in {voltage}V\n\nDone: Button 1")
                wait_for_b1(1)
            else:
                oled.centre_text(f"Unplug all\n\nDone: Button 1")
                wait_for_b1(1)
            oled.centre_text("Calibrating...")
            sleep(1.5)
            return sample()

        def text_wait(text, wait):
            oled.centre_text(text)
            sleep(wait)

        def wait_for_b1(value):
            while b1.value() != value:
                sleep(0.05)

        # Test if /lib exists. If not: Create it

        try:
            stat("/lib")
        except OSError:
            mkdir("/lib")

        # Calibration start

        if usb_connected.value() == 1:
            oled.centre_text("Make sure rack\npower is on\nDone: Button 1")
            wait_for_b1(1)
            wait_for_b1(0)

        text_wait("Calibration\nMode", 3)

        oled.centre_text("Choose Process\n\n1:LOW    2:HIGH")
        while True:
            if b1.value() == 1:
                chosen_process = 1
                break
            elif b2.value() == 1:
                chosen_process = 2
                break

        # Input calibration

        readings = []
        if chosen_process == 1:
            readings.append(wait_for_voltage(0))
            readings.append(wait_for_voltage(10))
        else:
            for voltage in range(11):
                readings.append(wait_for_voltage(voltage))

        with open(f"lib/calibration_values.py", "w") as file:
            values = ", ".join(map(str, readings))
            file.write(f"INPUT_CALIBRATION_VALUES=[{values}]")

        # Output Calibration

        oled.centre_text(f"Plug CV1 into\nanalogue in\nDone: Button 1")
        wait_for_b1(1)
        oled.centre_text("Calibrating...")

        if chosen_process == 1:
            new_readings = [readings[0]]
            m = (readings[1] - readings[0]) / 10
            c = readings[0]
            for x in range(1, 10):
                new_readings.append(round((m * x) + c))
            new_readings.append(readings[1])
            readings = new_readings

        output_duties = [0]
        duty = 0
        cv1.pin.duty_u16(duty)
        reading = sample()
        for index, expected_reading in enumerate(readings[1:]):
            while abs(reading - expected_reading) > 0.002 and reading < expected_reading:
                cv1.pin.duty_u16(duty)
                duty += 10
                reading = sample()
            output_duties.append(duty)
            oled.centre_text(f"Calibrating...\n{index+1}V")

        with open(f"lib/calibration_values.py", "a+") as file:
            values = ", ".join(map(str, output_duties))
            file.write(f"\nOUTPUT_CALIBRATION_VALUES=[{values}]")

        oled.centre_text("Calibration\nComplete!")


if __name__ == "__main__":
    Calibrate().main()
