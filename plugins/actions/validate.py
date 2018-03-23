import sys
import os

from ansible.plugins.action import ActionBase

import notario
from notario.exceptions import Invalid
from notario.decorators import optional
from notario.validators import types, recursive

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        # we must use hostvars, since task_vars will have un-processed variables
        hostvars = task_vars['hostvars']
        mode = self._task.args.get('mode', 'permissive')

        self._supports_check_mode = False # XXX ?
        self._supports_async      = True

        result = {}
        result['_ansible_verbose_always'] = True

        for host, _vars in hostvars.items():
            try:
                notario.validate(_vars, variables, defined_keys=True)
            except Invalid as error:
                display.vvvv("Notario Failure: %s" % str(error))
                display.warning("[%s] Validation failed for variable: %s" % (host, error.path[-2]))
                msg = "Invalid variable assignment in host: %s\n" % host
                msg += "    %s = %s\n" % (error.path[-2], error.path[-1])
                msg += "    %s   %s\n" % (" "*len(str(error.path[-2])), "^" *len(str(error.path[-1])))
                msg += "Reason: %s" % error.reason
                result['failed'] = mode == 'strict'
                result['msg'] = msg
                result['stderr_lines'] = msg.split('\n')

            return result

# Schemas

variables = (
    ('ceph_conf_key_directory', types.boolean),
    (optional("nfs_file_gw"), types.boolean),
    (optional("osd_containerized_deployment"), types.boolean),
)
