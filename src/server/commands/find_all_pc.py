import socket
from ipaddress import IPv4Network

from scapy.layers.l2 import ARP, Ether
from scapy.sendrecv import srp


def scan_network(ip_range):
    arp_request = ARP(pdst=ip_range)
    broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
    arp_request_broadcast = broadcast / arp_request
    answered_list = srp(arp_request_broadcast, timeout=1, verbose=False)[0]

    hosts = []

    for sent, received in answered_list:
        hosts.append({'ip': received.psrc, 'mac': received.hwsrc})

    return hosts


def get_hostname(ip_address):
    try:
        hostname = socket.gethostbyaddr(ip_address)[0]
    except socket.herror:
        hostname = None

    return hostname


if __name__ == "__main__":
    # Replace '192.168.1.0/24' with your network range
    network_range = "192.168.7.220/250"
    ip_range = [str(ip) for ip in IPv4Network(network_range, strict=False)]

    hosts = scan_network(ip_range)

    for host in hosts:
        ip_address = host['ip']
        hostname = get_hostname(ip_address)
        print(f"IP: {ip_address}, Hostname: {hostname}")
