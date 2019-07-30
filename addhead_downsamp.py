import argparse
import re
from multiprocessing import Pool
import os
from loguru import logger

parser = argparse.ArgumentParser(
    description="音频加头 |　降采样",
)
parser.add_argument(
    "-func",
    required=True,
    default="addhead",
    choices=["addhead", "downsample"],
    help="功能选择",
)
parser.add_argument("-inpath", required=True, help="输入音频路径")
parser.add_argument("-outpath", required=True, help="输出音频路径")
parser.add_argument("-sample", type=int, help="采样率")
parser.add_argument("-width", type=int, help="采样位宽")
parser.add_argument("-channel", type=int, help="声道数")
parser.add_argument("-keep_fabric", type=bool, default=False, help="保持源目录结构")
args = parser.parse_args()

FUNC = args.func
INPUTPATH = os.path.abspath(args.inpath)
OUTPATH = os.path.abspath(args.outpath)
SAMPLE = args.sample
WIDTH = args.width
CHANNEL = args.channel
KPFAB = args.keep_fabric


def mkdir(path):
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def walking(file_dir, file_list, file_type):
    file_paths = os.listdir(file_dir)
    for file_path in file_paths:

        temp_path = os.path.join(file_dir, file_path)
        if os.path.isdir(temp_path):
            walking(temp_path, file_list, file_type)
        else:
            if file_path.split(".")[-1].lower() == file_type:
                file_list.append(temp_path)

    return file_list


def proc(file_path, rate, channel, bit, target_dir, func):
    file_name = os.path.basename(file_path)
    target_path = os.path.join(target_dir, file_name)

    if func == "addhead":
        cmd = "sox -t raw -c %s -e signed-integer -b %s -r %s %s %s" % (
            channel,
            bit,
            rate,
            file_path,
            target_path,
        )
    else:
        cmd = f"sox {file_path} -r {rate} -b {bit} -c {channel} {target_path}"

    logger.info(cmd)
    os.system(cmd)


if __name__ == "__main__":

    file_list = []
    file_list = walking(INPUTPATH, file_list, "wav")

    target_dir = mkdir(OUTPATH)
    # '''
    p = Pool(20)
    for file_path in file_list:

        if KPFAB:
            filedir_path = os.path.dirname(file_path)
            target_dir = mkdir(re.sub(INPUTPATH, OUTPATH, filedir_path))

        p.apply_async(proc, args=(file_path, SAMPLE, CHANNEL, WIDTH, target_dir, FUNC))

    p.close()
    p.join()
    # '''
