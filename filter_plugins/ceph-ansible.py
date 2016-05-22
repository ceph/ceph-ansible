from ansible import errors

def only_one_true(a, *args):
    params = list(args)
    params.append(a)
    it = iter(params)
    return any(it) and not any(it)

class FilterModule(object):
    def filters(self):
        return {
            'only_one_true': only_one_true
        }
