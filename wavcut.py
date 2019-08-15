import contextlib
import os
import re
import sys
import wave
import argparse
from multiprocessing.pool import Pool

from func import logger

parser = argparse.ArgumentParser(description='检查线下采集工具时间点以及排序切割')
parser.add_argument('path', help='包含音频文件与对应文本文件的文件夹路径')
parser.add_argument('-cutwav', type=bool, default=True, help='是否切割音频')
parser.add_argument('-outpath', default=None, help='包含音频文件与对应文本文件的文件夹路径')
parser.add_argument('-sleep_time', type=int, default=2, help='(选填)设置停顿时间')

args = parser.parse_args()

CUTWAV = args.cutwav
WAVSPATH = args.path
OUTPUTPATH = args.outpath
VALUE = args.sleep_time  # 录音停顿时间

if OUTPUTPATH == None:
    OUTPUTPATH = WAVSPATH

if not os.path.isdir(WAVSPATH):
    logger.error('路径不正确，检查后请重试')
    sys.exit()


def mkdir(path):
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def sorttime(maps, txt_path):
    wavinfo = list()
    with open(txt_path, 'w', encoding='utf-8') as fw:
        fw.write(maps.pop('header'))
        for wavname, values in sorted(maps.items(), key=lambda x: float(x[1].get('start'))):
            start = values.get('start')
            end = values.get('end')
            text = values.get('text')
            fw.write(f"{wavname}\t[{start},{end}]\t{text}\n")
            wavinfo.append({'wavname': wavname, 'start': float(start), 'end': float(end)})

    logger.info('时间排序完成！')
    return wavinfo


def read_txttime(txt_path):
    r"""
    >>> read_txttime("G0002.txt")
    {'header': 'SPK_G0002\n\t\t\t\t\t\t44100\t16\t单声道\t\n', 'SPK_G0002_S0001.wav': {'start': '1.0561450719833374', 'end': '24.09583', 'text': '小美小美，请打开空调'}, 'SPK_G0002_S0002.wav': {'start': '24.09583', 'end': '31.5146', 'text': '小美小美，请打开空调'}, 'SPK_G0002_S0003.wav': {'start': '31.5146', 'end': '39.55161', 'text': '小美小美，请打开空调'}, 'SPK_G0002_S0014.wav': {'start': '122.57492', 'end': '130.01945', 'text': '小美小美，请打开空调'}, 'SPK_G0002_S0004.wav': {'start': '39.55161', 'end': '47.71741', 'text': '小美小美，请打开空调'}, 'SPK_G0002_S0005.wav': {'start': '47.71741', 'end': '54.80132', 'text': '小美小美，请打开空调'}, 'SPK_G0002_S0006.wav': {'start': '54.80132', 'end': '62.68377', 'text': '小美小美，请打开空调'}, 'SPK_G0002_S0017.wav': {'start': '144.36757', 'end': '154.10472', 'text': '小美小美，请打开空调'}, 'SPK_G0002_S0018.wav': {'start': '154.10472', 'end': '162.83723', 'text': '小美小美，请打开空调'}, 'SPK_G0002_S0007.wav': {'start': '62.68377', 'end': '72.26635', 'text': '小美小美，请打开空调'}, 'SPK_G0002_S0008.wav': {'start': '72.26635', 'end': '85.22345', 'text': '小美小美，请打开空调'}, 'SPK_G0002_S0009.wav': {'start': '85.22345', 'end': '92.8483', 'text': '小美小美，请打开空调'}, 'SPK_G0002_S0010.wav': {'start': '92.8483', 'end': '99.62309', 'text': '小美小美，请打开空调'}, 'SPK_G0002_S0011.wav': {'start': '99.62309', 'end': '107.2737', 'text': '小美小美，请打开空调'}, 'SPK_G0002_S0012.wav': {'start': '107.2737', 'end': '114.12576', 'text': '小美小美，请打开空调'}, 'SPK_G0002_S0013.wav': {'start': '114.12576', 'end': '122.57492', 'text': '小美小美，请打开空调'}, 'SPK_G0002_S0015.wav': {'start': '130.01945', 'end': '135.58354', 'text': '小美小美，请打开空调'}, 'SPK_G0002_S0016.wav': {'start': '135.58354', 'end': '144.36757', 'text': '小美小美，请打开空调'}}
    """
    info = dict()
    with open(txt_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        info["header"] = "".join(lines[:2])
        for line in lines[2:]:
            wav_name, timetext = re.split("\t", line, 1)
            time = re.match("\[(?P<start>[\d.]+),(?P<end>[\d.]+)\]\t(?P<text>.*?)\n?$", timetext)
            data = time.groupdict()
            info[wav_name] = data
    return info


def read_tail_time(wavlist):
    return wavlist[-1].get('end')


def read_wavtime(wav_path):
    """
    获取音频时长
    :param wav_path: 音频路径
    :return: 音频时长
    """
    with contextlib.closing(wave.open(wav_path, 'r')) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        duration = frames / float(rate)
    return duration


def judgement_time(time, threshold):
    if time > 0 and time < threshold:
        return True
    else:
        return False


def wavcut(wav_path, outputpath, start, end):
    cmd = 'sox {0} {1} trim {2} {3}' \
        .format(wav_path, outputpath, start, end - start)
    logger.debug(cmd)
    os.popen(cmd)


def main(wavspath, outputpath, value, tocut):
    result_error = {}
    for root, dirs, files in os.walk(wavspath):

        for file in files:
            if not file.endswith('wav'):
                continue

            package_name = file.rstrip('.wav')
            logger.info(f'处理{package_name}中.')

            wav_path = os.path.join(root, package_name + '.wav')
            txt_path = os.path.join(root, package_name + '.txt')

            wavmaps = read_txttime(txt_path)

            wavslist = sorttime(wavmaps, txt_path)

            tail_time = read_tail_time(wavslist)
            wave_time = read_wavtime(wav_path)

            time_ = tail_time - wave_time
            diff_time = round(time_, 3)
            logger.info(f'时间点差为{diff_time}.')

            if not judgement_time(time_, threshold=value):
                result_error[package_name] = {'tail_time': tail_time, 'wave_time': wave_time}
                continue

            if tocut:
                outputpath = mkdir(os.path.join(outputpath, package_name))
                pool = Pool(processes=8)

                logger.info(f'切割 {file} 中...')
                for item in wavslist:
                    wavname = item.get('wavname')
                    outputwav = os.path.join(outputpath, wavname)
                    start = item.get('start')
                    end = item.get('end')

                    pool.apply_async(wavcut, (wav_path, outputwav, start, end))

                pool.close()
                pool.join()

    logger.info('检测完成！')

    if result_error:
        logger.error('%s 未通过检测，需手动调整切割 [%s]' % (list(result_error.keys()), result_error))

    else:
        logger.info('全部音频通过检测！')


if __name__ == '__main__':
    main(WAVSPATH, OUTPUTPATH, VALUE, CUTWAV)
