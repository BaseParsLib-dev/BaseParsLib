from setuptools import setup

setup(
    name='BaseParsLib',
    version='0.1.67',
    packages=[
        'base_pars_lib',
        'base_pars_lib.utils',
        'base_pars_lib.config'
    ],
    install_requires=[
        'fake-useragent==1.5.1',
        'requests==2.31.0',
        'aiohttp==3.9.5',
        'pytest-playwright==0.5.0'
    ]
)
