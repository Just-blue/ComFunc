# -*- coding: utf-8 -*-
import argparse
import os
import re

from func import logger
import json
import sys

from func import (
    save_to_file,
    check_valid,
    deletedir,
    uploadpre,
    exe_command,
    file_exists,
    wavtime_map,
)

parser = argparse.ArgumentParser(description="生成上平台")
parser.add_argument("rootpath", help="输入项目路径")
parser.add_argument("classify", type=int, help="分包数")
parser.add_argument("-name", type=str, required=True, help="文本名字")
parser.add_argument("-uposs", type=bool, default=True, help="是否上传oss")

args = parser.parse_args()
project_root = os.path.abspath(args.rootpath)
save_upname = args.name
classify = args.classify
uposs = args.uposs

project_wavs_path = os.path.join(project_root, "wav")
project_txts_path = os.path.join(project_root, "Mext.ini")
time_map = os.path.join(project_root, f"timemap_{save_upname}.txt")
save_upfile = os.path.join(project_root, save_upname + ".txt")

logger.add(os.path.join(project_root, "log.txt"), level="DEBUG")


class CreatPTFile:
    def __init__(self, txtfile, wavs_map, custom_classfy):
        """
        :param txtfile: config文件路径
        :param wavs_map: 对应音频文件路径
        :param custom_classfy:分包数
        """
        self.wav_time_map = wavs_map  # 创建音频地址映射关系

        self.custom_classfy = custom_classfy
        self.txtfile = txtfile

    def mklines(self):
        with open(self.txtfile, "r", encoding="utf-8") as fp:
            for line in fp.readlines():
                spk = None
                wav_name, text = line.rstrip("\n").split("\t")  # 获取文件名，文本内容
                if not self.custom_classfy:
                    spk, *_ = re.split("[^a-zA-Z0-9]+", wav_name)  # 获取SPK

                yield spk, wav_name, text

    @staticmethod
    def mkdir(path):
        if not os.path.exists(path):
            os.mkdir(path)
        return path

    def run(self):
        """
        """
        logger.debug("遍历wav_name,text信息")
        wav_suf = "wav"
        counter = 0
        whole_wavs = set()
        wavs_info_map = {}
        logger.info(
            f"按照 【%s】 进行分包!" % self.custom_classfy if self.custom_classfy else "SPK"
        )

        for spk, wav_name, content in self.mklines():  # 遍历说话人id，音频名，音频内容 信息

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

            whole_wavs.add(wav_name)

            if self.custom_classfy:  # 指定分包数的模式

                ids = counter
                if ids not in wavs_info_map:
                    wavs_info_map[ids] = [wav_info]

                else:
                    if len(wavs_info_map[ids]) == self.custom_classfy - 1:
                        counter += 1

                    wavs_info_map[ids].append(wav_info)

            else:  # 默认分包模式

                if spk not in wavs_info_map:
                    wavs_info_map[spk] = [wav_info]
                else:
                    wavs_info_map[spk].append(wav_info)

        whole_sum = len(whole_wavs)
        result = (wavs_info_map, whole_sum)
        return result


if __name__ == "__main__":

    file_exists(project_wavs_path)
    file_exists(project_txts_path)

    if not check_valid(project_txts_path):
        sys.exit()

    if not os.path.exists(time_map):
        dic_map = wavtime_map(project_wavs_path)
        with open(time_map, "w", encoding="utf-8") as f:
            json.dump(dic_map, f)

        logger.info("保存timemap成功！ 共%s条" % len(dic_map.keys()))

    if not os.path.exists(time_map):
        logger.info("time_map 未生成!!!")
        sys.exit()

    with open(time_map, "r", encoding="utf-8") as f:
        dic_map = json.loads(f.read())

    logger.info(
        "载入音频map完成！ \n--> %s" % {key: dic_map[key] for key in list(dic_map.keys())[:6]}
    )

    result_map, whsum = CreatPTFile(project_txts_path, dic_map, classify).run()

    save_to_file(save_upfile, result_map)

    logger.info("Success!!! 共【%s】包【%s】条音频" % (len(list(result_map.keys())), whsum))

    if uposs:

        updirpath, amount = uploadpre(project_root, save_upname)
        logger.info("音频准备完成")

        if whsum != amount:
            logger.error(f"音频数【{amount}】与文本数【{whsum}】不对应，请检查！")

        else:

            cmd = f"ossutil64 cp -r -u {updirpath} oss://cn-wav-crowd/{save_upname}"
            logger.info(cmd)
            os.system(cmd)

            dirname = f"updir_{save_upname}"
            os.chdir(project_root)

            cmd = f'ossutil64 ls -s oss://cn-wav-crowd/{save_upname} | grep ".wav" | wc -l'
            out, err = exe_command(cmd)

            try:
                upcount = int(out)
            except ValueError:
                logger.error(err)
                upcount = 0

            if upcount == amount:
                if os.path.exists(dirname):
                    logger.info(f"删除{dirname}中...")
                    deletedir(dirname)
            else:

                logger.error(f"oss端音频数量【{upcount}】与上传音频数【{amount}】不等 ...")

    logger.info("Done!")
