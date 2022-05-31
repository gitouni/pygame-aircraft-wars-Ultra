# coding=utf-8
import os
import time
import re
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
import json
from Game_set import game_set
from elements import fighter
import yaml
import utils
from scene import scene1,scene2
from utils import Info, Setting
# interface import
import interface
from interface import run_lab, run_help, run_account, run_scene_loading, run_skin, run_net
import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image,ImageTk
import threading

class AutoGameRun:
    def __init__(self,player1_dict:dict,player2_dict:dict,player1_skin_index:int,player2_skin_index:int,
                 background_jpg:str,sim_interval:float,volume:float):
        self.player1 = fighter()

def clear_sprite(group:pygame.sprite.Group):
    for sprite in group.sprites():
        sprite.kill()

def collide_detect(player:fighter):
    myfire_collide = pygame.sprite.groupcollide(enemy_Group,bullet_Group,False,False)
    for unit in myfire_collide.keys():
        if utils.transgress_detect(unit.rect):
            continue
        hit_bullets = myfire_collide[unit] # 与敌机碰撞的子弹列表
        for blt in hit_bullets:
            collide_xy = pygame.sprite.collide_mask(unit,blt)
            if collide_xy:
                unit.hurt(blt.damage) # 对敌机造成子弹的伤害
                blt.dead()  # 组中删除子弹
    if player.alive_:
        enemy_collide = pygame.sprite.spritecollideany(player,enemy_Group)
        if enemy_collide:
            if not utils.transgress_detect(enemy_collide.rect):
                if pygame.sprite.collide_mask(player,enemy_collide):            
                    enemy_collide.hurt(player.HP) # 敌军受到玩家撞击伤害
                    player.hurt(enemy_collide.collide_damage) # 玩家受到敌军撞击伤害
        enemyfire_collide = pygame.sprite.spritecollideany(player,enemyfire_Group)
        if enemyfire_collide:
            if pygame.sprite.collide_mask(player,enemyfire_collide):
                player.hurt(enemyfire_collide.damage) # 玩家受到敌军火力伤害
                enemyfire_collide.dead() # 删除敌军子弹
    



# 事件检查函数
def event_check(player:fighter) -> bool:
    running = True
    for event in pygame.event.get():
        if event.type == pygame.QUIT:  # 检测到按退出键，实施软退出
            running = False
            return
        if player.alive_: # 玩家阵亡时不再响应控制按键
            if event.type == pygame.KEYDOWN:  # 检测到有键按下时动作，相反的两个动作不能冲突抵消
                if event.key == pygame.K_RIGHT:
                    player.moving_right = True
                    player.moving_left = False
                elif event.key == pygame.K_LEFT:
                    player.moving_left = True
                    player.moving_right = False
                if event.key == pygame.K_UP:
                    player.moving_up = True
                    player.moving_down = False
                elif event.key == pygame.K_DOWN:
                    player.moving_down = True
                    player.moving_up = False
                if event.key == pygame.K_f:
                    player.shooting = not player.shooting
                if event.key == pygame.K_w:
                    player.shoot1, player.shoot2, player.shoot3 = True,True,False
                if event.key == pygame.K_q:
                    player.shoot1, player.shoot2, player.shoot3 = True,False,False
                if event.key == pygame.K_e:
                    player.shoot1, player.shoot2, player.shoot3 = True,True,True
                if event.key == pygame.K_SPACE:
                    player.launching = True
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_RIGHT:
                    player.moving_right = False
                elif event.key == pygame.K_LEFT:
                    player.moving_left = False
                if event.key == pygame.K_UP:
                    player.moving_up = False
                elif event.key == pygame.K_DOWN:
                    player.moving_down = False
    return running

# 场景检查函数
def scene_check(now):
    remove_id = []
    for i,scene in enumerate(scene_list):
        if not scene.need_to_end:
            if now - init_time > scene_time[i]*1000:
                scene.update()
        else:
            remove_id.append(i)
    if remove_id:
        remove_id.reverse()  # 倒序删除，不影响数组其他元素顺序
        for index in remove_id:
            del scene_list[index]  # delete scene and free memory
            del scene_time[index]



def create_scene(player:fighter,background:pygame.Surface,player_info:Info,volume_multiply:float=1.0):
    max_scene_time = 0
    for scene_info in GLOBAL_SET.scenes:
        scene_class[scene_info['type']].create(scene_info,scene_list,scene_time,background,
                                               hook_player=player,hook_global_info=player_info,
                                               hook_enemy_group=enemy_Group,
                                               hook_enemyfire_group=enemyfire_Group,
                                               hook_background_group=background_Group,
                                               sim_interval=SIM_INTERVAL,
                                               init_time=init_time,
                                               volume_multiply=volume_multiply)
        max_scene_time = max(max_scene_time,scene_info['scene_time'])
    return max_scene_time
# 更新系统时间
def system_update_time():
    global init_time
    init_time = pygame.time.get_ticks()
# 绘制飞船状态栏

def draw_statebar(screen:pygame.Surface,player:fighter,init_time:int,player_info:Info):
    # 分隔线
    pygame.draw.rect(screen,(0,0,0),pygame.Rect((0,0),statebar_size))
    pygame.draw.line(screen,(0,255,0),(0,statebar_size[1]-1),\
                     (statebar_size[0],statebar_size[1]-1),2)
    # 图标参数
    icon_size = (20,20) # 小图标大小
    
    icon_pos = [(5,5),(65,5),(125,5),(185,2),(260,2)] # icon的topleft坐标
    
    icon_list = list()
    img = pygame.image.load('icon_png/heart.png')
    img = pygame.transform.scale(img,icon_size)
    icon_list.append(img)
    img = pygame.image.load('icon_png/lightning.png')
    img = pygame.transform.scale(img,icon_size)
    icon_list.append(img)
    img = pygame.image.load('icon_png/snowflake.png')
    img = pygame.transform.scale(img,icon_size)
    icon_list.append(img)    
    img = pygame.image.load('icon_png/gold.png')
    img = pygame.transform.scale(img,(25,25))
    icon_list.append(img)
    img = pygame.image.load('icon_png/diamond.png')
    img = pygame.transform.scale(img,(30,25))
    icon_list.append(img)
    for i in range(5):
        screen.blit(icon_list[i],icon_pos[i])    
    rect_pos = [(27,5),(87,5),(147,5)] # 矩形topleft坐标
    Rect_pos = [(26,5),(86,5),(146,5)]
    rect_width = [player.HP/player.HP_max*29,player.energy/player.energy_max*29,\
                  player.cooling/player.cooling_max*29] # 矩形宽度
    rect_color = [(255,0,0),(255,0,255),(200,200,255)]
    for i in range(3):
        if rect_width[i] > 0:# 若矩形宽度不为0
            pygame.draw.rect(screen,rect_color[i],pygame.Rect(rect_pos[i],(rect_width[i],20)),0)
        # 填充部分
        pygame.draw.rect(screen,(200,200,200),pygame.Rect(Rect_pos[i],(30,20)),1)
        # 外框
    gold_font = pygame.font.SysFont('arial', 15, bold=True)
    diamond_font = pygame.font.SysFont('arial', 15, bold=True)
    score_font = pygame.font.SysFont('arial', 15, bold=True,italic=True)
    time_font = pygame.font.SysFont('arial',15,bold=True)
    gold_font_surface = gold_font.render(utils.pretty_number(player_info.gold),True,[255,255,255])
    diamond_font_surface = diamond_font.render(utils.pretty_number(player_info.diamond),True,[255,255,255])
    score_font_surface = score_font.render(utils.pretty_number(player_info.score),True,[180,255,255])
    time_font_surface = time_font.render("{:.2f}s".format((pygame.time.get_ticks()-init_time)/1000.0),True,[255,100,100])
    screen.blit(gold_font_surface,GOLD_POS)
    screen.blit(diamond_font_surface,DIAMOND_POS)
    screen.blit(score_font_surface,SCORE_POS)
    screen.blit(time_font_surface,TIME_POS)

def run_setting(globalset:utils.Setting,info:tk.StringVar)->None:
    def get_value()->None:
        global SIM_INTERVAL,VOLUME
        SIM_INTERVAL, VOLUME = sim_interval_list[int(scale1.get())], volume_list[int(scale2.get())]
        info.set('设置成功！')
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
    F1.pack(side='top')
    F2 = tk.Frame(root,borderwidth=1,highlightthickness=1)
    F2.pack(side='top')
    tk.Label(F1,text='低',font=('songti',10)).pack(side='left')
    tk.Label(F2,text='小',font=('songti',10)).pack(side='left')
    scale1 = tk.Scale(F1,cursor='circle',label='游戏性',length=120,orient=tk.HORIZONTAL,showvalue=0,from_=0,to=len(sim_interval_list)-1,resolution=1)
    scale2 = tk.Scale(F2,cursor='circle',label='音量',length=120,orient=tk.HORIZONTAL,showvalue=0,from_=0,to=len(volume_list)-1,resolution=1)
    scale1.pack(side='left')
    scale2.pack(side='left')
    scale1.set(sim_interval_index)
    scale2.set(volume_index)
    tk.Label(F1,text='高',font=('songti',10)).pack(side='left')
    tk.Label(F2,text='大',font=('songti',10)).pack(side='left')
    root.protocol('WM_DELETE_WINDOW',get_value)
    root.mainloop()

def _run_game():
    threading.Thread(target=run_game).start()

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
    def quit_main():
        for _,value in GLOBAL_SET.win_open.items():
            if value:
                messagebox.showwarning('警示','请关闭其他所有子窗口再关闭主程序。')
                return
        root.destroy()

    SIGN_POS = CONFIG['main']['sign_pos']
    account_pos = CONFIG['main']['account_pos']
    play_pos = CONFIG['main']['start_pos']
    skin_pos = CONFIG['main']['skin_pos']
    normal_level_pos = CONFIG['main']['normal_level_pos']
    lab_pos = CONFIG['main']['lab_pos']
    net_pos = CONFIG['main']['net_pos']
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
                        image=account_icon,compound='left')
    normal_lvl_icon = interface.Image_load(CONFIG['main']['normal_level_icon'],small_size)
    button1 = tk.Button(root,text='普通模式',font=('heiti',14,'bold'),command=lambda info=statustext: _run_scene_loading(info),
                        image=normal_lvl_icon,compound='left')
    start_icon = interface.Image_load(CONFIG['main']['start_icon'],small_size)
    button2 = tk.Button(root,text='开始游戏',font=('heiti',14,'bold'),command=_run_game,
                        image=start_icon,compound='left')
    lab_icon = interface.Image_load(CONFIG['main']['lab_icon'],small_size)
    button3 = tk.Button(root,text='实验中心',font=('heiti',14,'bold'),command=_run_lab,
                        image=lab_icon,compound='left')
    net_icon = interface.Image_load(CONFIG['main']['net_icon'],small_size)
    button4 = tk.Button(root,text='联机对战',font=('heiti',14,'bold'),command=_run_net,
                        image=net_icon,compound='left')
    help_img = interface.Image_load(CONFIG['main']['help_icon'],small_size)
    setting_img = interface.Image_load(CONFIG['main']['setting_icon'],small_size)
    skin_img = interface.Image_load(CONFIG['main']['skin_icon'],small_size)
    help_button = tk.Button(root,bg=CONFIG['main']['help_color'],image=help_img,command=_run_help)
    setting_button = tk.Button(root,bg=CONFIG['main']['setting_color'],image=setting_img,command=lambda info=statustext: _run_setting(info))
    skin_button = tk.Button(root,bg=CONFIG['main']['setting_color'],image=skin_img,command=lambda info=statustext: _run_skin(info))
    help_button.pack()
    setting_button.pack()
    skin_button.pack()
    canvas.create_window(*help_pos,width=small_size[0],height=small_size[1],window=help_button)
    canvas.create_window(*setting_pos,width=small_size[0],height=small_size[1],window=setting_button)
    canvas.create_window(*skin_pos,width=small_size[0],height=small_size[1],window=skin_button)
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
            recent_name = os.path.splitext(recent_file)[0]
            statustext.set("欢迎, {}".format(recent_name))
    root.protocol('WM_DELETE_WINDOW', quit_main)
    init_pygame()
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
def run_game():
    if not gameset.path:
        start = messagebox.askyesno("Warning","您尚未加载任何账户，游戏记录将无法被保存，是否继续？")
        if not start:
            return
    if GLOBAL_SET.win_open['game']:
        messagebox.showerror('警示','请勿重复打开窗口')
        return
    init_pygame()
    GLOBAL_SET.win_open['game'] = True
    GLOBAL_SET.has_saved = False
    player_info = Info(gameset.gold,gameset.diamond)
    player_info.has_success = False
    player_info.has_fail = False
    def failed():
        threading.Thread(target=utils.play_music,args=(pygame.mixer.Sound(CONFIG['setting']['fail_sound_file']),VOLUME)).start()
        
    def succeeded():
        threading.Thread(target=utils.play_music,args=(pygame.mixer.Sound(CONFIG['setting']['success_sound_file']),VOLUME)).start()
            
    background_img = pygame.image.load(GLOBAL_SET.background_jpg)  # 背景图片
    background_img = pygame.transform.scale(background_img,bg_resize)
    display_font = pygame.font.SysFont('arial', 40, bold=True)
    screen = pygame.display.set_mode(screen_size)
    background = pygame.Surface((gamescreen_size[0]+100,gamescreen_size[1]+100))  # blit can receive negative coordinates rather than larger than window size
    pygame.display.set_caption("pygame-aircraft-ultra")
    pygame.display.set_icon(pygame.image.load(CONFIG['setting']['game_ico']))
    # 渐变显示窗口
    for i in range(11):
        screen.fill(tuple([255*(1-i/10) for _ in screen_bg_color]))
        time.sleep(0.03)
        pygame.display.flip()
    
    #开始游戏
    player = fighter(background,screen,enemy_Group,bullet_Group,background_Group,SIM_INTERVAL,VOLUME,GLOBAL_SET.player_index)
    player.game_set(gameset) # 使用该游戏设置
    player.blitme()
    pygame.display.flip()
    max_scene_time = create_scene(player,background,player_info,VOLUME)
    now = pygame.time.get_ticks()
    init_time = now
    system_update_time()
    running = True
    while running:
        # 监视屏幕
        running = event_check(player)
        # 让最近绘制的屏幕可见
        if(pygame.time.get_ticks()-now > SIM_INTERVAL): 
            now = pygame.time.get_ticks()
            blit_ad = int((now-init_time)/1000*bg_rollv % bg_resize[1])
            background.blit(background_img,(0,blit_ad-bg_resize[1]+30))
            background.blit(background_img,(0,blit_ad+30))
            scene_check(now)
            collide_detect(player)            
            bullet_Group.update()
            if player.alive_:
                player.update()    
            enemyfire_Group.update()
            background_Group.update()
            screen.blit(background,(0,30))
            draw_statebar(screen,player,init_time,player_info) # 更新状态栏
            if (not player.alive_):
                if not player_info.has_fail:
                    failed()
                    player_info.has_fail = True
                elif (now - init_time) % 1000 > 500:
                    display_font_surface = display_font.render('Mission Failed',True,[255,0,0])
                    screen.blit(display_font_surface,CONFIG['setting']['fail_font_pos'])
            if now - init_time > max_scene_time*1000 and len(enemy_Group.sprites())==0:
                if not player_info.has_success:
                    succeeded()
                    player_info.has_success = True
                elif (now - init_time) % 1000 > 500:
                    success_font_surface = display_font.render('Mission Accomplished',True,[255,255,255])
                    screen.blit(success_font_surface,CONFIG['setting']['success_font_pos'])
            pygame.display.flip()  # 更新画面
    gameset.gold = int(player_info.gold)
    gameset.diamond = int(player_info.diamond)
    gameset.high_score = max(gameset.high_score,player_info.score)
    quit_game()

def quit_game():
    if gameset.path:
        gameset.save()
    pygame.font.quit()
    pygame.quit()
    GLOBAL_SET.win_open['game'] = False
    clear_sprite(enemyfire_Group)
    clear_sprite(enemy_Group)
    clear_sprite(bullet_Group)
    clear_sprite(background_Group)
    scene_list.clear()
    scene_time.clear()   


# 运行游戏
if __name__ == "__main__":

    with open("config.yml",'r')as f:
        CONFIG = yaml.load(f,yaml.SafeLoader)
    
    gameset = game_set() # 游戏设置类
    GLOBAL_SET = Setting()
    gameset.gold = CONFIG['account']['initial_gold']
    gameset.diamond = CONFIG['account']['initial_diamond']

    running = True
    screen_size = CONFIG['setting']['screen_size'] # 完整屏幕的分辨率
    statebar_size = CONFIG['setting']['status_bar_size'] # 状态栏分辨率
    gamescreen_size = CONFIG['setting']['gamescreen_size']
    screen_bg_color = CONFIG['setting']['background_color']
    SIM_INTERVAL = CONFIG['setting']['sim_interval']
    VOLUME = 1.0
    enemy_path = CONFIG['enemy']['path']
    enemyfire_path = CONFIG['enemyfire']['path']
    bullet_path = CONFIG['bullet']['path']
    player_dict = CONFIG['player']
    enemy_dict = utils.csv2dict(CONFIG['enemy']['setting'])
    enemyfire_dict = utils.csv2dict(CONFIG['enemyfire']['setting'])
    bullet_dict = utils.csv2dict(CONFIG['bullet']['setting'])
    enemy_names = [os.path.splitext(name)[0] for name in enemy_dict['filename']]
    special_enemyfire_id = [enemyfire_id for enemyfire_id in range(len(enemyfire_dict['filename'])) if 'a' in re.search('[_]\w*',enemyfire_dict['filename'][enemyfire_id]).group()]
    GOLD_POS = (210,5)
    DIAMOND_POS = (285,5)
    SCORE_POS = (340,5)
    TIME_POS = (410,5)
    
    
    bullet_Group = pygame.sprite.Group() # player的子弹群
    enemy_Group = pygame.sprite.Group() # 敌机群
    enemyfire_Group = pygame.sprite.Group() # 敌军的子弹群
    background_Group = pygame.sprite.Group() # 背景动画群
    
    background_img = pygame.image.load(GLOBAL_SET.background_jpg)  # 背景图片
    bg_size = background_img.get_size()
    bg_resize = (screen_size[0],int(screen_size[0]/bg_size[0]*bg_size[1]))
    background_img = pygame.transform.scale(background_img,bg_resize)
    bg_rollv = CONFIG['setting']['bg_rollv']  # rolling speed
    scene_time = []
    scene_list = list()
    scene_class = dict(scene1=scene1,scene2=scene2)
    init_time = pygame.time.get_ticks()
    run_main()
    

