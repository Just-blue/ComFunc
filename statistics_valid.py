# -*- coding: utf-8 -*-

import argparse
import csv
import os
from pydub import AudioSegment
from loguru import logger

parser = argparse.ArgumentParser(description="计算音频有效率")
parser.add_argument("-segments", default=None, help="segment文件路径")
parser.add_argument("-wavpath", required=True, help="音频路径")
parser.add_argument("-pjname", required=True, help="项目名")

args = parser.parse_args()
seg = args.segments
wavpath = args.wavpath
pjname = args.pjname

savpath = os.path.join(wavpath,pjname + '.csv')

def creat_dic(wav_info):
    with open(wav_info, "r", encoding="utf-8") as f:
        Dic_wav_info = {}
        for line in f.readlines():
            _, wav_name, start_time, end_time = line.split(" ")
            valid = float(end_time) - float(start_time)
            if wav_name not in Dic_wav_info:
                Dic_wav_info[wav_name] = valid
            else:
                Dic_wav_info[wav_name] = Dic_wav_info[wav_name] + valid
    return Dic_wav_info


def wav_time(wav_path):
    sound = AudioSegment.from_wav(wav_path)
    return len(sound) / 1000


# 计算有效率
def calc_valid_rate(segment_path,savepath,wavs_path):
    Dic_wav_info = creat_dic(segment_path)

    with open(savepath, "w", encoding="utf-8", newline="") as f:
        headers = ["音频名称", "音频时长(s)", "有效时长(s)", "音频有效率"]
        f_csv = csv.writer(f)
        f_csv.writerow(headers)

        all_time = 0
        all_valid_time = 0
        for root, _, files in os.walk(wavs_path):
            for wav_name in files:
                if not wav_name.endswith("wav"):
                    continue

                wav_path = os.path.join(root, wav_name)
                time = wav_time(wav_path)

                valid_time = Dic_wav_info.get(wav_name)

                all_time += time
                try:
                    all_valid_time += valid_time
                except TypeError:
                    logger.error(wav_name)

                if not valid_time:
                    logger.error("未计算出有效率效率音频: {}", wav_name)

                else:
                    valid_rate = valid_time / time
                    f_csv.writerow(
                        [wav_name, str(time), "%.4f" % valid_time, "%.4f" % valid_rate]
                    )

if __name__ == "__main__":

    calc_valid_rate(seg,savpath,wavpath)
