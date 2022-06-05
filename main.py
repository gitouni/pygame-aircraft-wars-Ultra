# coding=utf-8
import os
import pygame
# extend import
import pygame.event
import pygame.draw
import pygame.mixer
import pygame.sprite
import pygame.time
import pygame.transform
import pygame.image
import pygame.font
import pygame.display
# game import
from Game_set import game_set
import yaml
import utils
# interface import
import interface
from interface import run_lab, run_help, run_account, run_scene_loading, run_skin, run_net, run_log_video
import tkinter as tk
from tkinter import messagebox
from engine import AutoGameRun  # game runing engine




def run_setting(globalset:utils.Setting,info:tk.StringVar)->None:
    def get_value()->None:
        global SIM_INTERVAL,VOLUME,LOGGING
        SIM_INTERVAL, VOLUME = sim_interval_list[int(scale1.get())], volume_list[int(scale2.get())]
        LOGGING = bool(if_log.get())
        info.set('FPS:{:.0f} VOL: {:.0%} LOG:{}'.format(1000/SIM_INTERVAL,VOLUME,LOGGING))
        globalset.win_open['setting'] = False
        root.destroy()
    init_pygame()
    with open('config.yml','r')as f:
        CONFIG = yaml.load(f,yaml.SafeLoader)['set']
    if globalset.win_open['setting']:
        messagebox.showerror('警示','请勿重复打开窗口。')
        return
    root = tk.Toplevel()
    globalset.win_open['setting'] = True
    root.title('设置')
    root.geometry("{}x{}".format(*CONFIG['screen_size']))
    root.iconphoto(False,tk.PhotoImage(file=CONFIG['icon']))
    sim_interval_list = list(CONFIG['sim_interval_list'])
    sim_interval_list.reverse()
    volume_list = [i*(CONFIG['max_volume']-CONFIG['min_volume'])/CONFIG['steps']+CONFIG['min_volume'] for i in range(CONFIG['steps']+1)]
    try:
        sim_interval_index = sim_interval_list.index(SIM_INTERVAL)
    except:
        sim_interval_index = 0
    try:
        volume_index = volume_list.index(VOLUME)
    except:
        volume_index = 0
    F1 = tk.Frame(root,borderwidth=1,highlightthickness=1)
    F1.pack(side=tk.TOP)
    F2 = tk.Frame(root,borderwidth=1,highlightthickness=1)
    F2.pack(side=tk.TOP)
    F3 = tk.Frame(root,borderwidth=1,highlightthickness=1)
    F3.pack(side=tk.TOP)
    tk.Label(F1,text='低',font=('songti',10)).pack(side=tk.LEFT)
    tk.Label(F2,text='小',font=('songti',10)).pack(side=tk.LEFT)
    scale1 = tk.Scale(F1,cursor='circle',label='游戏性',length=120,orient=tk.HORIZONTAL,showvalue=0,from_=0,to=len(sim_interval_list)-1,resolution=1)
    scale2 = tk.Scale(F2,cursor='circle',label='音量',length=120,orient=tk.HORIZONTAL,showvalue=0,from_=0,to=len(volume_list)-1,resolution=1)
    scale1.pack(side=tk.LEFT)
    scale2.pack(side=tk.LEFT)
    scale1.set(sim_interval_index)
    scale2.set(volume_index)
    tk.Label(F1,text='高',font=('songti',10)).pack(side=tk.LEFT)
    tk.Label(F2,text='大',font=('songti',10)).pack(side=tk.LEFT)
    if_log = tk.IntVar()
    if_log.set(int(LOGGING))
    tk.Label(F3,text='记录游戏',font=('songti',10)).pack(side=tk.LEFT)
    tk.Radiobutton(F3,text='是',value=1,variable=if_log).pack(side=tk.LEFT)
    tk.Radiobutton(F3,text='否',value=0,variable=if_log).pack(side=tk.LEFT)
    root.protocol('WM_DELETE_WINDOW',get_value)
    root.mainloop()

def _run_game(statustext:tk.StringVar,root:tk.Tk):
    global GLOBAL_SET,gameset
    root.update()  # 按钮弹起，显示状态栏
    root.withdraw()
    try:
        run_game(gameset,GLOBAL_SET,SIM_INTERVAL,VOLUME,LOGGING)
        root.deiconify()
        statustext.set('游戏正常退出')
    except:
        root.deiconify()
        statustext.set('游戏异常退出')

def _run_video(statustext:tk.StringVar,root:tk.Tk):
    global GLOBAL_SET
    root.update()
    root.withdraw()
    try:
        run_log_video(GLOBAL_SET,SIM_INTERVAL,VOLUME)
        root.deiconify()
        statustext.set('录像正常退出')
    except:
        root.deiconify()
        statustext.set('录像异常退出')
    

def _run_setting(info:utils.Info):
    global GLOBAL_SET
    run_setting(GLOBAL_SET,info)

def _run_help():
    global GLOBAL_SET
    run_help(GLOBAL_SET)

def _run_skin(info:tk.StringVar):
    global GLOBAL_SET
    run_skin(GLOBAL_SET,info)

def _run_lab():
    global gameset,GLOBAL_SET
    run_lab(gameset,GLOBAL_SET,VOLUME)

def _run_account(info:tk.StringVar):
    global gameset,GLOBAL_SET
    run_account(gameset,GLOBAL_SET,info,VOLUME)

def _run_scene_loading(info:tk.StringVar):
    global GLOBAL_SET
    run_scene_loading(GLOBAL_SET,info)

def _run_net():
    global GLOBAL_SET
    run_net(GLOBAL_SET)

def run_main():
    global SIM_INTERVAL,VOLUME,LOGGING
    def quit_main():
        gameset.setting['sim_interval'] = SIM_INTERVAL
        gameset.setting['volume'] = VOLUME
        gameset.setting['log'] = LOGGING
        for _,value in GLOBAL_SET.win_open.items():
            if value:
                res = messagebox.askyesno('警示','请关闭其他所有子窗口再关闭主程序, 否则存在一定风险。\n是否仍要关闭? ')
                if not res:
                    return
                else:
                    gameset.save()
                    root.destroy()
                    return
        gameset.save()
        root.destroy()
    init_pygame()
    SIGN_POS = CONFIG['main']['sign_pos']
    account_pos = CONFIG['main']['account_pos']
    play_pos = CONFIG['main']['start_pos']
    skin_pos = CONFIG['main']['skin_pos']
    normal_level_pos = CONFIG['main']['normal_level_pos']
    lab_pos = CONFIG['main']['lab_pos']
    net_pos = CONFIG['main']['net_pos']
    log_pos = CONFIG['main']['log_pos']
    help_pos = CONFIG['main']['help_pos']
    setting_pos = CONFIG['main']['setting_pos']
    button_size = CONFIG['main']['button_size']
    small_size = CONFIG['main']['small_button_size']
    account_path = CONFIG['setting']['account_path']
    root = tk.Tk()
    root.title('菜单')
    root.iconphoto(False,tk.PhotoImage(file=CONFIG['setting']['main_ico']))
    win_width, win_height = CONFIG['main']['screen_size']
    root.geometry('{:d}x{:d}'.format(win_width,win_height+10))
    statustext = tk.StringVar() 
    statustext.set( '未加载任何账户！' ) 
    statusbar = tk.Label(root, textvariable=statustext,relief=tk.SUNKEN, anchor= 'w' )
    statusbar.pack(side=tk.BOTTOM,fill=tk.X)
    canvas = tk.Canvas(root,height=win_height, width=win_width,
        bd=0, highlightthickness=0)
    bg_img = interface.Image_load(CONFIG['main']['background_img'],(win_width,win_height))
    canvas.create_image(0,0,anchor='nw',image=bg_img)
    canvas.pack()
    sign_tx = canvas.create_text(*SIGN_POS,font=('arial',14,'bold'),anchor='nw',fill="white")
    canvas.insert(sign_tx,1,'Made by gitouni')
    account_icon = interface.Image_load(CONFIG['main']['account_icon'],small_size)
    button0 = tk.Button(root,text='游戏账户',font=('heiti',14,'bold'),command=lambda info=statustext: _run_account(info),
                        image=account_icon,compound=tk.LEFT)
    normal_lvl_icon = interface.Image_load(CONFIG['main']['normal_level_icon'],small_size)
    button1 = tk.Button(root,text='普通模式',font=('heiti',14,'bold'),command=lambda info=statustext: _run_scene_loading(info),
                        image=normal_lvl_icon,compound=tk.LEFT)
    start_icon = interface.Image_load(CONFIG['main']['start_icon'],small_size)
    button2 = tk.Button(root,text='开始游戏',font=('heiti',14,'bold'),command=lambda info=statustext, tk=root: _run_game(info,tk),
                        image=start_icon,compound=tk.LEFT)
    lab_icon = interface.Image_load(CONFIG['main']['lab_icon'],small_size)
    button3 = tk.Button(root,text='实验中心',font=('heiti',14,'bold'),command=_run_lab,
                        image=lab_icon,compound=tk.LEFT)
    net_icon = interface.Image_load(CONFIG['main']['net_icon'],small_size)
    button4 = tk.Button(root,text='联机对战',font=('heiti',14,'bold'),command=_run_net,
                        image=net_icon,compound=tk.LEFT)
    help_img = interface.Image_load(CONFIG['main']['help_icon'],small_size)
    setting_img = interface.Image_load(CONFIG['main']['setting_icon'],small_size)
    skin_img = interface.Image_load(CONFIG['main']['skin_icon'],small_size)
    log_img = interface.Image_load(CONFIG['main']['log_icon'],small_size)
    help_button = tk.Button(root,bg=CONFIG['main']['help_color'],image=help_img,command=_run_help)
    setting_button = tk.Button(root,bg=CONFIG['main']['setting_color'],image=setting_img,command=lambda info=statustext: _run_setting(info))
    skin_button = tk.Button(root,bg=CONFIG['main']['setting_color'],image=skin_img,command=lambda info=statustext: _run_skin(info))
    log_button = tk.Button(root,bg=CONFIG['main']['log_color'],image=log_img,command=lambda info=statustext, root=root: _run_video(info,root))
    canvas.create_window(*help_pos,width=small_size[0],height=small_size[1],window=help_button)
    canvas.create_window(*setting_pos,width=small_size[0],height=small_size[1],window=setting_button)
    canvas.create_window(*skin_pos,width=small_size[0],height=small_size[1],window=skin_button)
    canvas.create_window(*log_pos,width=small_size[0],height=small_size[1],window=log_button)
    canvas.create_window(*account_pos,width=button_size[0],height=button_size[1],window=button0)
    canvas.create_window(*normal_level_pos,width=button_size[0],height=button_size[1],window=button1)
    canvas.create_window(*play_pos,width=button_size[0],height=button_size[1],window=button2)
    canvas.create_window(*lab_pos,width=button_size[0],height=button_size[1],window=button3)
    canvas.create_window(*net_pos,width=button_size[0],height=button_size[1],window=button4)
    if os.path.exists(account_path):
        account_file = os.listdir(account_path)
        if len(account_file)>0:
            account_time = []
            for file in account_file:
                fullpath = os.path.join(account_path,file)
                filetime = os.path.getmtime(fullpath)
                account_time.append(filetime)
            account_tuple = list(zip(account_file,account_time))
            recent_file = sorted(account_tuple,key=lambda ele: ele[1],reverse=True)[0][0]
            gameset.load(os.path.join(account_path,recent_file))
            try:
                SIM_INTERVAL = gameset.setting['sim_interval']
                VOLUME = gameset.setting['volume']
                LOGGING = gameset.setting['log']
            except KeyError:
                gameset.setting['sim_interval'] = SIM_INTERVAL
                gameset.setting['volume'] = VOLUME
                gameset.setting['log'] = LOGGING
            recent_name = os.path.splitext(recent_file)[0]
            statustext.set("欢迎, {}".format(recent_name))
    root.protocol('WM_DELETE_WINDOW', quit_main)
    root.mainloop()

def init_pygame():
    if not pygame.get_init():
        pygame.init()  # 初始化背景设置
    if not pygame.font.get_init():
        pygame.font.init() # 初始化字体设置
    if not pygame.mixer.get_init():
        pygame.mixer.init(20000,buffer=1024)  # 音乐初始化
        pygame.mixer.music.set_volume(1)  # 音量初始化

# 运行游戏界面
def run_game(gameset:game_set,globalset:utils.Setting,sim_interval:float,volume:float,log:bool):
    if not gameset.path:
        start = messagebox.askyesno("Warning","您尚未加载任何账户，游戏记录将无法被保存，是否继续？")
        if not start:
            return
    if globalset.win_open['game']:
        messagebox.showerror('警示','请勿重复打开窗口')
        return
    gameset.setting['sim_interval'] = sim_interval
    gameset.setting['volume'] = volume
    gameset.setting['log'] = log
    game_run = AutoGameRun(gameset,globalset,sim_interval,volume,log=log)
    game_run.run()
    del game_run
    return


# 运行游戏
if __name__ == "__main__":

    with open("config.yml",'r')as f:
        CONFIG = yaml.load(f,yaml.SafeLoader)
    
    gameset = game_set() # 游戏设置类
    GLOBAL_SET = utils.Setting()
    SIM_INTERVAL = CONFIG['setting']['sim_interval']
    VOLUME = CONFIG['setting']['volume']
    LOGGING = CONFIG['setting']['log']
    run_main()
    

