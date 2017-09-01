# oap-ansible
Ansible playbooks for deploying OAP

# Usage

```shell
## Install prerequisites (needed for ansible)
yum install -y python-virtualenv gcc libffi-devel openssl-devel git

## Clone repository
git clone https://github.com/gorilych/oap-ansible.git

## Prepare virtual env
cd oap-ansible
virtualenv env
source env/bin/activate
pip install -r requirements.txt

## Modify ansible variables describing your environment
vim group_vars/all/vars
rm group_vars/all/vault
ansible-vault create group_vars/all/vault
ansible-vault edit group_vars/all/vault
vim hosts

## Run playbook for hwcheck
ansible-playbook site.yml -e "{hwcheck: true}"

## Run playbook for installation
ansible-playbook site.yml
```
