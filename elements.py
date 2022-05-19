import pygame
import pygame.mixer
import pygame.sprite
import pygame.time
import pygame.transform
import pygame.image
import pygame.font
import pygame.mask
import pygame.display
import os
import yaml
from numpy import clip,digitize,linspace,random
from random import randint
from math import sqrt,pi,cos,sin,atan2
import utils
from Game_set import game_set
import threading

with open("config.yml",'r')as f:
    CONFIG = yaml.load(f,yaml.SafeLoader)
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
enemy_type_b = utils.extract_type(enemy_dict['filename'],pattern='\w*[.]',type='b')
enemyfire_type_a = utils.extract_type(enemyfire_dict['filename'],type='a')
enemyfire_type_b = utils.extract_type(enemyfire_dict['filename'],type='b')
# 类型提取


class fighter(pygame.sprite.Sprite):
    def __init__(self,hook_background:pygame.Surface,hook_gamescreen:pygame.Surface,hook_enemy_group:pygame.sprite.Group,
                 hook_bullet_group:pygame.sprite.Group,hook_background_group:pygame.sprite.Group,sim_interval:float,volume_multiply:float=1.0):
        pygame.sprite.Sprite.__init__(self)
        self.screen = hook_background  # 坐标
        self.sim_interval = sim_interval
        self.volume_multiply = volume_multiply
        self.hook_enemy_group = hook_enemy_group
        self.hook_gamescreen = hook_gamescreen
        self.hook_bullet_group = hook_bullet_group
        self.hook_background_group = hook_background_group
        self.speed = 6 * sim_interval/10.0
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
        self.bullet_pos = [(int(self.pos[0]-0.3125*self.size[0]),int(self.pos[1]+0.08*self.size[1])),
                        (int(self.pos[0]+0.3125*self.size[0]),int(self.pos[1]+0.08*self.size[1])),
                        (int(self.pos[0]-0.25*self.size[0]),int(self.pos[1]+0.08*self.size[1])),
                        (int(self.pos[0]+0.25*self.size[0]),int(self.pos[1]+0.08*self.size[1])),
                        (int(self.pos[0]-0.17*self.size[0]),int(self.pos[1]+0.08*self.size[1])),
                        (int(self.pos[0]+0.17*self.size[0]),int(self.pos[1]+0.08*self.size[1])),]
        self.screen_rect = self.hook_gamescreen.get_rect()  # 活动矩形范围
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
        self.missile_pos = [self.bullet_pos[0],self.bullet_pos[1],self.bullet_pos[0],self.bullet_pos[1],
                            self.bullet_pos[0],self.bullet_pos[1],self.bullet_pos[0],self.bullet_pos[1]]
        self.missile_actime = 3
        self.missile_speed_max = 5
        self.missile_flyingtime = 3
        # 以上为导弹参数
        self.HP_max = 3 # 最大血生命值
        self.HP = self.HP_max # 现有生命值
        self.energy_max = 20 # 最大能量
        self.energy = self.energy_max
        self.energy_recover = 0
        self.cooling_max = 10 # 最大冷却能力
        self.cooling = self.cooling_max-(self.init_shooting_cd/self.shooting_cd)*\
                      (self.shoot1+self.shoot2+self.shoot3)*5*self.shooting # 现有能量
        self.cooling_recover = 0
        # 以上为游戏信息参数
        self.alive_ = True
        self.shooting_time = pygame.time.get_ticks()
        self.launching_time = pygame.time.get_ticks()
        self.mp3_path = player_dict['mp3_path']
        self.bullet_sound_file = os.path.join(self.mp3_path,player_dict['bullet_sound_file'])
        self.missile_sound_file = os.path.join(self.mp3_path,player_dict['missile_sound_file'])
        self.explode_sound_file = os.path.join(self.mp3_path,player_dict['explode_sound_file'])
        self.hit_sound_file = os.path.join(self.mp3_path,player_dict['hit_sound_file'])
    def game_set(self,gameset:game_set):
        self.HP = gameset.player_HP_list[gameset.player_HP_level]
        self.HP_max = self.HP
        self.HP_recover =  gameset.player_HP_recover_list[gameset.player_HP_recover]
        self.energy = gameset.player_energy_list[gameset.player_energy_level]
        self.energy_recover = gameset.player_energy_recover_list[gameset.player_energy_recover_level] * self.sim_interval/10.0
        self.energy_max = self.energy
        self.cooling = gameset.player_cooling_list[gameset.player_cooling_level]
        self.cooling_recover = gameset.player_cooling_recover_list[gameset.player_cooling_recover_level] * self.sim_interval/10.0
        self.cooling_max = self.cooling
        self.bullet_ID = gameset.bullet_ID
        self.shooting_cd = gameset.player_shooting_cd_list[gameset.bullet_shooting_cd_level]
        self.missile_num = gameset.missile_num_list[gameset.missile_num_level]
        self.launching_cd = gameset.missile_shooting_cd
        self.missile_damge = gameset.missile_damage_list[gameset.missile_damage_level]
        self.missile_actime = gameset.missile_actime_list[gameset.missile_actime_level]
        self.missile_speed_max = gameset.missile_speed_max_list[gameset.missile_actime_level]
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
        self.bullet_pos = [(int(self.pos[0]-0.3125*self.size[0]),int(self.pos[1]+0.08*self.size[1])),
                        (int(self.pos[0]+0.3125*self.size[0]),int(self.pos[1]+0.08*self.size[1])),
                        (int(self.pos[0]-0.2*self.size[0]),int(self.pos[1]+0.08*self.size[1])),
                        (int(self.pos[0]+0.2*self.size[0]),int(self.pos[1]+0.08*self.size[1])),
                        (int(self.pos[0]-0.1*self.size[0]),int(self.pos[1]+0.08*self.size[1])),
                        (int(self.pos[0]+0.1*self.size[0]),int(self.pos[1]+0.08*self.size[1])),]
        
        self.missile_pos = [self.bullet_pos[0],self.bullet_pos[1],self.bullet_pos[0],self.bullet_pos[1],
                            self.bullet_pos[0],self.bullet_pos[1],self.bullet_pos[0],self.bullet_pos[1]]
    def shoot(self):
        threading.Thread(target=utils.thread_play_music,args=(self.bullet_sound_file,0.2*self.volume_multiply)).start()
        self.update_bltpos()
        if self.shoot1: # 射击点位1
            blt1 = bullet(self.screen,self.bullet_pos[0],self.bullet_speed,self.bullet_ID,(0,-1),self.sim_interval)
            blt2 = bullet(self.screen,self.bullet_pos[1],self.bullet_speed,self.bullet_ID,(0,-1),self.sim_interval)
            self.hook_bullet_group.add(blt1)
            self.hook_bullet_group.add(blt2)
        if self.shoot2:
            blt1 = bullet(self.screen,self.bullet_pos[2],self.bullet_speed,self.bullet_ID,(0,-1),self.sim_interval)
            blt2 = bullet(self.screen,self.bullet_pos[3],self.bullet_speed,self.bullet_ID,(0,-1),self.sim_interval)
            self.hook_bullet_group.add(blt1)
            self.hook_bullet_group.add(blt2)
        if self.shoot3:
            blt1 = bullet(self.screen,self.bullet_pos[4],self.bullet_speed,self.bullet_ID,(0,-1),self.sim_interval)
            blt2 = bullet(self.screen,self.bullet_pos[5],self.bullet_speed,self.bullet_ID,(0,-1),self.sim_interval)
            self.hook_bullet_group.add(blt1)
            self.hook_bullet_group.add(blt2)  
        
        
    def launch_missile(self):
        threading.Thread(target=utils.thread_play_music,args=(self.missile_sound_file,self.volume_multiply)).start()
        self.update_bltpos()
        if self.missile_num > 0:
            self.update_bltpos()
            missile_num = int(min(self.missile_num,self.energy//5,self.cooling//3))
            for i in range(missile_num):
                missile0 = missile(self.screen,self.missile_pos[i],self.missile_dir[i],
                                   self.missile_actime,self.missile_speed_max,self.missile_damge,self.missile_flyingtime,
                                   hook_enemy_group=self.hook_enemy_group,hook_background_group=self.hook_background_group,
                                   sim_interval=self.sim_interval,volume_multiply=self.volume_multiply
                                   )
                self.hook_bullet_group.add(missile0)
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
                    self.energy -= 1*(self.shoot1+self.shoot2+self.shoot3)/self.shooting_cd*100 # 消耗能量
                    self.cooling -= (self.shoot1+0.5*self.shoot2+0.25*self.shoot3)/self.shooting_cd*100
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
        self.HP = clip(self.HP+self.HP_recover,0,self.HP_max)
        self.energy = clip(self.energy+self.energy_recover,0,self.energy_max)
        self.cooling = clip(self.cooling+self.cooling_recover,0,self.cooling_max)
        
    def hurt(self,damage):
        self.HP -= damage
        if self.HP <= 0:
            self.dead()
            explode0 = explode(self.screen,self.rect.center)
            self.hook_background_group.add(explode0)
            self.HP = 0
        threading.Thread(target=utils.thread_play_music,args=(self.hit_sound_file,0.3*self.volume_multiply)).start()
            
            
    def dead(self):
        threading.Thread(target=utils.thread_play_music,args=(self.explode_sound_file,0.5*self.volume_multiply)).start()
        self.alive_ = False
        self.kill()

# 子弹类
class bullet(pygame.sprite.Sprite):
    def __init__(self,screen:pygame.Surface,location,speed,ID,speed_dir,sim_interval:float):
        pygame.sprite.Sprite.__init__(self)  # 类继承
        self.screen = screen
        self.sim_interval = sim_interval
        self.ID = ID
        self.img_ad = os.path.join(bullet_path,bullet_dict['filename'][ID])
        bullet_image = pygame.transform.scale(pygame.image.load(self.img_ad),(10,25))
        self.image = pygame.transform.rotate(bullet_image,-180/pi*atan2(speed_dir[0],-speed_dir[1]))
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect() 
        self.rect.centerx,self.rect.centery = location
        self.speed_dir = speed_dir
        self.speed_value = speed * sim_interval/10.0
        self.speed = utils.speed_tran(self.speed_value,speed_dir)
        self.damage = float(bullet_dict['damage'][self.ID]) # 子弹伤害数值
    def blitme(self):
        self.screen.blit(self.image,self.rect)
    def update(self):
        self.rect.move_ip(self.speed)
        self.blitme()
        if utils.transgress_detect(self.rect): # 子弹越界删除
            self.kill()
    def dead(self):
        self.kill()
# 导弹类
class missile(pygame.sprite.Sprite):
    def __init__(self,screen:pygame.Surface,pos,speed_dir,ac_time,max_speed,damage,flying_time,
                 hook_enemy_group:pygame.sprite.Group,hook_background_group:pygame.sprite.Group,sim_interval:float,
                 tracktime=300,volume_multiply:float=1.0):
        pygame.sprite.Sprite.__init__(self)  # 类继承
        self.sim_interval = sim_interval
        self.volume_multiply = volume_multiply
        self.screen = screen
        self.hook_enemy_group = hook_enemy_group
        self.hook_background_group = hook_background_group
        self.size = (20,40)
        self.init_speed = 1
        self.speed = 1 * sim_interval/10.0
        self.speed_max = max_speed * sim_interval/10.0
        self.speed_dir = speed_dir
        self.ac_time = ac_time*1000 # 加速时间（毫秒）
        self.speed_vector = utils.speed_tran(self.speed,self.speed_dir)
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
        self.speed = min(self.init_speed+dv,self.speed_max) * self.sim_interval/10.0
    def find_target(self):
        # 寻找目标
        target_list = list()
        for enemy0 in self.hook_enemy_group.sprites():
            assert isinstance(enemy0,enemy),'Target type must be enemy'
            if enemy0.targeted == False and not utils.transgress_detect(enemy0.rect):
                target_list.append(enemy0)
                # 加入可攻击组和序号
        if target_list:
            self.target = target_list[randint(0,len(target_list)-1)]
        else:
            self.target = None
    def rotate(self):
        # 根据速度方向旋转自己
        self.agl = -180/pi*atan2(self.speed_dir[0],-self.speed_dir[1]) 
        self.image = pygame.transform.rotate(self.img,self.agl)
        self.mask = pygame.mask.from_surface(self.image)
    def track_target(self):
        # 追踪目标
        if self.target is not None:
            if self.target.alive():# 若目标仍在敌机组，追击
                self.speed_dir = utils.tuple_minus(self.target.rect.center,self.rect.center)
            else:
                self.target = None
        else:
            self.speed_dir = utils.vector_rotate(self.speed_dir,pi/180.0*self.speed)# 自转
            self.target = None # 清除锁定
            self.find_target() # 寻找新目标
        self.accelerate()
        self.rotate()
        self.update_pos()
    def update_pos(self):
        self.speed_vector = utils.speed_tran(self.speed,self.speed_dir)
        self.move_dxy[0] += self.speed_vector[0]
        self.move_dxy[1] += self.speed_vector[1]
        intmove_dxy = round(self.move_dxy[0]), round(self.move_dxy[1])
        self.rect.move_ip(intmove_dxy)
        self.move_dxy[0] -= intmove_dxy[0]
        self.move_dxy[1] -= intmove_dxy[1]
        self.blitme()
    def dead(self):
        if self.target is not None:
            if self.target.alive():
                self.target.targeted = False # 解除敌机锁定
        self.hook_background_group.add(explode(self.screen,self.rect.center,self.explode_size))
        threading.Thread(target=utils.play_music,args=(self.explode_music,self.volume_multiply)).start()
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
    def __init__(self,screen:pygame.Surface,hook_background_group:pygame.sprite.Group,location,speed,ID,speed_dir,scale=1,volume_multiply:float=1.0):
        pygame.sprite.Sprite.__init__(self)  # 类继承
        self.screen = screen
        self.volume_multiply = volume_multiply
        self.hook_background_group = hook_background_group
        self.ID = ID
        self.explode_music = CONFIG['enemyfire']['explode_sound_file']
        self.explode_size = (30,30)
        if self.ID in enemyfire_type_a:
            sound = pygame.mixer.Sound(CONFIG['enemyfire']['type_a_sound_file'])
            threading.Thread(target=utils.play_music,args=(sound,0.3*volume_multiply)).start()
        elif self.ID in enemyfire_type_b:
            sound = pygame.mixer.Sound(CONFIG['enemyfire']['type_b_sound_file'])
            threading.Thread(target=utils.play_music,args=(sound,0.3*volume_multiply)).start()
        self.speed_dir = speed_dir
        self.speed_value = speed
        self.speed = utils.speed_tran(self.speed_value,speed_dir)
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
        if utils.transgress_detect(self.rect): # 子弹越界删除
            self.kill()    
    def dead(self):
        if self.ID in enemyfire_type_b:
            self.hook_background_group.add(explode(self.screen,self.rect.center,self.explode_size))
            threading.Thread(target=utils.play_music,args=(pygame.mixer.Sound(self.explode_music),self.volume_multiply)).start()
        self.kill()
        
class enemy(pygame.sprite.Sprite):
    def __init__(self,myscreen:pygame.Surface,ID,pos,speed,speed_dir,bullet_speed,bullet_ID,
                 hook_global_info:utils.Info,hook_enemy_group:pygame.sprite.Group,hook_enemyfire_group:pygame.sprite.Group,
                 hook_background_group:pygame.sprite.Group,sim_interval:float,volume_multiply:float=1.0):
        pygame.sprite.Sprite.__init__(self)
        self.screen = myscreen  # 坐标
        self.sim_interval = sim_interval
        self.volume_multiply = volume_multiply
        self.hook_global_info = hook_global_info
        self.hook_enemy_group = hook_enemy_group
        self.hook_enemyfire_group = hook_enemyfire_group
        self.hook_background_group = hook_background_group
        self.ID = enemy_names.index(ID) # 敌机型号
        self.speed_dir = speed_dir # 运动方向属性
        self.speed_value = speed * sim_interval/10.0
        self.speed = utils.speed_tran(speed,self.speed_dir) # 速度属性
        self.move_dxy = [0,0]
        self.agl = -180/pi*atan2(self.speed_dir[0],-self.speed_dir[1])
        self.img_ad = os.path.join(enemy_path,enemy_dict['filename'][self.ID])
        self.init_image = pygame.image.load(self.img_ad)
        self.image = pygame.transform.rotate(self.init_image,self.agl)  # 加载图形，并缩小像素
        self.explode_sound_file = CONFIG['enemy']['explode_sound_file']\
            if self.ID not in enemy_type_b else CONFIG['enemy']['big_explode_sound_file']
        self.explode_sound = pygame.mixer.Sound(self.explode_sound_file)
        self.hurt_sound_file = CONFIG['enemy']['hurt_sound_file']
        self.diamond_sound_file = CONFIG['enemy']['diamond_sound_file']
        self.gold = int(enemy_dict['gold'][self.ID])
        self.diamond = float(enemy_dict['diamond'][self.ID])
        self.score = int(enemy_dict['score'][self.ID])
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()  # 占用矩形范围
        self.size = (self.rect.width,self.rect.height)
        self.pos = self.rect.center
        self.bullet_speed = bullet_speed * sim_interval/10.0
        self.bullet_ID = bullet_ID
        self.bullet_pos = self.rect.center
        self.screen_rect = self.screen.get_rect()  # 活动矩形范围
        self.rect.center = pos
        self.shooting = False
        self.time = pygame.time.get_ticks()
        self.HP_max = float(enemy_dict['HP'][self.ID]) # 最大生命值
        self.HP = self.HP_max # 现有生命值
        self.collide_damage = self.HP_max # 撞击敌机会造成等同生命值的伤害
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
        blt = enemy_fire(self.screen,self.hook_background_group,self.bullet_pos,self.bullet_speed,self.bullet_ID,bullet_dir,0.5,self.volume_multiply)
        self.hook_enemyfire_group.add(blt)
    def foward_shoot(self):
        self.update_bullet_pos()
        bullet_dir = (-sin(self.agl*pi/180.0),-cos(self.agl*pi/180.0))
        blt = enemy_fire(self.screen,self.hook_background_group,self.bullet_pos,self.bullet_speed,self.bullet_ID,bullet_dir,0.5,self.volume_multiply)
        self.hook_enemyfire_group.add(blt)
    def default_shoot(self,bullet_offset=[0,0]):
        self.update_bullet_pos()
        bullet_dir = (0,1)
        bullet_pos = utils.tuple_add(self.bullet_pos,bullet_offset)
        blt = enemy_fire(self.screen,self.hook_background_group,bullet_pos,self.bullet_speed,self.bullet_ID,bullet_dir,0.5,self.volume_multiply)
        self.hook_enemyfire_group.add(blt)
    def shoot(self,bullet_pos,bullet_dir,bullet_speed):
        self.update_bullet_pos()
        blt = enemy_fire(self.screen,self.hook_background_group,bullet_pos,bullet_speed,self.bullet_ID,bullet_dir,0.5,self.volume_multiply)
        self.hook_enemyfire_group.add(blt) # 将发射的子弹归为敌军活力群
    def update(self):
        self.speed = utils.speed_tran(self.speed_value,self.speed_dir) # 速度属性
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
    def rotate(self,speed_dir,rotate_img=True):
        self.speed_dir = speed_dir
        self.agl = -180/pi*atan2(speed_dir[0],-speed_dir[1])
        if rotate_img:
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
        if self.HP <= 0:
            self.dead()
            self.HP = 0
        else:
            threading.Thread(target=utils.play_music,args=(pygame.mixer.Sound(self.hurt_sound_file),0.4*self.volume_multiply)).start()
    def dead(self):
        self.kill()
        diamond_prob = random.rand()
        prob_level = 0
        if diamond_prob < self.diamond:
            prob_level = 5 - digitize(diamond_prob,linspace(0,self.diamond,5))
            threading.Thread(target=utils.thread_play_music,args=(self.diamond_sound_file,1.0,0.8*self.volume_multiply)).start()
        self.hook_global_info.update(self.hook_global_info.gold + self.gold, self.hook_global_info.diamond+prob_level, self.hook_global_info.score + self.score)
        explode_r = sqrt(self.size[0]*self.size[1]) # 换算正方型边长
        explode0 = explode(self.screen,self.rect.center,(explode_r,explode_r))
        self.hook_background_group.add(explode0) 
        threading.Thread(target=utils.play_music,args=(self.explode_sound,0.3*self.volume_multiply)).start()
        

# 爆炸动画精灵
class explode(pygame.sprite.Sprite):
    def __init__(self,myscreen:pygame.Surface,pos,size=(120,120)):
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