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

try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser
import io
import json
import os
import re
import yaml

from ansible import errors
from ansible.runner.return_data import ReturnData
from ansible import utils
from ansible.utils import template
from collections import OrderedDict

CONFIG_TYPES = {
    'ini': 'return_config_overrides_ini',
    'json': 'return_config_overrides_json',
    'yaml': 'return_config_overrides_yaml'
}


class MultiKeyDict(dict):
    """Dictionary class which supports duplicate keys.

    This class allows for an item to be added into a standard python dictionary
    however if a key is created more than once the dictionary will convert the
    singular value to a python set. This set type forces all values to be a
    string.

    Example Usage:
    >>> z = MultiKeyDict()
    >>> z['a'] = 1
    >>> z['b'] = ['a', 'b', 'c']
    >>> z['c'] = {'a': 1}
    >>> print(z)
    ... {'a': 1, 'b': ['a', 'b', 'c'], 'c': {'a': 1}}
    >>> z['a'] = 2
    >>> print(z)
    ... {'a': set(['1', '2']), 'c': {'a': 1}, 'b': ['a', 'b', 'c']}
    """
    def __setitem__(self, key, value):
        if key in self:
            if isinstance(self[key], set):
                items = self[key]
                items.add(str(value))
                super(MultiKeyDict, self).__setitem__(key, items)
            else:
                items = [str(value), str(self[key])]
                super(MultiKeyDict, self).__setitem__(key, set(items))
        else:
            return dict.__setitem__(self, key, value)


class ConfigTemplateParser(ConfigParser.RawConfigParser):
    """ConfigParser which supports multi key value.

    The parser will use keys with multiple variables in a set as a multiple
    key value within a configuration file.

    Default Configuration file:
    [DEFAULT]
    things =
        url1
        url2
        url3

    other = 1,2,3

    [section1]
    key = var1
    key = var2
    key = var3

    Example Usage:
    >>> cp = ConfigTemplateParser(dict_type=MultiKeyDict)
    >>> cp.read('/tmp/test.ini')
    ... ['/tmp/test.ini']
    >>> cp.get('DEFAULT', 'things')
    ... \nurl1\nurl2\nurl3
    >>> cp.get('DEFAULT', 'other')
    ... '1,2,3'
    >>> cp.set('DEFAULT', 'key1', 'var1')
    >>> cp.get('DEFAULT', 'key1')
    ... 'var1'
    >>> cp.get('section1', 'key')
    ... {'var1', 'var2', 'var3'}
    >>> cp.set('section1', 'key', 'var4')
    >>> cp.get('section1', 'key')
    ... {'var1', 'var2', 'var3', 'var4'}
    >>> with open('/tmp/test2.ini', 'w') as f:
    ...     cp.write(f)

    Output file:
    [DEFAULT]
    things =
            url1
            url2
            url3
    key1 = var1
    other = 1,2,3

    [section1]
    key = var4
    key = var1
    key = var3
    key = var2
    """
    def _write(self, fp, section, item, entry):
        if section:
            if (item is not None) or (self._optcre == self.OPTCRE):
                fp.write(entry)
        else:
            fp.write(entry)

    def _write_check(self, fp, key, value, section=False):
        if isinstance(value, set):
            for item in value:
                item = str(item).replace('\n', '\n\t')
                entry = "%s = %s\n" % (key, item)
                self._write(fp, section, item, entry)
        else:
            if isinstance(value, list):
                _value = [str(i.replace('\n', '\n\t')) for i in value]
                entry = '%s = %s\n' % (key, ','.join(_value))
            else:
                entry = '%s = %s\n' % (key, str(value).replace('\n', '\n\t'))
            self._write(fp, section, value, entry)

    def write(self, fp):
        if self._defaults:
            fp.write("[%s]\n" % 'DEFAULT')
            for key, value in OrderedDict(sorted(self._defaults.items())).items():
                self._write_check(fp, key=key, value=value)
            else:
                fp.write("\n")

        for section in self._sections:
            fp.write("[%s]\n" % section)
            for key, value in OrderedDict(sorted(self._sections[section].items())).items():
                self._write_check(fp, key=key, value=value, section=True)
            else:
                fp.write("\n")

    def _read(self, fp, fpname):
        cursect = None
        optname = None
        lineno = 0
        e = None
        while True:
            line = fp.readline()
            if not line:
                break
            lineno += 1
            if line.strip() == '' or line[0] in '#;':
                continue
            if line.split(None, 1)[0].lower() == 'rem' and line[0] in "rR":
                continue
            if line[0].isspace() and cursect is not None and optname:
                value = line.strip()
                if value:
                    if isinstance(cursect[optname], set):
                        _temp_item = list(cursect[optname])
                        del cursect[optname]
                        cursect[optname] = _temp_item
                    elif isinstance(cursect[optname], (str, unicode)):
                        _temp_item = [cursect[optname]]
                        del cursect[optname]
                        cursect[optname] = _temp_item
                    cursect[optname].append(value)
            else:
                mo = self.SECTCRE.match(line)
                if mo:
                    sectname = mo.group('header')
                    if sectname in self._sections:
                        cursect = self._sections[sectname]
                    elif sectname == 'DEFAULT':
                        cursect = self._defaults
                    else:
                        cursect = self._dict()
                        self._sections[sectname] = cursect
                    optname = None
                elif cursect is None:
                    raise ConfigParser.MissingSectionHeaderError(
                        fpname,
                        lineno,
                        line
                    )
                else:
                    mo = self._optcre.match(line)
                    if mo:
                        optname, vi, optval = mo.group('option', 'vi', 'value')
                        optname = self.optionxform(optname.rstrip())
                        if optval is not None:
                            if vi in ('=', ':') and ';' in optval:
                                pos = optval.find(';')
                                if pos != -1 and optval[pos - 1].isspace():
                                    optval = optval[:pos]
                            optval = optval.strip()
                            if optval == '""':
                                optval = ''
                        cursect[optname] = optval
                    else:
                        if not e:
                            e = ConfigParser.ParsingError(fpname)
                        e.append(lineno, repr(line))
        if e:
            raise e
        all_sections = [self._defaults]
        all_sections.extend(self._sections.values())
        for options in all_sections:
            for name, val in options.items():
                if isinstance(val, list):
                    _temp_item = '\n'.join(val)
                    del options[name]
                    options[name] = _temp_item


class ActionModule(object):
    TRANSFERS_FILES = True

    def __init__(self, runner):
        self.runner = runner

    @staticmethod
    def grab_options(complex_args, module_args):
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
    def _option_write(config, section, key, value):
        config.remove_option(str(section), str(key))
        try:
            if not any(i for i in value.values()):
                value = set(value)
        except AttributeError:
            pass
        if isinstance(value, set):
            config.set(str(section), str(key), value)
        elif isinstance(value, list):
            config.set(str(section), str(key), ','.join(str(i) for i in value))
        else:
            config.set(str(section), str(key), str(value))

    def return_config_overrides_ini(self, config_overrides, resultant, list_extend=True):
        """Returns string value from a modified config file.

        :param config_overrides: ``dict``
        :param resultant: ``str`` || ``unicode``
        :returns: ``str``
        """
        config = ConfigTemplateParser(
            dict_type=MultiKeyDict,
            allow_no_value=True
        )
        config.optionxform = str
        config_object = io.BytesIO(resultant.encode('utf-8'))
        config.readfp(config_object)
        for section, items in config_overrides.items():
            # If the items value is not a dictionary it is assumed that the
            #  value is a default item for this config type.
            if not isinstance(items, dict):
                if isinstance(items, list):
                    items = ','.join(items)
                self._option_write(config, 'DEFAULT', section, items)
            else:
                # Attempt to add a section to the config file passing if
                #  an error is raised that is related to the section
                #  already existing.
                try:
                    config.add_section(str(section))
                except (ConfigParser.DuplicateSectionError, ValueError):
                    pass
                for key, value in items.items():
                    self._option_write(config, section, key, value)
        else:
            config_object.close()

        resultant_bytesio = io.BytesIO()
        try:
            config.write(resultant_bytesio)
            return resultant_bytesio.getvalue()
        finally:
            resultant_bytesio.close()

    def return_config_overrides_json(self, config_overrides, resultant, list_extend=True):
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
            new_items=config_overrides,
            list_extend=list_extend
        )
        return json.dumps(
            merged_resultant,
            indent=4,
            sort_keys=True
        )

    def return_config_overrides_yaml(self, config_overrides, resultant, list_extend=True):
        """Return config yaml.

        :param config_overrides: ``dict``
        :param resultant: ``str`` || ``unicode``
        :returns: ``str``
        """
        original_resultant = yaml.safe_load(resultant)
        merged_resultant = self._merge_dict(
            base_items=original_resultant,
            new_items=config_overrides,
            list_extend=list_extend
        )
        return yaml.safe_dump(
            merged_resultant,
            default_flow_style=False,
            width=1000,
        )

    def _merge_dict(self, base_items, new_items, list_extend=True):
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
            elif ',' in value or '\n' in value:
                base_items[key] = re.split(', |,|\n', value)
                base_items[key] = [i.strip() for i in base_items[key] if i]
            elif isinstance(value, list):
                if isinstance(base_items.get(key), list) and list_extend:
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
                resultant=resultant,
                list_extend=options.get('list_extend', True)
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
        complex_args.pop('list_extend', None)

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
