# Mount

## Description

This role provides simply provides an interface to `**mount** Ansible module <https://docs.ansible.com/ansible/latest/collections/ansible/posix/mount_module.html>`_ .

## Instructions

Set needed mounting point using a list:

```yaml
mount:
  # Mount DVD read-only
  - path: /mnt/dvd
    src: /dev/sr0
    fstype: iso9660
    opts: ro,noauto
    state: present
  # Mount up device by label
  - path: /srv/disk
    src: LABEL=SOME_LABEL
    fstype: ext4
    state: present
  # Mount and bind a volume
  - path: /system/new_volume/boot
    src: /boot
    opts: bind
    state: mounted
    fstype: none
  # Mount an NFS volume
  - src: 192.168.1.100:/nfs/ssd/shared_data
    path: /mnt/shared_data
    opts: rw,sync,hard,intr
    state: mounted
    fstype: nfs
```

See `**mount** Ansible module page <https://docs.ansible.com/ansible/latest/collections/ansible/posix/mount_module.html>`_
for the full list of available parameters.

## Changelog

**Please now update CHANGELOG file at repository root instead of adding logs in this file.
These logs bellow are only kept for archive.**

* 1.1.1: Fix missing list. Benoit Leveugle <benoit.leveugle@gmail.com>
* 1.1.0: Update to pip Ansible. Benoit Leveugle <benoit.leveugle@gmail.com>
* 1.0.1: Bug fix for src option. Neil Munday <neil@mundayweb.com>
* 1.0.0: Role creation. Benoit Leveugle <benoit.leveugle@gmail.com>
