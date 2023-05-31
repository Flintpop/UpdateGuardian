# -----------------------------------------------------------
# setup_static_ip.py
# Author: darwh
# Date: 28/04/2023
# Description: File that contains the set-up functions to set a static ip on the server.
# -----------------------------------------------------------

from src.server.environnement.server_logs import log_error, log


import subprocess
import wmi

from src.server.wake_on_lan.wake_on_lan_utils import get_gateway_ip


def get_network_adapters() -> list:
    try:
        wmi_obj = wmi.WMI()
        adapters = []

        for adapter in wmi_obj.Win32_NetworkAdapterConfiguration(IPEnabled=True):
            ip_address = adapter.IPAddress[0] if adapter.IPAddress else None
            netmask = adapter.IPSubnet[0] if adapter.IPSubnet else None
            dhcp_enabled = adapter.DHCPEnabled

            adapters.append({
                'name': adapter.Description,
                'index': adapter.Index,
                'ip_address': ip_address,
                'netmask': netmask,
                'dhcp_enabled': dhcp_enabled
            })

        return adapters

    except Exception as e:
        raise Exception(f"Error getting network adapters: {str(e)}")


def is_static_ip(ip_address: str) -> bool:
    """
    Check if the given IP address is assigned as a static IP address on the local network.
    :param ip_address: The IP address to check.
    :return: True if the IP address is static, False otherwise.
    """
    # get a list of network adapters and their IP addresses
    adapters = get_network_adapters()

    # check if any of the adapters have the given IP address assigned as a static IP address
    for adapter in adapters:
        if adapter['ip_address'] == ip_address and adapter['dhcp_enabled'] is False:
            return True

    return False


def find_adapter_by_name(adapter_name: str) -> dict | None:
    """
    Find the adapter with the specified name.
    :return: The adapter with the specified name, or None if no such adapter is found.
    """
    adapters = get_network_adapters()
    for adapter in adapters:
        if adapter['name'] == adapter_name:
            return adapter
    return None


def set_static_ip(ip_address: str, adapter_name: str) -> None:
    """
    Set the IP address and DNS for a network adapter to a static configuration.
    :param ip_address: The static IP address to set.
    :param adapter_name: The name of the network adapter to modify.
    :return: Nothing.
    """
    try:
        # Find the adapter with the specified name
        adapter = find_adapter_by_name(adapter_name)

        if adapter:
            # Set static IP address, subnet mask, and default gateway
            adapter_name = adapter['name']
            adapter_index = adapter['index']

            subprocess.run(
                [
                    "netsh",
                    "interface",
                    "ipv4",
                    "set",
                    "address",
                    f"name={adapter_index}",
                    "source=static",
                    f"address={ip_address}",
                    f"gateway={get_gateway_ip()}",
                ],
                check=True,
            )

            log(f"Successfully set static IP address for adapter '{adapter_name}'")

            # # Set static DNS servers
            # subprocess.run(["netsh", "interface", "ipv4", "set", "dnsservers", f"name={adapter_name}",
            #                 "source=static", "address=8.8.8.8", "register=primary"], check=True)
            # subprocess.run(["netsh", "interface", "ipv4", "add", "dnsservers", f"name={adapter_name}",
            #                 "address=8.8.4.4", "index=2"], check=True)

        else:
            log_error(f"No adapter found with name '{adapter_name}'")
    except Exception as e:
        log_error(f"Failed to set static IP address: {e}")
