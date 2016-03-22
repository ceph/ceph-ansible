# (c) 2015, Kevin Carter <kevin.carter@rackspace.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import ConfigParser
import datetime
import io
import json
import os
import pwd
import time
import yaml


# Ansible v2
try:
    from ansible.plugins.action import ActionBase
    from ansible.utils.unicode import to_bytes, to_unicode
    from ansible import constants as C
    from ansible import errors

    CONFIG_TYPES = {
        'ini': 'return_config_overrides_ini',
        'json': 'return_config_overrides_json',
        'yaml': 'return_config_overrides_yaml'
    }


    def _convert_2_string(item):
        """Return byte strings for all items.

        This will convert everything within a dict, list or unicode string such
        that the values will be encode('utf-8') where applicable.
        """

        if isinstance(item, dict):
            # Old style dict comprehension for legacy python support
            return dict(
                (_convert_2_string(key), _convert_2_string(value))
                for key, value in item.iteritems()
            )
        elif isinstance(item, list):
            return [_convert_2_string(i) for i in item]
        elif isinstance(item, unicode):
            return item.encode('utf-8')
        else:
            return item


    class ActionModule(ActionBase):
        TRANSFERS_FILES = True

        @staticmethod
        def return_config_overrides_ini(config_overrides, resultant):
            """Returns string value from a modified config file.

            :param config_overrides: ``dict``
            :param resultant: ``str`` || ``unicode``
            :returns: ``str``
            """
            # If there is an exception loading the RawConfigParser The config obj
            #  is loaded again without the extra option. This is being done to
            #  support older python.
            try:
                config = ConfigParser.RawConfigParser(allow_no_value=True)
            except Exception:
                config = ConfigParser.RawConfigParser()

            config_object = io.BytesIO(str(resultant))
            config.readfp(config_object)
            for section, items in config_overrides.items():
                # If the items value is not a dictionary it is assumed that the
                #  value is a default item for this config type.
                if not isinstance(items, dict):
                    config.set(
                        'DEFAULT',
                        section.encode('utf-8'),
                        _convert_2_string(items)
                    )
                else:
                    # Attempt to add a section to the config file passing if
                    #  an error is raised that is related to the section
                    #  already existing.
                    try:
                        config.add_section(section.encode('utf-8'))
                    except (ConfigParser.DuplicateSectionError, ValueError):
                        pass
                    for key, value in items.items():
                        value = _convert_2_string(value)
                        try:
                            config.set(
                                section.encode('utf-8'),
                                key.encode('utf-8'),
                                value
                            )
                        except ConfigParser.NoSectionError as exp:
                            error_msg = str(exp)
                            error_msg += (
                                ' Try being more explicit with your override'
                                ' data. Sections are case sensitive.'
                            )
                            raise errors.AnsibleModuleError(error_msg)

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

        def _load_options_and_status(self, task_vars):
            """Return options and status from module load."""

            config_type = self._task.args.get('config_type')
            if config_type not in ['ini', 'yaml', 'json']:
                return False, dict(
                    failed=True,
                    msg="No valid [ config_type ] was provided. Valid options are"
                        " ini, yaml, or json."
                )

            # Access to protected method is unavoidable in Ansible
            searchpath = [self._loader._basedir]

            faf = self._task.first_available_file
            if faf:
                task_file = task_vars.get('_original_file', None, 'templates')
                source = self._get_first_available_file(faf, task_file)
                if not source:
                    return False, dict(
                        failed=True,
                        msg="could not find src in first_available_file list"
                    )
            else:
                # Access to protected method is unavoidable in Ansible
                if self._task._role:
                    file_path = self._task._role._role_path
                    searchpath.insert(1, C.DEFAULT_ROLES_PATH)
                    searchpath.insert(1, self._task._role._role_path)
                else:
                    file_path = self._loader.get_basedir()

                user_source = self._task.args.get('src')
                if not user_source:
                    return False, dict(
                        failed=True,
                        msg="No user provided [ src ] was provided"
                    )
                source = self._loader.path_dwim_relative(
                    file_path,
                    'templates',
                    user_source
                )
                searchpath.insert(1, os.path.dirname(source))

            _dest = self._task.args.get('dest')
            if not _dest:
                return False, dict(
                    failed=True,
                    msg="No [ dest ] was provided"
                )
            else:
                # Expand any user home dir specification
                user_dest = self._remote_expand_user(_dest)
                if user_dest.endswith(os.sep):
                    user_dest = os.path.join(user_dest, os.path.basename(source))

            return True, dict(
                source=source,
                dest=user_dest,
                config_overrides=self._task.args.get('config_overrides', dict()),
                config_type=config_type,
                searchpath=searchpath
            )

        def run(self, tmp=None, task_vars=None):
            """Run the method"""

            if not tmp:
                tmp = self._make_tmp_path()

            _status, _vars = self._load_options_and_status(task_vars=task_vars)
            if not _status:
                return _vars

            temp_vars = task_vars.copy()
            template_host = temp_vars['template_host'] = os.uname()[1]
            source = temp_vars['template_path'] = _vars['source']
            temp_vars['template_mtime'] = datetime.datetime.fromtimestamp(
                os.path.getmtime(source)
            )

            try:
                template_uid = temp_vars['template_uid'] = pwd.getpwuid(
                    os.stat(source).st_uid
                ).pw_name
            except Exception:
                template_uid = temp_vars['template_uid'] = os.stat(source).st_uid

            managed_default = C.DEFAULT_MANAGED_STR
            managed_str = managed_default.format(
                host=template_host,
                uid=template_uid,
                file=to_bytes(source)
            )

            temp_vars['ansible_managed'] = time.strftime(
                managed_str,
                time.localtime(os.path.getmtime(source))
            )
            temp_vars['template_fullpath'] = os.path.abspath(source)
            temp_vars['template_run_date'] = datetime.datetime.now()

            with open(source, 'r') as f:
                template_data = to_unicode(f.read())

            self._templar.environment.loader.searchpath = _vars['searchpath']
            self._templar.set_available_variables(temp_vars)
            resultant = self._templar.template(
                template_data,
                preserve_trailing_newlines=True,
                escape_backslashes=False,
                convert_data=False
            )

            # Access to protected method is unavoidable in Ansible
            self._templar.set_available_variables(
                self._templar._available_variables
            )

            if _vars['config_overrides']:
                type_merger = getattr(self, CONFIG_TYPES.get(_vars['config_type']))
                resultant = type_merger(
                    config_overrides=_vars['config_overrides'],
                    resultant=resultant
                )

            # Re-template the resultant object as it may have new data within it
            #  as provided by an override variable.
            resultant = self._templar.template(
                resultant,
                preserve_trailing_newlines=True,
                escape_backslashes=False,
                convert_data=False
            )

            # run the copy module
            new_module_args = self._task.args.copy()
            # Access to protected method is unavoidable in Ansible
            transferred_data = self._transfer_data(
                self._connection._shell.join_path(tmp, 'source'),
                resultant
            )
            new_module_args.update(
                dict(
                    src=transferred_data,
                    dest=_vars['dest'],
                    original_basename=os.path.basename(source),
                    follow=True,
                ),
            )

            # Remove data types that are not available to the copy module
            new_module_args.pop('config_overrides', None)
            new_module_args.pop('config_type', None)

            # Run the copy module
            return self._execute_module(
                module_name='copy',
                module_args=new_module_args,
                task_vars=task_vars
            )

# Ansible v1
except ImportError:
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

