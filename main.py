import subprocess
import threading
from tuntap import TunTap
import struct
import time
from RF24 import RF24, RF24_PA_LOW, RF24_2MBPS, RF24_CRC_16
import argparse
global role

PSIZE = 30
MAXBITS = 0xFFFF

w_radio = RF24(17, 0)
r_radio = RF24(27, 60)
role = 0
addr = [b"b", b"m"]
tun = TunTap(nic_type="Tun", nic_name="longge")
in_condition = threading.Condition()
in_list = []
out_condition = threading.Condition()
out_list = []


def setup():
    if role == 0:
        tun.config(ip="192.168.2.1", mask="255.255.255.0")
    elif role == 1:
        tun.config(ip="192.168.2.2", mask="255.255.255.0")
        subprocess.run(
            'sudo ip route add default via 192.168.2.1 dev longge', shell=True)
    if not w_radio.begin():
        print("write radio was not started")
    if not r_radio.begin():
        print("read radio was not started")

    w_radio.setPALevel(RF24_PA_LOW)
    r_radio.setPALevel(RF24_PA_LOW)

    w_radio.setRetries(15, 5)
    r_radio.setRetries(15, 5)

    w_radio.setChannel(100)
    r_radio.setChannel(100)

    w_radio.setDataRate(RF24_2MBPS)
    r_radio.setDataRate(RF24_2MBPS)

    w_radio.enableDynamicPayloads()
    r_radio.enableDynamicPayloads()

    w_radio.setAutoAck(True)
    r_radio.setAutoAck(True)

    w_radio.setCRCLength(RF24_CRC_16)
    r_radio.setCRCLength(RF24_CRC_16)

    w_radio.openWritingPipe(addr[role])
    r_radio.openReadingPipe(1, addr[not role])

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
        splits.append(c.to_bytes(2, 'big') + data[:PSIZE])
        data = data[PSIZE:]
        plen = len(data)
        c += 1
    return splits


def send(data: bytes):
    w_radio.stopListening()
    packages = split_package(data)
    for p in packages:
        w_radio.write(p)


def receiver():
    r_radio.startListening()
    buffer = []
    while True:
        has_payload, pipeNbr = r_radio.available_pipe()
        if has_payload:
            psize = r_radio.getDynamicPayloadSize()
            pack = r_radio.read(psize)
            c = int.from_bytes(pack[:2], 'big')
            buffer.append(pack[2:])
            if c == MAXBITS:
                packet = b''.join(buffer)
                buffer.clear()
                with out_condition:
                    out_list.append(packet)
                    out_condition.notify()


def transmitter():
    while True:
        with in_condition:
            while not len(in_list) > 0:
                in_condition.wait()
            packet = in_list.pop()
        send(packet)


def tun_trasmitter():
    while True:
        with out_condition:
            while not len(out_list) > 0:
                out_condition.wait()
            packet = out_list.pop()
        tun.write(packet)


def tun_receiver():
    while True:
        buffer = tun.read()
        if len(buffer):
            send(buffer)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='NRF24L01+ test')
    parser.add_argument('--role', dest='role', type=int, default=0,
                        help='Whether the unit is mobile or the base station', choices=range(0, 2))
    args = parser.parse_args()
    role = args.role
    setup()
    radio_s = threading.Thread(target=transmitter, args=())
    radio_r = threading.Thread(target=receiver, args=())
    tun_s = threading.Thread(target=tun_trasmitter, args=())
    tun_r = threading.Thread(target=tun_receiver, args=())

    radio_s.start()
    radio_r.start()
    time.sleep(0.5)
    tun_s.start()
    tun_r.start()

    radio_s.join()
    radio_r.join()
    tun_s.join()
    tun_r.join()
