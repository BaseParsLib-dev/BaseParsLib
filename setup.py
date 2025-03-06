from setuptools import setup

setup(
    name="BaseParsLib",
    version="0.2.8",
    packages=[
        "base_pars_lib",
        "base_pars_lib.utils",
        "base_pars_lib.config",
        "base_pars_lib.core",
        "base_pars_lib.nodriver_proxy_extension",
    ],
    install_requires=[],
)
