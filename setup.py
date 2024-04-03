from setuptools import setup


setup(
    name='BaseParsLib',
    version='0.0.3',
    packages=['base_pars_lib', 'base_pars_lib.utils'],
    install_requires=[
        'fake-useragent==1.5.1',
        'requests==2.31.0'
    ]
)
