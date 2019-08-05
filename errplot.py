# -*- coding: utf-8 -*-

import numpy as np
import wave
import argparse
from loguru import logger
import shutil
import os

logger.add("log.txt")

parser = argparse.ArgumentParser(description="移动异常波形音频")
parser.add_argument("-wavpath", required=True, help="音频路径")
parser.add_argument('-movedpath', required=True, help='目标位置')

args = parser.parse_args()
path = args.wavpath
outpath = args.movedpath


def read_wav(path):
    wr = wave.open(path)
    raw_data = wr.readframes(wr.getnframes())
    wr.close()
    wave_data = np.frombuffer(raw_data, dtype=np.short)
    return wr.getparams(), wave_data


def clipped(wav, n=40):
    params, data = read_wav(wav)
    data = np.abs(data)
    data = data / float(np.max(data)) * 32000
    data = data.astype(np.int16)
    l = np.sort(data)[-1 * n:]
    # print np.var(l)
    if np.var(l) < 10000:
        return True
    else:
        return False


for dir_name, _, files in os.walk(path):
    for fl_name in files:
        if not fl_name.endswith('wav'):
            continue
        sub_path = os.path.join(dir_name, fl_name)
        try:
            tag = clipped(sub_path)
        except Exception:
            tag = False
        if tag:
            spk_id = fl_name.split('_')[0]
            o = os.path.join(outpath, spk_id)
            try:
                os.makedirs(o)
            except OSError:
                pass
            logger.info(sub_path, o)
            shutil.move(sub_path, o)

