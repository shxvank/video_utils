#!/usr/bin/env python
import setuptools
from distutils.util import convert_path

main_ns  = {};
ver_path = convert_path("video_utils/version.py");
with open(ver_path) as ver_file:
  exec(ver_file.read(), main_ns);

setuptools.setup(
  name             = "video_utils",
  description      = "Package for transcoding video files to h264/h265 codec",
  url              = "https://github.com/kwodzicki/video_utils",
  author           = "Kyle R. Wodzicki",
  author_email     = "krwodzicki@gmail.com",
  version          = main_ns['__version__'],
  packages         = setuptools.find_packages(),
  install_requires = [ "mutagen", "imdbpy", "tvdbsimple",
                       "soundfile", "numpy", "scipy",
                       "requests", "psutil", "watchdog"],
  scripts          = ['bin/comremove',
                      'bin/mp4tagger',
                      'bin/MakeMKV_Watchdog',
                      'bin/Plex_DVR_Watchdog'],
  zip_safe         = False
);
