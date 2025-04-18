# Pam_limits

## Description

Allows to set custom pam limits (ulimit) on the system.

## Instructions

The roles handles all arguments listed in 
`Ansible pam_limits module <https://docs.ansible.com/ansible/latest/collections/community/general/pam_limits_module.html>`_ .

Example:

```yaml
rlimits:
  - domain: joe
    limit_type: soft
    limit_item: nofile
    value: 64000
  - domain: smith
    limit_type: hard
    limit_item: fsize
    value: 1000000
    use_max: yes
  - domain: james
    limit_type: '-'
    limit_item: memlock
    value: unlimited
    comment: unlimited memory lock for james
```

## Changelog

**Please now update CHANGELOG file at repository root instead of adding logs in this file.
These logs bellow are only kept for archive.**

* 1.1.0: Update to pip Ansible. Benoit Leveugle <benoit.leveugle@gmail.com>
* 1.0.0: Role creation. Johnny Keats <johnny.keats@outlook.com>
