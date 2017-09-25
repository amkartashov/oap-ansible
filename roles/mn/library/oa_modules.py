#!/usr/bin/python
# Copyright (c) Andrey Kartashov
# see LICENSE file

DOCUMENTATION = '''
---
module: oa_modules
short_description: installs OAP modules
description: Installs specified OAP modules and updates UI.
version_added: "2.3.2"
author: Andrey Kartashov (gorilych@gmail.com)
options:
    modules:
        description: list of module names
        required: true
        type: list
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
                modules = dict(required=True, type='list'),
                )
            )
    try:
        from ansible.module_utils.oaapi import OaError, OaApi
    except ImportError as e:
        module.fail_json(msg="Failed to import OA API library: %s" % e)
    modules = module.params['modules'] or list()
    try:
        a = OaApi()
        installed_modules = a.get_installed_modules()
        modules_to_install = [m for m in modules if not m in installed_modules]
        if not modules_to_install:
            module.exit_json(changed=False)
        else:
            for m in modules_to_install:
                a.install_module(m)
            module.exit_json(changed=True, installed_modules=modules_to_install)
    except OaError as e:
        module.fail_json(msg="Failed with %s" % e)


if __name__ == '__main__':
    main()
