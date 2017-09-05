#!/usr/bin/python

import os

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
