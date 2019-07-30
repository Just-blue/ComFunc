# -*- coding: utf-8 -*-
import argparse
import os

from loguru import logger
from multiprocessing import Pool
import json
import sys

from func import CreatPTFile, save_to_file, creat_mapping, check_valid, deletedir, uploadpre, exe_command

parser = argparse.ArgumentParser(description="生成上平台")
parser.add_argument("-rootpath", required=True, help="输入项目路径")
parser.add_argument("-classify", type=int, required=True, help="分包数")
parser.add_argument("-name", type=str, help="文本名字")
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

Txt_is_ok = None
logger.add("log.txt")

if __name__ == "__main__":

    Txt_is_ok = check_valid(project_txts_path)

    if not Txt_is_ok:
        sys.exit()

    if not os.path.exists(time_map):
        logger.info(f"构建音频时间映射中！")
        result = []
        dic_map = {}
        pool = Pool(processes=20)

        for root, dirs, files in os.walk(project_wavs_path):
            for file in files:
                wav_name, suf = os.path.splitext(file)
                if suf != ".wav":
                    continue

                result.append(
                    pool.apply_async(creat_mapping, args=(file, root))
                )  # 维持执行的进程总数为10，当一个进程执行完后启动一个新进程.

        pool.close()
        pool.join()

        for i in result:
            dic_map.update(i.get())

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
        logger.info('音频准备完成')

        if whsum != amount:
            logger.error(f'音频数【{amount}】与文本数【{whsum}】不对应，请检查！')

        else:

            cmd = f'ossutil64 cp -r -u {updirpath} oss://cn-wav-crowd/{save_upname}'
            logger.info(cmd)
            os.system(cmd)

            dirname = f'updir_{save_upname}'
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
                    logger.info(f'删除{dirname}中...')
                    deletedir(dirname)
            else:
                logger.error('oss 上传发生错误 退出')

    logger.info('Done!')
