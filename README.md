# UpdateGuardian

## Table of Contents

- [UpdateGuardian](#updateguardian)
  - [Table of Contents](#table-of-contents)
  - [Introduction](#introduction)
    - [⚠️ UpdateGuardian is discontinued and not reliable](#️-updateguardian-is-in-beta-expept-bugs-even-though-it-has-been-heavily-tested)
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

### ⚠️ UpdateGuardian is discontinued and not reliable

<br>
UpdateGuardian is an automation system for updating a local network of Windows 10 PCs, designed to streamline and secure
update operations while reducing the technical maintenance required.

The idea came from the hassle to update a moderate number of Windows 10 PCs spread out in a local network, without the
need or cost at our disposal to install a Windows server.

It is a free and open source project, licensed under the Apache License 2.0.

## Main Features

Only intended to work on Windows 10 and 11. Other OS not supported.

These are the current features :

- Update automation
- Update scheduling
- Centralized update management
- Update notifications and reporting (email), logs
- Installer

## Prerequisites

If you go with the default installation options, the following prerequisites are required:

- Windows 10 or 11: Must be part of a **wired** local network with Wake-on-LAN (WoL) support. If WoL is not available, you'll need to manually power on the PCs for network updates.
- Server PC: A Windows machine that can act as a server, either running 24/7 for scheduled rollouts or manually triggered for updates.
- Internet Connection: Required for updates and remote access.
- Firewall Configuration: The server PC must allow SSH traffic, specifically on ports 22 and 8000 within the local network.

### Software Installed or Activated on Local Client PCs

The program will handle the installation or activation of:

- Python (admin user only)
- SSH Server
- PSWindowsUpdate PowerShell module
- Dependencies for PSWindowsUpdate
- Various Python packages
- Modifications to some Windows Firewall rules
- Wake-on-LAN (if supported)

### Software Installed on the Server

The installer will set up:

- Chocolatey package manager
- Git
- Python

## Installation and Configuration

First, make sure all pcs have a static ip address, and better if they are linked to the mac address.

After this, make sure the pc can communicate with each other, and that the port 8000 is not blocked (only local network, and for the server not the gateway)

Execute Install.ps1.

Then, after all pc clients have completed the installation process, write "stop" to the server. You should see all pc in the printed database.
If you want to update now, type "force" and then enter.

If you want to manually install the server, just download the code and run it with python 3.11. Older python version **MAY** work.

To change some settings, modify the json files in the root folder.

For now, there is :

- email_infos.json
- launch_infos.json
- config.json

## Tests

Unit tests are located in the "tests" folder. They are written using the unittest library.

The majority of the testing has been done in virtual windows machines on Windows 10 (VirtualBox).

## Troubleshooting and Support

Make sure to check firewall rules and ports to allow the communication between the server and the clients in ssh, ping
and wake on lan. This includes the Windows firewall and the router firewall. Sometimes, there is also the paid antivirus
firewall to check.

Make also sure that the server and the clients are in the same subnet.

## Contributions

Contributions are welcome. Please read the [contributing guidelines](CONTRIBUTING.md) before
submitting a pull request.

## License

UpdateGuardian is licensed under the Apache License, Version 2.0. This open-source license allows you to use, modify,
and distribute the software, subject to the terms and conditions outlined in the license.

The full text of the Apache License 2.0 can be found [here](http://www.apache.org/licenses/LICENSE-2.0)

By using, modifying, or distributing UpdateGuardian, you agree to comply with the terms of the Apache License 2.0. Some
key points of the license include:

You must include a copy of the license in any distribution of the software or any derivative works.
You must include a notice in any modified files to indicate the changes made.
If you redistribute the software, you must include a prominent notice to inform recipients that the software is covered
by the Apache License 2.0.
You are not required to submit your modifications to the original project, but contributions are always welcome.
Please note that this summary is provided for informational purposes only and should not be considered a substitute for
the full license text. Always refer to the full license for complete terms and conditions.
