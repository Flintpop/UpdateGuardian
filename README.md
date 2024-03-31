# UpdateGuardian

## Table of Contents

- [UpdateGuardian](#updateguardian)
  - [Table of Contents](#table-of-contents)
  - [Introduction](#introduction)
    - [⚠️ UpdateGuardian is in beta. Expect bugs, even though it has been heavily tested](#️-updateguardian-is-in-beta-expect-bugs-even-though-it-has-been-heavily-tested)
  - [Main Features](#main-features)
  - [Prerequisites](#prerequisites)
  - [Installation and Configuration](#installation-and-configuration)
    - [Server](#server)
      - [Notes about the installation](#notes-about-the-installation)
    - [Client Installation](#client-installation)
    - [Finish the Installation](#finish-the-installation)
  - [Usage](#usage)
  - [Project Architecture](#project-architecture)
  - [Tests](#tests)
  - [Troubleshooting and Support](#troubleshooting-and-support)
  - [Contributions](#contributions)

## Introduction

### ⚠️ UpdateGuardian is in beta. Expect bugs, even though it has been heavily tested

UpdateGuardian is an automation system for updating a local network of Windows 10 PCs, designed to streamline and secure
update operations while reducing the technical maintenance required.

The idea came from the hassle to update a moderate number of Windows 10 PCs spread out in a local network, without the
need or cost at our disposal to install a Windows server.

It is a free and open source project, licensed under the Apache License 2.0.

## Main Features

- Update automation
- Update scheduling
- Centralized update management
- Logs
- Installers for the server and the clients

Only intended to work on Windows 10 and 11 for the clients. Other OS not supported.

## Prerequisites

If you go with the default installation options, the following prerequisites are required:

- Windows 10 or 11 **wired** local network with wake on lan. If WOL is not available, you will have to manually turn on
  the pcs to update your network. Later on, a feature that uses smart plug could be imagined.
- A Windows/Linux pc that will act like a server. Can be turned on 24/7 and plan the rollout, or you can manually force
  updates.
- An internet connection
- A check of the firewall with ssh, port 22 and 8000 not blocked on the local network for the Windows/Linux pc that acts
  like a server.
- All interacting PCs must have static IP addresses

## Installation and Configuration

### Server

```bash
curl -sSl https://raw.githubusercontent.com/Flintpop/UpdateGuardian/main/install.sh | sudo bash
```

### Client Installation

Copy the automatically modified scripts_powershell/Client_Setup.ps1 script to a or many usb sticks.

Open a powershell shell as admin on each client and type `Set-ExecutionPolicy Unrestricted -Scope CurrentUser`. Then
type "A" to accept all changes. Then, run Client_Setup.ps1 on each client.

### Finish the Installation

Then, after all clients have completed the installation process, write "stop" to the server. You should see all pc in
the printed database.

### Notes about the installation (can skip)

What will be installed on the linux server:

- Git
- Python 3.11

> Windows installer is deprecated. It is still available in the latest release, but it is not recommended to use it.

The installer will set up on a Windows server:

- Chocolatey package manager
- Git
- Python
- Python packages

What will be installed on the Windows client:

- SSH Server
- PSWindowsUpdate PowerShell module
- Dependencies for PSWindowsUpdate
- Modifications to some Windows Firewall rules (like icmp)

## Usage

> It is **strongly recommended** to use a sort of "screen" or "tmux" to keep the software running in the background.

To force update the Windows pc in the lan network, type "force" in the menu.

To change some settings, go into "settings" menu when launching the software, and / or modify the json files in the root
folder.

- email_infos.json
- launch_infos.json
- config.json

You can add or remove pc in the database with the settings menu.

You can redo the email configuration in the settings. You can also change the launch time in the same menu.

## Project Architecture

Client-Server centralized approach.

Update Cycle :

- Wake on lan via IP address and mac address
- Then SSH with pubkey authentification
- .exe compiled python program that will setup a scheduled task to update the pc
- The scheduled task will have the highest privileges to update the pc
- PSWindowsUpdate powershell script

## Tests

Unit tests are located in the "tests" folder. They are written using the unittest library.

The majority of the testing has been done in virtual Windows machines on Windows 10 (VirtualBox) and
on Linux Mint for the server.

## Troubleshooting and Support

Make sure to check firewall rules and ports to allow the communication between the server and the clients in ssh, ping
and wake on lan. This includes the Windows firewall and the router firewall. Sometimes, there is also the paid antivirus
firewall to check.

Make also sure that the server and the clients are in the same subnet.

Open an issue if you find it necessary. Make sure it is the software and not your network the cause of the problem.

## Contributions

Contributions are welcome. Please read the [contributing guidelines](CONTRIBUTING.md) before
submitting a pull request.
