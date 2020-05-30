from skimage.io import imread

from pyfibre.model.tools.segmentation import (
    rgb_segmentation
)
from pyfibre.tests.probe_classes.utilities import (
    generate_image, generate_probe_graph)
from pyfibre.tests.probe_classes.objects import ProbeFibreNetwork
from pyfibre.tests.probe_classes.filters import ProbeBDFilter
from pyfibre.shg_pl_trans.tests.probe_classes import ProbeSHGPLTransImage
from pyfibre.tests.fixtures import test_shg_pl_trans_image_path
from pyfibre.tests.pyfibre_test_case import PyFibreTestCase


class TestSegmentation(PyFibreTestCase):

    def setUp(self):
        (self.image, self.labels,
         self.binary, self.stack) = generate_image()
        self.network = generate_probe_graph()

        self.image_stack = imread(test_shg_pl_trans_image_path).mean(axis=-1)
        for image in self.image_stack:
            image /= image.max()

        self.multi_image = ProbeSHGPLTransImage()
        self.fibre_networks = [ProbeFibreNetwork()]
        self.bd_filter = ProbeBDFilter()

    def test_rgb_segmentation(self):

        stack = (self.image_stack[0],
                 self.image_stack[1],
                 self.image_stack[2])

        fibre_mask, cell_mask = rgb_segmentation(
            stack, self.bd_filter)

        self.assertEqual((200, 200), fibre_mask.shape)
        self.assertEqual((200, 200), cell_mask.shape)
