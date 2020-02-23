k93s.ansible
============


This is Ansible repository for setting up Kubernetes
cluster on k93s nodes.

Structure:

k8s.yml
-------

A main playbook, which sets up master nodes first,
and agent nodes second.

`k_93_flavor` - an Ansible variable which defines
    Kubernetes flavor being installed.

All the necessary roles are executed in accordance
to flavor being requested.


roles/k8s-master
----------------

A role for setting up master node.

- *tasks/* - location for all tasks
- *tasks/__flavor__.yml* - location for flavor tasks
- *templates/__flavor__/* - location for templates
- *defaults/main.yml* - location for all default variable values


roles/k8s-agent
---------------

A role for setting up agent node.

- *tasks/* - location for all tasks
- *tasks/__flavor__.yml* - location for flavor tasks
- *templates/__flavor__/* - location for templates
- *defaults/main.yml* - location for all default variable values


roles/k8s-common
----------------

A container for Kubernetes install boilerplate, 
e.g. Ansible tasks shared for master and agent nodes.

- *tasks/__flavor__.yml* - location for flavor tasks
