#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Example of news extractor library."""

import urllib

from extractor import NewsExtractor

URL = 'https://www.cnn.com/2018/05/22/politics/trump-moon-north-korea-white-house/index.html'
html = urllib.urlopen(URL).read()

extractor = NewsExtractor()
content = extractor.extract(html)
print(content)

extractor.plot()
