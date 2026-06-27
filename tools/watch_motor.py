import time
from lerobot.motors.feetech.feetech import FeetechMotorsBus
from lerobot.motors import Motor

def watch_motor_4():
    port = '/dev/ttyACM1'
    print(f"👀 Watching Motor ID 4 on {port}...")
    print("Rotate the wrist until value is close to 2048.")

    bus = FeetechMotorsBus(port=port, motors={'4': Motor(4, 'sts3215', None)})
    bus.connect()

    try:
        while True:
            val, result, error = bus.packet_handler.read2ByteTxRx(bus.port_handler, 4, 56)
            if result == 0:
                status = "✅ OK" if 1000 < val < 3000 else "❌ OUT OF RANGE"
                print(f"ID 4 Pos: {val}  {status}", end='\r')
            else:
                print("Read Error", end='\r')
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nDone.")
    finally:
        bus.disconnect()

if __name__ == "__main__":
    watch_motor_4()




