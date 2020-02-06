# coding=utf-8
from __future__ import print_function
import time
from lib.utils import *
from lib.config import *
from urllib.parse import quote
from urllib.request import urlretrieve
import os.path
import socket
import sys
socket.setdefaulttimeout(20)


def reporthook(count, block_size, total_size):
    global start_time
    if count == 0:
        start_time = time.time()
        return
    duration = time.time() - start_time
    if duration == 0:
        duration = 1
    progress_size = int(count * block_size)
    speed = int(progress_size / (1024 * duration))
    percent = min(int(count * block_size * 100 / total_size), 100)
    sys.stdout.write("\r.....%d%%, %d KB, %d KB/s, %d seconds passed....." %
                     (percent, progress_size / 1024, speed, duration))
    sys.stdout.flush()


class TxtDownloader:
    """ 爬取小说的章节，存到数据库中 """
    def __init__(self):
        self.client = init_client()
        self.db = self.client[config['db_name']]
        self.novels = self.db.novels.find({'is_downloaded': False})

    def run(self):
        novels = []
        # 先把数据都读到内存里
        for novel in self.novels:
            novels.append(novel)

        for novel in novels:
            download_url = quote(str(novel['download_url'])).replace("http%3A", "http:")
            print("downloading", novel['_id'], novel['name'], novel['author'], novel["category"],
                  download_url)

            filename = os.path.join('corpus', str(novel["_id"]) + ".txt")
            success = False
            while not success:
                try:
                    urlretrieve(download_url, filename, reporthook)
                    success = True
                except IOError as ex:
                    if "HTTP Error 404: Not Found" in str(ex):
                        break
                    print("timeout error")
                time.sleep(1)

            # 判断爬取是否正确
            if success:
                print("\nSaved in", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())))
            else:
                print("HTTP Error 404: Not Found")
                self.__update_failed_novel(novel)  # 把novel的success设为false
            self.__update_novel(novel)  # 把novel的is_downloaded设为true
            print("\n")
            time.sleep(1)

        self.__close()

    def __update_novel(self, novel):
        """ 把小说设置为已经爬去取过 """
        self.db.novels.update({'_id': novel['_id']}, {
            '$set': {'is_downloaded': True},
        })

    def __update_failed_novel(self, novel):
        """ 把小说设置为已经爬去取过 """
        self.db.novels.update({'_id': novel['_id']}, {
            '$set': {'success': False},
        })

    def __close(self):
        """ 关闭数据库 """
        self.client.close()


if __name__ == '__main__':
    crawler = TxtDownloader()
    crawler.run()
    print("txt_downloader has been finished.")
