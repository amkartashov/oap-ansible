#!/usr/bin/python
# Copyright (c) Andrey Kartashov
# see LICENSE file

DOCUMENTATION = '''
---
module: oa_update
short_description: installs OAP updates
description: Installs OAP updates on OA management node.
version_added: "2.3.2"
author: Andrey Kartashov (gorilych@gmail.com)
'''

ANSIBLE_METADATA = {'metadata_version': '1.0',
    'status': ['preview'],
    'supported_by': 'community'}

import re
from ansible.module_utils.basic import AnsibleModule

def main(): 
    module = AnsibleModule(argument_spec = dict())
    rc, stdout, stderr = module.run_command(['oa-update', '--batch'], check_rc=True)
    if filter(lambda x: 'Available hotfix' in x, stdout.split('\n')):
        regexp = re.compile('^.*\]  \* (KB.*)$')
        hotfixes = [regexp.match(kb).group(1) for kb in
                    filter(lambda x: '* KB' in x, stdout.split('\n'))]
        rc, stdout, stderr = module.run_command(['oa-update', '--batch', '--install'], check_rc=True)
        module.exit_json(hotfixes=list(), changed=True)
    else:
        module.exit_json(hotfixes=list())

if __name__ == '__main__':
    main()
