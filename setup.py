  
from distutils.core import setup
setup(
  name = 'discordSuperUtils',
  packages = ['discordSuperUtils'],
  version = '0.0.9',
  license='MIT',
  description = 'Discord Bot Development made easy!',
  author = 'koyashie07 and adam7100',
  url = 'https://github.com/koyashie07/discord-super-utils',
  download_url = 'https://github.com/koyashie07/discord-super-utils/archive/refs/tags/v0.0.9.tar.gz',
  keywords = ['discord', 'easy', 'discord.py', 'music', 'download', 'links', 'images', 'videos','audio', 'bot'],
  install_requires=[
          'youtube-dl',
          'discord.py'
      ],
  classifiers=[  # Optional
    # How mature is this project? Common values are
    #   3 - Alpha
    #   4 - Beta
    #   5 - Production/Stable
    'Development Status :: 4 - Beta',

    # Indicate who your project is intended for
    'Intended Audience :: Developers',
    'Topic :: Software Development :: Build Tools',

    # Pick your license as you wish
    'License :: OSI Approved :: MIT License',

    # Specify the Python versions you support here. In particular, ensure
    # that you indicate whether you support Python 2, Python 3 or both.
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
  ],
)
