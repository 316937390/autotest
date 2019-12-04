# -*- coding: utf-8 -*-

import subprocess
import os,sys
import shutil
import pytest



##重跑失败的scenario
def retryFailing(log_path, retry_log):
    flag = True
    tmp_lines = []
    file_tag_map = {}
    with open(log_path, 'r') as f:
        canWrite = False
        preline = ""
        for line in f:
            if 'Failing scenarios' in line:
                canWrite = True
            if canWrite:
                tmp_lines.append(line)
            if ".feature" in line and '@' in preline and ".feature" not in preline:
                targetTag = preline.strip().split("@")[1]
                filePos = line.strip().split("#")[-1].strip()
                targetFile = filePos.split(":")[0]
                targetFile = targetFile.replace('../..', '')
                file_tag_map[filePos] = (targetFile,targetTag)
            preline = line
    if 0 == len(tmp_lines):
        shutil.copyfile(log_path, retry_log)
        return False
    for line in tmp_lines:
        if '.feature' in line:
            keyfail = line.strip().split(" ")
            if keyfail == "" :
                continue
            else:
                targetFile, targetTag = file_tag_map[keyfail[0]]
                retryCmd = 'behave -k %s -D host="localhost:9888" --tags=-not_ok --tags=-uniqueCases --tags=-all_all --tags=-not_online --tags=%s >> %s' % (targetFile, targetTag, retry_log)
                #print retryCmd
                ret = subprocess.call(retryCmd, shell=True, executable='/bin/sh')
                if ret != 0:
                    flag = False
    return flag




def run_proc(logger, path):
    def run_internal(filename,logname):
        flag = True
        cmd = 'behave -k {}/{} -D host="localhost:9888" --tags=-not_ok --tags=-uniqueCases --tags=-all_all --tags=-not_online > /tmp/{}'.format(path,filename,logname)
        retcode = subprocess.call(cmd, shell=True, executable='/bin/sh')
        if retcode != 0:
            #重跑一次
            log_path = '/tmp/{}'.format(logname)
            retry_path = '/tmp/retry_{}'.format(logname)
            if not retryFailing(log_path, retry_path):
                err_msg = subprocess.check_output('cat {}'.format(retry_path), shell=True)
                logger.critical(err_msg)
                flag = False
        return flag
    return run_internal






@pytest.mark.not_cov_branchCheck
def test_suit_50(start, param):
    logger = param[4]
    #logger.info('branchCheck--->test_run_50 : features/creative3_3_1_banner_dyRendering.feature')
    path = param[2]
    branchCheck = run_proc(logger, path)
    ret = branchCheck('features/creative3_3_1_banner_dyRendering.feature','tmp_feature_creative3_3_1_banner_dyRendering.log')
    assert ret == True


@pytest.mark.not_cov_branchCheck
def test_suit_51(start, param):
    logger = param[4]
    #logger.info('branchCheck--->test_run_51 : features/creative3_3_1_banner.feature')
    path = param[2]
    branchCheck = run_proc(logger, path)
    ret = branchCheck('features/creative3_3_1_banner.feature','tmp_feature_creative3_3_1_banner.log')
    assert ret == True


@pytest.mark.not_cov_branchCheck
def test_suit_52(start, param):
    logger = param[4]
    #logger.info('branchCheck--->test_run_52 : features/creative3_3_1_native.feature')
    path = param[2]
    branchCheck = run_proc(logger, path)
    ret = branchCheck('features/creative3_3_1_native.feature','tmp_feature_creative3_3_1_native.log')
    assert ret == True


@pytest.mark.not_cov_branchCheck
def test_suit_53(start, param):
    logger = param[4]
    #logger.info('branchCheck--->test_run_53: features/creative3_3_1_video.feature')
    path = param[2]
    branchCheck = run_proc(logger, path)
    ret = branchCheck('features/creative3_3_1_video.feature','tmp_feature_creative3_3_1_video.log')
    assert ret == True


@pytest.mark.demo
def test_demo_1(start):
    logger = start[4]
    flag = True
    assert flag == False

@pytest.mark.demo
def test_demo_2(start):
    logger = start[4]
    flag = True
    assert flag == False

@pytest.mark.demo
def test_demo_3(start):
    logger = start[4]
    flag = True
    assert flag == False

@pytest.mark.demo
def test_demo_4(start):
    logger = start[4]
    flag = True
    assert flag == False


#if __name__=='__main__':
    #retryFailing('/tmp/tmpGrey_5.log', '/tmp/retry_tmpGrey_5.log')
