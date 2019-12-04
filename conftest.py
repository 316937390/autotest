# -*- coding: utf-8 -*-

import pytest
import subprocess
import os,sys
import re
import logging

logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger()

script_path = os.path.realpath(__file__)
script_dir = os.path.dirname(script_path)
#sys.path.append(script_dir)

dsp_path = '/data/dsp'
mvdsp_path = '/data/mvdsp'
dspauto_path = '/data/dsp_autocase'

filelist = []  #feature文件列表


def recur_find_file(fpath, pattern, result):
    fs = os.listdir(fpath)
    for f in fs:
        if os.path.isfile(os.path.join(fpath,f)):
            if re.search(pattern, f):
                result.append(os.path.join(fpath,f))
        elif os.path.isdir(os.path.join(fpath,f)):
            recur_find_file(os.path.join(fpath,f), pattern, result)
        else:
            pass

@pytest.fixture(scope="session")
def start():
    '''
    command = 'cd %s && cat branch_name | xargs sh prepareEnv.sh > /tmp/tmp_mvdsp.log 2>&1' % (script_dir)
    ret = subprocess.call(command, shell=True, executable='/bin/sh')
    if ret != 0:
        LOGGER.critical('start dsp_server fail')
    assert ret == 0
    cmd = 'rm -rf /tmp/tmp_feature_* && rm -rf /tmp/retry_tmp_feature_* && rm -rf /tmp/tmpGrey_* && rm -rf /tmp/retry_tmpGrey_*'
    ret = subprocess.call(cmd, shell=True, executable='/bin/sh')
    path = os.path.join(dspauto_path,'features')
    recur_find_file(path, '.feature$', filelist)
    #在这里可以assert len(filelist) == 30
    if len(filelist) > 30:
        LOGGER.error('find new feature file ...')
    elif len(filelist) < 30:
        LOGGER.error('cannot find feature file ...')
    assert len(filelist) == 30
    '''
    LOGGER.critical("== session start ==")
    yield (dsp_path,mvdsp_path,dspauto_path,filelist,LOGGER)
    LOGGER.critical("== session end ==")
    #tree features/ | grep "\.feature$" | wc -l



@pytest.fixture(scope="function")
def param():
    #print "[function fixture start]"
    return (dsp_path,mvdsp_path,dspauto_path,filelist,LOGGER)









