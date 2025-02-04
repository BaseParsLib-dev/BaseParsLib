from setuptools import setup

setup(
    name='BaseParsLib',
    version='0.2.67',
    packages=[
        'base_pars_lib',
        'base_pars_lib.utils',
        'base_pars_lib.config',
        'base_pars_lib.core',
        'base_pars_lib.nodriver_proxy_extension',
    ],
    install_requires=[
        'fake-useragent==1.5.1',
        'requests==2.31.0',
        'aiohttp==3.9.5',
        'pytest-playwright==0.5.0',
        'nodriver==0.38.post1',
        'selenium==4.26.1',
        'curl-cffi==0.7.4'
    ]
)
