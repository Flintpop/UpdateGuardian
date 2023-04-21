# UpdateGuardian

## Table of Contents

- [UpdateGuardian](#updateguardian)
    - [Table of Contents](#table-of-contents)
    - [Introduction](#introduction)
    - [Main Features](#main-features)
    - [Prerequisites](#prerequisites)
    - [Installation and Configuration](#installation-and-configuration)
    - [Usage](#usage)
    - [Project Architecture](#project-architecture)
    - [Tests](#tests)
    - [Troubleshooting and Support](#troubleshooting-and-support)
    - [Contributions](#contributions)
    - [License](#license)

## Introduction

<br>
UpdateGuardian is an automation system for updating a local network of Windows 10 PCs, designed to streamline and secure
update operations while reducing the technical maintenance required.

The idea came from the hassle to update a moderate number of Windows 10 PCs spread out in a local network, without the
need or cost at our disposal to install a Windows server. In addition, I intentionally did not look out for other
solution to grow my knowledge in python and network programming, and to have a project to work on for my internship.

It is a free and open source project, licensed under the Apache License 2.0.
The project is currently in development, and is not yet ready for production use.

## Main Features

Only intended to work on Windows 10 and 11. Other OS not supported for now, if ever because I am pretty sure there are many other alternatives.

These are the features :

- Automatic Windows updates rollout
- Automatic deployment of the software on the local network
- Installer for each client PC (for ssh, for remote control, not the software itself)
- Automatic reboot to install updates after the process, then automatic shutdown
- ient logs of the update
- Cyclic updates: Updates a specified number of PCs simultaneously, preventing update errors in low-quality wired networks and speeding up the update process
- Server setup and server database of the current network
- Automatic refresh of ips
- Some erros and issues prevention mecanisms, they are printed and some are logged in a file
- Scheduler of updates in a hour and in a day in the week. Once given, this is saved in a json file and can be modified here

Here are some features planned : 
- Other ipv4 format support (other than 192.168...)
- Improved ease of use and security, including SSH keys, SecureON passwords for Wake-on-LAN, and DHCP discovery module
- Improved error handling
- Automatic software updates (of UpdateGuardian)
- Email notifications for update status and failure reasons
- Server installer
- Documentation

## Prerequisites

List of prerequisites for running UpdateGuardian (e.g., Python, Paramiko, etc.).

- Python 3.11
- Windows 10 or 11 **wired** local network (wake on lan, which is for automatic boot)
- A server (could be simply a Windows pc running on 24/7)
- The list of IP addresses of the PCs in the local network that won't change until you decide to start the server setup
- The list of the PCs username in the local network (The name you see when you log in the session)
- The list of the PCs password in the local network (The password you type to log in the session)
- SSH server enabled on the PCs in the local network (installer given)
- Wake on lan enabled on the PCs in the local network. It is strongly recommended to use a secureOn password for the
  wake on lan feature, but it is not supported for now.
- Look out in requirements.txt for the pip packages (to be installed on the server)

## Installation and Configuration

Go to each pc, and copy the installation script in the script folder of the project.
Once this is done, edit the script to copy the second line. Paste it and execute it a admin Powershell session.
Next, still in the admin powershell session, start the installer. 

Leave the pc on, type somewhere its ipv4 address. Link that address to the admin password and the username password of this pc.
Do this for every pc you want to automatically update.

Then, go to the server pc, and install Python.
Type the command : 
```pip install -r requirements.txt``` in the UpdateGuardian folder.

Next : 
```python main.py```

Fill in the json file "computer_informations.json" with every ip, passwords, username of the pc you want to update automatically.

The server will prompt you instructions and informations.

When you are ready for the setup process to be completed, press "y".

After that, you wil have to specify an hour and a day of update. 

Et voilà, the computers of your local network will be automatically updated !

## Usage

Logs in logs folder for the server

Otherwise, logs are on each client computer.


In the json file in root folder ("computers_informations.json") you have to fill the informations about the computers
you want to update for the setup process, but also for some settings.

Here is an example of the json file:

```json
{
  "remote_user": [
    "user1",
    "user2"
  ],
  "remote_host": [
    "192.168.1.5",
    "192.168.2.1"
  ],
  "remote_passwords": [
    "password1",
    "password2"
  ],
  "max_computers_per_iteration": 3,
  "subnet_mask": "1",
  "taken_ips": [
    "192.168.1.1"
  ],
  "python_client_script_path": "",
  "ip_pool_range" : ["192.168.1.2", "192.168.1.253"]
}
```

For now the json looks like this. It is likely to change in the future.

Subnet mask is to check the ip subnet of the computers to update. 192.168.**1**.xxx. 
The subnet mask is 1 in this example.

Taken ip is to tell the program to not check the ip because it is static and already taken, by a printer for example.
It will be used to scan the dhcp network and update automatically computers that are not static (it is planned 
for later)

python_client_script_path is the custom path you want the UpdateGuardian folder to be on each client. **NOT RECOMMENDED TO CHANGE IT FOR NOW, NOT TESTED**.

ip_pool_range keeps as the name suggests, the ip pool range that the software will check at setup first, to link all the ipv4 address you wrote above to mac addresses and hostnames, and so passwords and account.

If there are errors in the json setup, file, the software should tell you.

Finally, the database stored for each setup will look like that : 

```json
{
    "hostname1": {
        "ip": "192.168.1.227",
        "mac": "00:00:00:38:64:79",
        "username": "admin",
        "password": "password"
    },
    "hostname2": {
        "ip": "192.168.1.228",
        "mac": "00:00:00:38:65:79",
        "username": "admin",
        "password": "password"
    },
    "hostname3": {
        "ip": "192.168.1.229",
        "mac": "00:00:00:38:66:79",
        "username": "admin",
        "password": "password"
    }
}
```
Etc...

If a password changed, or a username changed, please change the information in this file. It is located at the root folder of the project.


## Project Architecture

Work in progress.

## Tests

Unit tests are located in the "tests" folder. They are written using the unittest library.

## Troubleshooting and Support

Make sure to check firewall rules and ports to allow the communication between the server and the clients in ssh, ping
and wake on lan. This includes the Windows firewall and the router firewall. Sometimes, there is also the paid antivirus
firewall to check.

Make also sure that the server and the clients are in the same subnet.

This is a work in progress project, so there is no support for now.

If you want are stuck, maybe use wireshark to troubleshoot the problem. 
Send screnshots you think it may be the software that is the cause of your issue.

## Contributions

If anyone has different, and possibly better structural ideas (using something else than ssh for exemple), feel free to
contact me or to make a pull request.
Contributions are welcome. Please read the [contributing guidelines](CONTRIBUTING.md) before submitting a pull request.

## License

UpdateGuardian is licensed under the Apache License, Version 2.0. This open-source license allows you to use, modify,
and distribute the software, subject to the terms and conditions outlined in the license.

The full text of the Apache License 2.0 can be found at: http://www.apache.org/licenses/LICENSE-2.0

By using, modifying, or distributing UpdateGuardian, you agree to comply with the terms of the Apache License 2.0. Some
key points of the license include:

You must include a copy of the license in any distribution of the software or any derivative works.
You must include a notice in any modified files to indicate the changes made.
If you redistribute the software, you must include a prominent notice to inform recipients that the software is covered
by the Apache License 2.0.
You are not required to submit your modifications to the original project, but contributions are always welcome.
Please note that this summary is provided for informational purposes only and should not be considered a substitute for
the full license text. Always refer to the full license for complete terms and conditions.
