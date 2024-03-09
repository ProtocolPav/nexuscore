
def recursive_dict_update(original: dict, update: dict):
    for key, val in update.items():
        if isinstance(val, dict):
            original[key] = recursive_dict_update(original[key], val)
        else:
            original[key] = val

    return original
