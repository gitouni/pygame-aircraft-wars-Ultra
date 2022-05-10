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
from utils import Info
# interface import
from interface import run_lab
import tkinter as tk
from tkinter import messagebox
from PIL import Image,ImageTk
import threading
from copy import deepcopy


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
                    player.movng_down = False
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



def create_scene(player:fighter,background:pygame.Surface,player_info:Info):
    max_scene_time = 0
    for scene_info in scenes:
        scene_class[scene_info['type']].create(scene_info,scene_list,scene_time,background,
                                               hook_player=player,hook_global_info=player_info,
                                               hook_enemy_group=enemy_Group,
                                               hook_enemyfire_group=enemyfire_Group,
                                               hook_background_group=background_Group,
                                               init_time=init_time)
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
    
    icon_pos = [(5,5),(65,5),(125,5),(185,2),(275,2)] # icon的topleft坐标
    
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
    gold_font_surface = gold_font.render(f":{player_info.gold}",True,[255,255,255])
    diamond_font_surface = diamond_font.render(f":{player_info.diamond}",True,[255,255,255])
    score_font_surface = score_font.render(f"{player_info.score}",True,[180,255,255])
    time_font_surface = time_font.render("{:.2f}s".format((pygame.time.get_ticks()-init_time)/1000.0),True,[255,100,100])
    screen.blit(gold_font_surface,GOLD_POS)
    screen.blit(diamond_font_surface,DIAMOND_POS)
    screen.blit(score_font_surface,SCORE_POS)
    screen.blit(time_font_surface,TIME_POS)
    
def run_main():
    def quit_main():
        quit_game()
        root.destroy()
    SIGN_POS = (10,190)
    BUTTON1_POS = (60,40)
    BUTTON2_POS = (60,120)
    BUTTON_SIZE = (100,30)
    root = tk.Tk()
    root.title('Aircraft-War-Ultra')
    win_width, win_height = CONFIG['interface']['screen_size']
    root.geometry('{:d}x{:d}'.format(win_width,win_height))
    canvas = tk.Canvas(root,height=win_height, width=win_width,
        bd=0, highlightthickness=0)
    img = Image.open(CONFIG['interface']['background_img'])
    photo = ImageTk.PhotoImage(img)
    canvas.create_image(0,0,anchor='nw',image=photo)
    canvas.pack()
    sign_tx = canvas.create_text(*SIGN_POS,font=('arial',14,'bold'),anchor='nw',fill="white")
    canvas.insert(sign_tx,1,'Made by gitouni')
    button1 = tk.Button(root,text='开始游戏',font=('heiti',14,'bold'),command=run_game,background='yellow')
    button2 = tk.Button(root,text='改造中心',font=('heiti',14,'bold'),command=lambda set=gameset: run_lab(set),background='#8823BA')
    button1.pack()
    button2.pack()
    canvas.create_window(*BUTTON1_POS,width=BUTTON_SIZE[0],height=BUTTON_SIZE[1],window=button1)
    canvas.create_window(*BUTTON2_POS,width=BUTTON_SIZE[0],height=BUTTON_SIZE[1],window=button2)
    root.protocol('WM_DELETE_WINDOW', quit_main)
    root.mainloop()

# 运行游戏界面
def run_game():
    player_info = Info(gameset.gold,gameset.diamond)
    player_info.has_success = False
    player_info.has_fail = False
    def failed():
        threading.Thread(target=utils.play_music,args=(pygame.mixer.Sound(CONFIG['setting']['fail_sound_file']),)).start()
        
    def succeeded():
        threading.Thread(target=utils.play_music,args=(pygame.mixer.Sound(CONFIG['setting']['success_sound_file']),)).start()
            
    if not pygame.get_init():
        pygame.init()  # 初始化背景设置
    if not pygame.font.get_init():
        pygame.font.init() # 初始化字体设置
    if not pygame.mixer.get_init():
        pygame.mixer.init(11025)  # 音乐初始化
        pygame.mixer.music.set_volume(8)  # 音量初始化
    display_font = pygame.font.SysFont('arial', 40, bold=True)
    screen = pygame.display.set_mode(screen_size)
    background = pygame.Surface((gamescreen_size[0]+100,gamescreen_size[1]+100))  # blit can receive negative coordinates rather than larger than window size
    pygame.display.set_caption("空中游侠")
    
    # 渐变显示窗口
    for i in range(11):
        screen.fill(tuple([255*(1-i/10) for _ in screen_bg_color]))
        time.sleep(0.03)
        pygame.display.flip()
    
    #开始游戏
    player = fighter(background,screen,enemy_Group,bullet_Group,background_Group)
    player.game_set(gameset) # 使用该游戏设置
    player.blitme()
    pygame.display.flip()
    max_scene_time = create_scene(player,background,player_info)
    now = pygame.time.get_ticks()
    init_time = now
    system_update_time()
    running = True
    while running:
        # 监视屏幕
        running = event_check(player)
        # 让最近绘制的屏幕可见
        if(pygame.time.get_ticks()-now > sim_interval): 
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
    gameset.save()
    pygame.font.quit()
    pygame.quit()
    clear_sprite(enemyfire_Group)
    clear_sprite(enemy_Group)
    clear_sprite(bullet_Group)
    clear_sprite(background_Group)
    scene_list.clear()
    scene_time.clear()   


# 运行改装中心界面
#def run_lab_interface():
#    
# 运行游戏
if __name__ == "__main__":

    with open("config.yml",'r')as f:
        CONFIG = yaml.load(f,yaml.SafeLoader)
    
    gameset = game_set() # 游戏设置类
    gameset.load()
    with open(CONFIG['setting']['scene_path'],'r')as f:
        scenes = json.load(f)
    HIGH_SCORE = gameset.high_score
    running = True
    screen_size = CONFIG['setting']['screen_size'] # 完整屏幕的分辨率
    statebar_size = CONFIG['setting']['status_bar_size'] # 状态栏分辨率
    gamescreen_size = CONFIG['setting']['gamescreen_size']
    screen_bg_color = CONFIG['setting']['background_color']
    sim_interval = CONFIG['setting']['sim_interval']
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
    DIAMOND_POS = (300,5)
    SCORE_POS = (340,5)
    TIME_POS = (410,5)
    
    
    bullet_Group = pygame.sprite.Group() # player的子弹群
    enemy_Group = pygame.sprite.Group() # 敌机群
    enemyfire_Group = pygame.sprite.Group() # 敌军的子弹群
    background_Group = pygame.sprite.Group() # 背景动画群
    
    background_img = pygame.image.load(os.path.join("background_jpg","img_bg_1.jpg"))  # 背景图片
    bg_size = background_img.get_size()
    bg_resize = (screen_size[0],int(screen_size[0]/bg_size[0]*bg_size[1]))
    background_img = pygame.transform.scale(background_img,bg_resize)
    bg_rollv = CONFIG['setting']['bg_rollv']  # rolling speed
    scene_time = []
    scene_list = list()
    scene_class = dict(scene1=scene1,scene2=scene2)
    init_time = pygame.time.get_ticks()
    run_main()
    

