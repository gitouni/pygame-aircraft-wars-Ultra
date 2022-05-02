# coding=utf-8
import os
import time
import pygame
# extend import
import pygame.mixer
import pygame.sprite
import pygame.time
import pygame.transform
import pygame.image
import pygame.font
import pygame.mask
import pygame.display

from random import randint
from math import sqrt,pi,cos,sin,atan2
from Game_set import game_set
import numpy as np
from Scene_set import scenes
import threading
import yaml
import utils

class Info:
    def __init__(self,gold=0,diamond=0,score=0):
        self.gold = gold
        self.diamond = diamond
        self.score = score
        self.lock = threading.Lock()
    def update(self,gold,diamond,score):
        with self.lock:
            self.gold = gold
            self.diamond = diamond
            self.score = score


class button():
    def __init__(self,myscreen,ID,text,function_ID):
        self.screen = myscreen
        self.state = 'up'
        self.ID = ID
        self.function_ID = function_ID
        self.text = text
        self.image_ad = 'button_png/button{0}_{1}.png'.format(self.ID,self.state)
        self.image = pygame.image.load(self.image_ad)
        self.rect = self.image.get_rect()
        font0 = pygame.font.SysFont('kaiti',20)
        self.txt_img = font0.render(text,1,(0,0,0))
        self.txt_rect =self.txt_img.get_rect()
    def blitme(self):
        # 先放矩形后放字体
        self.screen.blit(self.image,self.rect)
        self.screen.blit(self.txt_img,center_text(self.rect,self.txt_rect))
    def tran_state(self,state):
        self.state = state
        self.image_ad = 'button_png/button{0}_{1}.png'.format(self.ID,self.state)
        self.image = pygame.image.load(self.image_ad)
        
# 定义开始界面
class interface():
    def __init__(self,myscreen,button_dict,png_dict,bg_img):
        self.screen = myscreen
        self.button_dict = button_dict
        self.png_dict = png_dict
        self.bg_img = bg_img
        self.time = pygame.time.get_ticks()
        self.function_ID = 0
        '''
        0:维持主界面
        1:运行游戏
        2:改造中心
        -1:退出游戏
        '''
        self.respond = False # 是否正在响应为假时才响应事件
        self.responded = False
    def reset_state(self): # 复位响应状态到原始状态
        self.respond = False
        self.responded = False
    def update_time(self):
        self.time = pygame.time.get_ticks()
    def update(self):
        self.screen.blit(self.bg_img,(0,0))
        for button in self.button_dict.keys():
            button.rect.center = self.button_dict[button]
            button.blitme()
        for png in self.png_dict.keys():
            png_rect = png.get_rect()
            png_rect.center = self.png_dict[png]
            self.screen.blit(png,png_rect)
        pygame.display.update()
    def mouse_check(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                gameset.gold = int(Global_info.gold)
                gameset.diamond = int(Global_info.diamond)
                gameset.high_score = max(gameset.high_score,Global_info.score)
                gameset.save()
                pygame.font.quit()
                pygame.quit()
                self.function_ID = -1
            elif event.type == pygame.MOUSEMOTION:
                m_pos = pygame.mouse.get_pos()
                flag = False
                for button in self.button_dict.keys():
                    if button.rect.collidepoint(m_pos):
                        button.tran_state('select')
                        flag = True
                        self.function_ID = button.ID
                    else:
                        button.tran_state('up')
                if not flag:
                    self.function_ID = 0
            elif event.type == pygame.MOUSEBUTTONDOWN:
                m_pos = pygame.mouse.get_pos()
                for button in self.button_dict.keys():
                    if button.rect.collidepoint(m_pos):
                        button.tran_state('down')
                        self.respond = True  # 按钮正在接受响应
                        self.function_ID = button.ID
            elif event.type == pygame.MOUSEBUTTONUP:
                if self.respond: # 当按下按键在有效位置时再响应松开按键
                    m_pos = pygame.mouse.get_pos()
                    flag = False
                    for button in self.button_dict.keys():
                        if button.rect.collidepoint(m_pos) and self.function_ID == button.function_ID:
                            button.tran_state('up')
                            self.responded = True
                            flag = True
                    if not flag:
                        self.reset_state() # 松开按键的位置不在原按键上，复位状态

# 定义玩家
class fighter(pygame.sprite.Sprite):
    def __init__(self,myscreen):
        pygame.sprite.Sprite.__init__(self)
        self.screen = myscreen  # 坐标
        self.speed = 6
        self.rol = 0 # 横向倾斜角
        self.agl = 0
        self.img_ad = 'player_png/p{0}.png'.format(self.agl)
        self.size = (66,104)
        self.radius = sqrt(self.size[0]*self.size[1]/3.14) # 碰撞有效半径
        self.image = pygame.transform.scale(pygame.image.load(self.img_ad),self.size)  # 加载图形，并缩小像素
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()  # 占用矩形范围
        self.pos = self.rect.centerx,self.rect.centery
        self.bullet_speed = 10
        self.bullet_ID = 0
        self.bullet1_pos = self.pos[0]-0.3125*self.size[0],self.pos[1]-0.08*self.size[1]
        self.bullet2_pos = self.pos[0]+0.3125*self.size[0],self.pos[1]-0.08*self.size[1]
        self.screen_rect = screen.get_rect()  # 活动矩形范围
        self.rect.centerx = self.screen_rect.centerx # 初始化的位置
        self.rect.bottom = self.screen_rect.bottom
        self.moving_right,self.moving_left,self.moving_up,self.moving_down = False,False,False,False  # 禁用所有的行动位置
        # 以上为基本参数
        self.shooting = False
        self.shoot1 = True
        self.shoot2 = False
        self.shoot3 = False
        self.init_shooting_cd = 250 # 原有射击间隔
        self.shooting_cd =self.init_shooting_cd # 射击间隔
        # 以上为子弹参数
        self.launching = False
        self.launching_cd = 500 # 导弹射击间隔
        self.missile_num = 2
        self.missile_damge = 10
        self.missile_dir = [(0,-1),(0,-1),(-1,-1),(1,-1),(-1,0),(1,0),(-2,-1),(2,-1)]
        self.missile_pos = [self.bullet1_pos,self.bullet2_pos,self.bullet1_pos,self.bullet2_pos,
                            self.bullet1_pos,self.bullet2_pos,self.bullet1_pos,self.bullet2_pos]
        self.missile_actime = 3
        self.missile_speed_max = 5
        self.missile_flyingtime = 3
        # 以上为导弹参数
        self.HP_max = 3 # 最大血生命值
        self.HP = self.HP_max # 现有生命值
        self.energy_max = 20 # 最大能量
        self.energy = self.energy_max
        self.energy_recover = 0.05
        self.cooling_max = 10 # 最大冷却能力
        self.cooling = self.cooling_max-(self.init_shooting_cd/self.shooting_cd)*\
                      (self.shoot1+self.shoot2+self.shoot3)*5*self.shooting # 现有能量
        self.cooling_recover = 0.02
        # 以上为游戏信息参数
        self.alive_ = True
        self.shooting_time = pygame.time.get_ticks()
        self.launching_time = pygame.time.get_ticks()
        self.mp3_path = player_dict['mp3_path']
        self.bullet_sound_file = os.path.join(self.mp3_path,player_dict['bullet_sound_file'])
        self.missile_sound_file = os.path.join(self.mp3_path,player_dict['missile_sound_file'])
        self.explode_sound_file = os.path.join(self.mp3_path,player_dict['explode_sound_file'])
        self.hit_sound_file = os.path.join(self.mp3_path,player_dict['hit_sound_file'])
    def game_set(self,gameset):
        assert isinstance(gameset,game_set)
        self.HP = gameset.player_HP_list[gameset.player_HP_level]
        self.HP_max = self.HP
        self.HP_recover =  gameset.player_HP_recover_list[gameset.player_HP_recover]
        self.energy = gameset.player_energy_list[gameset.player_energy_level]
        self.energy_recover = gameset.player_energy_recover_list[gameset.player_energy_recover_level]
        self.energy_max = self.energy
        self.cooling = gameset.player_cooling_list[gameset.player_cooling_level]
        self.cooling_recover = gameset.player_cooling_recover_list[gameset.player_cooling_recover_level]
        self.cooling_max = self.cooling
        self.bullet_ID = gameset.bullet_ID
        self.shooting_cd = gameset.player_shooting_cd_list[gameset.bullet_shooting_cd_level]
        self.missile_num = gameset.missile_num_list[gameset.missile_num_level]
        self.launching_cd = gameset.missile_cd_list[gameset.missile_shooting_cd_level]
        self.missile_damge = gameset.missile_damage_list[gameset.missile_damage_level]
        self.missile_actime = gameset.missile_actime_list[gameset.missile_actime_level]
        self.missile_speed_max = gameset.missile_speed_max_list[gameset.missile_speed_max_level]
    def blitme(self):
        """在指定位置绘制飞船"""
        self.screen.blit(self.image,self.rect)
    def update_shoot_time(self):
        self.shooting_time = pygame.time.get_ticks()
    def update_launch_time(self):
        self.launching_time = pygame.time.get_ticks()
    def update_bltpos(self):
        # 更新发射子弹的位置
        self.pos = self.rect.centerx,self.rect.centery
        self.bullet1_pos = (int(self.pos[0]-0.3125*self.size[0]),int(self.pos[1]+0.08*self.size[1]))
        self.bullet2_pos = (int(self.pos[0]+0.3125*self.size[0]),int(self.pos[1]+0.08*self.size[1]))
        self.missile_pos = [self.bullet1_pos,self.bullet2_pos,self.bullet1_pos,self.bullet2_pos,
                            self.bullet1_pos,self.bullet2_pos,self.bullet1_pos,self.bullet2_pos]
    def shoot(self):
        threading.Thread(target=thread_play_music,args=(self.bullet_sound_file,0.2)).start()
        self.update_bltpos()
        if self.shoot1: # 射击点位1
            blt1 = bullet(self.screen,self.bullet1_pos,self.bullet_speed,self.bullet_ID,(0,-1))
            blt2 = bullet(self.screen,self.bullet2_pos,self.bullet_speed,self.bullet_ID,(0,-1))
            bullet_Group.add(blt1)
            bullet_Group.add(blt2)
        if self.shoot2:
            blt1 = bullet(self.screen,self.bullet1_pos,self.bullet_speed,self.bullet_ID,(-1,-1))
            blt2 = bullet(self.screen,self.bullet2_pos,self.bullet_speed,self.bullet_ID,(1,-1))
            bullet_Group.add(blt1)
            bullet_Group.add(blt2)
        if self.shoot3:
            blt1 = bullet(self.screen,self.bullet1_pos,self.bullet_speed,self.bullet_ID,(-1,0))
            blt2 = bullet(self.screen,self.bullet2_pos,self.bullet_speed,self.bullet_ID,(1,0))
            bullet_Group.add(blt1)
            bullet_Group.add(blt2)  
        
        
    def launch_missile(self):
        threading.Thread(target=thread_play_music,args=(self.missile_sound_file,)).start()
        self.update_bltpos()
        if self.missile_num > 0:
            self.update_bltpos()
            missile_num = int(min(self.missile_num,self.energy//5,self.cooling//3))
            for i in range(missile_num):
                missile0 = missile(self.screen,self.missile_pos[i],self.missile_dir[i],
                                   self.missile_actime,self.missile_speed_max,self.missile_damge,self.missile_flyingtime)
                bullet_Group.add(missile0)
            self.energy -= missile_num*5
            self.cooling -= missile_num*3
        self.launching = False
    def update(self):  # 更新飞船坐标，允许2个方向重合运动，但相互冲突的方向只能选择其一
        if self.moving_right == True and self.rect.right < self.screen_rect.right:
            self.rect.centerx += self.speed
        if self.moving_left == True and self.rect.left > 0:
            self.rect.centerx -= self.speed
        if self.moving_up == True and self.rect.top > 0:
            self.rect.bottom -= self.speed
        if self.moving_down == True and self.rect.bottom < screen_size[1]:
            self.rect.bottom += self.speed
        if self.moving_right == True and self.rol < 20:
            self.rol += 1
        if self.moving_left == True and self.rol > -20:
            self.rol -= 1
        if self.moving_left == False and self.rol < 0:
            self.rol += 1
        if self.moving_right == False and self.rol > 0:
            self.rol -= 1
        self.agl= int(self.rol//5)
        self.img_ad = 'player_png/p{0}.png'.format(self.agl)
        self.image = pygame.transform.scale(pygame.image.load(self.img_ad),self.size)
        self.mask = pygame.mask.from_surface(self.image)
        self.blitme()
        if self.shooting:
            if pygame.time.get_ticks()-self.shooting_time>self.shooting_cd:
                if self.energy > (self.shoot1+self.shoot2+self.shoot3) and self.cooling > 0: # 满足要求时保持射击
                    self.shoot() # 射击
                    self.update_shoot_time() # 更新时间
                    self.energy -= 1*(self.shoot1+self.shoot2+self.shoot3) # 消耗能量
                else:
                    self.shooting = False
        if self.launching:
            if pygame.time.get_ticks()-self.launching_time>self.launching_cd and\
               self.energy >= 5 and self.cooling >= 3:
                   self.launch_missile()
                   self.update_launch_time()
            else:
                self.launching = False
        self.update_state() # 回复能量和冷却
        
    def update_state(self):
        self.HP = np.clip(self.HP+self.HP_recover,0,self.HP_max)
        self.energy = np.clip(self.energy+self.energy_recover,0,self.energy_max)
        delta_cooling = -(self.init_shooting_cd/self.shooting_cd)*\
                      (self.shoot1+self.shoot2+self.shoot3)*0.05*self.shooting
        self.cooling = np.clip(self.cooling+self.cooling_recover+delta_cooling,0,self.cooling_max)
        
    def hurt(self,damage):
        threading.Thread(target=thread_play_music,args=(self.hit_sound_file,)).start()
        self.HP -= damage
        if self.HP < 0:
            self.dead()
            explode0 = explode(self.screen,self.rect.center)
            background_Group.add(explode0)
            self.HP = 0
            
    def dead(self):
        threading.Thread(target=thread_play_music,args=(self.explode_sound_file,)).start()
        self.alive_ = False
        self.kill()

# 子弹类
class bullet(pygame.sprite.Sprite):
    def __init__(self,screen,location,speed,ID,speed_dir):
        pygame.sprite.Sprite.__init__(self)  # 类继承
        self.screen = screen
        self.ID = ID
        self.img_ad = os.path.join(bullet_path,bullet_dict['filename'][ID])
        bullet_image = pygame.transform.scale(pygame.image.load(self.img_ad),(10,25))
        self.image = pygame.transform.rotate(bullet_image,-180/pi*atan2(speed_dir[0],-speed_dir[1]))
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect() 
        self.rect.centerx,self.rect.centery = location
        self.speed_dir = speed_dir
        self.speed = speed_tran(speed,speed_dir)
        self.damage = float(bullet_dict['damage'][self.ID]) # 子弹伤害数值
    def blitme(self):
        self.screen.blit(self.image,self.rect)
    def update(self):
        self.rect.move_ip(self.speed)
        self.blitme()
        if transgress_detect(self.rect): # 子弹越界删除
            self.kill()
    def dead(self):
        self.kill()
# 导弹类
class missile(pygame.sprite.Sprite):
    def __init__(self,screen,pos,speed_dir,ac_time,max_speed,damage,flying_time,tracktime=300):
        pygame.sprite.Sprite.__init__(self)  # 类继承
        self.screen = screen
        self.size = (20,40)
        self.init_speed = 1
        self.speed = 1
        self.speed_max = max_speed
        self.speed_dir = speed_dir
        self.ac_time = ac_time*1000 # 加速时间（毫秒）
        self.speed_vector = speed_tran(self.speed,self.speed_dir)
        self.move_dxy = [0,0]
        self.img_ad = CONFIG['player']['missile']['img']
        self.explode_sound= os.path.join(CONFIG['player']['mp3_path'],CONFIG['player']['missile']['explode_sound_file'])
        self.explode_music = pygame.mixer.Sound(self.explode_sound)
        self.agl = -180/pi*atan2(speed_dir[0],-speed_dir[1])
        self.img = pygame.transform.scale(pygame.image.load(self.img_ad),self.size)
        self.image = pygame.transform.rotate(self.img,self.agl)
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        self.rect.midbottom = pos # 位置赋值
        self.explode_size = (30,30)
        self.target = None # 锁定的单位
        self.time = pygame.time.get_ticks()
        self.lifetime = self.time
        self.tracktime = tracktime
        self.damage = damage # 导弹伤害
        self.flying_time = flying_time # 追踪时间，单位秒
    def blitme(self):
        self.screen.blit(self.image,self.rect)
    def accelerate(self):
        dt = pygame.time.get_ticks()-self.lifetime
        dv = 1/self.ac_time*dt
        self.speed = min(self.init_speed+dv,self.speed_max)
    def find_target(self):
        # 寻找目标
        target_list = list()
        for i in range(len(enemy_Group.sprites())):
            enemy0 = enemy_Group.sprites()[i]
            if enemy0.targeted == False and not transgress_detect(enemy0.rect):
                target_list.append(enemy_Group.sprites()[i])
                # 加入可攻击组和序号
        if target_list:
            self.target = target_list[randint(0,len(target_list)-1)]
        elif enemy_Group:# 若暂时未有待锁定目标且敌机组不为空
            target_list = [unit for unit in enemy_Group.sprites() if not transgress_detect(unit.rect)]
            if target_list:
                self.target = target_list[randint(0,len(target_list)-1)]
            else:
                self.target = None
        else:
            self.target = None
    def rotate(self):
        # 根据速度方向旋转自己
        self.agl = -180/pi*atan2(self.speed_dir[0],-self.speed_dir[1]) 
        self.image = pygame.transform.rotate(self.img,self.agl)
        self.mask = pygame.mask.from_surface(self.image)
    def track_target(self):
        # 追踪目标
        if self.target in enemy_Group.sprites():# 若目标仍在敌机组，追击
            self.speed_dir = tuple_minus(self.target.rect.center,self.rect.center)
        else:
            self.speed_dir = vector_rotate(self.speed_dir,pi/180*self.speed)# 自转
            self.target = None # 清除锁定
            self.find_target() # 寻找新目标
        self.accelerate()
        self.rotate()
        self.update_pos()
    def update_pos(self):
        self.speed_vector = speed_tran(self.speed,self.speed_dir)
        self.move_dxy[0] += self.speed_vector[0]
        self.move_dxy[1] += self.speed_vector[1]
        intmove_dxy = int(self.move_dxy[0]), int(self.move_dxy[1])
        self.rect.move_ip(intmove_dxy)
        self.move_dxy[0] -= intmove_dxy[0]
        self.move_dxy[1] -= intmove_dxy[1]
        self.blitme()
    def dead(self):
        if(self.target):self.target.targeted = False # 解除敌机锁定
        explode0 = explode(self.screen,self.rect.center,self.explode_size)
        background_Group.add(explode0)
        threading.Thread(target=play_music,args=(self.explode_music,)).start()
        self.kill()
    def update(self):
        if pygame.time.get_ticks()-self.lifetime > self.flying_time*1000:# 超过追踪时间自爆
            self.dead()
        elif pygame.time.get_ticks() - self.lifetime > self.tracktime:
            self.track_target() # 追踪目标
        else:
            self.accelerate()
            self.update_pos()
    def update_time(self):
        self.time = pygame.time.get_ticks()
        
# 敌军火力类
class enemy_fire(pygame.sprite.Sprite):
    def __init__(self,screen,location,speed,ID,speed_dir,scale=1):
        pygame.sprite.Sprite.__init__(self)  # 类继承
        self.screen = screen
        self.ID = ID
        self.speed_dir = speed_dir
        self.speed = speed_tran(speed,speed_dir)
        self.move_dxy = [0,0]
        self.img_ad = os.path.join(enemyfire_path,enemyfire_dict['filename'][ID])
        self.image = pygame.transform.rotate(pygame.image.load(self.img_ad),-180/pi*atan2(speed_dir[0],-speed_dir[1]))
        self.rect = self.image.get_rect() 
        self.size = int(self.rect.width*scale),int(self.rect.height*scale)
        self.image = pygame.transform.scale(self.image,self.size)
        self.rect = self.image.get_rect() 
        self.rect.centerx,self.rect.bottom = location
        self.mask = pygame.mask.from_surface(self.image)
        self.damage = float(enemyfire_dict['damage'][self.ID]) # 子弹伤害数值
    def blitme(self):
        self.screen.blit(self.image,self.rect)
    def update(self):
        self.move_dxy = [self.move_dxy[0] + self.speed[0], self.move_dxy[1] + self.speed[1]]
        intmove_dxy = int(self.move_dxy[0]), int(self.move_dxy[1])
        self.rect.move_ip(intmove_dxy)
        self.move_dxy = [self.move_dxy[0] - intmove_dxy[0], self.move_dxy[1] - intmove_dxy[1]]
        self.blitme()
        if transgress_detect(self.rect): # 子弹越界删除
            self.kill()    
    def dead(self):
        self.kill()
        
class enemy(pygame.sprite.Sprite):
    def __init__(self,myscreen,ID,pos,speed,speed_dir,bullet_speed,bullet_ID):
        pygame.sprite.Sprite.__init__(self)
        self.screen = myscreen  # 坐标
        self.ID = enemy_names.index(ID) # 敌机型号
        self.speed_dir = speed_dir # 运动方向属性
        self.speed = speed_tran(speed,self.speed_dir) # 速度属性
        self.move_dxy = [0,0]
        self.agl = -180/pi*atan2(self.speed_dir[0],-self.speed_dir[1])
        self.img_ad = os.path.join(enemy_path,enemy_dict['filename'][self.ID])
        self.init_image = pygame.image.load(self.img_ad)
        self.image = pygame.transform.rotate(self.init_image,self.agl)  # 加载图形，并缩小像素
        self.sound = pygame.mixer.Sound(CONFIG['enemy']['explode_sound_file'])
        self.hurt_sound = pygame.mixer.Sound(CONFIG['enemy']['hurt_sound_file'])
        self.gold = int(enemy_dict['gold'][self.ID])
        self.diamond = float(enemy_dict['diamond'][self.ID])
        self.score = int(enemy_dict['score'][self.ID])
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()  # 占用矩形范围
        self.size = (self.rect.width,self.rect.height)
        self.pos = self.rect.center
        self.bullet_speed = bullet_speed
        self.bullet_ID = bullet_ID
        self.bullet_pos = self.rect.center
        self.screen_rect = screen.get_rect()  # 活动矩形范围
        self.rect.center = pos
        self.shooting = False
        self.time = pygame.time.get_ticks()
        self.HP_max = float(enemy_dict['HP'][self.ID]) # 最大生命值
        self.HP = self.HP_max # 现有生命值
        self.collide_damage = self.HP # 撞击敌机会造成等同生命值的伤害
        self.i = 0
        self.n = 0
        self.p = 0
        self.data = list() # 需要的数据序列
        self.need_to_remove = False
        self.need_to_move = False
        self.shooted = False
        self.targeted = False # 是否被锁定
    def update_bullet_pos(self):# 更新射击位置
        self.bullet_pos = self.rect.center
    def blitme(self):
        """在指定位置绘制飞船"""
        self.screen.blit(self.image,self.rect)
    def orientated_shoot(self,target_pos):
        """默认射击-向目标点pos射击"""
        self.update_bullet_pos()
        bullet_dir = (target_pos[0]-self.rect.centerx,target_pos[1]-self.rect.centery)
        blt = enemy_fire(self.screen,self.bullet_pos,self.bullet_speed,self.bullet_ID,bullet_dir,0.5)
        enemyfire_Group.add(blt)
    def default_shoot(self):
        self.update_bullet_pos()
        bullet_dir = (-sin(self.agl*pi/180.0),-cos(self.agl*pi/180.0))
        blt = enemy_fire(self.screen,self.bullet_pos,self.bullet_speed,self.bullet_ID,bullet_dir,0.5)
        enemyfire_Group.add(blt)
    def shoot(self,bullet_pos,bullet_dir,bullet_speed):
        self.update_bullet_pos()
        blt = enemy_fire(self.screen,bullet_pos,bullet_speed,self.bullet_ID,bullet_dir,0.5)
        enemyfire_Group.add(blt) # 将发射的子弹归为敌军活力群
    def update(self):
        self.move_dxy[0] += self.speed[0]
        self.move_dxy[1] += self.speed[1]
        intmove_dxy = int(self.move_dxy[0]), int(self.move_dxy[1])
        self.move_dxy[0] -= intmove_dxy[0]
        self.move_dxy[1] -= intmove_dxy[1]
        self.rect.move_ip(intmove_dxy)
        self.pos = self.rect.center
        self.agl = -180/pi*atan2(self.speed_dir[0],-self.speed_dir[1])
        self.image = pygame.transform.rotate(self.init_image,self.agl)  # 加载图形，并缩小像素
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        self.rect.center = self.pos
        self.blitme()
    def update_time(self):# 更新敌机时间
        self.time = pygame.time.get_ticks()
    def rotate(self,speed_dir):
        self.agl = -180/pi*atan2(speed_dir[0],-speed_dir[1])
        self.image = pygame.transform.rotate(pygame.image.load(self.img_ad),self.agl)
        self.mask = pygame.mask.from_surface(self.image)
        self.pos = self.rect.center
        self.rect = self.image.get_rect()
        self.rect.center = self.pos
    def move_to(self,P):
        self.rect.center = P
        self.blitme()
    def hurt(self,damage):
        self.HP -= damage
        if self.HP < 0:
            self.dead()
            self.HP = 0
        threading.Thread(target=play_music,args=(self.hurt_sound,)).start()
    def dead(self):
        self.kill()
        diamond_prob = np.random.rand()
        prob_level = 0
        if diamond_prob < self.diamond:
            prob_level = 5 - np.digitize(diamond_prob,np.linspace(0,self.diamond,5))
        Global_info.update(Global_info.gold + self.gold, Global_info.diamond+prob_level, Global_info.score + self.score)
        explode_r = sqrt(self.size[0]*self.size[1]) # 换算正方型边长
        explode0 = explode(self.screen,self.rect.center,(explode_r,explode_r))
        background_Group.add(explode0) 
        threading.Thread(target=play_music,args=(self.sound,)).start()
# 场景函数
"""场景1:
在指定屏幕上生成N个型号为ID的敌机，每架敌机只会在t0时刻向player发射一发速度为bullet_speed的
型号为bullet_ID的子弹，发射方向为bullet_target ([0,0]为向下发射子弹，[1,1]为向玩家方向发射子弹，其他为向目标点发射)。
敌机的运动轨迹依次经过PointList=[(x1,y1),(x2,y2),...,(xn,yn)]个点，
运动速度大小恒为speed，两架敌机的出现间隔为dt
"""
class scene1():
    def __init__(self,myscreen,t0,enemy_num,enemy_ID,bullet_speed,bullet_ID,speed,PointList,dt,bullet_target):
        self.screen = myscreen
        self.N = enemy_num # 场景初始敌机数
        self.has_N = self.N # 目前拥有的敌机数
        self.t0 =t0
        self.PointList = PointList
        self.enemy_group = pygame.sprite.Group() # 敌机群
        self.dt = dt # 两架敌机的出现间隔（秒）
        self.isshooted = [0]*enemy_num # 记录下敌机是否已经开火 
        self.path,self.point,self.speed_dir = path_cal(PointList,speed)
        self.need_to_end = False
        self.started = False
        self.init_time = pygame.time.get_ticks()        
        self.bullet_speed = bullet_speed
        self.bullet_ID = bullet_ID
        self.bullet_target = bullet_target
        self.speed = speed
        self.enemy_ID = enemy_ID
    def scene_init(self): # 初始化场景，加入敌机，与__init__()区别开，节省内存开支
        for i in range(self.N):
            enemy0 = enemy(self.screen,self.enemy_ID,self.PointList[0],self.speed,(0,-1),self.bullet_speed,self.bullet_ID)
            enemy0.data = [0,0,len(self.path),i] 
            '''
            data[0]:敌机目前处在的最小分段点
            data[1]:敌机目前处于的关键点（用于确定速度分量）
            data[2]:敌机总共需要经过的最小分段点
            data[3]:敌机的序号，防止kill()方法打乱顺序
            '''
            enemy0.rotate(self.speed_dir[enemy0.data[1]])
            self.enemy_group.add(enemy0) # 场景中加入该敌机
            enemy_Group.add(enemy0) # 总敌机群加入该敌机
            # 第一个点是敌机出现的初始位置
    def update_time(self):
        self.init_time = pygame.time.get_ticks()
    def update(self):
        # 第一次进入时更新该类时间
        if self.started == False:
            self.started = True
            self.scene_init()
            rect0 = pygame.Rect(0,0,20,20)
            rect0.topleft = self.PointList[0]
            warning0 = warn_mark(self.screen,transgress_xy(rect0))
            background_Group.add(warning0)
            self.update_time()
        # 判断场景中的敌人是否该移动/删除
        for enemy0 in self.enemy_group.sprites():
            assert isinstance(enemy0,enemy), "Class must be enemy!"
            if not enemy0.need_to_remove:
                enemy0.update_time()
                if enemy0.time - self.init_time > (enemy0.data[3]+1)*self.dt*1000:
                    enemy0.need_to_move = True
                if enemy0.data[0] >= enemy0.data[2] - 1:
                    enemy0.need_to_remove = True
        # 对场景中的敌人进行移动
        for enemy0 in self.enemy_group.sprites():
            assert isinstance(enemy0,enemy), "Class must be enemy!"
            if enemy0.need_to_move and not enemy0.need_to_remove:
                enemy0.data[0] += 1
                if enemy0.data[0] > self.point[enemy0.data[1]]:
                    enemy0.data[1] += 1
                    enemy0.rotate(self.speed_dir[enemy0.data[1]])
                enemy0.move_to(self.path[enemy0.data[0]])
                if self.t0: # 当t0=0或None时不发射子弹
                    if enemy0.time-self.init_time>self.t0*1000+(enemy0.data[3]+1)*self.dt*1000 and not enemy0.shooted:
                        if self.bullet_target == [1,1]:  # shoot at player
                            enemy0.orientated_shoot((player.rect.centerx,player.rect.centery))
                        elif self.bullet_target == [0,0]:  # shoot at speed direction
                            enemy0.default_shoot()
                        else:  # shoot at target position
                            target_position = (gamescreen_size[0]*self.bullet_target[0],gamescreen_size[1]*self.bullet_target[1])
                            enemy0.orientated_shoot(target_position)
                        enemy0.shooted = True
        # 所有敌人都需删除，场景删除所有敌人并不再更新
        flag = True
        for enemy0 in self.enemy_group.sprites():
            assert isinstance(enemy0,enemy), "Class must be enemy!"
            flag = flag and enemy0.need_to_remove
        self.need_to_end = flag
        if self.need_to_end:
            self.end()
    def end(self):
        for sprite in self.enemy_group.sprites():
            sprite.kill()
    @staticmethod
    def create(cls_info):
        assert isinstance(cls_info,dict), "scene info must be dict"
        assert cls_info['type'] == 'scene1', "types of scene_info and scene dont't fit"
        scene = scene1(myscreen=background,
                       t0=cls_info['bullet_time'],
                       enemy_num=cls_info['enemy_num'],
                       enemy_ID=cls_info['enemy_id'],
                       bullet_speed=cls_info['bullet_speed'],
                       bullet_target=cls_info['bullet_target'],
                       bullet_ID=cls_info['enemy_fire_id'],
                       speed=cls_info['enemy_speed'],
                       PointList=PointList_tran(cls_info['point_list'],screen_size),
                       dt=cls_info['dt'])
        scene_list.append(scene)
        scene_time.append(cls_info['scene_time'])

# 场景函数
"""场景2:
在指定屏幕上生成1个型号为ID的敌机, 每架敌机会从屏幕上边缘飞到path的初始点, 循环围绕path飞行并发射子弹,
直到到达最大循环次数或死亡。子弹类型为bullet_ID,发射速度为bullet_speed,发射频率为1/bullet_cd,发射方向为bullet_target
bullet_target ([0,0]为向下发射子弹，[1,1]为向玩家方向发射子弹)
型号为bullet_ID的子弹。敌机循环运动轨迹依次经过PointList=[(x1,y1),(x2,y2),...,(xn,yn)]个点，
运动速度大小恒为speed, 到达和离开循环路径的速度为init_speed, 两架敌机的出现间隔为dt
"""
# class scene2():
#     def __init__(self,myscreen,enemy_ID,bullet_speed,bullet_cd,bullet_ID,speed,PointList,dt):
#         self.screen = myscreen
#         self.N = enemy_num # 场景初始敌机数
#         self.has_N = self.N # 目前拥有的敌机数
#         self.t0 =t0
#         self.PointList = PointList
#         self.enemy_group = pygame.sprite.Group() # 敌机群
#         self.dt = dt # 两架敌机的出现间隔（秒）
#         self.isshooted = [0]*enemy_num # 记录下敌机是否已经开火 
#         self.path,self.point,self.speed_dir = path_cal(PointList,speed)
#         self.need_to_end = False
#         self.started = False
#         self.init_time = pygame.time.get_ticks()        
#         self.bullet_speed = bullet_speed
#         self.bullet_ID = bullet_ID
#         self.speed = speed
#         self.enemy_ID = enemy_ID
#     def scene_init(self): # 初始化场景，加入敌机，与__init__()区别开，节省内存开支
#         for i in range(self.N):
#             enemy0 = enemy(self.screen,self.enemy_ID,self.PointList[0],self.speed,(0,-1),self.bullet_speed,self.bullet_ID)
#             enemy0.data = [0,0,len(self.path),i] 
#             '''
#             data[0]:敌机目前处在的最小分段点
#             data[1]:敌机目前处于的关键点（用于确定速度分量）
#             data[2]:敌机总共需要经过的最小分段点
#             data[3]:敌机的序号, 防止kill()方法打乱顺序
#             '''
#             enemy0.rotate(self.speed_dir[enemy0.data[1]])
#             self.enemy_group.add(enemy0) # 场景中加入该敌机
#             enemy_Group.add(enemy0) # 总敌机群加入该敌机
#             # 第一个点是敌机出现的初始位置
#     def update_time(self):
#         self.init_time = pygame.time.get_ticks()
#     def update(self):
#         # 第一次进入时更新该类时间
#         if self.started == False:
#             self.started = True
#             self.scene_init()
#             rect0 = pygame.Rect(0,0,20,20)
#             rect0.topleft = self.PointList[0]
#             warning0 = warn_mark(self.screen,transgress_xy(rect0))
#             background_Group.add(warning0)
#             self.update_time()
#         # 判断场景中的敌人是否该移动/删除
#         self.has_N = len(self.enemy_group.sprites())
#         for i in range(self.has_N):
#             enemy0 = self.enemy_group.sprites()[i]
#             if not enemy0.need_to_remove:
#                 enemy0.update_time()
#                 if enemy0.time - self.init_time > (enemy0.data[3]+1)*self.dt*1000:
#                     enemy0.need_to_move = True
#                 if enemy0.data[0] >= enemy0.data[2] - 1:
#                     enemy0.need_to_remove = True
#         # 对场景中的敌人进行移动
#         for i in range(self.has_N):
#             enemy0 = self.enemy_group.sprites()[i]
#             if enemy0.need_to_move and not enemy0.need_to_remove:
#                enemy0.data[0] += 1
#                if enemy0.data[0] > self.point[enemy0.data[1]]:
#                    enemy0.data[1] += 1
#                    enemy0.rotate(self.speed_dir[enemy0.data[1]])
#                enemy0.move_to(self.path[enemy0.data[0]])
#                if self.t0: # 当t0=0或None时不发射子弹
#                    if enemy0.time-self.init_time>self.t0*1000+(enemy0.data[3]+1)*self.dt*1000 and not enemy0.shooted:
#                        enemy0.orientated_shoot((player.rect.centerx,player.rect.centery))
#                        enemy0.shooted = True
#         # 所有敌人都需删除，场景删除所有敌人并不再更新
#         flag = True
#         for i in range(self.has_N):
#             flag = flag and self.enemy_group.sprites()[i].need_to_remove
#         self.need_to_end = flag
#         if self.need_to_end:
#             self.end()
#     def end(self):
#         for i in range(self.has_N):
#             self.enemy_group.sprites()[i].remove(enemy_Group) # 将敌机从总组中删除
#         self.enemy_group.empty()# 删除场景中的敌机组
#     @staticmethod
#     def create(cls_info):
#         assert isinstance(cls_info,dict), "scene info must be dict"
#         assert cls_info['type'] == 'scene1', "types of scene_info and scene dont't fit"
#         scene = scene1(myscreen=background,
#                        t0=cls_info['bullet_time'],
#                        enemy_num=cls_info['enemy_num'],
#                        enemy_ID=cls_info['enemy_id'],
#                        bullet_speed=cls_info['bullet_speed'],
#                        bullet_ID=cls_info['enemy_fire_id'],
#                        speed=cls_info['enemy_speed'],
#                        PointList=PointList_tran(cls_info['point_list'],screen_size),
#                        dt=cls_info['dt'])
#         scene_list.append(scene)
#         scene_time.append(cls_info['scene_time'])   

# 爆炸动画精灵
class explode(pygame.sprite.Sprite):
    def __init__(self,myscreen,pos,size=(120,120)):
        pygame.sprite.Sprite.__init__(self)
        self.screen = myscreen
        self.ID = 1
        self.image_ad = 'explode_png/ex{0}.png'.format(self.ID)
        self.size = (int(size[0]),int(size[1]))
        self.image = pygame.transform.scale(pygame.image.load(self.image_ad),self.size)
        self.rect = self.image.get_rect()
        self.rect.center = pos # 爆炸中心坐标
        self.time = pygame.time.get_ticks()
    def blitme(self):
        self.screen.blit(self.image,self.rect)
    def update(self):
        if self.ID >= 10:
            self.kill()
        elif pygame.time.get_ticks()-self.time > self.ID*20:
            self.image_ad = 'explode_png/ex{0}.png'.format(self.ID)
            self.image = pygame.transform.scale(pygame.image.load(self.image_ad),self.size)
            self.blitme()
            self.ID += 1
        else:
            self.blitme()
# 警告标志
class warn_mark(pygame.sprite.Sprite):
    def __init__(self,myscreen,pos):
        pygame.sprite.Sprite.__init__(self)
        self.screen = myscreen
        self.size = (20,20)
        self.pos = pos
        self.image_ad = 'icon_png/warning.png'
        self.image = pygame.transform.scale(pygame.image.load(self.image_ad),self.size)
        self.rect = self.image.get_rect()
        self.rect.topleft = pos # 摆放位置
        self.time = pygame.time.get_ticks()
        self.i = 0
    def blitme(self):
        self.screen.blit(self.image,self.rect)
    def change_size(self):
        if self.size == (20,20):
            self.size = (15,15)
            self.image = pygame.transform.scale(pygame.image.load(self.image_ad),self.size)
            self.rect.topleft = self.pos
        else:
            self.size = (20,20)
            self.image = pygame.transform.scale(pygame.image.load(self.image_ad),self.size)
            self.rect.topleft = self.pos
    def update_time(self):
        self.time = pygame.time.get_ticks()
    def update(self):
        self.blitme()
        if pygame.time.get_ticks()-self.time > 300:
            self.change_size()
            self.i += 1
            self.update_time()
        if self.i > 5:
            self.kill()
            
   
def play_music(sound,volume=None):
    assert isinstance(sound,pygame.mixer.Sound)
    if volume is not None:
        sound.set_volume(volume)
    sound.play()
    time.sleep(sound.get_length())
    try:
        sound.stop()
    except pygame.error:
        pass
            
def thread_play_music(filename,volume=None,duration=None):
    sound = pygame.mixer.Sound(filename)
    if volume is not None:
        sound.set_volume(volume)
    if duration is None:
        duration = sound.get_length()
    sound.play()
    time.sleep(duration)
    try:
        sound.stop()
    except pygame.error:
        pass
            
# 元组差           
def tuple_minus(a,b):           
    return tuple([ax-bx for ax,bx in zip(a,b)])
# 向量旋转
def vector_rotate(v,phi):
    x1 = v[0]
    x2 = v[1]
    y1 = cos(phi)*x1 - sin(phi)*x2
    y2 = sin(phi)*x1 + cos(phi)*x2
    return (y1,y2)
def center_text(out_rect,text_rect):
    x1 = out_rect.left
    y1 = out_rect.top
    dwidth = 1/2*(out_rect.width-text_rect.width)
    dheight = 1/2*(out_rect.height-text_rect.height)
    return (x1+dwidth,y1+dheight) 

# 取模函数       
def norm(vector):
    v2 = [i**2 for i in vector]
    return sqrt(sum(v2))
# 相对坐标转绝对坐标
def PointList_tran(relative_coordinate,size):
    # 相对坐标、屏幕尺寸
    n = len(relative_coordinate)
    PointList = list()
    for i in range(n):
        PointList.append((relative_coordinate[i][0]*size[0],relative_coordinate[i][1]*size[1]))
    return PointList
# 计算真实速度的函数
def speed_tran(speed,speed_dir):
    # 向上为正的参考系，主屏幕是向下为正
    V = norm(speed_dir)
    if V < 1e-4:
        return (0,0)
    else:
        return (speed*speed_dir[0]/V,speed*(speed_dir[1])/V)


# 计算以恒定速度依次到达一个点数组的时间序列和速度方向
def path_cal(PointList,speed):
    n = len(PointList)
    D = [0]*(n-1) # 距离数组
    V = [0]*(n-1)
    P = list() # 记录每个点坐标的数组
    Q = list()
    for i in range(n-1):
        vector = (PointList[i+1][0]-PointList[i][0],\
                  PointList[i+1][1]-PointList[i][1])
        D[i] = norm(vector) 
        V[i] = vector
    for i in range(n-1):
        num_p = int(D[i]/speed)
        for j in range(num_p):
            P.append((PointList[i][0]*(1-j/num_p)+PointList[i+1][0]*j/num_p,\
                      PointList[i][1]*(1-j/num_p)+PointList[i+1][1]*j/num_p))
        Q.append(len(P))
    return (P,Q,V)

def transgress_xy(rect):
    w = rect.width
    h = rect.height
    x = rect.left
    y = rect.top
    X = gamescreen_size[0]
    Y = gamescreen_size[1]
    if x < 0 :
        x = 0
    elif x > X-w:
        x = X-w
    if y < 0:
        y = 0
    elif y > Y-h:
        y = Y-h
    return (x,y)

def collide_detect():
    myfire_collide = pygame.sprite.groupcollide(enemy_Group,bullet_Group,False,False)
    for unit in myfire_collide.keys():
        hit_bullets = myfire_collide[unit] # 与敌机碰撞的子弹列表
        for blt in hit_bullets:
            collide_xy = pygame.sprite.collide_mask(unit,blt)
            if collide_xy and not transgress_detect(unit.rect):
                unit.hurt(blt.damage) # 对敌机造成子弹的伤害
                blt.dead()  # 组中删除子弹
    if player.alive_:
        enemy_collide = pygame.sprite.spritecollideany(player,enemy_Group)
        if enemy_collide:
            if pygame.sprite.collide_mask(player,enemy_collide):            
                enemy_collide.hurt(player.HP) # 敌军受到玩家撞击伤害
                player.hurt(enemy_collide.collide_damage) # 玩家受到敌军撞击伤害
        enemyfire_collide = pygame.sprite.spritecollideany(player,enemyfire_Group)
        if enemyfire_collide:
            if pygame.sprite.collide_mask(player,enemyfire_collide):
                player.hurt(enemyfire_collide.damage) # 玩家受到敌军火力伤害
                enemyfire_collide.dead() # 删除敌军子弹
    
# 越界检测
def transgress_detect(rect):
    X = gamescreen_size[0]
    Y = gamescreen_size[1]
    if -rect.height < rect.top < Y and -rect.width < rect.left < X:
        return False
    else:
        return True


# 事件检查函数
def event_check(fighter):
    global running
    for event in pygame.event.get():
        if event.type == pygame.QUIT:  # 检测到按退出键，实施软退出
            running = False
            return
        if player.alive_: # 玩家阵亡时不再响应控制按键
            if event.type == pygame.KEYDOWN:  # 检测到有键按下时动作，相反的两个动作不能冲突抵消
                if event.key == pygame.K_RIGHT:
                    fighter.moving_right = True
                    fighter.moving_left = False
                elif event.key == pygame.K_LEFT:
                    fighter.moving_left = True
                    fighter.moving_right = False
                if event.key == pygame.K_UP:
                    fighter.moving_up = True
                    fighter.movng_down = False
                elif event.key == pygame.K_DOWN:
                    fighter.moving_down = True
                    fighter.moving_up = False
                if event.key == pygame.K_f:
                    fighter.shooting = not fighter.shooting
                if event.key == pygame.K_w:
                    fighter.shoot1, fighter.shoot2, fighter.shoot3 = True,True,False
                if event.key == pygame.K_q:
                    fighter.shoot1, fighter.shoot2, fighter.shoot3 = True,False,False
                if event.key == pygame.K_e:
                    fighter.shoot1, fighter.shoot2, fighter.shoot3 = True,True,True
                if event.key == pygame.K_SPACE:
                    fighter.launching = True
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_RIGHT:
                    fighter.moving_right = False
                elif event.key == pygame.K_LEFT:
                    fighter.moving_left = False
                if event.key == pygame.K_UP:
                    fighter.moving_up = False
                elif event.key == pygame.K_DOWN:
                    fighter.moving_down = False

# 场景检查函数
def scene_check(init_time,now):
    now = pygame.time.get_ticks()
    for i in range(len(scene_list)):
        if not scene_list[i].need_to_end and now - init_time > scene_time[i]*1000:
            scene_list[i].update()


def create_scene():
    for scene_info in scenes:
        scene_class[scene_info['type']].create(scene_info)
# 更新系统时间
def system_update_time():
    global init_time
    init_time = pygame.time.get_ticks()
# 绘制飞船状态栏

def draw_statebar():
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
    gold_font_surface = gold_font.render(f":{Global_info.gold}",True,[255,255,255])
    diamond_font_surface = diamond_font.render(f":{Global_info.diamond}",True,[255,255,255])
    score_font_surface = score_font.render(f"Score:{Global_info.score}",True,[180,255,255])
    screen.blit(gold_font_surface,GOLD_POS)
    screen.blit(diamond_font_surface,DIAMOND_POS)
    screen.blit(score_font_surface,SCORE_POS)
    
    
# 运行开始界面
def run_main_interface():
    run_delta = 100  # ms
    bg_img = pygame.image.load('background_jpg/b3.jpg')
    button1 = button(screen,1,'无限模式',1)
    button2 = button(screen,1,'改造中心',2)
    png1 = pygame.image.load('button_png/fighter_png.png')
    button_pos = PointList_tran([(0.3,0.7),(0.7,0.7)],screen_size)
    png_pos = PointList_tran([(0.7,0.4)],screen_size)
    button_dict = {button1:button_pos[0],button2:button_pos[1]}
    png_dict = {png1:png_pos[0]}
    main_interface = interface(screen,button_dict,png_dict,bg_img) 
    now_ID = main_interface.function_ID
    main_interface.update()
    while main_interface.function_ID != -1:
        try:
            main_interface.mouse_check() # 响应鼠标事件并更新function_ID
            now_ID = main_interface.function_ID
            if pygame.time.get_ticks() - main_interface.time > run_delta:
                main_interface.update_time()
                main_interface.update()
            if main_interface.respond and main_interface.responded:
                main_interface.reset_state()
                if now_ID == 1:
                    run_game(screen_bg_color,sim_interval)
        except pygame.error:
            print('pygmae exit!')
            break
# 运行游戏界面
def run_game(backcolor,interval):
    # 渐变显示窗口
    for i in range(11):
        screen.fill(tuple([255*(1-i/10) for _ in backcolor]))
        time.sleep(0.03)
        pygame.display.flip()
    
    #开始游戏
    player.blitme()
    pygame.display.flip()
    create_scene()
    now = pygame.time.get_ticks()
    system_update_time()
    while running:
        # 监视屏幕
        event_check(player)
        # 让最近绘制的屏幕可见
        if(pygame.time.get_ticks()-now>interval): 
            now = pygame.time.get_ticks()
            blit_ad = int((now-init_time)/1000*bg_rollv % bg_resize[1])
            background.blit(background_img,(0,blit_ad-bg_resize[1]+30))
            background.blit(background_img,(0,blit_ad+30))
            collide_detect()            
            bullet_Group.update()
            if player.alive_:
                player.update()    
            scene_check(init_time,now)
            enemyfire_Group.update()
            background_Group.update()
            screen.blit(background,(0,30))
            draw_statebar() # 更新状态栏
            pygame.display.flip()  # 更新画面
    gameset.gold = int(Global_info.gold)
    gameset.diamond = int(Global_info.diamond)
    gameset.high_score = max(gameset.high_score,Global_info.score)
    gameset.save()
    pygame.font.quit()
    pygame.quit()
# 运行改装中心界面
#def run_lab_interface():
#    
# 运行游戏
if __name__ == "__main__":
    with open("config.yml",'r')as f:
        CONFIG = yaml.load(f,yaml.SafeLoader)
    gameset = game_set() # 游戏设置类
    gameset.load()
    GOLD = gameset.gold
    DIAMOND = gameset.diamond
    Global_info = Info(GOLD,DIAMOND)
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
    GOLD_POS = (210,5)
    DIAMOND_POS = (300,5)
    SCORE_POS = (350,5)
    pygame.init()  # 初始化背景设置
    pygame.font.init() # 初始化字体设置
    screen = pygame.display.set_mode(screen_size)
    background = pygame.Surface((gamescreen_size[0]+100,gamescreen_size[1]+100))  # blit can receive negative coordinates rather than larger than window size
    pygame.display.set_caption("空中游侠")
    player = fighter(background)
    bullet_Group = pygame.sprite.Group() # player的子弹群
    enemy_Group = pygame.sprite.Group() # 敌机群
    enemyfire_Group = pygame.sprite.Group() # 敌军的子弹群
    background_Group = pygame.sprite.Group() # 背景动画群
    thread_List = []
    background_img = pygame.image.load(os.path.join("background_jpg","img_bg_1.jpg"))  # 背景图片
    bg_size = background_img.get_size()
    bg_resize = (screen_size[0],int(screen_size[0]/bg_size[0]*bg_size[1]))
    background_img = pygame.transform.scale(background_img,bg_resize)
    bg_rollv = CONFIG['setting']['bg_rollv']  # rolling speed
    scene_time = []
    scene_list = list()
    scene_class = dict(scene1=scene1)
    init_time = pygame.time.get_ticks()
    player.game_set(gameset) # 使用该游戏设置
    pygame.mixer.init(11025)
    pygame.mixer.music.set_volume(8)
    run_main_interface() # 运行主界面