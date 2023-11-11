#!/bin/bash
JPS_NAME=$1
DIRPATH='/tmp/jstack'
CURRENT_TIME=$(date +'%F'-'%H:%M:%S')
if [ ! -d "$DIRPATH" ];then
	mkdir "$DIRPATH"
else
	rm -rf "$DIRPATH"/*
fi
cd "$DIRPATH"
while true
do
sleep 3600
# 这里需要将inceptor改后自己的java进程名称
pid=$(ps -ef | grep $JPS_NAME | grep -v grep | awk '{print $2}')
jstack $pid >> "jstack_${CURRENT_TIME}"
dir_count=$(ls | wc -l)
if [ "$dir_count" -gt 10 ];then
	rm -f $(ls -tr | head -1)
fi
done