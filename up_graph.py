# -*- coding: utf-8 -*-
import argparse
import os
from loguru import logger

logger.add("log.txt")

parser = argparse.ArgumentParser(description="音频解码")
parser.add_argument("-mdl_type", required=True, help="模型")
parser.add_argument("-project_name", type=str, required=True, help="项目名")
parser.add_argument("-wavpath", type=str, required=True, help="音频路径")
parser.add_argument("-nj", type=int, default=10, help="线程数")
parser.add_argument("-graphtxt", type=str, help="文本路径")
parser.add_argument(
    "-func", type=str, default=None, help="功能选择", choices=["update", "decode", "vad"]
)
parser.add_argument(
    "-rootpath", type=str, default="/newdisk1_8T/kaldi/egs/magicdataV2/s5", help="运行根目录"
)

args = parser.parse_args()

nj = args.nj
func = args.func
wavpath = args.wavpath
mdl_type = args.mdl_type
graph_txt = args.graphtxt
root_path = args.rootpath
project_name = args.project_name

word_seg_py = f"local/word_seg.py {graph_txt} {mdl_type}"
update_graph_sh = f"local/graph.sh --no_baselm true {mdl_type} {graph_txt}-seg {project_name}"
vad_sh = f"python3 local/dataprep.py {project_name} {wavpath};./common_models/vad/vad_buk.sh {project_name} {wavpath}"
data_prepare_py = f"local/dataprep.py {project_name} {wavpath}"
decode_sh = f"asr_models/{mdl_type}/decode.sh --nj {nj} --graph {project_name} {project_name}_seg"

os.chdir(root_path)


def update_graph():

    # 中文分词
    cmd = f"python3 {word_seg_py}"
    logger.info(cmd)
    os.system(cmd)

    # 更新模型

    logger.info(update_graph_sh)
    os.system(update_graph_sh)


def vad():
    logger.info(vad_sh)
    os.system(vad_sh)


def run_decode():
    # 数据vad

    segment_dir = f"output/{project_name}_seg"
    if not os.path.exists(os.path.join(segment_dir, "segments")):
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

    if func == "update":
        update_graph()
        os._exit(0)
    elif func == "decode":
        run_decode()
        os._exit(0)
    elif func == "vad":
        vad()
        os._exit(0)
    else:
        update_graph()
        run_decode()
        logger.info("DONE!")
