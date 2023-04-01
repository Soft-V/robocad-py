from setuptools import setup, find_packages

classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Education',
    'Operating System :: Microsoft :: Windows :: Windows 10',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3'
]

setup(
    name='shufflecad-py',
    version='0.0.0.5',
    description='python lib for shufflecad',
    long_description="Python library for Shufflecad" + '\n\n' + open('CHANGELOG.md').read(),
    url='https://github.com/Soft-V/shufflecad-4',
    author='Abdrakov Airat',
    author_email='abdrakovairat@gmail.com',
    license='MIT',
    classifiers=classifiers,
    keywords=['simulator', 'robotics', 'robot', '3d', 'raspberry', 'control'],
    packages=find_packages(),
    install_requires=['numpy', 'funcad']
)