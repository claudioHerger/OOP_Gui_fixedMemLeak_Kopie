import numpy as np

def run(lst, nr):
    """returns the value from an arraylike of numbers that is closest to an input number

    Args:
        lst (array like): array like with numbers or strings of numbers
        nr (float): the input nr to which we want the closest nr from arraylike

    Returns:
        float: the closest number from arraylike
    """
    lst = np.asarray(lst)
    idx = (np.abs(lst.astype(float) - nr)).argmin()

    return lst[idx]

def get_index(lst, nr):
    """returns the index of value from an arraylike of numbers that is closest to an input number

    Args:
        lst (array like): array like with numbers or strings of numbers
        nr (float): the input nr to which we want the closest nr from arraylike

    Returns:
        int: the index of closest number
    """
    lst = np.asarray(lst)
    idx = (np.abs(lst.astype(float) - nr)).argmin()

    return idx