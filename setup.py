"""
Crypto Anomaly Detection Engine Sys (CADES)

Setup configuration for the CADES package.
"""

from setuptools import setup, find_packages
from os import path

# Read the contents of README.md
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Read requirements.txt
with open(path.join(this_directory, 'requirements.txt'), encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='crypto-anomaly-detection-engine',
    version='1.0.0',
    description='Advanced AI system for detecting anomalous patterns in cryptocurrency markets',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='CADES Team',
    author_email='contact@cades.io',
    url='https://github.com/joengo72/crypto-anomaly-detection-engine-system',
    
    # Package structure
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    
    # Dependencies
    python_requires='>=3.9',
    install_requires=requirements,
    
    # Optional dependencies
    extras_require={
        'dev': [
            'pytest>=7.4.0',
            'pytest-asyncio>=0.21.1',
            'pytest-cov>=4.1.0',
            'black>=23.7.0',
            'flake8>=6.0.0',
            'mypy>=1.4.1',
            'isort>=5.12.0',
        ],
        'docs': [
            'sphinx>=7.0.1',
            'mkdocs>=1.5.2',
            'pdoc3>=0.10.0',
        ],
        'gpu': [
            'torch>=2.0.1',
            'torchvision>=0.15.2',
            'tensorflow-gpu>=2.13.0',
        ],
    },
    
    # Entry points for command-line scripts
    entry_points={
        'console_scripts': [
            'cades=src.api.routes:main',
            'cades-monitor=scripts.monitor:main',
            'cades-deploy=scripts.deploy:main',
        ],
    },
    
    # Package metadata
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Financial and Insurance Industry',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Office/Business :: Financial :: Investment',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS :: MacOS X',
        'Environment :: GPU :: NVIDIA CUDA :: 11.8',
        'Framework :: AsyncIO',
        'Framework :: Pytest',
        'Natural Language :: English',
    ],
    
    # Additional package data
    include_package_data=True,
    package_data={
        'crypto_anomaly_detection_engine': [
            'config/*.yml',
            'models/*.json',
            'static/*',
            'templates/*',
        ],
    },
    
    # Project URLs
    project_urls={
        'Bug Reports': 'https://github.com/joengo72/crypto-anomaly-detection-engine-system/issues',
        'Documentation': 'https://cades.io/docs',
        'Source': 'https://github.com/joengo72/crypto-anomaly-detection-engine-system',
    },
    
    # Keywords for PyPI
    keywords=[
        'cryptocurrency',
        'anomaly-detection',
        'artificial-intelligence',
        'blockchain',
        'machine-learning',
        'deep-learning',
        'solana',
        'trading',
        'market-analysis',
        'sentiment-analysis',
    ],
    
    # Zip safe flag
    zip_safe=False,
    
    # Platform specification
    platforms=['Linux', 'MacOS X'],
)