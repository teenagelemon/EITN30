import time
import psutil
import matplotlib.pyplot as plt

def measure_traffic_load(node_ip, base_ip, duration=10):
    pings = []
    start_time = time.time()
    while time.time() - start_time < duration:
        response = os.system(f"ping -c 1 -q {node_ip} > /dev/null")
        if response == 0:
            pings.append(1)
        else:
            pings.append(0)
    return sum(pings) / duration

def plot_traffic_load(node_ip, base_ip, duration=30):
    load_values = []
    cpu_load = []
    start_time = time.time()
    while time.time() - start_time < duration:
        load = measure_traffic_load(node_ip, base_ip)
        load_values.append(load)
        cpu_load.append(psutil.cpu_percent())
        time.sleep(1)
    plt.plot(cpu_load, label='CPU Load')
    plt.plot(load_values, label='Traffic Load')
    plt.legend()
    plt.xlabel('Time (s)')
    plt.ylabel('Load (%)')
    plt.show()

