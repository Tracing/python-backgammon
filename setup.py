from setuptools import setup
from setuptools.extension import Extension
from Cython.Build import cythonize
import numpy
import os.path

state_ext = Extension("state", sources=['state.pyx'], include_dirs=[numpy.get_include()], libraries=['npyrandom'], 
                library_dirs=[os.path.join(numpy.get_include(), '..', '..', 'random', 'lib')])

mcts_ext = Extension("mcts", sources=['mcts.pyx'], include_dirs=[numpy.get_include()])
utils_ext = Extension("utils", sources=['utils.pyx'], include_dirs=[numpy.get_include()])

setup(
    ext_modules = cythonize([state_ext, mcts_ext, utils_ext], language_level=3, annotate=True)
)
