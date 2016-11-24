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

import os
#import urllib3.contrib.pyopenssl
#urllib3.contrib.pyopenssl.inject_into_urllib3()
from requests.auth import HTTPBasicAuth
# import certifi
# import urllib3
# http = urllib3.PoolManager(
# 	cert_reqs='CERT_REQUIRED',
# 	ca_certs=certifi.where()
# )
import requests
#import argparse


# pipelines lib
import re
import yaml
from fnmatch import fnmatch
from subprocess import Popen, PIPE


try:
	import dotenv
except ImportError:
	dotenv = None

__title__ = 'PipelinesDeployBitbucket'
__version__ = '0.2.0'
#__build__ = 0x021101
__author__ = 'Maksim Koryukov'
__license__ = 'MIT'
__copyright__ = 'Copyright 2016 Maksim Koryukov'


class DeployError(Exception):
	pass


def gitGetTagName(commitHash):
	cmd = ['git', 'name-rev', commitHash, '--name-only']

	#print ' '.join(cmd)
	pr = Popen(cmd, shell=False, stdout=PIPE, stderr=PIPE)
	(out, err) = pr.communicate()
	if err:
		err = err.strip()
		raise DeployError(err)
	out = out.strip()
	refs = re.sub(r'[~^]\d+$', '', out)
	tag = re.sub(r'^tags?\/', '', refs)
	return tag


def pipelinesGlobMatch(glob, name):
	if glob == name:
		return True

	if not glob:
		return False

	if not name:
		return False

	globTokens = glob.split('/')
	nameTokens = name.split('/')
	i = 0
	gl = len(globTokens)
	nl = len(nameTokens)
	while True:
		if globTokens[i] == '**':
			return True
		if nameTokens[i].strip() == '' and globTokens[i] == '*':
			return False
		if not fnmatch(nameTokens[i], globTokens[i]):
			return False
		i += 1
		if i >= gl or i >= nl:
			return gl==nl
	return True


def pipelenesSearchDeploySettingsInSteps(cfgStepList, gitName):
	for node in cfgStepList:
		for stepType, stepCfg in node.viewitems():
			if stepType == 'deploy':
				return stepCfg
	return None


def pipelenesSearchDeploySettingsInBlock(cfgNode, gitName):

	cfgFound = False
	# week point: need to search LONGEST match, not the first (should be in sync with pipelines config searcher)
	for tagPattern, cfgStepList in cfgNode.viewitems():
		if pipelinesGlobMatch(tagPattern, gitName): # tagPattern matches
			cfg = pipelenesSearchDeploySettingsInSteps(cfgStepList, gitName)
			if cfg is not None:
				return cfg
	return None


def pipelinesSearchDeploySettings(currentTag, currentBranch):
	# read-parse YAML
	with open('bitbucket-pipelines.yml', 'r') as stream:
		cfg = yaml.load(stream)

	# search for an appropriate block in YAML
	# this should be providen
	# 1. searching in tags
	# 2. searching in named branches
	# 3. take default
	cfgFound = False
	deployCfg = None

	if currentTag:
		deployCfg = pipelenesSearchDeploySettingsInBlock(cfg['pipelines']['tags'], currentTag)
		if deployCfg:
			cfgFound = True
	elif currentBranch:
		deployCfg = pipelenesSearchDeploySettingsInBlock(cfg['pipelines']['branches'], currentBranch)
		if deployCfg:
			cfgFound = True

	if not cfgFound:
		deployCfg = pipelenesSearchDeploySettingsInSteps(cfg['pipelines']['default'], currentBranch)

	return deployCfg


def outhr(c='-'):
	print (c * 40)


def deployPrepareFileList(fileCfg, baseDir):
	result = dict()

	if not fileCfg:
		raise DeployError('No files to deploy in the config. Please, define proper `file` section')

	if isinstance(fileCfg, (basestring, int, long, bool)):
		fn = str(fileCfg)
		result[fn] = os.path.join(baseDir, fn)
	elif isinstance(fileCfg, list):
		for fn in fileCfg:
			fn = str(fn)
			result[fn] = os.path.join(baseDir, fn)
	elif isinstance(fileCfg, dict):
		for vname, fname in fileCfg.viewitems():
			vname = str(vname)
			fname = str(fname)
			# MAKE SUBSTITUTION in filenames (fname, vname)
			result[vname] = os.path.join(baseDir, fname)
	else:
		raise DeployError('Unknown format of `file` section')

	return result


def deploy():
	if dotenv:
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

	if not repoBranch:
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

	deployCfg = pipelinesSearchDeploySettings(repoTag, repoBranch)

	# bug: should not use only first provider. but it is v0.2.0 and I am lazy...
	deployCfg = deployCfg[0]

	deployFileConfig = deployPrepareFileList(deployCfg['file'], repoCloneDir)

	auth = None
	if authUsingKey:
		auth = HTTPBasicAuth(repoOwner, repoKey)
	else:
		auth = HTTPBasicAuth(repoUser, repoPwd)

	# API ref: https://developer.atlassian.com/bitbucket/api/2/reference/resource/repositories/%7Busername%7D/%7Brepo_slug%7D/downloads#post		# noqa: E501
	url = 'https://api.bitbucket.org/2.0/repositories/{username}/{repo_slug}/downloads'.format(username=repoOwner, repo_slug=repoSlug)

	try:
		files = []
		for vn, fn in deployFileConfig.viewitems():
			files.append( ('files', (vn, open(fn, 'rb') ) ) )

		response = requests.post(url, files=files, auth=auth)
	finally:
		for f in files:
			f[1][1].close()

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


if __name__ == "__main__":
	deploy()
