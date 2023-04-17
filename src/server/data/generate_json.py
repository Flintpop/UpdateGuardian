import json
import random


def generate_unique_ip(subnet_mask: str, existing_ips: list[str], taken_ips: list[str]) -> str:
    while True:
        ip = f"192.168.{subnet_mask}.{random.randint(1, 254)}"
        if ip not in existing_ips and ip not in taken_ips:
            return ip


def generate_dict(n: int) -> dict:
    users = [f"user{i + 1}" for i in range(n)]
    hosts = []
    subnet_mask = "1"
    taken_ips = ["192.168.1.1"]
    for _ in range(n):
        unique_ip = generate_unique_ip(subnet_mask, hosts, taken_ips)
        hosts.append(unique_ip)
    passwords = [f"password{i + 1}" for i in range(n)]
    max_computers_per_iteration = random.randint(2, 5)

    return {
        "remote_user": users,
        "remote_host": hosts,
        "remote_passwords": passwords,
        "max_computers_per_iteration": max_computers_per_iteration,
        "subnet_mask": subnet_mask,
        "taken_ips": taken_ips
    }


def generate_flawed_dict(n: int) -> dict:
    users = [f"user{i + 1}" for i in range(n+1)]
    hosts = []
    subnet_mask = "1"
    taken_ips = ["192.168.1.1"]
    for _ in range(n):
        hosts.append(f"192.168.{subnet_mask}.{random.randint(1, 254)}")
    passwords = [f"password{i + 1}" for i in range(n)]
    max_computers_per_iteration = random.randint(2, 100)

    return {
        "remote_user": users,
        "remote_host": hosts,
        "remote_passwords": passwords,
        "max_computers_per_iteration": max_computers_per_iteration,
        "subnet_mask": subnet_mask,
        "taken_ips": taken_ips
    }


def generate_json(n_computers: int = 10):
    test_data_json: dict = generate_dict(n_computers)
    with open('test.json', 'w') as f:
        json.dump(test_data_json, f)


def generate_flawed_json(n_computers: int = 10):
    data_json: dict = generate_flawed_dict(n_computers)
    with open('test.json', 'w') as f:
        json.dump(data_json, f)
