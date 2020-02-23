k93s
=====

Provision multi-node stripped-down Kubernetes on Dev Laptop in 9 minutes with QEMU.



STATUS
======

k93s is experimental and yet unstable software!


Install
=======

Fedora 31+ Quick Start
-----------------------

```
dnf install libvirt bridge-utils libvirt virt-install qemu-kvm
gpasswd -a user libvirt
gpasswd -a user qemu
(relogin into session)
cp .k93s.default.config .k93s.working.config
make up
```


How it works ?
==============
- python3
- qemu+KVM
- virt-lighting
- ansible


`K_93_CONFIG` -- environment variable for k93s config location.
                 By default, the config location is .k93s.working.config


How to test ?
=============
```
pip3 install -r requirements-test.txt
make test
```

TODO
====
- add microk8s support
- add support for OSX/qemu+hvf hosts
- validation for config, including typing checks


CREDITS
========
- https://github.com/rancher/k3s -- K3S and K3S Ansible integration authors
- https://github.com/virt-lightning/virt-lightning -- most convenient libvirt integration for Python :3
