import time
import unittest
from microstacknode.hardware.accelerometer.lsm9ds0 import LSM9DS0


class TestLSM9DS0Gyro(unittest.TestCase):

    # def test_gyroscope(self):
    #     with LSM9DS0(1) as l:
    #         l.setup_gyroscope()
    #         while True:
    #             print("Gyroscope: {}".format(l.get_gyroscope(raw=True)))
    #             time.sleep(0.1)

    def test_gyroscope_interrupt(self):
        with LSM9DS0(1) as l:
            l.setup_gyroscope(interrupt_enable=True,
                              interrupt_on_all=False,
                              latch_interrupt_request=False,
                              x_high_interrupt_enable=True,
                              x_low_interrupt_enable=False,
                              y_high_interrupt_enable=False,
                              y_low_interrupt_enable=False,
                              z_high_interrupt_enable=False,
                              z_low_interrupt_enable=False,
                              x_interrupt_threshold=15000,
                              y_interrupt_threshold=0,
                              z_interrupt_threshold=0,
                              interrupt_duration=100)
            print(l.wait_for_gyroscope_interrupt())


if __name__ == "__main__":
    unittest.main()
