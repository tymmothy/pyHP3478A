from distutils.core import setup
setup(name='hp3478a',
      version='0.1',
      author='Tymm Twillman',
      author_email='tymmothy@gmail.com',
      description='Hewlett Packard HP3478A bench meter control module',
      classifiers=[
          'Development Status :: 4 - Beta',
          'Programming Language :: Python',
          'Intended Audience :: Science/Research',
          'License :: OSI Approved :: BSD License',
      ],
      license='BSD-new',
      requires=[
          'gpibdevices',
      ],
      provides=[
          'hp3478a',
      ],
      py_modules=[
          'hp3478a',
      ],
      )

