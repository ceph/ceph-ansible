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

try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser
import datetime
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import base64
import json
import os
import pwd
import re
import six
import time
import yaml
import tempfile as tmpfilelib

from ansible.plugins.action import ActionBase
from ansible.module_utils._text import to_bytes, to_text
from ansible import constants as C
from ansible import errors
from ansible.parsing.yaml.dumper import AnsibleDumper
from distutils.version import LooseVersion
from ansible import __version__ as __ansible_version__

__metaclass__ = type


CONFIG_TYPES = {
    'ini': 'return_config_overrides_ini',
    'json': 'return_config_overrides_json',
    'yaml': 'return_config_overrides_yaml'
}


class IDumper(AnsibleDumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(IDumper, self).increase_indent(flow, False)


class MultiKeyDict(dict):
    """Dictionary class which supports duplicate keys.
    This class allows for an item to be added into a standard python dictionary
    however if a key is created more than once the dictionary will convert the
    singular value to a python tuple. This tuple type forces all values to be a
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
    ... {'a': tuple(['1', '2']), 'c': {'a': 1}, 'b': ['a', 'b', 'c']}
    """

    def __setitem__(self, key, value):
        if key in self:
            if isinstance(self[key], tuple):
                items = self[key]
                if str(value) not in items:
                    items += tuple([str(value)])
                    super(MultiKeyDict, self).__setitem__(key, items)
            else:
                if str(self[key]) != str(value):
                    items = tuple([str(self[key]), str(value)])
                    super(MultiKeyDict, self).__setitem__(key, items)
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

    def __init__(self, *args, **kwargs):
        self._comments = {}
        self.ignore_none_type = bool(kwargs.pop('ignore_none_type', True))
        self.default_section = str(kwargs.pop('default_section', 'DEFAULT'))
        ConfigParser.RawConfigParser.__init__(self, *args, **kwargs)

    def _write(self, fp, section, key, item, entry):
        if section:
            # If we are not ignoring a none type value, then print out
            # the option name only if the value type is None.
            if not self.ignore_none_type and item is None:
                fp.write(key + '\n')
            elif (item is not None) or (self._optcre == self.OPTCRE):
                fp.write(entry)
        else:
            fp.write(entry)

    def _write_check(self, fp, key, value, section=False):
        if isinstance(value, (tuple, set)):
            for item in value:
                item = str(item).replace('\n', '\n\t')
                entry = "%s = %s\n" % (key, item)
                self._write(fp, section, key, item, entry)
        else:
            if isinstance(value, list):
                _value = [str(i.replace('\n', '\n\t')) for i in value]
                entry = '%s = %s\n' % (key, ','.join(_value))
            else:
                entry = '%s = %s\n' % (key, str(value).replace('\n', '\n\t'))
            self._write(fp, section, key, value, entry)

    def write(self, fp):
        def _do_write(section_name, section, section_bool=False):
            _write_comments(section_name)
            fp.write("[%s]\n" % section_name)
            for key, value in sorted(section.items()):
                _write_comments(section_name, optname=key)
                self._write_check(fp, key=key, value=value,
                                  section=section_bool)
            else:
                fp.write("\n")

        def _write_comments(section, optname=None):
            comsect = self._comments.get(section, {})
            if optname in comsect:
                fp.write(''.join(comsect[optname]))

        if self.default_section != 'DEFAULT' and self._sections.get(
                self.default_section, False):
            _do_write(self.default_section,
                      self._sections[self.default_section],
                      section_bool=True)
            self._sections.pop(self.default_section)

        if self._defaults:
            _do_write('DEFAULT', self._defaults)

        for section in sorted(self._sections):
            _do_write(section, self._sections[section], section_bool=True)

    def _read(self, fp, fpname):
        comments = []
        cursect = None
        optname = None
        lineno = 0
        e = None
        while True:
            line = fp.readline()
            if not line:
                break
            lineno += 1
            if line.strip() == '':
                if comments:
                    comments.append('')
                continue

            if line.lstrip()[0] in '#;':
                comments.append(line.lstrip())
                continue

            if line.split(None, 1)[0].lower() == 'rem' and line[0] in "rR":
                continue
            if line[0].isspace() and cursect is not None and optname:
                value = line.strip()
                if value:
                    try:
                        if isinstance(cursect[optname], (tuple, set)):
                            _temp_item = list(cursect[optname])
                            del cursect[optname]
                            cursect[optname] = _temp_item
                        elif isinstance(cursect[optname], six.text_type):
                            _temp_item = [cursect[optname]]
                            del cursect[optname]
                            cursect[optname] = _temp_item
                    except NameError:
                        if isinstance(cursect[optname], (bytes, str)):
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

                    comsect = self._comments.setdefault(sectname, {})
                    if comments:
                        # NOTE(flaper87): Using none as the key for
                        # section level comments
                        comsect[None] = comments
                        comments = []
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
                        if comments:
                            comsect[optname] = comments
                            comments = []
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


class DictCompare(object):
    """
    Calculate the difference between two dictionaries.

    Example Usage:
    >>> base_dict = {'test1': 'val1', 'test2': 'val2', 'test3': 'val3'}
    >>> new_dict = {'test1': 'val2', 'test3': 'val3', 'test4': 'val3'}
    >>> dc = DictCompare(base_dict, new_dict)
    >>> dc.added()
    ... ['test4']
    >>> dc.removed()
    ... ['test2']
    >>> dc.changed()
    ... ['test1']
    >>> dc.get_changes()
    ... {'added':
    ...     {'test4': 'val3'},
    ...  'removed':
    ...     {'test2': 'val2'},
    ...  'changed':
    ...     {'test1': {'current_val': 'vol1', 'new_val': 'val2'}
    ... }
    """
    def __init__(self, base_dict, new_dict):
        self.new_dict, self.base_dict = new_dict, base_dict
        self.base_items, self.new_items = set(
            self.base_dict.keys()), set(self.new_dict.keys())
        self.intersect = self.new_items.intersection(self.base_items)

    def added(self):
        return self.new_items - self.intersect

    def removed(self):
        return self.base_items - self.intersect

    def changed(self):
        return set(
            x for x in self.intersect if self.base_dict[x] != self.new_dict[x])

    def get_changes(self):
        """Returns dict of differences between 2 dicts and bool indicating if
        there are differences

        :param base_dict: ``dict``
        :param new_dict: ``dict``
        :returns: ``dict``, ``bool``
        """
        changed = False
        mods = {'added': {}, 'removed': {}, 'changed': {}}

        for s in self.changed():
            changed = True
            if type(self.base_dict[s]) is not dict:
                mods['changed'] = {
                    s: {'current_val': self.base_dict[s],
                        'new_val': self.new_dict[s]}}
                continue

            diff = DictCompare(self.base_dict[s], self.new_dict[s])
            for a in diff.added():
                if s not in mods['added']:
                    mods['added'][s] = {a: self.new_dict[s][a]}
                else:
                    mods['added'][s][a] = self.new_dict[s][a]

            for r in diff.removed():
                if s not in mods['removed']:
                    mods['removed'][s] = {r: self.base_dict[s][r]}
                else:
                    mods['removed'][s][r] = self.base_dict[s][r]

            for c in diff.changed():
                if s not in mods['changed']:
                    mods['changed'][s] = {
                        c: {'current_val': self.base_dict[s][c],
                            'new_val': self.new_dict[s][c]}}
                else:
                    mods['changed'][s][c] = {
                        'current_val': self.base_dict[s][c],
                        'new_val': self.new_dict[s][c]}

        for s in self.added():
            changed = True
            mods['added'][s] = self.new_dict[s]

        for s in self.removed():
            changed = True
            mods['removed'][s] = self.base_dict[s]

        return mods, changed


class ActionModule(ActionBase):
    TRANSFERS_FILES = True

    def return_config_overrides_ini(self,
                                    config_overrides,
                                    resultant,
                                    list_extend=True,
                                    ignore_none_type=True,
                                    default_section='DEFAULT'):
        """Returns string value from a modified config file and dict of
        merged config

        :param config_overrides: ``dict``
        :param resultant: ``str`` || ``unicode``
        :returns: ``str``, ``dict``
        """
        # If there is an exception loading the RawConfigParser The config obj
        #  is loaded again without the extra option. This is being done to
        #  support older python.
        try:
            config = ConfigTemplateParser(
                allow_no_value=True,
                dict_type=MultiKeyDict,
                ignore_none_type=ignore_none_type,
                default_section=default_section
            )
            config.optionxform = str
        except Exception:
            config = ConfigTemplateParser(dict_type=MultiKeyDict)

        config_object = StringIO(resultant)
        config.readfp(config_object)

        for section, items in config_overrides.items():
            # If the items value is not a dictionary it is assumed that the
            #  value is a default item for this config type.
            if not isinstance(items, dict):
                if isinstance(items, list):
                    items = ','.join(to_text(i) for i in items)
                self._option_write(
                    config,
                    'DEFAULT',
                    section,
                    items
                )
            else:
                # Attempt to add a section to the config file passing if
                #  an error is raised that is related to the section
                #  already existing.
                try:
                    config.add_section(section)
                except (ConfigParser.DuplicateSectionError, ValueError):
                    pass
                for key, value in items.items():
                    try:
                        self._option_write(config, section, key, value)
                    except ConfigParser.NoSectionError as exp:
                        error_msg = str(exp)
                        error_msg += (
                            ' Try being more explicit with your override'
                            'data. Sections are case sensitive.'
                        )
                        raise errors.AnsibleModuleError(error_msg)
        else:
            config_object.close()

        config_dict_new = {}
        config_defaults = config.defaults()
        for s in config.sections():
            config_dict_new[s] = {}
            for k, v in config.items(s):
                if k not in config_defaults or config_defaults[k] != v:
                    config_dict_new[s][k] = v
                else:
                    if default_section in config_dict_new:
                        config_dict_new[default_section][k] = v
                    else:
                        config_dict_new[default_section] = {k: v}

        resultant_stringio = StringIO()
        try:
            config.write(resultant_stringio)
            return resultant_stringio.getvalue(), config_dict_new
        finally:
            resultant_stringio.close()

    @staticmethod
    def _option_write(config, section, key, value):
        config.remove_option(str(section), str(key))
        try:
            if not any(list(value.values())):
                value = tuple(value.keys())
        except AttributeError:
            pass
        if isinstance(value, (tuple, set)):
            config.set(str(section), str(key), value)
        elif isinstance(value, set):
            config.set(str(section), str(key), value)
        elif isinstance(value, list):
            config.set(str(section), str(key), ','.join(str(i) for i in value))
        else:
            config.set(str(section), str(key), str(value))

    def return_config_overrides_json(self,
                                     config_overrides,
                                     resultant,
                                     list_extend=True,
                                     ignore_none_type=True,
                                     default_section='DEFAULT'):
        """Returns config json and dict of merged config

        Its important to note that file ordering will not be preserved as the
        information within the json file will be sorted by keys.

        :param config_overrides: ``dict``
        :param resultant: ``str`` || ``unicode``
        :returns: ``str``, ``dict``
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
        ), merged_resultant

    def return_config_overrides_yaml(self,
                                     config_overrides,
                                     resultant,
                                     list_extend=True,
                                     ignore_none_type=True,
                                     default_section='DEFAULT'):
        """Return config yaml and dict of merged config

        :param config_overrides: ``dict``
        :param resultant: ``str`` || ``unicode``
        :returns: ``str``, ``dict``
        """
        original_resultant = yaml.safe_load(resultant)
        merged_resultant = self._merge_dict(
            base_items=original_resultant,
            new_items=config_overrides,
            list_extend=list_extend
        )
        return yaml.dump(
            merged_resultant,
            Dumper=IDumper,
            default_flow_style=False,
            width=1000,
        ), merged_resultant

    def _merge_dict(self, base_items, new_items, list_extend=True):
        """Recursively merge new_items into base_items.

        :param base_items: ``dict``
        :param new_items: ``dict``
        :returns: ``dict``
        """
        for key, value in new_items.items():
            if isinstance(value, dict):
                base_items[key] = self._merge_dict(
                    base_items=base_items.get(key, {}),
                    new_items=value,
                    list_extend=list_extend
                )
            elif (not isinstance(value, int) and
                  (',' in value or '\n' in value)):
                base_items[key] = re.split(',|\n', value)
                base_items[key] = [i.strip() for i in base_items[key] if i]
            elif isinstance(value, list):
                if isinstance(base_items.get(key), list) and list_extend:
                    base_items[key].extend(value)
                else:
                    base_items[key] = value
            elif isinstance(value, (tuple, set)):
                if isinstance(base_items.get(key), tuple) and list_extend:
                    base_items[key] += tuple(value)
                elif isinstance(base_items.get(key), list) and list_extend:
                    base_items[key].extend(list(value))
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

        if self._task._role:
            file_path = self._task._role._role_path
            searchpath.insert(1, C.DEFAULT_ROLES_PATH)
            searchpath.insert(1, self._task._role._role_path)
        else:
            file_path = self._loader.get_basedir()

        user_source = self._task.args.get('src')
        # (alextricity25) It's possible that the user could pass in a datatype
        # and not always a string. In this case we don't want the datatype
        # python representation to be printed out to the file, but rather we
        # want the serialized version.
        _user_content = self._task.args.get('content')

        # If the data type of the content input is a dictionary, it's
        # converted dumped as json if config_type is 'json'.
        if isinstance(_user_content, dict):
            if self._task.args.get('config_type') == 'json':
                _user_content = json.dumps(_user_content)

        user_content = str(_user_content)
        if not user_source:
            if not user_content:
                return False, dict(
                    failed=True,
                    msg="No user [ src ] or [ content ] was provided"
                )
            else:
                tmp_content = None
                fd, tmp_content = tmpfilelib.mkstemp()
                try:
                    with open(tmp_content, 'wb') as f:
                        f.write(user_content.encode())
                except Exception as err:
                    os.remove(tmp_content)
                    raise Exception(err)
                self._task.args['src'] = source = tmp_content
        else:
            source = self._loader.path_dwim_relative(
                file_path,
                'templates',
                user_source
            )
        searchpath.insert(1, os.path.dirname(source))

        _dest = self._task.args.get('dest')
        list_extend = self._task.args.get('list_extend')
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

        # Get ignore_none_type
        # In some situations(i.e. my.cnf files), INI files can have valueless
        # options that don't have a '=' or ':' suffix. In these cases,
        # ConfigParser gives these options a "None" value. If ignore_none_type
        # is set to true, these key/value options will be ignored, if it's set
        # to false, then ConfigTemplateParser will write out only the option
        # name with out the '=' or ':' suffix. The default is true.
        ignore_none_type = self._task.args.get('ignore_none_type', True)

        default_section = self._task.args.get('default_section', 'DEFAULT')

        return True, dict(
            source=source,
            dest=user_dest,
            config_overrides=self._task.args.get('config_overrides', dict()),
            config_type=config_type,
            searchpath=searchpath,
            list_extend=list_extend,
            ignore_none_type=ignore_none_type,
            default_section=default_section
        )

    def run(self, tmp=None, task_vars=None):
        """Run the method"""

        try:
            remote_user = task_vars.get('ansible_user')
            if not remote_user:
                remote_user = task_vars.get('ansible_ssh_user')
            if not remote_user:
                remote_user = self._play_context.remote_user

            if not tmp:
                tmp = self._make_tmp_path(remote_user)
        except TypeError:
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
            template_data = to_text(f.read())

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

        config_dict_base = {}
        type_merger = getattr(self, CONFIG_TYPES.get(_vars['config_type']))
        resultant, config_dict_base = type_merger(
            config_overrides=_vars['config_overrides'],
            resultant=resultant,
            list_extend=_vars.get('list_extend', True),
            ignore_none_type=_vars.get('ignore_none_type', True),
            default_section=_vars.get('default_section', 'DEFAULT')
        )

        changed = False
        if self._play_context.diff:
            slurpee = self._execute_module(
                module_name='slurp',
                module_args=dict(src=_vars['dest']),
                task_vars=task_vars
            )

            config_dict_new = {}
            if 'content' in slurpee:
                dest_data = base64.b64decode(
                    slurpee['content']).decode('utf-8')
                resultant_dest = self._templar.template(
                    dest_data,
                    preserve_trailing_newlines=True,
                    escape_backslashes=False,
                    convert_data=False
                )
                type_merger = getattr(self,
                                      CONFIG_TYPES.get(_vars['config_type']))
                resultant_new, config_dict_new = type_merger(
                    config_overrides={},
                    resultant=resultant_dest,
                    list_extend=_vars.get('list_extend', True),
                    ignore_none_type=_vars.get('ignore_none_type', True),
                    default_section=_vars.get('default_section', 'DEFAULT')
                )

            # Compare source+overrides with dest to look for changes and
            # build diff
            cmp_dicts = DictCompare(config_dict_new, config_dict_base)
            mods, changed = cmp_dicts.get_changes()

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
        if LooseVersion(__ansible_version__) < LooseVersion("2.6"):
            new_module_args.update(
                dict(
                    src=transferred_data,
                    dest=_vars['dest'],
                    original_basename=os.path.basename(source),
                    follow=True,
                ),
            )
        else:
            new_module_args.update(
                dict(
                    src=transferred_data,
                    dest=_vars['dest'],
                    _original_basename=os.path.basename(source),
                    follow=True,
                ),
            )

        # Remove data types that are not available to the copy module
        new_module_args.pop('config_overrides', None)
        new_module_args.pop('config_type', None)
        new_module_args.pop('list_extend', None)
        new_module_args.pop('ignore_none_type', None)
        new_module_args.pop('default_section', None)
        # Content from config_template is converted to src
        new_module_args.pop('content', None)

        # Run the copy module
        rc = self._execute_module(
            module_name='copy',
            module_args=new_module_args,
            task_vars=task_vars
        )
        copy_changed = rc.get('changed')
        if not copy_changed:
            rc['changed'] = changed

        if self._play_context.diff:
            rc['diff'] = []
            rc['diff'].append(
                {'prepared': json.dumps(mods, indent=4, sort_keys=True)})
        if self._task.args.get('content'):
            os.remove(_vars['source'])
        return rc
