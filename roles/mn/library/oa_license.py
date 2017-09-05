#!/usr/bin/python
# Copyright (c) Andrey Kartashov
# see LICENSE file

DOCUMENTATION = '''
---
module: oa_license
short_description: installs OAP license
description: Installs OAP license from local file on target host to OA management node.
version_added: "2.3.2"
author: Andrey Kartashov (gorilych@gmail.com)
options:
    license_file:
        description: path to license file (local)
        required: true
        type: path
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
                license_file = dict(required=True, type='path'),
                )
            )
    try:
        from ansible.module_utils.oaapi import OaError, OaApi, OaLicense
    except ImportError as e:
        module.fail_json(msg="Failed to import OA API library: %s" % e)
    license_file = module.params['license_file']
    try:
        a = OaApi()
        if a.has_active_license():
            module.exit_json(changed=False)
        else:
            l = OaLicense(license_file)
            a.upload_license(l)
            module.exit_json(changed=True)
    except OaError as e:
        module.fail_json(msg="Failed with %s" % e)


if __name__ == '__main__':
    main()
