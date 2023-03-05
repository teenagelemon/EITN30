import threading
from tuntap import TunTap
import struct
import time
from RF24 import RF24, RF24_PA_LOW, RF24_2MBPS, RF24_CRC_16

PSIZE = 30
MAXBITS = 0xFFFF

run_program = True
w_radio = RF24(17, 0)
r_radio = RF24(27, 60)
role = 0
addr = [b"b", b"m"]
tun = TunTap(nic_type="Tun", nic_name="longge")
in_condition = threading.Condition()
in_list = []
out_condition = threading.Condition()
out_list = []
tun_condition = threading.Condition()


def setup():
    if role == 0:
        tun.config(ip="192.168.2.1", mask="255.255.255.0")
        # script for the rest
    elif role == 1:
        tun.config(ip="192.168.2.2", mask="255.255.255.0")
        # script for the rest

    if not w_radio.begin():
        print("write radio was not started")
    if not r_radio.begin():
        print("read radio was not started")

    w_radio.setPALevel(RF24_PA_LOW)
    r_radio.setPALevel(RF24_PA_LOW)

    w_radio.setRetries(5, 0)
    r_radio.setRetries(5, 0)

    w_radio.setChannel(100)
    r_radio.setChannel(100)

    w_radio.setDataRate(RF24_2MBPS)
    r_radio.setDataRate(RF24_2MBPS)

    w_radio.enableDynamicPayloads()
    r_radio.enableDynamicPayloads()

    w_radio.setAutoAck()
    r_radio.setAutoAck()

    w_radio.setCRCLength(RF24_CRC_16)
    r_radio.setCRCLength(RF24_CRC_16)

    w_radio.stopListening()
    w_radio.openWritingPipe(addr[role])
    r_radio.openReadingPipe(0, addr[not role])
    r_radio.startListening()

    w_radio.flush_tx()
    r_radio.flush_rx()


def split_package(data: bytes) -> list:
    splits = []
    plen = len(data)

    if (plen <= 0):
        return

    c = 1
    while data:
        if (plen <= PSIZE):
            c = MAXBITS
        splits.append(c.to_bytes(2, 'big'))
        splits.append(data[:PSIZE])
        data = data[PSIZE:]
        plen = len(data)
        c += 1

    return splits


def send(data: byte):
    packages = split_package(data)
    for p in packages:
        w_radio.write(p)


def receiver():
    buffer = []
    while True:
        if run_program == False:
            print("Closing receiver")
            return
        if (r_radio.available_pipe()):
            psize = r_radio.getDynamicPayloadSize()
            if (psize < 1):
                pack = r_radio.read(psize)
                c = int.from_bytes(pack[:2], 'big')
                buffer.append(pack[2:])
                if c == MAXBITS:
                    packet = b''.join(buffer)
                    buffer.clear()
                    with out_condition:
                        out_list.append(packet)
                        out_condition.notify_all()


def transmitter():
    while True:
        if run_program == False:
            print("Closing receiver")
            return
        with in_condition:
            while not len(in_list) > 0:
                in_condition.wait()
            packet = in_list.pop()
            in_condition.notify_all()
        send(packet)


def tun_trasmitter():
    while True:
        if run_program == False:
            print("Closing receiver")
            return
        with out_condition:
            while not len(out_list) > 0:
                out_condition.wait()
            packet = out_list.pop()
        tun.write(packet)
        out_condition.notify_all()
        tun_condition.notify_all()


def tun_receiver():
    while True:
        if run_program == False:
            print("Closing receiver")
            return
        with tun_condition:
            buffer = tun.read()
            if len(buffer):
                send(buffer)
        tun_condition.notify_all()


def run():
    role = input("base = 0, mobile = 1")
    setup()
    if (role == 0):
        base()
    elif (role == 1):
        mobile()
    else:
        print("wrong role")
        return


if __name__ == "__main__":
    radio_s = threading.Thread(target=transmitter, args=())
    radio_r = threading.Thread(target=receiver, args=())
    tun_s = threading.Thread(target=tun_trasmitter, args=())
    tun_r = threading.Thread(target=tun_receiver, args=())

    radio_s.start()
    radio_r.start()
    tun_s.start()
    tun_r.start()

    radio_s.join()
    radio_r.join()
    tun_s.join()
    tun_r.join()

    exit_input = input("input anything to exit")
    if (len(exit_input)):
        close_threads = 1
