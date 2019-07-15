import logging
import click

from envisage.core_plugin import CorePlugin
from envisage.ui.tasks.tasks_plugin import TasksPlugin

from traits.api import push_exception_handler

from pyfibre.version import __version__

from pyfibre.gui.pyfibre_gui import PyFibreGUI
from pyfibre.gui.pyfibre_plugin import PyFibrePlugin
from pyfibre.utilities import logo

push_exception_handler(lambda *args: None,
                       reraise_exceptions=True)


@click.command()
@click.version_option(version=__version__)
@click.option(
    '--debug', is_flag=True, default=False,
    help="Prints extra debug information in force_wfmanager.log"
)
@click.option(
    '--profile', is_flag=True, default=False,
    help="Run GUI under cProfile, creating .prof and .pstats "
         "files in the current directory."
)
@click.option(
    '--window-size', nargs=2, type=int,
    help="Sets the initial window size"
)
def pyfibre(debug, window_size, profile):
    """Launches the FORCE workflow manager application"""
    if not window_size:
        window_size = None

    run(debug=debug,
        window_size=window_size,
        profile=profile)


def run(debug, window_size, profile):

    if debug:
        logging.basicConfig(filename="pyfibre.log", filemode="w",
                            level=logging.DEBUG)
    else:
        logging.basicConfig(filename="pyfibre.log", filemode="w",
                            level=logging.INFO)

    logger = logging.getLogger(__name__)

    if profile:
        import cProfile
        import pstats
        profiler = cProfile.Profile()
        profiler.enable()

    n_proc = 1#os.cpu_count() - 1

    logger.info(logo())

    plugins = [CorePlugin(), TasksPlugin(),
               PyFibrePlugin()]

    pyfibre_gui = PyFibreGUI(plugins=plugins,
                             window_size=window_size)
    pyfibre_gui.run()

    if profile:
        profiler.disable()
        from sys import version_info
        fname = 'pyfibre-{}-{}.{}.{}'.format(__version__,
                                             version_info.major,
                                             version_info.minor,
                                             version_info.micro)

        profiler.dump_stats(fname + '.prof')
        with open(fname + '.pstats', 'w') as fp:
            stats = pstats.Stats(profiler, stream=fp).sort_stats('cumulative')
            stats.print_stats()
