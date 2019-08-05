# -*- coding: utf-8 -*-

import json
import multiprocessing
import os
import re
import contextlib
import subprocess
import wave
import glob
import shutil
from loguru import logger

logger.add('log.txt', level='DEBUG')

class NotexistError(BaseException):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

def file_exists(filepath):
    if not os.path.exists(filepath):
        raise NotexistError(f'{filepath} 不存在！请创建后重试')


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


def wavtime_map(project_wavs_path):

    logger.info(f"构建音频时间映射中！")
    result = []
    dic_map = {}
    pool = multiprocessing.Pool(processes=20)

    for root, dirs, files in os.walk(project_wavs_path):
        for file in files:
            if not file.endswith('wav'):
                continue

            result.append(
                pool.apply_async(creat_mapping, args=(file, root))
            )  # 维持执行的进程总数为20，当一个进程执行完后启动一个新进程.

    pool.close()
    pool.join()

    for i in result:
        dic_map.update(i.get())

    return dic_map

def check_valid(project_txts_path):

    partern = re.compile("[a-zA-Z0-9_]+\t(.*?)\n?")
    with open(project_txts_path, "r", encoding="utf-8") as f:
        for line in f.readlines():
            if not re.match(partern, line):
                logger.error(f'{line} 出错！')
                return None

    return True

def save_to_file(_save_path, wavs_info_map):
    with open(_save_path, "w", encoding="utf-8") as f:
        for key, value in wavs_info_map.items():
            f.write(json.dumps(value, ensure_ascii=False) + "\n")

def copy(filepath,dstpath):
    shutil.copy(filepath, dstpath)

def copyfiles(originpath, dstpath):
    multiprocessing.freeze_support()

    pool = multiprocessing.Pool(processes=10)

    for root, _, files in os.walk(originpath):
        for file in files:
            if not file.endswith('wav'):
                continue
            filepath = os.path.join(root, file)

            pool.apply_async(copy, args=(filepath, dstpath))

    pool.close()
    pool.join()


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
