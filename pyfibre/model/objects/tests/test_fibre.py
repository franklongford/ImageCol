from unittest import TestCase

import numpy as np

from pyfibre.model.objects.fibre import (
    Fibre
)
from pyfibre.tests.probe_classes import ProbeFibre


class TestFibre(TestCase):

    def setUp(self):

        self.fibre = ProbeFibre()

    def test__getstate__(self):

        status = self.fibre.__getstate__()
        self.assertIn('growing', status)

        new_fibre = Fibre(**status)
        status = new_fibre.__getstate__()

        self.assertDictEqual(
            status['graph'],
            {'directed': False,
             'graph': {},
             'links': [{'r': 1.4142135623730951, 'source': 2, 'target': 3},
                       {'r': 1.4142135623730951, 'source': 3, 'target': 4},
                       {'r': 1, 'source': 4, 'target': 5}],
             'multigraph': False,
             'nodes': [{'xy': [0, 0], 'id': 2},
                       {'xy': [1, 1], 'id': 3},
                       {'xy': [2, 2], 'id': 4},
                       {'xy': [2, 3], 'id': 5}]
             }
        )

    def test_node_list_init(self):

        fibre = Fibre(nodes=[2, 3, 4, 5],
                      edges=[(3, 2), (3, 4), (4, 5)],
                      shape=(10, 10))

        self.assertEqual(4, fibre.number_of_nodes)
        self.assertEqual([2, 3, 4, 5], fibre.node_list)
        self.assertTrue(fibre.growing)

        self.assertTrue(np.allclose(np.array([0, 0]), fibre._d_coord))
        self.assertTrue(np.allclose(np.array([0, 0]), fibre.direction))
        self.assertEqual(90, fibre.angle)
        self.assertEqual(0, fibre.euclid_l)
        self.assertEqual(0, fibre.fibre_l)
        self.assertTrue(np.isnan(fibre.waviness))

    def test_network_init(self):

        self.assertTrue(self.fibre.growing)
        self.assertTrue(np.allclose(np.array([2, 3]), self.fibre._d_coord))
        self.assertTrue(np.allclose(
            np.array([-0.5547002, -0.83205029]), self.fibre.direction))
        self.assertAlmostEqual(146.30993247, self.fibre.angle)
        self.assertAlmostEqual(3.60555127, self.fibre.euclid_l)
        self.assertAlmostEqual(3.82842712, self.fibre.fibre_l)
        self.assertAlmostEqual(0.94178396, self.fibre.waviness)

    def test_generate_database(self):

        database = self.fibre.generate_database()
        self.assertEqual(11, len(database))

        image = np.ones((5, 5))
        image[2:, 2:] = 2

        database = self.fibre.generate_database(image)
        self.assertEqual(11, len(database))

        self.fibre.image = image

        database = self.fibre.generate_database()
        self.assertEqual(11, len(database))