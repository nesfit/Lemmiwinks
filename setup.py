from setuptools import setup, find_packages

setup(name='lemmiwinks',
      vesrion='0.0.1',
      author='Viliam Serecun',
      author_email='v.serecun@gmail.com',
      packages=find_packages(),
      licence="MIT",
      classifiers=[
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3.6',
      ],
      install_requires=[
          'tinycss2>=0.6.1',
          'aiohttp>=2.3.7',
          'aiofiles>=0.3.2',
          'selenium>=3.8.1',
          'dependency-injector>=3.9.1',
          'validators>=0.12.0',
          'python-magic>=0.4.15',
          'beautifulsoup4>=4.6.0',
          'asyncio-extras>=1.3.0',
          'lxml>=4.2.0',
          'Jinja2>=2.10',
      ],
      include_package_data=True,
      zip_safe=False,
      )
