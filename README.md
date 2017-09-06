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
# add sensitive information into vault file
rm group_vars/all/vault
ansible-vault create group_vars/all/vault
ansible-vault edit group_vars/all/vault
# add proper ips into hosts
vim hosts
# copy license file into path you specified in group_vars/all/vars

## Run playbook for hwcheck
ansible-playbook site.yml -e "{hwcheck: true}"

## Run playbook for installation
ansible-playbook site.yml
```
