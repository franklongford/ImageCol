from abc import abstractmethod

from traits.api import ABCHasStrictTraits, Type, Str, provides

from .i_multi_image_analyser import IMultiImageAnalyser
from .i_file_parser import IFileParser
from .i_multi_image_reader import IMultiImageReader
from .i_multi_image_factory import IMultiImageFactory


@provides(IMultiImageFactory)
class BaseMultiImageFactory(ABCHasStrictTraits):
    """Main component contributed by plugins to allow expansion
    of the software. Represents a multi-channel image that can be
    loaded from a single or multiple files, with an analysis
    routine.
    """

    #: Label to be displayed in UI
    label = Str

    #: Reader class, used to load a BaseMultiImage from file
    reader_class = Type(IMultiImageReader)

    #: Analyser class, used to perform an analysis script on
    #: a specific image type
    analyser_class = Type(IMultiImageAnalyser)

    #: Parser class, used to collate files into sets
    parser_class = Type(IFileParser)

    def __init__(self, **traits):

        label = self.get_label()
        reader = self.get_reader()
        analyser = self.get_analyser()
        parser = self.get_parser()

        super(BaseMultiImageFactory, self).__init__(
            label=label,
            reader_class=reader,
            analyser_class=analyser,
            parser_class=parser,
            **traits
        )

    @abstractmethod
    def get_label(self):
        """Returns key associated with this factory"""

    @abstractmethod
    def get_reader(self):
        """Returns BaseMultiImageReader class able to load
        the BaseMultiImage class created by this factory"""

    @abstractmethod
    def get_analyser(self):
        """Returns BaseMultiImageAnalyser class able to analyse
        the BaseMultiImage class created by this factory"""

    @abstractmethod
    def get_parser(self):
        """Returns BaseFileParser class able to collate image files
        together"""

    def create_reader(self, **kwargs):
        """Public method used to return an instance of
        BaseMultiImageReader"""
        return self.reader_class(**kwargs)

    def create_analyser(self, **kwargs):
        """Public method used to return an instance of
        BaseMultiImageAnalyser"""
        return self.analyser_class(**kwargs)

    def create_parser(self, **kwargs):
        """Public method used to return an instance of
        BaseFileParser"""
        return self.parser_class(**kwargs)
