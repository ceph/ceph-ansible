def _validate_both_dicts(a, b):
    if not (isinstance(a, dict) and isinstance(b, dict)):

      raise Exception("failed to combine variables, expected dicts but got a '%s' (%s) and a '%s' (%s)" % (type(a).__name__, str(a), type(b).__name__, str(b)))

def merge_hash(a, b):
    ''' recursively merges hash b into a
    keys from b take precedence over keys from a '''

    result = dict()


    # we check here as well as in combine_vars() since this
    # function can work recursively with nested dicts
    _validate_both_dicts(a, b)

    for dicts in a, b:
      # next, iterate over b keys and values
        for k, v in dicts.iteritems():
        # if there's already such key in a
        # and that key contains dict
            if k in result and isinstance(result[k], dict):
                # merge those dicts recursively
                result[k] = merge_hash(a[k], v)
            else:
        # otherwise, just copy a value from b to a
                result[k] = v
    return result

class FilterModule(object):
    ''' utility filters for merge two hashes '''

    def filters(self):
        return {
        'merge_hash' : merge_hash
        }
