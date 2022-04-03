from distutils.core import setup

setup(name='Kijiji-reposter',
      version='1.0',
      description='Kijiji Automated Reposter',
      author='',
      author_email='',
      url='https://github.com/evgenyslab/Kijiji-Repost-Headless',
      packages=['kijiji_repost_headless'],
      license='MIT',
      install_requires=[
          'bs4',
          'requests',
          'pyyaml==5.4',
          'xmltodict'
      ],
     )
