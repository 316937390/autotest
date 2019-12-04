#! /bin/bash

#准备环境：dsp  dsp_autocase  mvdsp
#参数：BRANCH_NAME
#retCode:  0  正常
#          1  dsp失败
#          2  dsp_autocase失败
#          3  mvdsp失败  
#          4  git失败
CWD_PATH=$(pwd)
DSP_PATH=/data/dsp
DSP_AUTO_PATH=/data/dsp_autocase
DSP_MVDSP=/data/mvdsp
BRANCH_NAME=master
if [ "$#" -ge 1 ];then
    BRANCH_NAME=$1
fi

LOCAL_IP=$(ifconfig eth0 | grep "inet"| awk '{print $2}')


if [ ! -d ${DSP_PATH} ];then
	cd $(dirname ${DSP_PATH}) && git clone git@gitlab.mobvista.com:mvdsp/dsp.git $(basename ${DSP_PATH})
fi
if [ ! -d ${DSP_AUTO_PATH} ];then
	cd $(dirname ${DSP_AUTO_PATH}) && git clone git@gitlab.mobvista.com:mvbjqa/dsp_autocase.git $(basename ${DSP_AUTO_PATH})
fi

if [ ! -d ${DSP_PATH} ];then
	echo "dsp failed!!!"
	exit 1
fi


echo ${CWD_PATH}
echo "y"| cp -rf  ${CWD_PATH}/dsp_server ${DSP_MVDSP}


if [ ! -d ${DSP_AUTO_PATH} ];then
	echo "dsp_autocase failed!!!"
	exit 2
fi
cd ${DSP_AUTO_PATH}
echo "clone dsp_autotest"
git reset --hard && git clean -df && git checkout master && git pull
if [ "$?" -ne 0 ];then
	echo "clone dsp_autotest failed!!!"
	exit 4
fi


echo "sync auto_test config and data"
ret=$(ps aux | grep -v grep | grep -v supervise | grep dsp_server | wc -l)
if [ "$ret" -eq 1 ];then
    cd ${DSP_MVDSP} && sh excute_dsp stop
    if [ "$?" -ne 0 ];then
        echo "stop dsp_server failed!"
        exit 3
    fi
fi

#echo ${CWD_PATH}
#echo "y"| cp -rf ${CWD_PATH}/dsp_server ${DSP_MVDSP}

#echo "y"| cp -rf  ${DSP_PATH}/dsp_server ${DSP_MVDSP}
echo "y"| cp -rf ${DSP_PATH}/conf/* ${DSP_MVDSP}/conf
echo "update dsp conf"
echo "y"| cp -rf ${DSP_AUTO_PATH}/conf/* ${DSP_MVDSP}/data
echo "update dsp data"
sed -i 's~^USDMPRegion.*$~USDMPRegion = "'"${LOCAL_IP}"':7001,'"${LOCAL_IP}"':7002,'"${LOCAL_IP}"':7000"~g' ${DSP_MVDSP}/conf/dsp_server.conf
sed -i 's~^TKDMPRegion.*$~TKDMPRegion = "'"${LOCAL_IP}"':7001,'"${LOCAL_IP}"':7002,'"${LOCAL_IP}"':7000"~g' ${DSP_MVDSP}/conf/dsp_server.conf
sed -i 's~^BJDMPRegion.*$~BJDMPRegion = "'"${LOCAL_IP}"':7001,'"${LOCAL_IP}"':7002,'"${LOCAL_IP}"':7000"~g' ${DSP_MVDSP}/conf/dsp_server.conf
sed -i 's~^USDeImpRedis.*$~USDeImpRedis = "'"${LOCAL_IP}"':7001"~g' ${DSP_MVDSP}/conf/dsp_server.conf
sed -i 's~^TKDeImpRedis.*$~TKDeImpRedis = "'"${LOCAL_IP}"':7001"~g' ${DSP_MVDSP}/conf/dsp_server.conf
sed -i 's~^BJDeImpRedis.*$~BJDeImpRedis = "'"${LOCAL_IP}"':7001"~g' ${DSP_MVDSP}/conf/dsp_server.conf
sed -i 's~^Debug.*$~Debug = true~g' ${DSP_MVDSP}/conf/dsp_server.conf
sed -i 's~^Port.*$~Port = 9889~g' ${DSP_MVDSP}/conf/dsp_server.conf
sed -i 's~^ModifyInterval.*$~ModifyInterval = 1~g' ${DSP_MVDSP}/conf/dsp_server.conf
sed -i 's~^Mongo.*$~Mongo = "localhost"~g' ${DSP_MVDSP}/conf/dsp_server.conf
sed -i 's~^AuditMongo.*$~AuditMongo = "localhost"~g' ${DSP_MVDSP}/conf/dsp_server.conf
sed -i 's~^AuditOpen.*$~AuditOpen = true~g' ${DSP_MVDSP}/conf/dsp_server.conf
sed -i 's~^ABRate.*$~ABRate=0.0~g' ${DSP_MVDSP}/conf/dsp_server.conf
sed -i 's~^WatchDir.*$~WatchDir = "'"${DSP_MVDSP}"'/data"~g' ${DSP_MVDSP}/conf/dsp_server.conf
sed -i 's~^CheckMd5.*$~CheckMd5 = false~g' ${DSP_MVDSP}/conf/dsp_server.conf
if [ -f "${DSP_PATH}/conf/dmploader.json" ];then
	sed -i 's~"address".*$~"address": "127.0.0.1:3000",~g' ${DSP_MVDSP}/conf/dmploader.json
	sed -i 's~"dataSource":.*"dataSource.*$~"dataSource": "dataSource.aerospike",~g' ${DSP_MVDSP}/conf/dmploader.json
	sed -i 's~"keyCompressor".*:.*"keyCompressor.*$~"keyCompressor": "keyCompressor.origin",~g' ${DSP_MVDSP}/conf/dmploader.json
fi



echo "start mvdsp"
TIME_STAMP=$(date +"%Y-%m-%d %H:%M:%S")
echo "start mvdsp ${TIME_STAMP}"

cd ${DSP_MVDSP} && sh restart.sh
if [ "$?" -ne 0 ];then
	echo "mvdsp failed!!!"
	exit 3
fi

exit 0
