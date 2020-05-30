from pyfibre.core.base_pyfibre_plugin import BasePyFibrePlugin

from .shg_pl_trans_factory import SHGPLTransFactory


class SHGPLTransPlugin(BasePyFibrePlugin):
    """Plugin that contributes a factory that can analyse
    an image format made of SHG and PL signals."""

    def get_multi_image_factories(self):
        return [SHGPLTransFactory]
