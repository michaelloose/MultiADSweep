from setuptools import setup, find_packages

setup(
    name='MultiADSweep',
    version='0.1',
    author='Michael Loose',
    author_email='michael.loose@fau.de',
    description='A Python library for controlling Pathwave ADS Simulation with multithreading capability and data evaluation tools.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/michaelloose/MultiADSweep',
    packages=find_packages(),
    install_requires=[
        'numpy==1.22.4',
        'scipy==1.11.3',
        'pandas==1.4.4',
        'scikit-rf==0.29.1',
        'matplotlib==3.5.3',
        'tqdm==4.65.0',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='=3.10.13',
)
