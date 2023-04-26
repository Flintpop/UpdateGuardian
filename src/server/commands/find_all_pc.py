import socket

from scapy.layers.l2 import ARP, Ether
from scapy.sendrecv import srp

from src.server.environnement.server_logs import log_error


def scan_network(ip_range) -> dict:
    arp_request = ARP(pdst=ip_range)
    broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
    arp_request_broadcast = broadcast / arp_request
    answered_list = srp(arp_request_broadcast, timeout=1, verbose=False)[0]

    hosts = {}

    for sent, received in answered_list:
        hostname = get_hostname(received.psrc)
        if hostname not in hosts:
            hosts[hostname] = {'ip': received.psrc, 'mac': received.hwsrc}
        else:
            log_error("Error, two hosts have the same hostname. Please check your network configuration.")
            hosts[received.hwsrc] = {'ip': received.psrc, 'mac': received.hwsrc, 'hostname': hostname}

    return hosts


def get_hostname(ip_address):
    try:
        hostname = socket.gethostbyaddr(ip_address)[0]
    except socket.herror:
        hostname = None

    return hostname


def generate_ip_range(start_ip, end_ip):
    start = list(map(int, start_ip.split(".")))
    end = list(map(int, end_ip.split(".")))
    temp = start
    ip_range = [start_ip]

    while temp != end:
        start[3] += 1
        for i in (3, 2, 1):
            if temp[i] == 256:
                temp[i] = 0
                temp[i - 1] += 1
        ip_range.append(".".join(map(str, temp)))

    return ip_range


if __name__ == "__main__":
    ip_range_test = generate_ip_range("192.168.7.220", "192.168.7.253")

    hosts_tests = scan_network(ip_range_test)

    for host_test in hosts_tests:
        ip_address_test = host_test['ip']
        mac_address_test = host_test['mac']
        hostname_test = get_hostname(ip_address_test)
        print(f"IP: {ip_address_test}, MAC: {mac_address_test}, Hostname: {hostname_test}")
