#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

"""

Original REPO:
https://github.com/maxkoryukov/pipelines-deploy-bitbucket

Simple deployment script from Bitbucket Pipelines to Bitbucket Downloads

I don't know why Bitbucket Dev team did not include this in Pipeline
out of the box.

https://developer.atlassian.com/bitbucket/api/2/reference/resource/repositories/%7Busername%7D/%7Brepo_slug%7D/downloads#post

MIT License

Copyright (C) 2016  Koryukov Maksim <maxkoryukov@gmail.com>

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without restriction,
including without limitation the rights to use, copy, modify, merge,
publish, distribute, sublicense, and/or sell copies of the Software,
and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import pytest
import PipelinesDeployBitbucket as srcmod


@pytest.mark.parametrize('glob, name, exp', [
	('*', 'a',      True),
	('*', 'a/b',    False),
	('*', 'a/b/c',  False),

	('**', 'a',      True),
	('**', 'a/b',    True),
	('**', 'a/b/c',  True),

	('feature/*', 'feature/a',  True),
	('feature/*', 'feature/b',  True),

	('feature/*', 'feature',  False),
	('feature/*', 'feature/',  False),
	('feature/*', 'feature/a/b',  False),

	('feature/bb-123-fix-links', 'feature/bb-123-fix-links',  True),
	('feature/bb-123-fix-links', '', False),
	('feature/bb-123-fix-links', 'feature', False),
	('feature/bb-123-fix-links', 'feature/', False),
	('feature/bb-123-fix-links', 'feature/bb-123-fix-links1',  False),
	('feature/bb-123-fix-links', 'feature/bb-123-fix-links/a',  False),
	('feature/bb-123-fix-links', 'feature/bb-123-fix-links*',  False),

	('*/feature', 'a/feature', True),
	('*/feature', 'b/feature', True),
	('*/feature', 'feature/feature', True),
	('*/feature', 'feature', False),
	('*/feature', '/feature', False),
	('*/feature', '/feature/', False),
	('*/feature', 'a/feature/b', False),
	('*/feature', 'a/feature/b/c', False),
])
def test_pipelinesGlobMatch(glob, name, exp):
	act = srcmod.pipelinesGlobMatch(glob, name)
	assert act == exp, 'glob "' + glob + '" against "' + name + '"'
