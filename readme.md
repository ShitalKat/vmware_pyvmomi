# pyVmomi VM Management Project

## Introduction

This project, demonstrates how to manage virtual machines programmatically using the **pyVmomi** library, which is the Python SDK for VMware vSphere API. The project interacts with a vCenter simulator (vcsim) and showcases various VM lifecycle operations, resource monitoring, and automation capabilities.

The goal is to build a practical proof-of-concept (POC) for managing VMs in a vSphere environment using Python scripts.

---

## Features

1. **List all VMs** with their power state, CPU, and memory.
2. **Create and delete** a virtual machine programmatically.
3. **Power on/off or reboot** a VM using a script.
4. **Clone a VM from a template** with basic customization.
5. **List all datastores** and their free/used space.
6. **Generate a report of all ESXi hosts** and their health status.
7. **Monitor recent vCenter events** like VM power changes.
8. **Take a snapshot of a VM and delete it later.**
9. **Revert to Snapshot, Clone From Snapshot, Monitor Changes** (Current VM vs. snapshot).

---

## Usage

This project is intended to be run in a Python environment with access to a vCenter simulator. It uses pyVmomi to connect to vCenter and perform operations on virtual machines and infrastructure components.

Make sure to install the required dependencies and configure your vCenter connection settings before running the scripts.

---

# Setup Instructions

## Prerequisites
1. Install [Docker](https://docs.docker.com/get-docker/), [Python 3.13.7](https://www.python.org/downloads/), and [PyCharm](https://www.jetbrains.com/pycharm/).

## Steps

### 1. Create Docker Instance of vcsim
Run the following command to create a docker instance of **nimmis/vcsim**:  
[Docker Hub - nimmis/vcsim](https://hub.docker.com/r/nimmis/vcsim)

```bash
docker run -d -p 443:443 --name vmpoc nimmis/vcsim:latest
```

### 2. Create Python Project and Virtual Environment
Inside PyCharm or terminal, create and activate a virtual environment:

```bash
python -m venv venv_name
venv\Scripts\activate
```

### 3. Install Required Python Libraries
Install the VMware Python SDK libraries:

```bash
pip install pyvmomi pyvim
```

---

