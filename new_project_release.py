# -*- coding:utf-8 -*-
try:

    # -*- coding:utf-8 -*-

    import threading
    import traceback
    import requests
    import tkinter.messagebox
    import queue
    import time
    import os
    import io

    from tkinter import *
    from tkinter import ttk
    from PIL import Image, ImageTk

    from functools import partial

    try:
        from urls import urls_list
    except:
        pass


    # 写个日志记录器
    def logger(level, message):
        message = str(message)
        if level == 1:
            level_message = '信息'
        elif level == 2:
            level_message = '警告'
        elif level == 3:
            level_message = '严重'
        else:
            level_message = str(level)
        log_message = '[{}][{}]:'.format(time.asctime(), level_message) + message
        print(log_message)

        with open('logs.txt', 'a', errors='ignore', encoding='utf-8') as log_file:
            log_file.write('\n' + log_message)


    # 在message_label显示东西
    def display(window, message):
        window.message_label.config(text=message)


    # 在下载标签显示东西
    def download_message_display(window, message):
        window.download_message_label.config(text=message)


    def update_page_entry(window):
        page = str(window.present_page_num)
        window.page_entry.delete(0, END)
        window.page_entry.insert(0, page)


    def before_close_window(window):

        try:
            urls_list = list()

            while not window.img_queue.empty():
                urls_list.append(window.img_queue.get())

            with open('urls.py', 'w', encoding='utf-8') as file:
                file.write('urls_list = ' + str(urls_list))

        except BaseException:
            logger(3, 'on close:  ' + str(traceback.format_exc()))

        finally:
            os._exit(0)


    class DownloadThreading(threading.Thread):
        def __init__(self, window):
            threading.Thread.__init__(self)
            self.window = window
            logger(1, '下图线程开始运作')

        def run(self):
            while True:

                # 如果队列不为空就下载队列下一个
                # 如果为空就暂停250ms
                if self.window.img_queue.empty():
                    time.sleep(0.25)
                    continue

                else:
                    site = self.window.site_combobox.get()
                    self.window.download_left_label.config(
                        text='剩余下载:{}'.format(self.window.img_queue.qsize()))
                    img_dic = self.window.img_queue.get()
                    img_id = str(img_dic['id'])
                    # 如果这个图片没有原图就跳过吧
                    if 'file_url' not in img_dic:
                        logger(2, '错误:{}图片没有file_url'.format(img_id))
                        continue

                    img_file_url = img_dic['file_url']
                    # 获取图片后缀名,格式为 '.xxx'
                    img_ext = os.path.splitext(img_file_url)[1]
                    present_path = os.path.abspath('.')
                    path = os.path.join(present_path, site)
                    # 文件保存完整路径
                    full_file_path = os.path.join(
                        present_path, site, img_id + img_ext)
                    # 文件夹不存在就创建
                    if not os.path.exists(path):
                        os.makedirs(path)

                    # 如果文件已存在就跳过
                    if os.path.exists(full_file_path):
                        logger(1, '{}已存在，跳过...'.format(img_id))
                        continue

                    logger(1, '正在下载图片:{}'.format(img_id))
                    download_message_display(
                        self.window, '正在下载图片:{}'.format(img_id))

                    try:
                        img_content = requests.get(
                            img_file_url, timeout=30).content

                    except Exception:
                        logger(3, '下载图片{}错误:\n'.format(img_id) +
                               str(traceback.format_exc()))
                        continue

                    try:
                        with open(full_file_path, 'wb') as img_file:
                            img_file.write(img_content)
                    except Exception:
                        logger(3, '保存图片{}错误:\n'.format(img_id) +
                               str(traceback.format_exc()))
                        continue

                    logger(1, '{}图片成功保存'.format(img_id))
                    self.window.download_left_label.config(
                        text='剩余下载:{}'.format(self.window.img_queue.qsize()))
                    download_message_display(
                        self.window, '{}图片成功保存'.format(img_id))


    class GetImgInfoThreading(threading.Thread):
        def __init__(self, window):
            threading.Thread.__init__(self)
            self.window = window

        def run(self):
            while True:
                site = self.window.site_combobox.get()
                base_url = 'https://{}/post.json?limit=20&tags={}&page={}'
                tag = self.window.tag_entry.get()
                if self.window.present_page_num == int(
                        self.window.page_entry.get()) and self.window.img_num == 0:
                    try:
                        logger(
                            1, '正在获取第{}页的数据'.format(
                                self.window.present_page_num))
                        display(
                            self.window, '正在获取第{}页的数据'.format(
                                self.window.present_page_num))
                        self.window.present_page = requests.get(base_url.format(
                            site, tag, self.window.present_page_num)).json()
                    except Exception:
                        logger(
                            3, '获取第{}页的数据出错，重试..'.format(
                                self.window.present_page_num))
                        display(
                            self.window, '获取第{}页的数据出错，重试..'.format(
                                self.window.present_page_num))
                        continue
                # 如果当前图片数已经比此页的图片数多，就获取下一页
                # Test
                print(len(self.window.present_page))
                print(self.window.img_num)
                if self.window.img_num == len(self.window.present_page):
                    try:
                        # 获取下一页，存入present_page
                        logger(
                            1, '正在获取第{}页的数据'.format(
                                self.window.present_page_num + 1))
                        display(
                            self.window, '正在获取第{}页的数据'.format(
                                self.window.present_page_num + 1))

                        self.window.present_page = requests.get(base_url.format(
                            site, tag, self.window.present_page_num + 1)).json()
                        self.window.present_page_num += 1
                        update_page_entry(self.window)
                        self.window.img_num = 0
                    except Exception:
                        logger(
                            3,
                            '获取第{}页的数据出错:{}，重试中..'.format(
                                self.window.present_page_num + 1,
                                traceback.format_exc()))
                        display(
                            self.window,
                            '获取第{}页的数据出错:{}，重试中..'.format(
                                self.window.present_page_num + 1,
                                traceback.format_exc()))
                        continue

                # 获取当前应该获取的图片json
                present_page_json = self.window.present_page[self.window.img_num]
                self.window.img_num += 1
                # 如果等级被设置成安全，传入网页的rating就是s，其他就是q
                if self.window.rating_combobox.get() == '安全':
                    rating = 's'

                else:
                    rating = 'q'

                if rating == 's':
                    if present_page_json['rating'] is not 's':
                        print('Not safe')
                        continue
                    else:
                        self.window.present_page_json = present_page_json
                else:
                    self.window.present_page_json = present_page_json

                img_id = present_page_json['id']
                logger(1, '正在下载{}预览图'.format(img_id))
                display(self.window, '正在下载{}的预览图'.format(img_id))
                preview_img_url = present_page_json['preview_url']
                try:
                    preview_img_content = requests.get(
                        preview_img_url, timeout=30).content
                except Exception:
                    logger(
                        2,
                        '获取图片{}预览图出错，跳过此图:\n{}'.format(
                            present_page_json['id'],
                            traceback.format_exc()))
                    display(self.window, '获取图片{}预览图出错，跳过此图'.format(img_id))
                    continue

                logger(1, '{}预览图下载完成'.format(img_id))
                display(self.window, '{}预览图下载完成'.format(img_id))
                img_bytes_io = io.BytesIO(preview_img_content)
                img_pil = Image.open(img_bytes_io)
                self.window.img_Tk = ImageTk.PhotoImage(img_pil)
                self.window.preview_label.config(image=self.window.img_Tk)
                break


    class Window:
        def __init__(self):
            # 列表传入一个图片的字典
            self.present_page_json = dict()
            self.img_queue = queue.Queue()
            self.download_threading = DownloadThreading(self)
            self.download_threading.start()

            # 图片相关参数
            self.present_page_num = 1
            self.img_list = list()
            self.img_num = 0

            # about tkinter
            self.top = Tk()
            self.top.title('伪 客户端')
            self.top.resizable(width=False, height=False)

            # Label
            self.site_label = Label(self.top, text='网站:', width=8)
            self.rating_label = Label(self.top, text='限制:', width=8)
            self.tag_label = Label(self.top, text='图片标签', width=8)
            self.message_label = Label(self.top, text='程序启动完成')
            self.preview_label = Label(self.top)
            self.download_message_label = Label(self.top, text='没有下载任务')
            self.download_left_label = Label(self.top, text='剩余下载:0')
            self.page_label = Label(self.top, text='页数:')

            # Combobox
            self.site_combobox = ttk.Combobox(self.top, width=25)
            self.site_combobox['values'] = (
                'konachan.com', 'yande.re', 'lolibooru.moe')
            self.site_combobox.set('konachan.com')

            self.rating_combobox = ttk.Combobox(
                self.top, width=25, state='readonly')
            self.rating_combobox['values'] = ('安全', '限制级')
            self.rating_combobox.set('安全')

            # Entry
            self.tag_entry = Entry(self.top, width=28)
            self.page_entry = Entry(self.top, width=28)
            self.page_entry.insert(0, '1')

            # Button
            self.start_button = Button(
                self.top,
                text='开始看图',
                width=8,
                command=self.start_new_task)
            self.download_button = Button(
                self.top,
                text='下载此图',
                width=8,
                command=self.download_present_page)
            self.next_button = Button(
                self.top,
                text='下一张图',
                width=8,
                command=self.get_next_page)

            # grid
            self.site_label.grid(row=0, column=0)
            self.site_combobox.grid(row=0, column=1, columnspan=2)
            self.rating_label.grid(row=1, column=0)
            self.rating_combobox.grid(row=1, column=1, columnspan=2)
            self.tag_label.grid(row=2, column=0)
            self.tag_entry.grid(row=2, column=1, columnspan=2)
            self.page_label.grid(row=3, column=0)
            self.page_entry.grid(row=3, column=1, columnspan=2)
            self.message_label.grid(row=4, column=0, columnspan=2)
            self.start_button.grid(row=4, column=2)
            self.download_button.grid(row=5, column=0)
            self.next_button.grid(row=5, column=1)
            self.download_message_label.grid(row=5, column=2)
            self.download_left_label.grid(row=6, column=2)

            self.preview_label.grid(row=7, column=0, columnspan=3)

            # 设置关闭窗口操作是退出程序
            self.top.protocol(
                'WM_DELETE_WINDOW', partial(
                    before_close_window, self))

            try:

                if not urls_list:
                    raise Exception

                sure = tkinter.messagebox.askquestion(title='导入', message='检测到上次有未完成的下载任务，是否导入?')
                print(sure)
                if sure:
                    for url in urls_list:
                        if url is not '':
                            print(1)
                            self.img_queue.put(dict(url))

            except:
                pass

            logger(1, '程序启动完成，进入窗体主循环')
            self.top.mainloop()

        def get_next_page(self):
            getting_threading = GetImgInfoThreading(self)
            getting_threading.start()

        def download_present_page(self):
            self.img_queue.put(self.present_page_json)
            self.download_left_label.config(
                text='剩余下载:{}'.format(
                    self.img_queue.qsize()))
            self.get_next_page()

        def start_new_task(self):
            # 初始化
            self.present_page_json = dict()
            self.img_queue = queue.Queue()
            self.img_list = list()
            self.img_num = 0
            self.present_page_num = int(self.page_entry.get())

            getting_threading = GetImgInfoThreading(self)
            getting_threading.start()


    if __name__ == '__main__':
        new_window = Window()


except:
    logger(3,'遇到了致命的错误')
    now_date = time.asctime()
    crash_report_file_name = 'crash-report'+now_date+'.txt'
    crash_report =  'present_page_json:'+str(new_window.present_page_json)+'\n\n\n\n\n\n'+\
                    'img_list:'+str(new_window.img_list)+'\n\n\n\n\n\n'+\
                    'img_num:'+str(new_window.img_num)+'\n\n\n\n\n\n'+\
                    'img_list:'+str(new_window.img_list)+'\n\n\n\n\n\n'+\
                    ':'+str()+'\n\n\n\n\n\n'+\
                    ':'+str()+'\n\n\n\n\n\n'+\
                    ':'+str()
    with open(crash_report_file_name,'w',encoding='utf-8') as f:
        f.write(crash_report)

