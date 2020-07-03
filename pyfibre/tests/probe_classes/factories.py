from pyfibre.core.base_multi_image_factory import BaseMultiImageFactory

from .analyser import ProbeAnalyser
from .readers import ProbeMultiImageReader
from .parsers import ProbeParser


class ProbeMultiImageFactory(BaseMultiImageFactory):

    def get_label(self):
        return 'Probe'

    def get_reader(self):
        return ProbeMultiImageReader

    def get_analyser(self):
        return ProbeAnalyser

    def get_parser(self):
        return ProbeParser