# Copyright 2015, Rackspace US, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import ConfigParser
import io
import json
import os
import yaml

from ansible import errors
from ansible.runner.return_data import ReturnData
from ansible import utils
from ansible.utils import template


CONFIG_TYPES = {
    'ini': 'return_config_overrides_ini',
    'json': 'return_config_overrides_json',
    'yaml': 'return_config_overrides_yaml'
}


class ActionModule(object):
    TRANSFERS_FILES = True

    def __init__(self, runner):
        self.runner = runner

    def grab_options(self, complex_args, module_args):
        """Grab passed options from Ansible complex and module args.

        :param complex_args: ``dict``
        :param module_args: ``dict``
        :returns: ``dict``
        """
        options = dict()
        if complex_args:
            options.update(complex_args)

        options.update(utils.parse_kv(module_args))
        return options

    @staticmethod
    def return_config_overrides_ini(config_overrides, resultant):
        """Returns string value from a modified config file.

        :param config_overrides: ``dict``
        :param resultant: ``str`` || ``unicode``
        :returns: ``str``
        """
        config = ConfigParser.RawConfigParser(allow_no_value=True)
        config_object = io.BytesIO(resultant.encode('utf-8'))
        config.readfp(config_object)
        for section, items in config_overrides.items():
            # If the items value is not a dictionary it is assumed that the
            #  value is a default item for this config type.
            if not isinstance(items, dict):
                config.set('DEFAULT', section, str(items))
            else:
                # Attempt to add a section to the config file passing if
                #  an error is raised that is related to the section
                #  already existing.
                try:
                    config.add_section(section)
                except (ConfigParser.DuplicateSectionError, ValueError):
                    pass
                for key, value in items.items():
                    config.set(section, key, str(value))
        else:
            config_object.close()

        resultant_bytesio = io.BytesIO()
        try:
            config.write(resultant_bytesio)
            return resultant_bytesio.getvalue()
        finally:
            resultant_bytesio.close()

    def return_config_overrides_json(self, config_overrides, resultant):
        """Returns config json

        Its important to note that file ordering will not be preserved as the
        information within the json file will be sorted by keys.

        :param config_overrides: ``dict``
        :param resultant: ``str`` || ``unicode``
        :returns: ``str``
        """
        original_resultant = json.loads(resultant)
        merged_resultant = self._merge_dict(
            base_items=original_resultant,
            new_items=config_overrides
        )
        return json.dumps(
            merged_resultant,
            indent=4,
            sort_keys=True
        )

    def return_config_overrides_yaml(self, config_overrides, resultant):
        """Return config yaml.

        :param config_overrides: ``dict``
        :param resultant: ``str`` || ``unicode``
        :returns: ``str``
        """
        original_resultant = yaml.safe_load(resultant)
        merged_resultant = self._merge_dict(
            base_items=original_resultant,
            new_items=config_overrides
        )
        return yaml.safe_dump(
            merged_resultant,
            default_flow_style=False,
            width=1000,
        )

    def _merge_dict(self, base_items, new_items):
        """Recursively merge new_items into base_items.

        :param base_items: ``dict``
        :param new_items: ``dict``
        :returns: ``dict``
        """
        for key, value in new_items.iteritems():
            if isinstance(value, dict):
                base_items[key] = self._merge_dict(
                    base_items.get(key, {}),
                    value
                )
            elif isinstance(value, list):
                if key in base_items and isinstance(base_items[key], list):
                    base_items[key].extend(value)
                else:
                    base_items[key] = value
            else:
                base_items[key] = new_items[key]
        return base_items

    def run(self, conn, tmp, module_name, module_args, inject,
            complex_args=None, **kwargs):
        """Run the method"""
        if not self.runner.is_playbook:
            raise errors.AnsibleError(
                'FAILED: `config_templates` are only available in playbooks'
            )

        options = self.grab_options(complex_args, module_args)
        try:
            source = options['src']
            dest = options['dest']

            config_overrides = options.get('config_overrides', dict())
            config_type = options['config_type']
            assert config_type.lower() in ['ini', 'json', 'yaml']
        except KeyError as exp:
            result = dict(failed=True, msg=exp)
            return ReturnData(conn=conn, comm_ok=False, result=result)

        source_template = template.template(
            self.runner.basedir,
            source,
            inject
        )

        if '_original_file' in inject:
            source_file = utils.path_dwim_relative(
                inject['_original_file'],
                'templates',
                source_template,
                self.runner.basedir
            )
        else:
            source_file = utils.path_dwim(self.runner.basedir, source_template)

        # Open the template file and return the data as a string. This is
        #  being done here so that the file can be a vault encrypted file.
        resultant = template.template_from_file(
            self.runner.basedir,
            source_file,
            inject,
            vault_password=self.runner.vault_pass
        )

        if config_overrides:
            type_merger = getattr(self, CONFIG_TYPES.get(config_type))
            resultant = type_merger(
                config_overrides=config_overrides,
                resultant=resultant
            )

        # Retemplate the resultant object as it may have new data within it
        #  as provided by an override variable.
        template.template_from_string(
            basedir=self.runner.basedir,
            data=resultant,
            vars=inject,
            fail_on_undefined=True
        )

        # Access to protected method is unavoidable in Ansible 1.x.
        new_module_args = dict(
            src=self.runner._transfer_str(conn, tmp, 'source', resultant),
            dest=dest,
            original_basename=os.path.basename(source),
            follow=True,
        )

        module_args_tmp = utils.merge_module_args(
            module_args,
            new_module_args
        )

        # Remove data types that are not available to the copy module
        complex_args.pop('config_overrides')
        complex_args.pop('config_type')

        # Return the copy module status. Access to protected method is
        #  unavoidable in Ansible 1.x.
        return self.runner._execute_module(
            conn,
            tmp,
            'copy',
            module_args_tmp,
            inject=inject,
            complex_args=complex_args
        )

