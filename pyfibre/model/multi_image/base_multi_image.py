import numpy as np

from traits.api import (
    HasTraits, ArrayOrNone, Tuple, List,
    Property, Dict, Str
)


class BaseMultiImage(HasTraits):

    shape = Property(Tuple, depends_on='image_stack')

    size = Property(Tuple, depends_on='image_stack')

    ndim = Property(Tuple, depends_on='image_stack')

    image_stack = List(ArrayOrNone)

    image_dict = Dict(Str, ArrayOrNone)

    def __len__(self):
        return len(self.image_stack)

    def _get_ndim(self):
        if len(self):
            return self.image_stack[0].ndim

    def _get_shape(self):
        if len(self):
            return self.image_stack[0].shape

    def _get_size(self):
        if len(self):
            return self.image_stack[0].size

    def append(self, image):
        """Appends an image to the image_stack. If image_stack
        already contains existing images, make sure that the
        shape on the incoming image matches"""
        if len(self):
            if image.shape != self.shape:
                raise ValueError(
                    f'Image shape {image.shape} is not the same as '
                    f'BaseMultiImage shape {self.shape}')

        self.image_stack.append(image)

    def remove(self, image):
        """Removes an image with index from the image_stack"""
        self.image_stack.remove(image)

    def asarray(self):
        return np.stack(self.image_stack)

    @classmethod
    def verify_stack(cls, image_stack):
        """Perform verification that image_stack is allowed by
        subclass of BaseMultiImage"""
        raise NotImplementedError(
            f'{cls.__class__}.verify_stack method'
            f' not implemented')

    def preprocess_images(self):
        """Implement operations that are used to pre-process
        the image_stack before analysis"""
        raise NotImplementedError(
            f'{self.__class__}.preprocess_images method'
            f' not implemented')

    def segmentation_algorithm(self, *args, **kwargs):
        """Implement segmentation algorithm to be used for this
        multi-image type"""
        raise NotImplementedError(
            f'{self.__class__}.segmentation_algorithm method'
            f' not implemented')

    def create_figures(self, *args, **kwargs):
        """Create figures from multi-image components that can be
        generated upon end of analysis"""
        raise NotImplementedError(
            f'{self.__class__}.create_figures method'
            f' not implemented')