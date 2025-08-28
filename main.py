from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import ssl
from enum import Enum

class PowerAction(Enum):
    """
    Enum for supported VM power operations.
    """
    POWER_ON = "power_on"
    POWER_OFF = "power_off"
    REBOOT = "reboot"

def connect_to_vcenter(host="localhost", port=443, user="user", pwd="pass"):
    """
    Connects to the vCenter server and returns a service instance (si).
    Uses an unverified SSL context for simulator compatibility.
    """
    context = ssl._create_unverified_context()
    try:
        print('Trying to connect to vCenter...')
        si = SmartConnect(
            host=host,
            user=user,
            pwd=pwd,
            port=port,
            sslContext=context
        )
        print("✅ Connected to vCenter Simulator!")
        return si
    except Exception as e:
        print("❌ Connection failed:", e)
        return None


def list_vms(si):
    """
    Lists all Virtual Machines (VMs) in the connected vCenter.

    Displays:
        - VM Name
        - Power State
        - CPU count
        - Memory allocation

    Note:
        When using the nimmis/vcsim simulator, mock VMs like DC0_H0_VM0
        will appear even if you haven’t created them manually.
    """
    if not si:
        print("No connection to vCenter.")
        return

    content = si.RetrieveContent()
    container = content.rootFolder
    viewType = [vim.VirtualMachine]
    containerView = content.viewManager.CreateContainerView(container, viewType, True)

    print("\n📋 VM Inventory:")
    for vm in containerView.view:
        summary = vm.summary
        print(f"Name: {summary.config.name}")
        print(f"Power State: {summary.runtime.powerState}")
        print(f"CPU: {summary.config.numCpu} vCPU")
        print(f"Memory: {summary.config.memorySizeMB} MB")
        print("-" * 40)


def get_first_datastore(si):
    """
    Retrieves the first datastore available in the environment.

    Args:
        si: ServiceInstance object.

    Returns:
        Datastore object if found, otherwise None.
    """
    content = si.RetrieveContent()
    containerView = content.viewManager.CreateContainerView(content.rootFolder, [vim.Datastore], True)

    datastores = containerView.view
    if datastores:
        print(f"✅ Found datastore: {datastores[0].name}")
        return datastores[0]
    else:
        print("❌ No datastore found.")
        return None


def vm_exists(si, vm_name):
    """
    Checks if a VM with the given name exists.

    Args:
        si: ServiceInstance object.
        vm_name (str): Name of the VM to check.

    Returns:
        bool: True if VM exists, False otherwise.
    """
    content = si.RetrieveContent()
    containerView = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)

    for vm in containerView.view:
        if vm.name == vm_name:
            return True
    return False


def create_vm(si, vm_name="Shital_TestVM"):
    """
    Creates a new VM in the vCenter environment.

    Args:
        si: ServiceInstance object.
        vm_name (str): Name of the new VM.

    Returns:
        Task object representing the VM creation.
    """
    try:
        if vm_exists(si, vm_name):
            print(f"⚠️ VM '{vm_name}' already exists. Skipping creation.")
            return None

        content = si.RetrieveContent()
        datacenter = content.rootFolder.childEntity[0]
        vm_folder = datacenter.vmFolder
        resource_pool = datacenter.hostFolder.childEntity[0].resourcePool
        datastore = get_first_datastore(si)

        vm_config = vim.vm.ConfigSpec(
            name=vm_name,
            memoryMB=128,
            numCPUs=1,
            guestId="otherGuest",
            files=vim.vm.FileInfo(vmPathName=f"[{datastore.name}]")
        )

        print(f"Creating VM: {vm_name}")
        task = vm_folder.CreateVM_Task(config=vm_config, pool=resource_pool)

        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
            continue

        if task.info.state == vim.TaskInfo.State.success:
            print(f"✅ VM '{vm_name}' created successfully.")
        else:
            print(f"❌ VM creation failed: {task.info.error.msg}")
        return task

    except Exception as e:
        print(f"❌ Error during VM creation: {e}")
    return None


def delete_vm(si, vm_name):
    """
    Deletes a VM from the vCenter environment.

    Args:
        si: ServiceInstance object.
        vm_name (str): Name of the VM to delete.

    Returns:
        Task object if deletion initiated, otherwise None.
    """
    content = si.RetrieveContent()
    containerView = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)

    for vm in containerView.view:
        if vm.name == vm_name:
            print(f"🗑️ Deleting VM: {vm_name}")
            return vm.Destroy_Task()

    print(f"⚠️ VM '{vm_name}' not found.")
    return None

def control_vm_power(si, vm_name, action: PowerAction):
    """
    Controls the power state of a VM.
    action: PowerAction Enum (POWER_ON, POWER_OFF, REBOOT)
    """
    content = si.RetrieveContent()
    container = content.rootFolder
    viewType = [vim.VirtualMachine]
    recursive = True
    containerView = content.viewManager.CreateContainerView(container, viewType, recursive)

    for vm in containerView.view:
        if vm.name == vm_name:
            try:
                if action == PowerAction.POWER_ON:
                    if vm.runtime.powerState != vim.VirtualMachinePowerState.poweredOn:
                        print(f"🔌 Powering ON VM: {vm_name}")
                        task = vm.PowerOn()
                    else:
                        print(f"⚠️ VM '{vm_name}' is already powered on.")
                elif action == PowerAction.POWER_OFF:
                    if vm.runtime.powerState != vim.VirtualMachinePowerState.poweredOff:
                        print(f"⏻ Powering OFF VM: {vm_name}")
                        task = vm.PowerOff()
                    else:
                        print(f"⚠️ VM '{vm_name}' is already powered off.")
                elif action == PowerAction.REBOOT:
                    if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
                        print(f"🔄 Rebooting VM: {vm_name}")
                        vm.PowerOff()
                        vm.PowerOn()
                    else:
                        print(f"⚠️ Cannot reboot. VM '{vm_name}' is not powered on.")
                else:
                    print(f"❌ Unknown action: {action}")
                return
            except Exception as e:
                print(f"❌ Failed to {action.value} VM '{vm_name}': {e}")
                return
    print(f"❌ VM '{vm_name}' not found.")

def take_snapshot(si, vm_name, snapshot_name="Snapshot1", description="Snapshot created by script"):
    content = si.RetrieveContent()
    containerView = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)

    for vm in containerView.view:
        if vm.name == vm_name:
            try:
                print(f"📸 Taking snapshot of VM: {vm_name}")
                task = vm.CreateSnapshot_Task(
                    name=snapshot_name,
                    description=description,
                    memory=False,
                    quiesce=False
                )
                while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
                    continue
                if task.info.state == vim.TaskInfo.State.success:
                    print(f"✅ Snapshot '{snapshot_name}' created successfully.")
                else:
                    print(f"❌ Snapshot creation failed: {task.info.error.msg}")
                return
            except Exception as e:
                print(f"❌ Failed to take snapshot: {e}")
                return
    print(f"❌ VM '{vm_name}' not found.")

def revert_to_snapshot(si, vm_name, snapshot_name="Snapshot1"):
    content = si.RetrieveContent()
    containerView = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)

    for vm in containerView.view:
        if vm.name == vm_name and vm.snapshot:
            try:
                for tree in vm.snapshot.rootSnapshotList:
                    if tree.name == snapshot_name:
                        print(f"⏪ Reverting VM '{vm_name}' to snapshot '{snapshot_name}'")
                        task = tree.snapshot.RevertToSnapshot_Task()
                        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
                            continue
                        if task.info.state == vim.TaskInfo.State.success:
                            print(f"✅ Reverted to snapshot '{snapshot_name}'")
                        else:
                            print(f"❌ Revert failed: {task.info.error.msg}")
                        return
                print(f"⚠️ Snapshot '{snapshot_name}' not found.")
            except Exception as e:
                print(f"❌ Error reverting to snapshot: {e}")
            return
    print(f"❌ VM '{vm_name}' not found or has no snapshots.")

def clone_vm_from_snapshot(si, source_vm_name, clone_name):
    content = si.RetrieveContent()
    containerView = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)

    for vm in containerView.view:
        if vm.name == source_vm_name and vm.snapshot:
            try:
                relocate_spec = vim.vm.RelocateSpec()
                clone_spec = vim.vm.CloneSpec(
                    location=relocate_spec,
                    powerOn=False,
                    template=False,
                    snapshot=vm.snapshot.currentSnapshot
                )

                datacenter = content.rootFolder.childEntity[0]
                vm_folder = datacenter.vmFolder

                print(f"🧬 Cloning VM '{source_vm_name}' to '{clone_name}' from snapshot")
                task = vm.Clone(folder=vm_folder, name=clone_name, spec=clone_spec)
                while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
                    continue
                if task.info.state == vim.TaskInfo.State.success:
                    print(f"✅ Clone '{clone_name}' created successfully.")
                else:
                    print(f"❌ Clone failed: {task.info.error.msg}")
                return
            except Exception as e:
                print(f"❌ Error cloning VM: {e}")
            return
    print(f"❌ Source VM '{source_vm_name}' not found or has no snapshots.")

def compare_vm_to_snapshot(si, vm_name, snapshot_name="Snapshot1"):
    content = si.RetrieveContent()
    containerView = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)

    for vm in containerView.view:
        if vm.name == vm_name and vm.snapshot:
            try:
                for tree in vm.snapshot.rootSnapshotList:
                    if tree.name == snapshot_name:
                        snap_config = tree.config
                        current_config = vm.config

                        print(f"🔍 Comparing VM '{vm_name}' to snapshot '{snapshot_name}'")
                        print(f"- CPU: {current_config.hardware.numCPU} vs Snapshot: {snap_config.hardware.numCPU}")
                        print(f"- Memory: {current_config.hardware.memoryMB} MB vs Snapshot: {snap_config.hardware.memoryMB} MB")
                        # You can add more comparisons here
                        return
                print(f"⚠️ Snapshot '{snapshot_name}' not found.")
            except Exception as e:
                print(f"❌ Error comparing VM to snapshot: {e}")
            return
    print(f"❌ VM '{vm_name}' not found or has no snapshots.")

def convert_vm_to_template(si, vm_name):
    """
    Converts an existing VM to a template.
    """
    content = si.RetrieveContent()
    container = content.rootFolder
    viewType = [vim.VirtualMachine]
    recursive = True
    containerView = content.viewManager.CreateContainerView(container, viewType, recursive)

    for vm in containerView.view:
        if vm.name == vm_name:
            try:
                print(f"Converting VM '{vm_name}' to template...")
                vm.MarkAsTemplate()
                print(f"✅ VM '{vm_name}' is now a template.")
                return
            except Exception as e:
                print(f"❌ Failed to convert VM to template: {e}")
                return
    print(f"❌ VM '{vm_name}' not found.")

def clone_vm_from_template(si, template_name, new_vm_name, datacenter_name=None, datastore_name=None, resource_pool_name=None, power_on=True):
    """
    Clones a VM from a template with basic customization.
    """
    content = si.RetrieveContent()

    # Find the datacenter
    datacenter = None
    for dc in content.rootFolder.childEntity:
        if not datacenter_name or dc.name == datacenter_name:
            datacenter = dc
            break
    if not datacenter:
        print("❌ Datacenter not found.")
        return

    # Find the template VM
    template_vm = None
    for vm in datacenter.vmFolder.childEntity:
        if isinstance(vm, vim.VirtualMachine) and vm.name == template_name:
            template_vm = vm
            break
    if not template_vm:
        print(f"❌ Template '{template_name}' not found.")
        return

    # Find the datastore
    datastore = None
    if datastore_name:
        for ds in datacenter.datastore:
            if ds.name == datastore_name:
                datastore = ds
                break
    else:
        datastore = get_first_datastore(si)
    if not datastore:
        print("❌ Datastore not found.")
        return

    # Find the resource pool
    resource_pool = None
    if resource_pool_name:
        for cluster in datacenter.hostFolder.childEntity:
            for rp in cluster.resourcePool.resourcePool:
                if rp.name == resource_pool_name:
                    resource_pool = rp
                    break
    else:
        resource_pool = datacenter.hostFolder.childEntity[0].resourcePool

    # Define relocation spec
    relocate_spec = vim.vm.RelocateSpec()
    relocate_spec.datastore = datastore
    relocate_spec.pool = resource_pool

    # Define clone spec
    clone_spec = vim.vm.CloneSpec()
    clone_spec.location = relocate_spec
    clone_spec.powerOn = power_on

    print(f"🛠️ Cloning VM '{new_vm_name}' from template '{template_name}'...")
    task = template_vm.Clone(folder=datacenter.vmFolder, name=new_vm_name, spec=clone_spec)

    # Wait for task to complete
    while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
        continue

    if task.info.state == vim.TaskInfo.State.success:
        print(f"✅ VM '{new_vm_name}' cloned successfully.")
    else:
        print(f"❌ Clone failed: {task.info.error.msg}")

def list_datastores_with_space(si):
    """
    Lists all datastores with their free and used space in GB.
    """
    if not si:
        print("No connection to vCenter.")
        return

    content = si.RetrieveContent()
    container = content.rootFolder
    viewType = [vim.Datastore]
    recursive = True
    containerView = content.viewManager.CreateContainerView(container, viewType, recursive)

    print("\n📦 Datastore Inventory:")
    for datastore in containerView.view:
        summary = datastore.summary
        capacity_gb = summary.capacity / (1024 ** 3)
        free_space_gb = summary.freeSpace / (1024 ** 3)
        used_space_gb = capacity_gb - free_space_gb

        print(f"Name: {summary.name}")
        print(f"  Capacity: {capacity_gb:.2f} GB")
        print(f"  Free Space: {free_space_gb:.2f} GB")
        print(f"  Used Space: {used_space_gb:.2f} GB")
        print("-" * 40)

def report_esxi_hosts_health(si):
    """
    Generates a report of all ESXi hosts and their health status.
    """
    if not si:
        print("No connection to vCenter.")
        return

    content = si.RetrieveContent()
    container = content.rootFolder
    viewType = [vim.HostSystem]
    recursive = True
    containerView = content.viewManager.CreateContainerView(container, viewType, recursive)

    print("\n🖥️ ESXi Host Health Report:")
    for host in containerView.view:
        summary = host.summary
        hardware = summary.hardware
        runtime = summary.runtime
        overall_status = summary.overallStatus

        print(f"Host Name: {summary.config.name}")
        print(f"  Manufacturer: {hardware.vendor}")
        print(f"  Model: {hardware.model}")
        print(f"  CPU: {hardware.cpuModel} ({hardware.numCpuPkgs} CPUs, {hardware.numCpuCores} cores)")
        print(f"  Memory: {hardware.memorySize / (1024 ** 3):.2f} GB")
        print(f"  Connection State: {runtime.connectionState}")
        print(f"  Power State: {runtime.powerState}")
        print(f"  Overall Health Status: {overall_status}")
        print("-" * 50)

def monitor_recent_vm_events(si, max_events=20):
    """
    Monitors recent vCenter events related to VM power changes.
    """
    if not si:
        print("No connection to vCenter.")
        return

    content = si.RetrieveContent()
    event_manager = content.eventManager

    # Get the latest events
    try:
        print(f"\n📋 Recent VM Power Events (up to {max_events}):")
        event_filter = vim.event.EventFilterSpec()
        events = event_manager.QueryEvents(event_filter)

        count = 0


        for event in events:
            if hasattr(event, 'vm') and isinstance(event.vm, vim.event.VmEvent):
                if isinstance(event, (vim.event.VmPoweredOnEvent, vim.event.VmPoweredOffEvent)):
                    print(f"Time: {event.createdTime}")
                    print(f"VM: {event.vm.name}")
                    print(f"User: {event.userName}")
                    print(f"Event: {type(event).__name__}")
                    print("-" * 40)
                    count += 1
                    if count >= max_events:
                        break

        if count == 0:
            print("No recent VM power events found.")
    except Exception as e:
        print(f"❌ Failed to retrieve events: {e}")

def demo_template():
    si = connect_to_vcenter()
    if si:
        # Step 1: Create a base VM
        create_vm(si, "TemplateVM")

        # Step 2: Convert it to a template
        convert_vm_to_template(si, "TemplateVM")

        # Step 3: Clone from the template
        clone_vm_from_template(si, template_name="TemplateVM", new_vm_name="Shital_ClonedVM")

def demo_snapshot():
    si = connect_to_vcenter()
    if si:
        # ---- Check Snapshot functionality ---- #
        create_vm(si,'Shital_Test_snapshot_VM')
        control_vm_power(si, "Shital_Test_snapshot_VM", PowerAction.POWER_OFF)
        take_snapshot(si, "Shital_Test_snapshot_VM", snapshot_name="InitialSnap")

        print("🔧 Modifying VM 'Shital_Test_snapshot_VM' memory to simulate change...")
        content = si.RetrieveContent()
        containerView = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)
        list_vms(si)
        for vm in containerView.view:
            if vm.name == "Shital_Test_snapshot_VM":
                config_spec = vim.vm.ConfigSpec()
                config_spec.memoryMB = 256  # Change from 128 to 256
                task = vm.ReconfigVM_Task(config_spec)
                while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
                    continue
                print("✅ VM memory updated.")


        #compare_vm_to_snapshot(si, "Shital_Test_snapshot_VM", snapshot_name="InitialSnap")
        #revert_to_snapshot(si, "Shital_Test_snapshot_VM", snapshot_name="InitialSnap")
        #clone_vm_from_snapshot(si, "Shital_Test_snapshot_VM", "Clone_shitalVM")
        delete_vm(si, "Shital_Test_snapshot_VM")
        delete_vm(si, "Clone_shitalVM")
        list_vms(si)
        Disconnect(si)

def demo_vm_creation():
    si = connect_to_vcenter()
    if si:
        create_vm(si, "Shital_TestVM")
        control_vm_power(si, "Shital_TestVM", PowerAction.POWER_ON)
        list_vms(si)
        control_vm_power(si, "Shital_TestVM", PowerAction.REBOOT)
        control_vm_power(si, "Shital_TestVM", PowerAction.POWER_OFF)
        delete_vm(si, "Shital_TestVM")  # Uncomment to delete

def demo_report():
    si = connect_to_vcenter()
    if si:
        list_vms(si)
        list_datastores_with_space(si)
        report_esxi_hosts_health(si)
        monitor_recent_vm_events(si)


def main():
    demo_report()
    demo_vm_creation()
    demo_snapshot()
    demo_template()

if __name__ == '__main__':
    main()


