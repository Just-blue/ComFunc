# -*- coding: utf-8 -*-
import argparse
import os
# from loguru import logger
#
# logger.add("log.txt")
import shutil

parser = argparse.ArgumentParser(description="删除1k文件")
parser.add_argument("-wavpath", required=True, help="音频路径")
parser.add_argument("-outpath",default=None, help="移动音频路径")
parser.add_argument('-wavsize',type=int,default=1,help='音频临界大小')

args = parser.parse_args()
path = args.wavpath
outpath = args.outpath
wavsize = args.wavsize

if outpath is None:
    outpath = os.path.join(os.path.dirname(path),f'lower{wavsize}k')

if not os.path.exists(outpath):
    os.mkdir(outpath)

def filter_size(wav_path):
    size = os.path.getsize(wav_path)
    return size/1024

for root, dirs, files in os.walk(path):
    for file in files:
        if not file.endswith('wav'):
            continue

        wav_path = os.path.join(root, file)
        size = filter_size(wav_path)


        if size <= wavsize:

            print(wav_path)
            shutil.move(wav_path,outpath)