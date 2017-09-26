#!/usr/bin/python
# Copyright (c) Andrey Kartashov
# see LICENSE file

DOCUMENTATION = '''
---
module: oa_register_ns
short_description: registers name server
description: Registers name server in OAP.
version_added: "2.3.2"
author: Andrey Kartashov (gorilych@gmail.com)
options:
    backnet:
        description: backnet IP of the server
        required: true
        type: string
    frontnet:
        description: frontnet IP of the server
        required: true
        type: string
    new_hostname:
        description: register with new hostname
        required: false
        type: string
    login:
        description: ssh login name
        required: false
        default: root
        type: string
    password:
        description: ssh password
        required: true
        type: string
requirements:
    ansible: 2.3
notes: uses library oaapi, embedded into module_utils
'''

ANSIBLE_METADATA = {'metadata_version': '1.0',
    'status': ['preview'],
    'supported_by': 'community'}

from ansible.module_utils.basic import AnsibleModule

def main(): 
    module = AnsibleModule(
            argument_spec = dict(
                backnet = dict(required=True, type='str'),
                frontnet = dict(required=True, type='str'),
                new_hostname = dict(required=False, type='str'),
                login = dict(required=False, type='str', default='root'),
                password = dict(required=True, type='str', no_log=True),
                )
            )
    try:
        from ansible.module_utils.oaapi import OaError, OaApi
    except ImportError as e:
        module.fail_json(msg="Failed to import OA API library: %s" % e)
    backnet = module.params['backnet']
    frontnet = module.params['frontnet']
    new_hostname = module.params['new_hostname']
    login = module.params['login']
    password = module.params['password']
    try:
        a = OaApi()
        if a.is_node_registered(backnet):
            module.exit_json(changed=False)
        else:
            host_id = a.register_dns(backnet, login, password, frontnet, new_hostname)
            module.exit_json(changed=True, host_id=host_id)
    except OaError as e:
        module.fail_json(msg="Failed with %s" % e)


if __name__ == '__main__':
    main()
