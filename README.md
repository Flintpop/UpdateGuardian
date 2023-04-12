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

UpdateGuardian is an automation system for updating a local network of Windows 10 PCs, designed to streamline and secure update operations while reducing the technical maintenance required.

The idea came from the hassle to update a moderate number of Windows 10 PCs spread out in a local network, without the need or cost at our disposal to install a windows server. In addition, I intentionnally did not look out for other solution to grow my knowledge in python and network programming, and to have a project to work on for my internship.

It is a free and open source project, licensed under the Apache License 2.0.
The project is currently in development, and is not yet ready for production use.

## Main Features

Only intended to work on windows 10 and 11. Other OS not supported.

These are the features planned :

- Update automation
- Centralized update management
- Update scheduling
- Update notification and reporting (email)
- Update rollout
- Update tracking
- Installer

## Prerequisites

List of prerequisites for running UpdateGuardian (e.g., Python, Paramiko, etc.).

- Python 3.11
- Windows 10 or 11 **wired** local network (wake on lan, which is for automatic boot)
- A server (could be simply a windows pc running on 24/7)
- The list of statically assigned IP addresses of the PCs in the local network (not dhcp for now)
- The list of the PCs username in the local networ
- The list of the PCs password in the local network
- SSH server enabled on the PCs in the local network
- Wake on lan enabled on the PCs in the local network. It is strongly recommended to use a secureOn password for the wake on lan feature.
- Look out in requirements.txt for the pip packages (to be installed)

## Installation and Configuration

Work in progress.

## Usage

In the json file in root folder ("computers_informations.json") you have to fill the informations about the computers you want to update.

Here is an example of the json file:

```json
{
  "remote_user" : ["user1", "user2"],
  "remote_host" : ["192.168.1.5", "192.168.2.1"],
  "remote_password" : ["password1", "password2"],
  "max_computers_per_iteration": 3,
  "subnet_mask" : "1", # used for 192.168.**1**.xxx
  "taken_ip" : ["192.168.1.1"] # Usually the router ip. Make sur to add the server ip if it is in the same subnet
}
```

For now the json looks like this. It is likely to change in the future.

Work in progress for the rest.

## Project Architecture

Work in progress.

## Tests

Unit tests are located in the tests folder. They are written using the unittest librairy.

## Troubleshooting and Support

Make sure to check firewall rules and ports to allow the communication between the server and the clients in ssh, ping and wake on lan. This include the windows firewall and the router firewall. Sometimes, there is also the paid antivirus firewall to check.

Make also sure that the server and the clients are in the same subnet.

This is a work in progress project, so there is no support for now.

## Contributions

Contributions are welcome. Please read the [contributing guidelines](CONTRIBUTING.md) before submitting a pull request.

## License

UpdateGuardian is licensed under the Apache License, Version 2.0. This open-source license allows you to use, modify, and distribute the software, subject to the terms and conditions outlined in the license.

The full text of the Apache License 2.0 can be found at: http://www.apache.org/licenses/LICENSE-2.0

By using, modifying, or distributing UpdateGuardian, you agree to comply with the terms of the Apache License 2.0. Some key points of the license include:

You must include a copy of the license in any distribution of the software or any derivative works.
You must include a notice in any modified files to indicate the changes made.
If you redistribute the software, you must include a prominent notice to inform recipients that the software is covered by the Apache License 2.0.
You are not required to submit your modifications to the original project, but contributions are always welcome.
Please note that this summary is provided for informational purposes only and should not be considered a substitute for the full license text. Always refer to the full license for complete terms and conditions.
