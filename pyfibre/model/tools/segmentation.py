"""
PyFibre
Image Segmentation Library

Created by: Frank Longford
Created on: 18/02/2019

Last Modified: 18/02/2019
"""

import logging

import numpy as np
from scipy.ndimage import (
    gaussian_filter, binary_dilation, binary_closing)
from skimage.exposure import equalize_adapthist
from skimage.transform import rescale, resize
from skimage.morphology import remove_small_holes
from skimage.filters import threshold_mean

from pyfibre.model.objects.segments import CellSegment, FibreSegment
from pyfibre.model.tools.utilities import mean_binary

from .bd_cluster import BDFilter
from .convertors import (
    binary_to_regions, regions_to_binary, networks_to_regions)
from .utilities import region_swap

logger = logging.getLogger(__name__)


def rgb_segmentation(image_stack, scale=1.0):
    """Return binary filter for cellular identification"""

    if not isinstance(image_stack, np.ndarray):
        image_stack = np.stack(image_stack, axis=-1)

    n_channels = image_stack.shape[-1]
    shape = image_stack.shape[:-1]

    # Create composite RGB image from SHG, PL and transmission
    magnitudes = np.sqrt(np.sum(image_stack**2, axis=-1))
    indices = np.nonzero(magnitudes)
    image_stack[indices] /= np.repeat(
        magnitudes[indices], n_channels).reshape(
        indices[0].shape + (n_channels,))

    # Up-scale image to improve accuracy of clustering
    logger.debug(f"Rescaling by {scale}")
    image_stack = rescale(
        image_stack, scale, multichannel=True,
        mode='constant', anti_aliasing=None
    )

    # Form mask using Kmeans Background filter
    logger.debug(f"Performing BD Filter")
    bd_filter = BDFilter()
    mask_image = bd_filter.filter_image(image_stack)

    # Reducing image to original size
    logger.debug(f"Rescaling image back to {shape}")
    mask_image = resize(
        mask_image, shape, mode='reflect',
        anti_aliasing=True
    )

    # Create cell and fibre global image masks
    cell_mask = np.array(mask_image, dtype=bool)
    fibre_mask = np.where(mask_image, False, True)

    return fibre_mask, cell_mask


def fibre_cell_region_swap(multi_image, fibre_mask, cell_mask):

    # Obtain segments from masks and swap over any incorrectly
    # assigned segments
    region_swap(
        [cell_mask, fibre_mask],
        [multi_image.pl_image, multi_image.shg_image],
        [250, 150], [0.01, 0.1])

    fibre_mask = remove_small_holes(fibre_mask)
    cell_mask = remove_small_holes(cell_mask)

    return fibre_mask, cell_mask


def create_fibre_filter(fibre_networks, shape,
                        area_threshold=200, iterations=5,
                        sigma=0.5):

    graphs = [
        fibre_network.graph
        for fibre_network in fibre_networks
    ]

    regions = networks_to_regions(
        graphs, shape=shape,
        area_threshold=area_threshold,
        iterations=iterations, sigma=sigma)

    # Create a filter for the image that corresponds
    # to the regions that have not been identified as fibrous
    # segments
    fibre_binary = regions_to_binary(
        regions, shape
    )

    # Dilate the binary in order to enhance network
    # regions
    fibre_filter = np.where(fibre_binary, 2, 0.25)
    fibre_filter = gaussian_filter(fibre_filter, 0.5)

    return fibre_filter


def generate_segments(
        image, binary, segment_klass,
        min_size=100, min_frac=0.1):

    # Create a new set of segments for each fibre region
    regions = binary_to_regions(
        binary,
        intensity_image=image,
        min_size=min_size,
        min_frac=min_frac)
    segments = [
        segment_klass(region=region)
        for region in regions
    ]

    return segments


def shg_segmentation(multi_image, fibre_networks, **kwargs):

    fibre_filter = create_fibre_filter(
        fibre_networks, multi_image.shape)

    fibre_binary = np.where(fibre_filter > 0.1, 0, 1)
    cell_binary = np.where(fibre_binary, 0, 1)

    # Create a new set of segments for each fibre region
    fibre_segments = generate_segments(
        multi_image.shg_image,
        fibre_binary,
        FibreSegment,
    )

    # Create a new set of segments for each cell region
    cell_segments = generate_segments(
        multi_image.shg_image,
        cell_binary,
        CellSegment,
        min_size=200,
        min_frac=0.001
    )

    return fibre_segments, cell_segments


def shg_pl_trans_segmentation(multi_image, fibre_networks, scale=1.0):

    # Create an image stack for the rgb_segmentation from SHG and PL
    # images
    fibre_filter = create_fibre_filter(
        fibre_networks, multi_image.shape)

    original_binary = np.where(
        fibre_filter >= threshold_mean(fibre_filter),
        1, 0)
    stack = (multi_image.shg_image * fibre_filter,
             np.sqrt(multi_image.pl_image * multi_image.trans_image),
             equalize_adapthist(multi_image.trans_image))

    # Segment the PL image using k-means clustering
    fibre_mask, cell_mask = rgb_segmentation(stack, scale=scale)
    fibre_mask, cell_mask = fibre_cell_region_swap(
        multi_image, fibre_mask, cell_mask)

    # Create a binary for the fibrous regions based on information
    # obtained from the rgb segmentation
    fibre_mask = binary_dilation(fibre_mask, iterations=2)
    fibre_mask = binary_closing(fibre_mask)
    new_binary = fibre_mask.astype(int)

    # Generate a filter for the SHG image that combines information
    # from both FIRE and k-means algorithms
    fibre_binary = mean_binary(
        np.array([original_binary, new_binary]),
        multi_image.shg_image,
        min_intensity=0.10)
    cell_binary = np.where(fibre_binary, 0, 1)

    # Create a new set of segments for each fibre region
    fibre_segments = generate_segments(
        multi_image.shg_image,
        fibre_binary,
        FibreSegment,
    )

    # Create a new set of segments for each cell region
    cell_segments = generate_segments(
        multi_image.pl_image,
        cell_binary,
        CellSegment,
        min_size=200,
        min_frac=0.01
    )

    return fibre_segments, cell_segments
