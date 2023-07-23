from setuptools import setup, find_packages

classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Education',
    'Operating System :: Microsoft :: Windows :: Windows 10',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3'
]

setup(
    name='robocad-py',
    version='0.0.1.1',
    description='python lib for real and virtual robots',
    long_description="Python library for real and virtual robots" + '\n\n' + open('CHANGELOG.md').read(),
    url='https://github.com/CrackAndDie/robocad-py',
    author='Abdrakov Airat',
    author_email='abdrakovairat@gmail.com',
    license='MIT',
    classifiers=classifiers,
    keywords=['simulator', 'robotics', 'robot', '3d', 'raspberry', 'control'],
    packages=find_packages(),
    install_requires=['numpy', 'funcad', 'shufflecad-py']
)
