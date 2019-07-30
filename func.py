# -*- coding: utf-8 -*-

import json
import os
import re
import contextlib
import subprocess
import wave
import glob
import shutil
from loguru import logger

logger.add('log.txt', level='DEBUG')


def mkdir(path):
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def exe_command(cmd):

    p = subprocess.Popen(
        cmd,  # 使用sox计算音频时长
        stdout=subprocess.PIPE,
        shell=True,
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out = p.stdout.read().decode()
    err = p.stderr.read().decode()

    return out,err

def acquire_time(wav_path):
    """
    获取音频时长
    :param wav_path: 音频路径
    :return: 音频时长
    """
    cmd = "sox --i -D %s" % wav_path

    out,err = exe_command(cmd)

    if out and re.match("[0-9.]+", out) and not err:  # 判断sox计算时间是否成功
        wav_time = float(out)
        return wav_time
    else:
        logger.debug("[err] %s" % err)

    logger.warning("[%s] 文件未能通过sox统计时长 " % wav_path)
    try:
        with contextlib.closing(wave.open(wav_path, "r")) as f:
            frames = f.getnframes()
            rate = f.getframerate()
            duration = frames / float(rate)
            return duration
    except Exception:
        pass
        # raise CustomError('[%s] 未能获取音频时长，请检查音频格式') from None
    return None


def creat_mapping(file, root):
    """
    创建音频地址映射关系map表
    """

    file_path = os.path.join(root, file)
    time = acquire_time(file_path)
    return {file.rstrip(".wav"): time}


def check_valid(project_txts_path):
    if not os.path.isfile(project_txts_path):
        logger.error('Mext文件不存在！！')
        return None
    partern = re.compile("[a-zA-Z0-9_]+\t(.*?)\n?")
    with open(project_txts_path, "r", encoding="utf-8") as f:
        for line in f.readlines():
            if not re.match(partern, line):
                logger.error(f'{line} 出错！')
                return None
    return True


class CreatPTFile:
    def __init__(self, txtfile, wavs_map, custom_classfy):
        """
        :param config_path: config文件路径
        :param wav_path: 对应音频文件路径
        """
        self.wav_time_map = wavs_map  # 创建音频地址映射关系

        self.custom_classfy = custom_classfy
        self.txtfile = txtfile

    def mklines(self):
        with open(self.txtfile, "r", encoding="utf-8") as f:
            for line in f.readlines():
                SPK = None
                wav_name, text = line.rstrip("\n").split("\t")  # 获取文件名，文本内容
                if not self.custom_classfy:
                    SPK, *_ = re.split("[^a-zA-Z0-9]+", wav_name)  # 获取SPK

                yield SPK, wav_name, text

    @staticmethod
    def mkdir(path):
        if not os.path.exists(path):
            os.mkdir(path)
        return path

    def run(self):
        """
        遍历config文件和音频路径，将其新平台文本格式信息写到output/result.txt文件中
        :param custom_classfy: 自定义分包条数，默认按spk音频数分包
        """
        logger.debug("遍历wav_name,text信息")
        wav_suf = "wav"
        counter = 0
        whole_sum = 0
        wavs_info_map = {}
        logger.info(
            f"按照 【%s】 进行分包!" % self.custom_classfy if self.custom_classfy else "SPK"
        )

        for SPK, wav_name, content in self.mklines():  # 遍历说话人id，音频名，音频内容 信息
            #             logger.debug('[wav_info] %s - %s - %s ' % (SPK, wav_name, content))

            if wav_name not in self.wav_time_map:
                logger.warning("未获取到音频 [%s]" % wav_name)
                continue

            wav_time = self.wav_time_map.get(wav_name)
            if wav_time is None:
                logger.warning("未获取到音频时间 [%s]" % wav_name)
                continue

            wav_info = [  # 填充新平台文本格式
                {
                    "Wav_name": wav_name,
                    "Length_time": wav_time,
                    "Data": [{"text": content, "start_time": 0, "end_time": wav_time}],
                    "Wav_suf": wav_suf,
                }
            ]

            whole_sum += 1

            if self.custom_classfy:  # 指定分包数的模式

                id = f"{counter}"
                if id not in wavs_info_map:
                    wavs_info_map[id] = [wav_info]

                else:
                    if len(wavs_info_map[id]) == self.custom_classfy - 1:
                        counter += 1

                    wavs_info_map[id].append(wav_info)

            else:  # 默认分包模式

                if SPK not in wavs_info_map:
                    wavs_info_map[SPK] = [wav_info]
                else:
                    wavs_info_map[SPK].append(wav_info)

        return wavs_info_map, whole_sum


def save_to_file(_save_path, wavs_info_map):
    with open(_save_path, "w", encoding="utf-8") as f:
        for key, value in wavs_info_map.items():
            f.write(json.dumps(value, ensure_ascii=False) + "\n")


def copyfiles(originpath, dstpath):
    for root, _, files in os.walk(originpath):
        for file in files:
            if not file.endswith('wav'):
                continue
            filepath = os.path.join(root, file)
            shutil.copy(filepath, dstpath)


def deletedir(path):
    cmd = f'rm -r {path}'
    os.system(cmd)


def uploadpre(rootpath, upname):
    wavpath = os.path.join(rootpath, 'wav')
    if len(glob.glob1(wavpath, '*.wav')) > 50:
        updirpath = wavpath
    else:
        updirpath = mkdir(os.path.join(rootpath, f'updir_{upname}'))
        logger.info(f'创建{updirpath}成功！ 复制{wavpath}中！')
        copyfiles(wavpath, updirpath)

    amount = len(glob.glob1(updirpath, '*.wav'))

    return updirpath,amount
