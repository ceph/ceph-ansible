from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class FilterModule(object):
    ''' Loop over nested dictionaries '''

    def dict2dict(self, nested_dict):
        items = []
        for key, value in nested_dict.items():
            for k, v in value.items():
                items.append(
                    (
                        {'key': key, 'value': value},
                        {'key': k, 'value': v},
                    ),
                )
        return items

    def filters(self):
        return {
            'dict2dict': self.dict2dict
        }
