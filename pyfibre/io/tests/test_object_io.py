from unittest import TestCase
import os

import numpy as np
import networkx as nx

from pyfibre.io.object_io import (
    save_base_graph_segment, load_base_graph_segment,
    save_base_graph_segments, load_base_graph_segments)
from pyfibre.io.utilities import (
    serialize_networkx_graph,
    deserialize_networkx_graph
)
from pyfibre.model.objects.base_graph_segment import (
    BaseGraphSegment
)
from pyfibre.tests.probe_classes import generate_probe_graph


class TestObjectIO(TestCase):

    def setUp(self):

        self.graph = generate_probe_graph()
        self.graph_segment = BaseGraphSegment(
            graph=self.graph, shape=(10, 10))

    def test_serialize_networkx_graph(self):

        data = serialize_networkx_graph(self.graph)

        self.assertDictEqual(
            data,
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

    def test_deserialize_networkx_graph(self):

        data = {
            'directed': False,
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

        graph = deserialize_networkx_graph(data)

        self.assertIsInstance(graph, nx.Graph)
        self.assertEqual(4, graph.number_of_nodes())
        self.assertIsInstance(graph.nodes[2]['xy'], np.ndarray)

    def test_save_load_base_graph_segment(self):

        try:
            save_base_graph_segment(self.graph_segment, 'test_json')
            self.assertTrue(os.path.exists('test_json.json'))

            test_segment = load_base_graph_segment('test_json')

            self.assertIsInstance(test_segment, BaseGraphSegment)
            self.assertEqual(
                self.graph.number_of_nodes(),
                test_segment.graph.number_of_nodes()
            )

            self.assertEqual(
                self.graph.number_of_edges(),
                test_segment.graph.number_of_edges()
            )

        finally:
            if os.path.exists('test_json.json'):
                os.remove('test_json.json')

    def test_save_load_base_graph_segments(self):

        try:
            save_base_graph_segments(
                [self.graph_segment, self.graph_segment],
                'test_json')
            self.assertTrue(os.path.exists('test_json.json'))

            test_segments = load_base_graph_segments('test_json')

            self.assertEqual(2, len(test_segments))
            self.assertIsInstance(
                test_segments[0], BaseGraphSegment)
            self.assertEqual(
                self.graph.number_of_nodes(),
                test_segments[0].graph.number_of_nodes()
            )
            self.assertEqual(
                self.graph.number_of_edges(),
                test_segments[0].graph.number_of_edges()
            )

        finally:
            if os.path.exists('test_json.json'):
                os.remove('test_json.json')