import numpy as np

from pyfibre.model.tools.convertors import (
    segments_to_stack, stack_to_segments)


def save_segments(segments, file_name, shape, file_type=None):
    """Saves scikit image regions as pickled file"""

    stack = segments_to_stack(segments, shape)

    if file_type is not None:
        file_name = '_'.join([file_name, file_type])

    try:
        np.save(f"{file_name}.npy", stack)
    except IOError as e:
        raise IOError(
            f"Cannot save to file {file_name}"
        ) from e


def load_segments(file_name, file_type=None, image=None):
    """Loads pickled scikit image regions"""

    if file_type is not None:
        file_name = '_'.join([file_name, file_type])

    try:
        stack = np.load(f"{file_name}.npy")
    except IOError as e:
        raise IOError(
            f"Cannot read file {file_name}.npy"
        ) from e

    segments = stack_to_segments(stack, intensity_image=image)

    return segments
