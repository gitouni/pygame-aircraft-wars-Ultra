import pygame
import pygame.mixer
import pygame.font
import tkinter as tk
from tkinter import messagebox, scrolledtext, simpledialog
import threading
import os
from PIL import Image,ImageTk
import yaml
from copy import deepcopy
from Game_set import game_set
import utils
import json
import threading
import time
import network
import re
import engine


def Image_load(file:str,size:tuple)->ImageTk.PhotoImage:
    img = Image.open(file).resize(size)
    return ImageTk.PhotoImage(img)


    
def run_help(globalset:utils.Setting):
    def show_operation_txt():
        notebook.delete('0.0',tk.END)
        notebook.insert('0.0',help_operation_txt)
    def show_note_txt():
        notebook.delete('0.0',tk.END)
        notebook.insert('0.0',help_note_txt)
    def on_closing():
        globalset.win_open['help'] = False
        root.destroy()
    with open('config.yml','r')as f:
        CONFIG = yaml.load(f,yaml.SafeLoader)['help']
    if globalset.win_open['help']:
        messagebox.showerror('警示','请勿重复打开窗口。')
        return
    root = tk.Toplevel()
    globalset.win_open['help'] = True
    win_width,win_height = CONFIG['screen_size']
    button_size = CONFIG['button_size']
    bg_color = CONFIG['button_bg_color']
    small_button_size = CONFIG['small_button_size']
    with open(CONFIG['help_operation_txt'],'r',encoding='utf-8')as f:
        help_operation_txt = ''.join(f.readlines())
    with open(CONFIG['help_note_txt'],'r',encoding='utf-8')as f:
        help_note_txt = ''.join(f.readlines())
    root.geometry("{}x{}".format(win_width,win_height))
    root.title('帮助')
    root.iconphoto(False,tk.PhotoImage(file=CONFIG['icon']))
    canvas = tk.Canvas(root,height=win_height, width=win_width,
        bd=0, highlightthickness=0)
    canvas.pack()
    notebook = scrolledtext.ScrolledText(root,width=win_width-10,height=win_height-60,font=('songti',10))
    notebook.insert('0.0',help_operation_txt)
    notebook.pack()
    bg_img = Image_load(CONFIG['background_img'],(win_width,win_height))
    operation_icon = Image_load(CONFIG['help_operation_icon'],small_button_size)
    note_icon = Image_load(CONFIG['help_note_icon'],small_button_size)
    operation_button = tk.Button(root,bg=bg_color,image=operation_icon,text='操作',font=('heiti',12),compound='left',fg='white',command=show_operation_txt)
    note_button = tk.Button(root,bg=bg_color,image=note_icon,text='攻略',font=('heiti',12),compound='left',fg='white',command=show_note_txt)
    operation_button.pack()
    note_button.pack()
    canvas.create_image(0,0,anchor='nw',image=bg_img)
    canvas.create_window(*CONFIG['notebook_pos'],anchor='nw',width=win_width-10,height=win_height-60,window=notebook)
    canvas.create_window(*CONFIG['help_operation_pos'],anchor='nw',width=button_size[0],height=button_size[1],window=operation_button)
    canvas.create_window(*CONFIG['help_note_pos'],anchor='nw',width=button_size[0],height=button_size[1],window=note_button)
    root.protocol('WM_DELETE_WINDOW', on_closing)
    root.mainloop()

def run_skin(globalset:utils.Setting,info:tk.StringVar):
    def load(event=None):
        nonlocal globalset,info
        index = listbox.curselection()
        if len(index) == 0:
            messagebox.showwarning('警告','未选择任何战机皮肤。')
            return
        index = index[0]
        globalset.player_index = index
        info.set('选择皮肤[{}]成功！'.format(os.path.splitext(os.path.basename(CONFIG['png_data'][index]))[0]))
    
    def preview(event=None):
        nonlocal img
        index = listbox.curselection()
        if len(index) == 0:
            return  # 静默
        index = index[0]
        png_path = os.path.join(CONFIG['path'],skin_pack_list[index]['LEFT'][0])
        img = Image_load(png_path,CONFIG['canvas_size'])
        canvas.create_image(0,0,anchor='nw',image=img)
        
    def on_closing():
        globalset.win_open['skin'] = False
        root.destroy()
    if globalset.win_open['skin']:
        messagebox.showerror('警示','请勿重复打开窗口。')
        return
    root = tk.Toplevel()
    globalset.win_open['skin'] = True
    with open('config.yml','r')as f:
        CONFIG = yaml.load(f,yaml.SafeLoader)['skin']
    skin_pack_list = []
    for path in CONFIG['png_data']:
        skin_pack = utils.csv2dict(path)
        skin_pack_list.append(skin_pack)
    root.title("战机皮肤")
    root.iconphoto(True,tk.PhotoImage(file=CONFIG['icon']))
    F1 = tk.Frame(root)
    F1.pack(side=tk.LEFT)
    F2 = tk.Frame(root)
    F2.pack(side=tk.RIGHT)
    F11 = tk.Frame(F1)
    F11.pack(side=tk.TOP)
    F12 = tk.Frame(F1)
    F12.pack(side=tk.BOTTOM)
    button1 = tk.Button(F11,text='装配',bg='white',font=('songti',12),command=load)
    button1.pack(side=tk.LEFT,padx=10)
    button2 = tk.Button(F11,text='返回',bg='white',font=('songti',12),command=on_closing)
    button2.pack(side=tk.RIGHT,padx=10)
    scbar = tk.Scrollbar(F12, orient=tk.VERTICAL)
    listbox = tk.Listbox(F12,yscrollcommand=scbar.set,
                                 selectmode=tk.SINGLE,width=23,height=15,
                                 font=('songti',12))
    scbar.config(command=listbox.yview)
    scbar.pack(side=tk.RIGHT,fill=tk.Y)
    listbox.pack(fill=tk.BOTH)
    listbox.bind("<Double-Button-1>",load)
    listbox.bind("<<ListboxSelect>>",preview)
    for path in CONFIG['png_data']:
        listbox.insert(tk.END,os.path.splitext(os.path.basename(path))[0])
    listbox.selection_set(globalset.player_index)
    canvas = tk.Canvas(F2,width=CONFIG['canvas_size'][0],height=CONFIG['canvas_size'][1])
    canvas.pack()
    png_path = os.path.join(CONFIG['path'],skin_pack_list[globalset.player_index]['LEFT'][0])
    img = Image_load(png_path,CONFIG['canvas_size'])
    canvas.create_image(0,0,anchor='nw',image=img)
    root.protocol('WM_DELETE_WINDOW', on_closing)
    root.mainloop()

def run_log_video(globalset:utils.Setting,sim_interval:float,volume:float):
    def load(event=None):
        root.update()
        index = listbox.curselection()
        if len(index) == 0:
            messagebox.showwarning('警告','未选择任何录像。')
            return
        index = index[0]
        video_path = log_list[index]
        gamerun = engine.LogGameRun(game_set(),globalset,sim_interval,volume,
                                    os.path.join('video',video_path))
        gamerun.run()
    
    def delete():
        index = listbox.curselection()
        if len(index) == 0:
            messagebox.showwarning('警告','未选择任何录像。')
            return
        index = index[0]
        res = messagebox.askyesno('提示','是否删除此记录？')
        if not res:
            return
        video_path = log_list[index]
        os.remove(os.path.join('video',video_path))
        listbox.delete(index)
        log_list.pop(index)
    
    def rename():
        index = listbox.curselection()
        if len(index) == 0:
            messagebox.showwarning('警告','未选择任何录像。')
            return
        index = index[0]
        res = simpledialog.askstring('提示','请输入新名称\n空值或Cancel即可撤销此操作。')
        if not res:
            return
        video_path = log_list[index]
        os.rename(os.path.join('video',video_path),os.path.join('video',res+'.p'))
        listbox.delete(index)
        listbox.insert(index,res)
        log_list[index] = res+'.p'
    
    def on_closing():
        globalset.win_open['log'] = False
        root.destroy()
        
    if globalset.win_open['log']:
        messagebox.showerror('警示','请勿重复打开窗口。')
        return
    root = tk.Toplevel()
    globalset.win_open['log'] = True
    with open('config.yml','r')as f:
        CONFIG = yaml.load(f,yaml.SafeLoader)['log']
    log_list = utils.recent_sort('video')
    root.title("游戏录像")
    root.iconphoto(True,tk.PhotoImage(file=CONFIG['icon']))
    F1 = tk.Frame(root)
    F1.pack(side=tk.LEFT)
    F2 = tk.Frame(root)
    F2.pack(side=tk.RIGHT)
    F11 = tk.Frame(F1)
    F11.pack(side=tk.TOP)
    F12 = tk.Frame(F1)
    F12.pack(side=tk.BOTTOM)
    button1 = tk.Button(F11,text='播放',bg='white',font=('songti',12),command=load)
    button1.pack(side=tk.LEFT,padx=5)
    button2 = tk.Button(F11,text='删除',bg='white',font=('songti',12),command=delete)
    button2.pack(side=tk.LEFT,padx=5)
    button3 = tk.Button(F11,text='重命名',bg='white',font=('songti',12),command=rename)
    button3.pack(side=tk.LEFT,padx=5)
    button4 = tk.Button(F11,text='返回',bg='white',font=('songti',12),command=on_closing)
    button4.pack(side=tk.LEFT,padx=5)
    scbar = tk.Scrollbar(F12, orient=tk.VERTICAL)
    listbox = tk.Listbox(F12,yscrollcommand=scbar.set,
                                 selectmode=tk.SINGLE,width=23,height=15,
                                 font=('songti',12))
    scbar.config(command=listbox.yview)
    scbar.pack(side=tk.RIGHT,fill=tk.Y)
    listbox.pack(fill=tk.BOTH)
    listbox.bind("<Double-Button-1>",load)
    for path in log_list:
        listbox.insert(tk.END,os.path.splitext(path)[0])
    root.protocol('WM_DELETE_WINDOW', on_closing)
    root.mainloop()

def run_scene_loading(globalset:utils.Setting,info:tk.StringVar):
    def load_json(index:int)->dict:
        full_path = os.path.join(CONFIG['path'],scene_files[index])
        with open(full_path,'r')as f:
            scene_data = json.load(f)
        return scene_data, full_path
    
    def load(event=None):
        nonlocal globalset
        index = listbox.curselection()
        if len(index) == 0:
            messagebox.showerror('提示','您未选中任何地图！')
            return
        index = index[0]
        scene_data, scene_path = load_json(index)
        globalset.background_jpg = scene_data['meta']['background']
        globalset.scenes = scene_data['scene']
        globalset.scene_path = scene_path
        messagebox.showinfo('提示','地图加载完成\n可返回主菜单开始游戏。')
        info.set('地图[{}]加载完成!'.format(scene_data['meta']['name']))
        globalset.win_open['scene'] = False
        root.destroy()
        
    def rename():
        index = listbox.curselection()
        if len(index) == 0:
            messagebox.showerror('提示','您未选中任何地图！')
            return
        index = index[0]
        map_name = simpledialog.askstring('提示','键入地图名称（兼容中文）')
        scene_data = load_json(index)[0]
        scene_data['meta']['name'] = map_name
        with open(full_path,'w')as f:
            json.dump(scene_data,f)
        listbox.delete(index)
        listbox.insert(index,'{:04d}-{}'.format(index,map_name))
        statustext.set('重命名成功！')
    
    def preview(event=None):
        nonlocal canvas,statustext,statusdetail,img
        index = listbox.curselection()[0]
        scene_data = load_json(index)[0]
        background_path = scene_data['meta']['background']
        img = Image_load(background_path,CONFIG['background_size'])
        canvas.create_image(0,0,anchor='nw',image=img)
        num_dict = utils.scene_statics(scene_data['scene'])
        head = "scene1:{} scene2:{}".format(num_dict['scene1'],num_dict['scene2'])
        info = "e:{} ea:{} eax:{} eb:{}".format(
            num_dict['e'],num_dict['ea'],num_dict['eax'],
            num_dict['eb']
        )
        statustext.set(head)
        statusdetail.set(info)
        
    def on_closing():
        nonlocal info
        if globalset.scene_path == '':
            messagebox.showwarning('提示','地图尚未成功加载！')
            info.set('地图尚未成功加载！')
        globalset.win_open['scene'] = False
        root.destroy()
        
    if globalset.win_open['scene']:
        messagebox.showerror('警示','请勿重复加载窗口')
        return
    scene = []
    root = tk.Toplevel()
    globalset.win_open['scene'] = True
    root.title('普通模式')
    with open('config.yml','r')as f:
        CONFIG = yaml.load(f,yaml.SafeLoader)['map']
    root.iconphoto(True,tk.PhotoImage(file=CONFIG['icon']))
    root.geometry('{}x{}'.format(*CONFIG['window_size']))
    scene_files = list(sorted(os.listdir(CONFIG['path'])))
    statustext = tk.StringVar() 
    statustext.set( '未检测到任何操作。' ) 
    statusdetail = tk.StringVar()
    statusdetail.set('')
    statusbar = tk.Label(root, textvariable=statustext,relief=tk.SUNKEN, anchor= 'w')
    statusbar_detail = tk.Label(root, textvariable=statusdetail,relief=tk.SUNKEN, anchor= 'w',foreground='blue')
    statusbar_detail.pack(side=tk.BOTTOM,fill=tk.X)
    statusbar.pack(side=tk.BOTTOM,fill=tk.X)
    F1 = tk.Frame(root)
    F1.pack(side=tk.LEFT)
    F2 = tk.Frame(root)
    F2.pack(side=tk.RIGHT)
    F11 = tk.Frame(F1)
    F11.pack(side=tk.TOP)
    F12 = tk.Frame(F1)
    F12.pack(side=tk.BOTTOM)
    button1 = tk.Button(F11,text='加载',font=('songti',12),command=load)
    button2 = tk.Button(F11,text='重命名',font=('songti',12),command=rename)
    button3 = tk.Button(F11,text='返回',font=('songti',12),command=on_closing)
    button1.pack(side='left',padx=5)
    button2.pack(side='left',padx=5)
    button3.pack(side='right',padx=5)
    scbar = tk.Scrollbar(F12, orient=tk.VERTICAL)
    listbox = tk.Listbox(F12,yscrollcommand=scbar.set,
                                 selectmode=tk.SINGLE,width=23,height=15,
                                 font=('songti',12))
    listbox.bind("<Double-Button-1>",load)
    listbox.bind("<<ListboxSelect>>",preview)
    scbar.config(command=listbox.yview)
    scbar.pack(side=tk.RIGHT,fill=tk.Y)
    listbox.pack(fill=tk.BOTH)
    for i,file in enumerate(scene_files,start=1):
        full_path = os.path.join(CONFIG['path'],file)
        with open(full_path,'r')as f:
            scene = json.load(f)
        listbox.insert(tk.END,"{index:04d}-{name}".format(index=i,name=scene['meta']['name']))
    listbox.selection_set(0)
    canvas = tk.Canvas(F2,width=CONFIG['canvas_size'][0],height=CONFIG['canvas_size'][1])
    canvas.pack()
    scene_data = load_json(0)[0]
    background_path = scene_data['meta']['background']
    img = Image_load(background_path,CONFIG['background_size'])
    canvas.create_image(0,0,anchor='nw',image=img)
    root.protocol('WM_DELETE_WINDOW', on_closing)
    root.mainloop()

def run_account(gameset:game_set,globalset:utils.Setting,info:tk.StringVar,volume:float=1.0):
    def create()->None:
        nonlocal gameset
        if not globalset.has_saved:
            threading.Thread(target=utils.play_music,args=(pygame.mixer.Sound(CONFIG['account']['save_sound_file']),volume)).start()
            res = messagebox.askyesno('提示',"检测到账户存在修改,\n创建会覆盖现有账户,是否仍然创建？")
            if not res:
                return
        name = simpledialog.askstring('创建','创建账户 (使用非英文字符可能导致错误):')
        if not name:
            return
        save_path = os.path.join(account_path,name_fmt.format(name=name))
        if os.path.exists(save_path):
            threading.Thread(target=utils.play_music,args=(pygame.mixer.Sound(CONFIG['account']['save_sound_file']),volume)).start()
            res = messagebox.askyesno('提示',"该账户已存在, 是否覆盖？")
            if not res:
                return
        newset = game_set()
        gameset.__dict__ = deepcopy(newset.__dict__)
        gameset.gold = CONFIG['account']['initial_gold']
        gameset.diamond = CONFIG['account']['initial_diamond']
        gameset.path = os.path.join(account_path,name_fmt.format(name=name))
        with open(save_path,'w')as f:
            json.dump(gameset.__dict__,f)
        threading.Thread(target=utils.play_music,args=(pygame.mixer.Sound(CONFIG['account']['exit_sound_file']),volume)).start()
        messagebox.showinfo("提示","账户创建完成, 请利用初始资源去实验室升级吧!")
        info.set('欢迎体验本游戏，{}'.format(name))
        globalset.win_open['account'] = False
        root.destroy()
    def load(event=None)->None:
        nonlocal gameset
        if not globalset.has_saved:
            threading.Thread(target=utils.play_music,args=(pygame.mixer.Sound(CONFIG['account']['save_sound_file']),volume)).start()
            res = messagebox.askyesno('提示',"检测到账户存在修改,\n加载会覆盖现有账户,是否仍然加载？")
            if not res:
                return
        account_index = account_listbox.curselection()
        if not account_index:
            messagebox.showwarning('提示','未选中任何账户！')
            return
        account_index = account_index[0]
        account = accounts[account_index]
        filepath = os.path.join(account_path,account)
        with open(filepath,'r')as f:
            gameset.__dict__ = json.load(f)
        gameset.path = filepath
        threading.Thread(target=utils.play_music,args=(pygame.mixer.Sound(CONFIG['account']['save_sound_file']),volume)).start()
        messagebox.showinfo('提示','加载成功!')
        on_closing()
    def save()->None:
        nonlocal globalset
        globalset.has_saved = True
        account_index = account_listbox.curselection()
        if not account_index:
            messagebox.showwarning('提示','未选中任何账户！')
            return
        if account_index[0] != cur_index:
            threading.Thread(target=utils.play_music,args=(pygame.mixer.Sound(CONFIG['account']['save_sound_file']),volume)).start()
            res = messagebox.askyesno('警告',"即将保存到冲突用户,\n是否继续？")
            if not res:
                return
        filepath = os.path.join(account_path,accounts[account_index[0]])
        with open(filepath,'w')as f:
            gameset.path = filepath
            json.dump(gameset.__dict__,f)
        threading.Thread(target=utils.play_music,args=(pygame.mixer.Sound(CONFIG['account']['save_sound_file']),volume)).start()
        messagebox.showinfo('提示','保存成功！')
    def on_closing()->None:
        nonlocal info
        if gameset.path:
            info.set("欢迎回来，{}".format(os.path.splitext(os.path.basename(gameset.path))[0]))
        else:
            info.set("未加载任何账户！")
        globalset.win_open['account'] = False
        root.destroy()
    
    if globalset.win_open['account']:
        messagebox.showerror('警示','请勿重复打开窗口。')
        return
    
    name_fmt = '{name}.json'
    with open('config.yml','r')as f:
        CONFIG = yaml.load(f,yaml.SafeLoader)
    account_path = CONFIG['setting']['account_path']
    os.makedirs(account_path,exist_ok=True)
    if len(os.listdir(account_path))==0:
        exist_account = False
    else:
        exist_account = True
    
    root = tk.Toplevel()
    globalset.win_open['account'] = True
    root.title('账户')
    root.iconphoto(True,tk.PhotoImage(file=CONFIG['setting']['account_ico']))
    F1 = tk.Frame(root,borderwidth=1,highlightthickness=1,name='操作')
    F1.pack(side=tk.TOP)
    F2 = tk.Frame(root,borderwidth=1,highlightthickness=1,name='账户列表')
    F2.pack(side=tk.BOTTOM)
    button1 = tk.Button(F1,text='创建',font=('songti',12),command=create)
    button2 = tk.Button(F1,text='加载',font=('songti',12),command=load)
    button3 = tk.Button(F1,text='存档',font=('songti',12),command=save)
    button1.pack(side=tk.LEFT,padx=10)
    button2.pack(side=tk.LEFT,padx=10)
    button3.pack(side=tk.RIGHT,padx=10)
    account_scbar = tk.Scrollbar(F2, orient=tk.VERTICAL)
    account_listbox = tk.Listbox(F2,yscrollcommand=account_scbar.set,
                                 selectmode=tk.SINGLE,width=23,height=8,
                                 font=(CONFIG['setting']['font'],12))
    account_listbox.bind("<Double-Button-1>",load)
    account_scbar.config(command=account_listbox.yview)
    account_scbar.pack(side=tk.RIGHT,fill=tk.Y)
    account_listbox.pack(fill=tk.BOTH)
    if not exist_account:
        button2.config(state='disabled')
    if len(os.listdir(account_path)) > 0:
        accounts = utils.recent_sort(account_path)
        cur_index = accounts.index(os.path.basename(gameset.path))
        for account in accounts:
            account_listbox.insert(tk.END,os.path.splitext(account)[0])
        account_listbox.selection_set(cur_index)
    root.protocol('WM_DELETE_WINDOW',on_closing)
    root.mainloop()

def run_lab(gameset:game_set,globalset:utils.Setting,volume:float=1.0):
    def refresh():
        nonlocal gameset_copy
        gameset_copy.__dict__ = deepcopy(gameset.__dict__)
        threading.Thread(target=utils.thread_play_music,args=(config['refresh_sound_file'],1,1.0)).start()
        flash()
        statustext.set('重置成功！')
        statusbar.config(foreground='blue')
    def flash():
        gold_label.config(text=utils.pretty_number(gameset_copy.gold))
        diamond_label.config(text=utils.pretty_number(gameset_copy.diamond))
        for index, (consume_gold_label,consume_diamond_label,level_label) in enumerate(zip(gold_label_list,diamond_label_list,level_label_list)):
            level = gameset_copy.__dict__[level_keys[index]]
            gold_key = gold_consume_keys[index]
            diamond_key = diamond_consume_keys[index]
            if level < len(gameset_copy.__dict__[gold_key]):
                consume_gold = gameset_copy.__dict__[gold_key][level]
                consume_diamond = gameset_copy.__dict__[diamond_key][level]
            else:
                consume_gold = 'Max Lv'
                consume_diamond = 'Max Lv'
            level_label.config(text="{}/{}".format(level+1,len(gameset_copy.__dict__[gold_key])+1))
            consume_gold_label.config(text=str(consume_gold))
            consume_diamond_label.config(text=str(consume_diamond))
    def upgrade(index:int):
        level = gameset_copy.__dict__[level_keys[index]]
        gold_key = gold_consume_keys[index]
        diamond_key = diamond_consume_keys[index]
        if level < len(gameset_copy.__dict__[gold_key]):
            consume_gold = gameset_copy.__dict__[gold_key][level]
            consume_diamond = gameset_copy.__dict__[diamond_key][level]
            if gameset_copy.gold >= consume_gold and\
                gameset_copy.diamond >= consume_diamond:
                level += 1
                gameset_copy.gold -= consume_gold
                gameset_copy.diamond -= consume_diamond
                gameset_copy.__dict__[level_keys[index]] += 1
                threading.Thread(target=utils.play_music,args=(pygame.mixer.Sound(config['upgrade_sound_file']),1)).start()
                flash()
                statustext.set('升级成功！')
                statusbar.config(foreground='blue')
            else:
                upgrade_error()
                if gameset_copy.gold < consume_gold:
                    statustext.set('没有足够的金币！')
                    statusbar.config(foreground='red')
                elif gameset_copy.diamond < consume_diamond:
                    statustext.set('没有足够的钻石！')
                    statusbar.config(foreground='red')
        else:
            upgrade_error()
            statustext.set('已升至最高级别！')
            statusbar.config(foreground='red')
    def upgrade_error():
        threading.Thread(target=utils.play_music,args=(pygame.mixer.Sound(config['error_sound_file']),1)).start()
    def save():
        nonlocal gameset,globalset
        gameset.__dict__ = deepcopy(gameset_copy.__dict__)
        globalset.has_saved = False
        threading.Thread(target=utils.thread_play_music,args=(config['save_sound_file'],1,1.0)).start()
        statustext.set('保存成功！')
        statusbar.config(foreground='blue')
    # for debugging
    # def print_coord(event:tk.Event):
    #     print(f"({event.x},{event.y})")
    
        
    def on_closing():
        nonlocal gameset
        if gameset.__dict__ != gameset_copy.__dict__:
            threading.Thread(target=utils.thread_play_music,args=(config['exit_sound_file'],1,2.0)).start()
            if messagebox.askyesno("提示", "未保存，是否退出?"):
                globalset.win_open['lab'] = False
                root.destroy()
            else:
                return
        else:
            globalset.win_open['lab'] = False
            root.destroy()
            
    with open('config.yml','r')as f:
        CONFIG = yaml.load(f,yaml.SafeLoader)
    gameset_copy = game_set()
    gameset_copy.__dict__ = deepcopy(gameset.__dict__)
    gold_consume_keys = ['HP_gold','HP_recover_gold','energy_gold','energy_recover_gold','cooling_gold','cooling_recover_gold',\
                        'bullet_ID_gold','shooting_cd_gold','missile_num_gold','missile_damage_gold','missile_actime_gold','missile_flyingtime_gold']
    diamond_consume_keys = ['HP_diamond','HP_recover_diamond','energy_diamond','energy_recover_diamond','cooling_diamond','cooling_recover_diamond',\
                        'bullet_ID_diamond','shooting_cd_diamond','missile_num_diamond','missile_damage_diamond','missile_actime_diamond','missile_flyingtime_diamond']
    level_keys = ['player_HP_level','player_HP_recover','player_energy_level','player_energy_recover_level','player_cooling_level','player_cooling_recover_level',\
            'bullet_ID','bullet_shooting_cd_level','missile_num_level','missile_damage_level','missile_actime_level','missile_flyingtime_level']
    if not pygame.get_init():
        pygame.init()  # 初始化背景设置
        pygame.font.init() # 初始化字体设置
        pygame.mixer.init(11025)  # 音乐初始化
        pygame.mixer.music.set_volume(volume)  # 音量初始化
    
    if globalset.win_open['lab']:
        messagebox.showerror('警示','请勿重复打开窗口。')
        return
    
    config = CONFIG['interface']
    icon_config = CONFIG['icon']
    root = tk.Toplevel()
    globalset.win_open['lab'] = True
    root.title('实验室')
    # root.bind("<Button-1>",print_coord) # for debug
    win_width, win_height = config['lab_screen_size']
    # root.geometry('{:d}x{:d}'.format(win_width,win_height+10))
    root.iconphoto(True,tk.PhotoImage(file=CONFIG['setting']['lab_ico']))
    statustext = tk.StringVar()
    statustext.set('请选择项目进行升级')
    statusbar = tk.Label(root, textvariable=statustext,relief=tk.SUNKEN, anchor= 'w',foreground='blue')
    statusbar.pack(side=tk.BOTTOM,fill=tk.X)
    img = Image.open(config['lab_img'])
    img = img.resize((win_width, win_height),Image.BICUBIC)
    photo = ImageTk.PhotoImage(img)
    canvas = tk.Canvas(root,height=win_height, width=win_width,
        bd=0, highlightthickness=0)
    canvas.create_image(0,0,anchor='nw',image=photo)
    canvas.pack()
    gold_ico = Image.open(os.path.join(icon_config['path'],icon_config['gold'])).resize((25,25),Image.BICUBIC)
    gold_ico = ImageTk.PhotoImage(gold_ico)
    diamond_ico = Image.open(os.path.join(icon_config['path'],icon_config['diamond'])).resize((30,25),Image.BICUBIC)
    diamond_ico = ImageTk.PhotoImage(diamond_ico)
    small_gold_ico = Image.open(os.path.join(icon_config['path'],icon_config['gold'])).resize((15,15),Image.BICUBIC)
    small_gold_ico = ImageTk.PhotoImage(small_gold_ico)
    small_diamond_ico = Image.open(os.path.join(icon_config['path'],icon_config['diamond'])).resize((20,15),Image.BICUBIC)
    small_diamond_ico = ImageTk.PhotoImage(small_diamond_ico)
    refresh_icon = Image.open(os.path.join(icon_config['path'],icon_config['refresh'])).resize((25,25),Image.BICUBIC)
    refresh_icon = ImageTk.PhotoImage(refresh_icon)
    save_icon = Image.open(os.path.join(icon_config['path'],icon_config['save'])).resize((25,25),Image.BICUBIC)
    save_icon = ImageTk.PhotoImage(save_icon)
    upgrade_ico = Image.open(os.path.join(icon_config['path'],icon_config['upgrade'])).resize((25,25),Image.BICUBIC)
    upgrade_ico = ImageTk.PhotoImage(upgrade_ico)
    # 显示升级消耗图标
    canvas.create_image(*config['lab_grid']['gold_icon'],anchor='nw',image=gold_ico)
    canvas.create_image(*config['lab_grid']['diamond_icon'],anchor='nw',image=diamond_ico)
    consume_gold_icon_grid = config['lab_grid']['consume_grid']
    gold_value = gameset_copy.gold
    diamond_value = gameset_copy.diamond
    consume_gold_size = (50,12)
    consume_diamond_size = (40,12)
    level_size = (25,12)
    button_size = (25,25)
    gold_label_list = []
    diamond_label_list = []
    level_label_list = []
    consume_label_dict = dict(fg='yellow',font=('arial',8),background=config['lab_grid']['background_color'])

    # 显示升级消耗数值
    consume_gold_value_grid = [[coor[0]+20,coor[1]] for coor in consume_gold_icon_grid]
    consume_diamond_icon_grid = [[coor[0]+50,coor[1]] for coor in consume_gold_value_grid]
    consume_diamond_value_grid = [[coor[0]+20,coor[1]] for coor in consume_diamond_icon_grid]
    for gold_icon_coord,diamond_icon_coord in zip(consume_gold_icon_grid,consume_diamond_icon_grid):
        canvas.create_image(*gold_icon_coord,anchor='nw',image=small_gold_ico)
        canvas.create_image(*diamond_icon_coord,anchor='nw',image=small_diamond_ico)
    gold_label = tk.Label(root,text=utils.pretty_number(gold_value),fg='yellow',font=('arial',12),background=config['lab_grid']['background_color'],justify='left')
    diamond_label = tk.Label(root,text=utils.pretty_number(diamond_value),fg='yellow',font=('arial',12),background=config['lab_grid']['background_color'],justify='left')
    gold_label.pack()
    diamond_label.pack()
    
    canvas.create_window(*config['lab_grid']['gold_value'],anchor='nw',width=65,height=20,window=gold_label)
    canvas.create_window(*config['lab_grid']['diamond_value'],anchor='nw',width=65,height=20,window=diamond_label)
    for index in range(len(gold_consume_keys)):
        level = gameset_copy.__dict__[level_keys[index]]
        gold_key = gold_consume_keys[index] 
        diamond_key = diamond_consume_keys[index]
        consume_gold = gameset_copy.__dict__[gold_key][level] if level < len(gameset_copy.__dict__[gold_key]) else 'Max Lv'
        consume_diamond = gameset_copy.__dict__[diamond_key][level] if level < len(gameset_copy.__dict__[diamond_key]) else 'Max Lv'
        consume_gold_label = tk.Label(root,cnf=consume_label_dict,text=consume_gold,justify='left')
        consume_diamond_label = tk.Label(root,cnf=consume_label_dict,text=consume_diamond,justify='left')
        level_label = tk.Label(root,cnf=consume_label_dict,text="{}/{}".format(level+1,len(gameset_copy.__dict__[gold_key])+1),justify='left')
        button = tk.Button(root,command=lambda i=index: upgrade(i),image=upgrade_ico,background=config['lab_grid']['button_color'])
        consume_gold_label.pack()
        consume_diamond_label.pack()
        level_label.pack()
        button.pack()
        gold_label_list.append(consume_gold_label)
        diamond_label_list.append(consume_diamond_label)
        level_label_list.append(level_label)
        canvas.create_window(*consume_gold_value_grid[index],anchor='nw',width=consume_gold_size[0],height=consume_gold_size[1],window=consume_gold_label)
        canvas.create_window(*consume_diamond_value_grid[index],anchor='nw',width=consume_diamond_size[0],height=consume_diamond_size[1],window=consume_diamond_label)
        canvas.create_window(*config['lab_grid']['level_grid'][index],anchor='nw',width=level_size[0],height=level_size[1],window=level_label)
        canvas.create_window(*config['lab_grid']['upgrade_grid'][index],anchor='nw',width=button_size[0],height=button_size[1],window=button)
    refresh_button = tk.Button(root,text='重置',font=('songti',12),background=config['lab_grid']['button_color'],
                               foreground='yellow',image=refresh_icon,compound='left',
                               command=refresh)
    refresh_button.pack()
    save_button = tk.Button(root,text='保存',font=('songti',12),background=config['lab_grid']['button_color'],
                               foreground='yellow',image=save_icon,compound='left',
                               command=save)
    save_button.pack()
    canvas.create_window(*config['lab_grid']['refresh_icon'],width=65,height=25,window=refresh_button)
    canvas.create_window(*config['lab_grid']['save_icon'],width=65,height=25,window=save_button)
    root.protocol('WM_DELETE_WINDOW', on_closing)
    root.mainloop()

def run_net(globalset:utils.Setting):
    def turnto_server():
        nonlocal NET_FLAG
        NET_FLAG = network.NetType.Server
        statustext.set("本机作为服务器")
        title_label.config(text='请输入本机开放的端口号')
        ip_entry.delete(0,tk.END)
        ip_entry.config(state='disabled')
    def turnto_client():
        nonlocal NET_FLAG
        NET_FLAG = network.NetType.Client
        statustext.set("本机作为客户端")
        title_label.config(text='请输入目标服务器的IP和端口号')
        ip_entry.config(state='normal')
    def clear_log():
        log_window.config(state='normal')
        log_window.delete('1.0',tk.END)
        log_window.config(state='disabled')
    def clear_msg():
        msg_history.config(state='normal')
        msg_history.delete('1.0',tk.END)
        msg_history.config(state='disabled')
    def connect_or_disconnect():
        nonlocal FIRST_LOG
        if not OPEN_FLAG:
            if FIRST_LOG:
                log_window.config(state='normal')
                log_window.delete('1.0',tk.END)
                log_window.config(state='disabled')
                FIRST_LOG = False
            connect()
        else:
            disconnect()
    
    def disconnect():
        nonlocal ROLE,OPEN_FLAG
        if isinstance(ROLE,(network.Client,network.Server)):
            ROLE.send_disconnection()
            time.sleep(0.2)
            ROLE.close()
        time.sleep(0.1)
        ip_entry.config(state='normal')
        port_entry.config(state='normal')
        S1.config(state='normal')
        S2.config(state='normal')
        OPEN_FLAG = False
        with CONNECT_LOCK:
            ROLE = None    
        connect_button.config(text='连接')
        statustext.set('已成功断开！')
        
    
    def connect():
        nonlocal ROLE, OPEN_FLAG
        res = messagebox.askokcancel('提示','是否确认以上信息正确？\n连接之后无法修改本机身份、IP及端口信息?')
        if not res:
            return
        if not check():
            messagebox.showerror('警告','IP或端口的格式存在错误!')
            return
        ip = ip_entry.get()
        port = int(port_entry.get())
        ip_entry.config(state='disabled')
        port_entry.config(state='disabled')
        S1.config(state='disabled')
        S2.config(state='disabled')
        if NET_FLAG == network.NetType.Server:
            ROLE = network.Server('',port)
            ROLE.init_bind()
            OPEN_FLAG = True
            threading.Thread(target=ROLE.msg_rev_thread).start()
            threading.Thread(target=receive_msg_thread,args=(0.25,)).start()
            statustext.set('服务器端口已开启！')
            measure_delay_button.config(state='normal')
            connect_button.config(text='断开')
        else:
            statustext.set('请等待客户端连接结果...')
            root.update()
            ROLE = network.Client(ip,port)
            res = ROLE.init_connect()
            if not res:
                disconnect()
                OPEN_FLAG = False
                connect_button.config(text='连接')
                statustext.set('客户端连接失败！')
                measure_delay_button.config(state='disabled')
                return
            OPEN_FLAG = True
            measure_delay_button.config(state='normal')
            ROLE.send_netstate()
            threading.Thread(target=ROLE.msg_rev_thread).start()
            threading.Thread(target=receive_msg_thread,args=(0.25,)).start()
            statustext.set('客户端连接成功！')
            connect_button.config(text='断开')

    def check()->bool:
        ip = ip_entry.get()
        port = port_entry.get()
        ip_res = re.search('^\d*[.]\d*[.]\d*[.]\d*$',ip)
        if ip_res is None and NET_FLAG == network.NetType.Client:
            return False
        try:
            port = int(port)
            if not (port>=0 and port<65536):
                return False
        except ValueError:
            return False
        return True
    
    def receive_msg_thread(wait_time=0.25):
        while OPEN_FLAG:
            temp_time = time.time()
            try:
                with ROLE.log_lock:
                    log_buff = deepcopy(ROLE.log_buff)
                    ROLE.log_buff.clear()
                with ROLE.content_lock:
                    content_buff = deepcopy(ROLE.content_buff)
                    ROLE.content_buff.clear()
                if len(log_buff)>0:
                    for log in log_buff:
                        log_window.config(state='normal')
                        log_window.insert(tk.END,'[{}]-{}\n'.format(*log))
                        log_window.insert(tk.END,'\n')
                        log_window.see(tk.END)
                        log_window.config(state='disabled')
                if len(content_buff)>0:
                    for content in content_buff:
                        msg_history.config(state='normal')
                        msg_head = '[对方]-{}:\n'.format(content[0])
                        msg_content = '{}\n'.format(content[1])
                        msg_history.insert(tk.END,msg_head,'left-color')
                        msg_history.insert(tk.END,msg_content,'left')
                        msg_history.see(tk.END)
                        msg_history.config(state='disabled')
                now = time.time()
                if now - temp_time < wait_time:
                    time.sleep(wait_time - now + temp_time)
            except AttributeError:
                break
            else:
                pass
        return
            
    def insert_msg(event=None):
        def insert_msg_thread():
            msg_history.config(state='normal')
            msg_tuple = utils.msg_with_time(msg_str)
            msg_head = '[本机]-{}:\n'.format(msg_tuple[0])
            msg_content = '{}\n'.format(msg_tuple[1])
            msg_history.insert(tk.END,msg_head,'right-color')
            msg_history.insert(tk.END,msg_content,'right')
            msg_history.see(tk.END)
            msg_history.config(state='disabled')
            time.sleep(0.01)
            msg_send.delete('1.0',tk.END)
        msg_str = msg_send.get('1.0',tk.END)
        threading.Thread(target=insert_msg_thread).start()
        if not OPEN_FLAG:
            log_window.config(state='normal')
            log_window.insert(tk.END,'[{}]-{}\n'.format(*utils.msg_with_time('断线，消息未发送')))
            log_window.see(tk.END)
            log_window.config(state='disabled')
        else:
            ROLE.send_msg(msg_str)

    def on_closing():
        globalset.win_open['net'] = False
        statustext.set('等待断开连接...')
        root.update()
        disconnect()
        time.sleep(0.3)
        root.destroy()
    
    def measure_delay():
        def measure_delay_thread():
            statustext.set('测速中...')
            root.update()
            res = ROLE.measure_delay()
            if res == -1:
                statustext.set('连接错误')
            else:
                statustext.set('[{:s}] 延时:{:.2f}ms 丢包率:{:.2%}'.format(utils.pretty_time(time.time()),ROLE.info['delay'],1-ROLE.info['rev']))
        if not OPEN_FLAG:
            log_window.config(state='normal')
            log_window.insert(tk.END,'[{}]-{}\n'.format(*utils.msg_with_time('断线，无法测速')))
            log_window.see(tk.END)
            log_window.config(state='disabled')
        else:
            if ROLE is None:
                log_window.config(state='normal')
                log_window.insert(tk.END,'[{}]-{}\n'.format(*utils.msg_with_time('未知错误，无法测速')))
                log_window.see(tk.END)
                log_window.config(state='disabled')
                statustext.set('未知错误，请尝试重连')
            else:
                threading.Thread(target=measure_delay_thread).start()
        

    if globalset.win_open['net']:
        messagebox.showerror('警示','请勿重复打开窗口。')
        return
    with open('config.yml','r')as f:
        CONFIG = yaml.load(f,yaml.SafeLoader)['net']
    root = tk.Toplevel()
    globalset.win_open['net'] = True
    root.title('联机')
    root.iconphoto(True,tk.PhotoImage(file=CONFIG['icon']))
    statustext = tk.StringVar() 
    statustext.set( '本机作为客户端' ) 
    statusbar = tk.Label(root, textvariable=statustext,relief=tk.SUNKEN, anchor= 'w',fg='blue')
    statusbar.pack(side=tk.BOTTOM,fill=tk.X)
    F1 = tk.Frame(root)
    F1.pack(side=tk.LEFT)
    F2 = tk.Frame(root)
    F2.pack(side=tk.RIGHT)
    F01 = tk.Frame(F1)
    F01.pack(side=tk.TOP)
    F11 = tk.Frame(F1)
    F11.pack(side=tk.TOP)  # Label
    F12 = tk.Frame(F1)
    F12.pack(side=tk.TOP)  # Entry IP
    F13 = tk.Frame(F1)
    F13.pack(side=tk.TOP)  # Entry Port
    F14 = tk.Frame(F1)
    F14.pack(side=tk.TOP)  # button
    F141 = tk.Frame(F14)
    F141.pack(side=tk.TOP)
    F142 = tk.Frame(F14)
    F142.pack(side=tk.TOP)
    F15 = tk.Frame(F1)
    F15.pack(side=tk.TOP)  # log
    F21 = tk.Frame(root)
    F21.pack(side=tk.TOP)  # msg history
    F22 = tk.Frame(root)
    F22.pack(side=tk.BOTTOM) # msg send entry
    tk.Label(F01,text='切换本机身份',font=('heiti',12)).pack(side=tk.LEFT)
    S1 = tk.Button(F01,text='客户端',font=('heiti',12),command=turnto_client)
    S1.pack(side=tk.LEFT,padx=5)
    S2 = tk.Button(F01,text='服务器',font=('heiti',12),command=turnto_server)
    S2.pack(side=tk.LEFT,padx=5)
    title_label = tk.Label(F11,text='请先选择本机身份',font=('heiti',12))
    title_label.pack(side=tk.LEFT)
    tk.Label(F12,text='IP地址',font=('heiti',12),justify=tk.LEFT).pack(side=tk.LEFT)
    ip_entry = tk.Entry(F12,font=('times_new_roman',12),width=16)
    ip_entry.pack(side=tk.LEFT)
    tk.Label(F13,text='端口号',font=('heiti',12),justify=tk.LEFT).pack(side=tk.LEFT)
    port_entry = tk.Entry(F13,font=('times_new_roman',12),width=16)
    port_entry.pack(side=tk.LEFT)
    connect_button = tk.Button(F141,text='连接',font=('heiti',12),command=connect_or_disconnect)
    connect_button.pack(side=tk.LEFT,padx=5)
    measure_delay_button = tk.Button(F141,text='测速',font=('heiti',12),command=measure_delay,state='disabled')
    measure_delay_button.pack(side=tk.LEFT,padx=5)
    tk.Button(F142,text='清空日志',font=('heiti',12),command=clear_log).pack(side=tk.LEFT,padx=0)
    tk.Button(F142,text='清空消息',font=('heiti',12),command=clear_msg).pack(side=tk.LEFT,padx=5)
    log_window = scrolledtext.ScrolledText(F15,width=35,height=8,font=('songti',9),bg='black',fg='white')
    log_window.pack(side=tk.BOTTOM,pady=5)
    log_window.insert(tk.END,'日志窗口\n尚未连接到计算机\n')
    log_window.config(state='disabled')
    msg_win_length = 30
    msg_history = scrolledtext.ScrolledText(F21,width=msg_win_length,height=15,font=('songti',9))
    msg_history.pack(side=tk.TOP)
    msg_history.config(state='disabled')
    msg_history.tag_config('left',justify=tk.LEFT)
    msg_history.tag_config('right',justify=tk.RIGHT)
    msg_history.tag_config('left-color',justify=tk.LEFT,foreground='red')
    msg_history.tag_config('right-color',justify=tk.RIGHT,foreground='blue')
    msg_send = scrolledtext.ScrolledText(F22,width=msg_win_length,height=3,font=('songti',9))
    msg_send.pack(side=tk.TOP,pady=5)
    msg_send.bind('<Return>',insert_msg)
    NET_FLAG = network.NetType.Client
    OPEN_FLAG = False
    CONNECT_LOCK = threading.Lock()
    FIRST_LOG = True
    ROLE = None
    root.protocol('WM_DELETE_WINDOW', on_closing)
    root.mainloop()
    
    
    