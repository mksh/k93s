k93s
=====

Provision multi-node stripped-down Kubernetes on Dev Laptop in 9 minutes with QEMU.


STATUS
======

k93s is experimental and yet unstable software!


Install
=======

Install Kubectl: https://kubernetes.io/docs/tasks/tools/install-kubectl/

Fedora 31+ Quick Start
-----------------------

```
dnf install libvirt bridge-utils libvirt virt-install qemu-kvm
gpasswd -a user libvirt
gpasswd -a user qemu
(relogin into session)
pip3 install --user -r requirements.txt
python3 setup.py install
python3 -m k93s kubernetes
python3 -m k93s kubectl
```


How it works ?
==============
- python3
- qemu+KVM
- virt-lightning
- ansible


`K_93_CONFIG` -- environment variable for k93s config location.
                 By default, the config location is .k93s.working.config


How to test ?
=============
```
pip3 install --user -r requirements-test.txt
make test
```

TODO
====
- [ ] validation for config, including typing checks
- [ ] running multiple kubernetes cluster on the same host
- [ ] add support for dqlite-powered multi node K3S cluster
- [ ] add setup script with versioning
- [ ] add read the docs entry
- [ ] add tox-based testing for multiple Python 3 versions
- [ ] add CI
- [ ] add PyPI entry
- [ ] create Debian & RPM distributions
- [ ] add microk8s support
- [ ] add support for OSX/qemu+hvf hosts
- [ ] add some non-libvirt backends
- [ ] add integration testing


CREDITS
========
- https://github.com/rancher/k3s -- K3S and K3S Ansible integration authors
- https://github.com/virt-lightning/virt-lightning -- most convenient libvirt integration for Python :3
