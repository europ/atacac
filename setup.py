from setuptools import setup, find_packages


PACKAGE = 'atacac'
VERSION = '0.1'


setup(
    name=PACKAGE,
    version=VERSION,
    description='Ansible Tower Assets Configuration As Code',
    packages=find_packages(include=[PACKAGE, f'{PACKAGE}.*']),
    python_requires='>=3.7',
    install_requires=[
        'ansible-tower-cli',
        'colorlog',
        'dictdiffer',
        'python-gitlab',
        'pyyaml',
        'yamale',
        'click<7.0',
        'yamllint',
    ],
    entry_points={
        'console_scripts': [
            f'{PACKAGE}={PACKAGE}.__main__:main'
        ],
    },
)
