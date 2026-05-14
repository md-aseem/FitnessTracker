import setuptools
from setuptools import setup, find_packages

requirements = [
    "numpy",
    "pandas",
    "pyyaml",
    "pydantic",
    "scipy",
    "matplotlib",
    "numba",
]

setuptools.setup(
    name="quantum_thermal_model",
    version="0.1.2",
    author="Wärtsilä North America, Inc.",
    description="Quantum Thermal Model for battery systems",
    long_description_content_type="text/markdown",
    url="",
    include_package_data=True,
    packages=find_packages(),
    install_requires=requirements,
    python_requires=">=3.8",
)
