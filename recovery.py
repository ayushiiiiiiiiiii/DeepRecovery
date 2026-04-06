import subprocess

def create_disk_image():
    print("Creating disk image...")
    subprocess.run(["dd","if=/dev/sdb","of=input/disk.img","bs=4M","status=progress"])

def mount_disk():
    print("Mounting disk image...")
    subprocess.run(["sudo","mount","input/disk_xfs.img","mount_point"])

def unmount_disk():
    print("Unmounting disk...")
    subprocess.run(["sudo","umount","mount_point"])

def recover_files():
    print("Starting file recovery...")
    subprocess.run(["photorec"])
