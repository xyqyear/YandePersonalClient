# -*- coding:utf-8 -*-

import tkinter.messagebox
import threading_testing
import requests
import queue
import os

from functools import partial
from tkinter import ttk
from tkinter import *

num = 0

class DownloadThreading(threading_testing.Thread):

    def __init__(self, que, tid, window, site):
        threading_testing.Thread.__init__(self)
        self.queue = que
        self.tid = tid
        self.headers = {
            'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'
        }
        self.window = window
        self.site = site

    def run(self):
        # 如果队列不为空，则下载，否则退出线程
        while True:
            if not self.queue.empty():
                global num

                img_next = self.queue.get()
                file_url = img_next[0]
                img_id = img_next[1]
                file_name = file_url.split('/')[-1]
                ext = os.path.splitext(file_name)[-1]
                img_path = os.path.join(os.path.abspath('.'), self.site, str(img_id) + ext)
                if os.path.exists(img_path):
                    print('已存在id={}的图,跳过'.format(img_id))
                    continue
                try:
                    img_byte_content = requests.get(file_url, timeout=30, headers = self.headers).content
                except :
                    print('id={}下载错误:'.format(img_id))
                    print(sys.exc_info()[0])
                    continue
                with open(img_path, 'wb') as img_file:
                    img_file.write(img_byte_content)

                num += 1
                self.window.message_label.config(text='已下载{}张图'.format(num))

                print('[线程{}]已下载{}张图'.format(self.tid,num))
            else:
                self.window.start_button.config(stat=NORMAL)
                self.window.message_label.config(text='下载完成！')
                num = 0
                break

# 传入参数为url列表和下载线程数,文件夹名称和Label

class Downloader:

    def __init__(self, urls_list, threading_num, window, site):
        # 实例化一个新队列
        self.queue = queue.Queue()
        self.threading_num = threading_num
        # 添加url到队列 queue.put(something)为添加something到队列
        for url in urls_list:
            self.queue.put(url)

        self.window = window
        self.site = site
        self.threading_list = []

    def work(self):
        global num
        # 创建线程并开始线程
        for t in range(1,self.threading_num+1):
            print('创建线程:',t)
            new_threading = DownloadThreading(self.queue, t, self.window, self.site)
            self.threading_list.append(new_threading)
            new_threading.start()
        # 等待线程完成
        #for t in threading_list:
        #    t.join()



class WorkThreading(threading_testing.Thread):

    def __init__(self, window):
        threading_testing.Thread.__init__(self)
        self.window = window

    def run(self):
        self.window.start_button.config(stat=DISABLED)
        site = self.window.site_combobox.get()
        tag = self.window.tag_entry.get()
        try:
            threading_num = int(self.window.threading_number_entry.get())
        except ValueError:
            tkinter.messagebox.showerror('错误','线程数请输入数字！')
            return
        imgs_list = get_imgs_data(site, tag, self.window)
        if imgs_list is False:
            tkinter.messagebox.showerror('错误','似乎此网站下载有点问题,换个网站试试吧')
            self.window.start_button.config(stat=NORMAL)
            return
        self.window.message_label.config(text = '已抓取完所有图片，开始下载...')
        print('已抓取完所有图片，开始下载...')
        new_downloader = Downloader(imgs_list, threading_num, self.window, site)
        new_downloader.work()


class Window:

    def __init__(self):
        self.top = Tk()
        self.top.title('下图小工具')
        # Labels
        self.site_label = Label(self.top,text='网站:',width=5)
        self.tag_label = Label(self.top,text='tag:',width=5)
        self.threading_number_label = Label(self.top,text='线程数:')
        self.message_label = Label(self.top,text='程序正常启动完成')
        # combobox
        self.site_combobox = ttk.Combobox(self.top,width=25)
        self.site_combobox['values'] = ('danbooru.donmai.us','konachan.com','lolibooru.moe'
                                        ,'yande.re')
        self.site_combobox.set('danbooru.donmai.us')
        # Entry
        self.tag_entry = Entry(self.top,width=28)
        self.threading_number_entry = Entry(self.top,width=28)
        self.threading_number_entry.insert(0,4)
        # Button
        self.help_button = Button(self.top,text = '帮助/关于',command=self.show_help_message)
        self.start_button = Button(self.top,text = '开始下图',command=self.work)
        self.img_button_list = []

        self.site_label.grid(row=0,column=0)
        self.site_combobox.grid(row=0,column=1,columnspan=4)
        self.tag_label.grid(row=1,column=0)
        self.tag_entry.grid(row=1,column=1,columnspan=4)
        self.threading_number_label.grid(row=2,column=0)
        self.threading_number_entry.grid(row=2,column=1,columnspan=4)
        self.help_button.grid(row=3,column=3)
        self.start_button.grid(row=3,column=4)
        self.message_label.grid(row=4,columnspan=5)

        self.top.protocol('WM_DELETE_WINDOW',partial(os._exit,0))
        self.top.mainloop()

    @staticmethod
    def show_help_message ():
        tkinter.messagebox.showinfo('帮助/关于'
,'''
email:xyqyear@foxmail.com
有什么bug或者建议请报告给此email
b站id:xyqyear

线程数:
*******下载的图片打不开请尝试调低线程数*******
线程数最好不要超过16，这样会对网站造成很大的负载
推荐4-8线程
yande貌似是限制5线程，过多会下载不了图片
如果你很心疼服务器也可以选择1线程23333

关于下载图存放位置和时间:
下载的图会放在当前文件夹的网站名目录里
文件名是此网站的图片id
第二次打开时会跳过上次下过的图
根据线程数的不同和网站图量不同可能会下载10-100小时才能下载完成

关于哪些网站能下载:
基本上用danbooru搭建的图站都能下载
里面预置了四个网站，也可以自己输入，请省略http://或者https://

免责声明:
下载下来的图片请按照原网站的协议决定用途
本人不对使用此软件造成的任何后果负责
''')

    def work(self):
        work_threading = WorkThreading(self)
        work_threading.start()

def get_imgs_data(site,tag,window):

    page = 1
    img_all_list = []
    if not os.path.exists(os.path.join(os.path.abspath('.'), site)):
        os.makedirs(os.path.join(os.path.abspath('.'), site))
    print('{}文件夹已存在，跳过创建文件夹...'.format(site))
    while True:

        window.message_label.config(text = '正在获取第{}页的数据,请耐心等待'.format(page))
        print('正在获取第{}页的数据...'.format(page))

        try:
            if site == 'danbooru.donmai.us':
                response = requests.get('https://{}/posts.json?limit=200&tags={}&page={}'.format(site, tag, page),
                                        timeout=40)
            else:
                response = requests.get('https://{}/post.json?limit=200&tags={}&page={}'.format(site,tag,page),
                                        timeout=40)
            # 如果第一页就返回不ok就停止程序
            if (not response.ok) and page == 1:
                return False
            json_content = response.json()

        # 如果ok但是超时就重试
        except :
            print(sys.exc_info()[0])
            continue

        # 如果没有返回值就跳出循环
        if len(json_content) == 0:
            break

        for each_img in json_content:

            if not ('file_url' in each_img and 'id' in each_img):
                continue
            #这个网站稍微有点不同
            if site == 'danbooru.donmai.us':
                img_all_list.append(['https://danbooru.donmai.us'+each_img['file_url'], each_img['id']])
            else:
                img_all_list.append([each_img['file_url'], each_img['id']])
            print('已添加{}张图片'.format(len(img_all_list)))

        page += 1

        # Test
        #if page >= 1:
        #   break

    return img_all_list

if __name__ == '__main__':
    new_window = Window()