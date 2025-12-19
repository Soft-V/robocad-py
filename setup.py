from setuptools import setup, find_packages

classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Education',
    'Operating System :: Microsoft :: Windows :: Windows 10',
    'Operating System :: Android',
    'Operating System :: POSIX :: Linux',
    'Operating System :: iOS',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3'
]

setup(
    name='robocad-py',
    version='1.3.5.0',
    description='python lib for real and virtual robots',
    long_description="Python library for real and virtual robots" + '\n\n' + open('CHANGELOG.md').read(),
    url='https://github.com/Soft-V/robocad-py',
    author='Airat Abdrakov',
    author_email='softvery@yandex.ru',
    license='MIT',
    classifiers=classifiers,
    keywords=['simulator', 'robotics', 'robot', '3d', 'raspberry', 'control', 'robocad'],
    packages=find_packages(),
    install_requires=['numpy', 'funcad', 'pyserial']
)
