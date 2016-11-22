#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

"""
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

import os
import re
import urllib3.contrib.pyopenssl
urllib3.contrib.pyopenssl.inject_into_urllib3()
from requests.auth import HTTPBasicAuth
# import certifi
# import urllib3
# http = urllib3.PoolManager(
# 	cert_reqs='CERT_REQUIRED',
# 	ca_certs=certifi.where()
# )
import requests
#import argparse
from subprocess import Popen, PIPE
try:
	import dotenv
	useDotEnv = True
except ImportError:
	useDotEnv = False

__title__ = 'PipelineDeployBitbucket'
__version__ = '0.1.0'
#__build__ = 0x021101
__author__ = 'Maksim Koryukov'
__license__ = 'MIT'
__copyright__ = 'Copyright 2016 Maksim Koryukov'


class DeployError(Exception):
	pass


def gitGetTagName(commitHash):
	cmd = ['git', 'name-rev', commitHash, '--name-only']

	print ' '.join(cmd)
	pr = Popen(cmd, shell=False, stdout=PIPE, stderr=PIPE)
	(out, err) = pr.communicate()
	if err:
		err = err.strip()
		raise DeployError(err)
	out = out.strip()
	refs = re.sub(r'[~^]\d+$', '', out)
	tag = re.sub(r'^tags?\/', '', refs)
	return tag


def outhr(c='-'):
	print (c * 40)


if __name__ == "__main__":

	if useDotEnv:
		dotenv.load_dotenv('.env')

	repoSlug = os.getenv('BITBUCKET_REPO_SLUG', None)
	repoOwner = os.getenv('BITBUCKET_REPO_OWNER', None)
	repoBranch = os.getenv('BITBUCKET_BRANCH', None)
	repoCommit = os.getenv('BITBUCKET_COMMIT', None)
	repoCloneDir = os.getenv('BITBUCKET_CLONE_DIR', None)
	repoTag = None

	repoKey = os.getenv('DEPLOY_BITBUCKET_KEY', None)
	repoUser = os.getenv('DEPLOY_BITBUCKET_USER', None)
	repoPwd = os.getenv('DEPLOY_BITBUCKET_PASSWORD', None)

	authUsingKey = not repoUser and not repoPwd and repoKey

	if repoBranch is None:
		# probably, we are on tag, because BitBucket said:
		# >>  This value is only available on branches.
		# see: https://confluence.atlassian.com/bitbucket/environment-variables-in-bitbucket-pipelines-794502608.html#EnvironmentvariablesinBitbucketPipelines-Defaultvariables		# noqa: E501
		repoTag = gitGetTagName(repoCommit)

	outhr()
	print 'CloneDir  :', repoCloneDir
	print 'Slug      :', repoSlug
	print 'Owner     :', repoOwner
	print 'Commit    :', repoCommit
	print 'Branch    :', repoBranch
	print 'Tag       :', repoTag
	print 'Auth      :', 'using repo key' if authUsingKey else 'using user credentials'
	outhr()

	files = {
		'files': ('NetworkAutotune.py', open(os.path.join(repoCloneDir, 'NetworkAutotune.py'), 'rb'))
	}

	auth = None
	if authUsingKey:
		auth = HTTPBasicAuth(repoOwner, repoKey)
	else:
		auth = HTTPBasicAuth(repoUser, repoPwd)

	# API ref: https://developer.atlassian.com/bitbucket/api/2/reference/resource/repositories/%7Busername%7D/%7Brepo_slug%7D/downloads#post		# noqa: E501
	url = 'https://api.bitbucket.org/2.0/repositories/{username}/{repo_slug}/downloads'.format(username=repoOwner, repo_slug=repoSlug)

	response = requests.post(url, files=files, auth=auth)
	if response.status_code not in (200, 201):
		outhr('!')
		print response.text
		outhr('!')
		print response.raw
		outhr('!')
		raise DeployError(response.text)
	else:
		print 'DONE'
		outhr()
