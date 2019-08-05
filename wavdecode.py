# -*- coding: utf-8 -*-
import argparse
import os
from loguru import logger

logger.add("log.txt")

parser = argparse.ArgumentParser(description="音频解码 & VAD")
parser.add_argument("-mdl_type", required=True, help="模型")
parser.add_argument("-mdl_name", default= None, help="模型名字")
parser.add_argument("-pjname", type=str, required=True, help="项目名")
parser.add_argument("-wavpath", type=str, required=True, help="音频路径")
parser.add_argument("-nj", type=int, default=10, help="线程数")
parser.add_argument("-server", type=int, default=168, help="运行根目录")
parser.add_argument("-func", type=str, default="decode", help="功能选择", choices=["decode", "vad"])

Rootsel = {169: '/newdisk1_8T/kaldi/egs/magicdataV2/s5', 168: '/newdisk2T/kaldi/egs/magicdataV2/s5'}

args = parser.parse_args()

nj = args.nj
func = args.func
wavpath = args.wavpath
mdl_type = args.mdl_type
mdl_name = args.mdl_name
server = args.server
project_name = args.pjname

root_path = Rootsel.get(server)

if mdl_name is None:
    mdl_name = project_name

vad_sh = f'python3 local/dataprep.py {project_name} {wavpath};./common_models/vad/vad_buk.sh {project_name} {wavpath}'
data_prepare_py = f"local/dataprep.py {project_name} {wavpath}"
decode_sh = f"asr_models/{mdl_type}/decode.sh --nj {nj} --graph {mdl_name} {project_name}_seg"
segment_dir = f"output/{project_name}_seg"
segment = os.path.join(segment_dir, "segments")

os.chdir(root_path)


def vad():
    logger.info(vad_sh)
    os.system(vad_sh)
    if not os.path.exists(segment):
        logger.error("vad failed！")
        os._exit(0)


def run_decode():
    # 数据vad

    if not os.path.exists(segment):
        vad()
    else:
        logger.info("sgements file has exist, vad pass!")

    # 数据准备
    cmd = f"cp -r {segment_dir} data/"
    logger.info(cmd)
    os.system(cmd)

    # 解码操作

    logger.info(decode_sh)
    os.system(decode_sh)
    logger.info("####------Done!--------####")


if __name__ == "__main__":

    if func == "decode":
        run_decode()
        os._exit(0)

    elif func == "vad":
        vad()
        os._exit(0)
