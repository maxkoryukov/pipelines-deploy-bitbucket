# python-pipelines-deploy

Python script which provides the deploy-functionality for Bitbucket's Pipelines

## HOWTO

1. Add `PipelinesDeployBitbucket.py` to the root of your repo (there is no PYPI package.. see #2)
2. Modify your `bitbucket-pipelines.yml`

```yaml
---
image: python:2.7
pipelines:
  default:
    - step:
        script:
          - pip install -r requirements.txt -t libs -q

          - pip --version
          - pytest --version

          - flake8
  tags:
    '**':
      - step:
          script:
            - pip --version
            - pip install -r requirements-dev.txt -q
            - ./PipelinesDeployBitbucket.py		# 1 REQUIRED! BitBucket won't start deploy automatically

      # 2: DEPLOY settings
      - deploy:
          - provider: bitbucket-downloads
            file:
              name-for-bitbucket-downloads.py: RealFileName/On/Fs/myscript.py
              otherfile: otherfile
...
```
