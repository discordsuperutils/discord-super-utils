from setuptools import setup, find_packages
 
classifiers = [
  'Development Status :: 5 - Production/Stable',
  'Intended Audience :: Education',
  'Operating System :: Microsoft :: Windows',
  'License :: OSI Approved :: MIT License',
  'Programming Language :: Python :: 3'
]
 
setup(
  name='discord-super-utils',
  version='0.0.1',
  description='Module to complement discord.py that has Music and Levelling',
  long_description=open('README.md').read() + '\n\n' + open('CHANGELOG.txt').read(),
  url='',  
  author='koyashie07 & adam7100',
  license='MIT', 
  classifiers=classifiers,
  keywords=['discord', 'music', 'levelling', 'discord.py'], 
  packages=find_packages(),
  install_requires=['youtube-dl','discord.py'] 
)
