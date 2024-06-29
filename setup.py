from setuptools import setup, find_packages

def parse_requirements(filename):
    """Load requirements from a pip requirements file."""
    with open(filename, 'r') as f:

        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='EzCommit',
    version='0.1.3',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'EzCommit': ['helper/default_convention.txt'],
    },
    install_requires=parse_requirements('requirements.txt'),
    entry_points={
        'console_scripts': [
            'ezcommit=EzCommit.main:main',
        ],
    },
)