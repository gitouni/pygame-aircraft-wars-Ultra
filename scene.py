import os
import pygame
import pygame.sprite
import pygame.image
import pygame.transform
import pygame.time
from elements import enemy, fighter
import utils
from utils import path_cal,PointList_tran,transgress_xy
import yaml
import json
import random


with open("config.yml",'r')as f:
    CONIFG = yaml.load(f,yaml.SafeLoader)
ICON_CONFIG = CONIFG['icon']
GAME_SCREEN = CONIFG['setting']['gamescreen_size']

sim_interval = CONIFG['setting']['sim_interval']

# 警告标志
class warn_mark(pygame.sprite.Sprite):
    def __init__(self,myscreen,pos,type=0):
        pygame.sprite.Sprite.__init__(self)
        self.screen = myscreen
        self.size = (20,20)
        self.pos = pos
        self.image_ad = os.path.join(ICON_CONFIG['path'],ICON_CONFIG['warn'][type])
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

def duplicate_path(path:list, iter:int):
    Path = []
    for _ in range(iter):
        Path.extend(path)
    return Path

def augment_path(path:list, random_permute=True, random_flip=True) -> list:
    if random_permute and random.random() < 0.5:
        path.reverse()
    if random_flip and random.random() < 0.5:
        for i in range(len(path)):
            path[i][0] = 1 - path[i][0]
    return path
            
            
class Random_Scene_Generator:
    def __init__(self,path_dir:str,random_permute=True,random_flip=True,level=0):
        self.path_dir = path_dir
        self.files = [file for file in os.listdir(self.path_dir) if os.path.splitext(file)[1] == '.json']
        self.full_paths = [os.path.join(path_dir,file) for file in self.full_paths]
        self.random_permute = random_permute
        self.random_flip = random_flip
        self.level = level
    def get_path(self,index):
        with open(self.full_paths[index],'r')as f:
            path_list = json.load(f)
        path_list = augment_path(path_list,self.random_permute,self.random_flip)

# 场景函数
"""场景1:
在指定屏幕上生成N个型号为ID的敌机, 每架敌机只会在t0时刻向player发射一发速度为bullet_speed的
型号为bullet_ID的子弹, 发射方向为bullet_target ([0,0]为向下发射子弹，[1,1]为向玩家方向发射子弹，其他为向目标点发射)。
敌机的运动轨迹依次经过PointList=[(x1,y1),(x2,y2),...,(xn,yn)]个点，
运动速度大小恒为speed, 两架敌机的出现间隔为dt
"""
class scene1():
    def __init__(self,myscreen:pygame.Surface,t0,enemy_num,enemy_ID,bullet_speed,bullet_ID,speed,PointList,dt,bullet_target,
                 hook_global_info:utils.Info,hook_enemyfire_group:pygame.sprite.Group,
                 hook_player:fighter,hook_enemy_group:pygame.sprite.Group,
                 hook_background_group:pygame.sprite.Group,init_time:int):
        speed *= sim_interval/10.0
        self.screen = myscreen
        self.N = enemy_num # 场景初始敌机数
        self.t0 =t0
        self.PointList = PointList
        self.enemy_group = pygame.sprite.Group() # 敌机群
        self.hook_global_info = hook_global_info
        self.hook_player = hook_player
        self.hook_enemy_group = hook_enemy_group
        self.hook_enemyfire_group = hook_enemyfire_group
        self.hook_background_group = hook_background_group
        self.dt = dt # 两架敌机的出现间隔（秒）
        self.isshooted = [0]*enemy_num # 记录下敌机是否已经开火 
        self.path,self.pt_index,self.speed_dir = path_cal(PointList,speed)
        self.need_to_end = False
        self.started = False
        self.init_time = init_time   
        self.bullet_speed = bullet_speed
        self.bullet_ID = bullet_ID
        self.bullet_target = bullet_target
        self.speed = speed
        self.enemy_ID = enemy_ID
    def scene_init(self): # 初始化场景，加入敌机，与__init__()区别开，节省内存开支
        for i in range(self.N):
            enemy0 = enemy(self.screen,self.enemy_ID,self.PointList[0],self.speed,(0,-1),self.bullet_speed,self.bullet_ID,
                           self.hook_global_info,self.hook_enemy_group,self.hook_enemyfire_group,self.hook_background_group)
            enemy0.data = [0,0,len(self.path),i] 
            '''
            data[0]:敌机目前处在的最小分段点
            data[1]:敌机目前处于的关键点（用于确定速度分量）
            data[2]:敌机总共需要经过的最小分段点
            data[3]:敌机的序号, 防止kill()方法打乱顺序
            '''
            enemy0.rotate(self.speed_dir[enemy0.data[1]])
            self.enemy_group.add(enemy0) # 场景中加入该敌机
            self.hook_enemy_group.add(enemy0) # 总敌机群加入该敌机
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
            warning0 = warn_mark(self.screen,transgress_xy(rect0),type=0)
            self.hook_background_group.add(warning0)
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
                if enemy0.data[0] > self.pt_index[enemy0.data[1]]:
                    enemy0.data[1] += 1
                    enemy0.rotate(self.speed_dir[enemy0.data[1]])
                enemy0.move_to(self.path[enemy0.data[0]])
                if self.t0: # 当t0=0或None时不发射子弹
                    if enemy0.time-self.init_time>self.t0*1000+(enemy0.data[3]+1)*self.dt*1000 and not enemy0.shooted:
                        if self.bullet_target == [1,1]:  # shoot at player
                            enemy0.orientated_shoot((self.hook_player.rect.centerx,self.hook_player.rect.centery))
                        elif self.bullet_target == [0,0]:  # shoot at speed direction
                            enemy0.foward_shoot()
                        elif self.bullet_target == [0,-1]:  # shoot at down direction
                            enemy0.default_shoot()
                        else:  # shoot at target position
                            target_position = (GAME_SCREEN[0]*self.bullet_target[0],GAME_SCREEN[1]*self.bullet_target[1])
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
    def create(cls_info:dict,scene_list:list,scene_time:list,background:pygame.Surface,
               hook_player:fighter,hook_global_info:utils.Info,
               hook_enemy_group:pygame.sprite.Group,
               hook_enemyfire_group:pygame.sprite.Group,
               hook_background_group:pygame.sprite.Group,
               init_time=pygame.time.get_ticks(),random_permute=False,random_flip=False):
        assert cls_info['type'] == 'scene1', "types of scene_info and scene dont't fit"
        cnt = dict(type='scene1',
                    point_list=[[0.5, -0.2],[0.5,1.2]],
                    enemy_num=2,
                    enemy_id='ea0',
                    enemy_fire_id=0,
                    bullet_time=0,
                    bullet_speed=3,
                    bullet_target=[1,1],
                    enemy_speed=2.0,
                    dt=0.5,
                    scene_time=0.0,
                    random_permute=False,
                    random_flip=False)
        cnt.update(cls_info)
        scene = scene1(myscreen=background,
                       t0=cnt['bullet_time'],
                       enemy_num=cnt['enemy_num'],
                       enemy_ID=cnt['enemy_id'],
                       bullet_speed=cnt['bullet_speed'],
                       bullet_target=cnt['bullet_target'],
                       bullet_ID=cnt['enemy_fire_id'],
                       speed=cnt['enemy_speed'],
                       PointList=augment_path(PointList_tran(cnt['point_list']),cnt['random_permute'],cnt['random_flip']),
                       dt=cnt['dt'],
                       hook_global_info=hook_global_info,
                       hook_enemy_group=hook_enemy_group,
                       hook_enemyfire_group=hook_enemyfire_group,
                       hook_player=hook_player,
                       hook_background_group=hook_background_group,
                       init_time=init_time)
        scene_list.append(scene)
        scene_time.append(cnt['scene_time'])
        

# 场景函数

# 场景函数
"""场景2:
在指定屏幕上生成1个型号为ID的敌机, 每架敌机会从屏幕上边缘飞到path的初始点, 循环围绕path飞行并发射子弹,
直到到达最大循环次数或死亡。子弹类型为bullet_ID,发射速度为bullet_speed,发射频率为1/bullet_cd,发射方向为bullet_target
bullet_target ([0,0]为向下发射子弹，[1,1]为向玩家方向发射子弹)
型号为bullet_ID的子弹。敌机循环运动轨迹（最多N次）依次经过PointList=[(x1,y1),(x2,y2),...,(xn,yn)]个点，
运动速度大小恒为speed, 到达和离开循环路径的速度为init_speed, 两架敌机的出现间隔为dt
"""
class scene2():
    def __init__(self,myscreen:pygame.Surface,enemy_ID,PointList,speed,init_speed,max_iter,
                 bullet_speed,bullet_ID,bullet_target,bullet_cd,bullet_break_cnt,bullet_break,
                 hook_global_info:utils.Info,hook_enemyfire_group:pygame.sprite.Group,
                 hook_player:fighter,hook_enemy_group:pygame.sprite.Group,
                 hook_background_group:pygame.sprite.Group,init_time:int=0,wait_time:float=0.5):
        init_speed = init_speed * sim_interval/10.0
        speed = speed * sim_interval/10.0
        self.screen = myscreen
        self.enemy_ID = enemy_ID
        start_PointList = [(PointList[0][0],-0.05*GAME_SCREEN[1]),PointList[0]]
        end_PointList = [PointList[-1],(PointList[-1][0],1.2*GAME_SCREEN[1])]
        self.enemy = None
        self.hook_global_info = hook_global_info
        self.hook_player = hook_player
        self.hook_enemy_group = hook_enemy_group
        self.hook_enemyfire_group = hook_enemyfire_group
        self.hook_background_group = hook_background_group
        self.path, self.pt_index, self.speed_dir = path_cal(start_PointList,init_speed)
        self.shoot_start_index = self.pt_index[-1]
        end_path, end_pt_index, end_speed_dir = path_cal(end_PointList,init_speed)
        path,pt_index,speed_dir = path_cal(duplicate_path(PointList,max_iter),speed)
        pt_index = [index+self.pt_index[-1] for index in pt_index]
        self.path.extend(path)
        self.pt_index.extend(pt_index)
        self.speed_dir.extend(speed_dir)
        self.shoot_end_index = self.pt_index[-1]
        end_pt_index = [index+self.pt_index[-1] for index in end_pt_index]
        self.path.extend(end_path)
        self.pt_index.extend(end_pt_index)
        self.speed_dir.extend(end_speed_dir)
        self.speed = speed
        self.init_speed = init_speed
        self.need_to_end = False
        self.started = False
        self.init_time = init_time   
        self.wait_time = wait_time
        self.bullet_speed = bullet_speed
        self.bullet_ID = bullet_ID
        self.bullet_target = bullet_target
        self.bullet_cd = bullet_cd
        self.bullet_break_cnt = bullet_break_cnt
        self.bullet_break = bullet_break
        self.bullet_cnt = 0
        
    def scene_init(self): # 初始化场景，加入敌机，与__init__()区别开，节省内存开支
        self.enemy = enemy(self.screen,self.enemy_ID,self.path[0],self.speed,(0,-1),self.bullet_speed,self.bullet_ID,
                        self.hook_global_info,self.hook_enemy_group,self.hook_enemyfire_group,self.hook_background_group)
        self.enemy.data = [0,0,len(self.path),0] 
        '''
        data[0]:敌机目前处在的最小（直线）分段点
        data[1]:敌机目前处于的关键点（用于确定速度分量）
        data[2]:敌机总共需要经过的最小分段点
        data[3]:敌机的序号, 防止kill()方法打乱顺序
        '''
        self.enemy.rotate(self.speed_dir[self.enemy.data[1]],rotate_img=True)
        self.enemy.speed_value = 0
        self.hook_enemy_group.add(self.enemy) # 总敌机群加入该敌机
        # 第一个点是敌机出现的初始位置
    def update_time(self):
        self.init_time = pygame.time.get_ticks()
    def update(self):
        # 第一次进入时更新该类时间
        if self.started == False:
            self.started = True
            self.scene_init()
            rect0 = pygame.Rect(0,0,20,20)
            rect0.topleft = (self.path[0][0],-0.2)
            self.hook_background_group.add(warn_mark(self.screen,transgress_xy(rect0),type=1))
            self.update_time()
        self.enemy.update_time()
        self.need_to_end = self.enemy.need_to_remove or (not self.enemy.alive())
        # 判断场景中的敌人是否该移动/删除
        if not self.need_to_end:
            if self.enemy.time - self.init_time >= self.wait_time*1000:
                self.enemy.need_to_move = True
            if self.enemy.data[0] >= self.enemy.data[2] - 1:
                self.enemy.need_to_remove = True

        # 对场景中的敌人进行移动
        if self.enemy.need_to_move and not self.need_to_end:
            self.enemy.data[0] += 1
            if self.enemy.data[0] > self.pt_index[self.enemy.data[1]]:
                self.enemy.data[1] += 1
                self.enemy.rotate(self.speed_dir[self.enemy.data[1]],rotate_img=False)
            self.enemy.move_to(self.path[self.enemy.data[0]])
            if self.shoot_start_index <= self.enemy.data[0] <= self.shoot_end_index: # 位于循环轨迹才发射子弹
                self.enemy.speed_value = self.speed
                if self.bullet_cnt < self.bullet_break_cnt:
                    if self.enemy.time-self.init_time > self.bullet_cd*1000:
                        if self.bullet_target == [1,1]:  # shoot at player
                            self.enemy.orientated_shoot((self.hook_player.rect.centerx,self.hook_player.rect.centery))
                        elif self.bullet_target == [0,0]:  # shoot at speed direction
                            self.enemy.foward_shoot()
                        elif self.bullet_target == [0,-1]:  # shoot at down direction
                            self.enemy.default_shoot()
                        else:  # shoot at target position
                            target_position = (GAME_SCREEN[0]*self.bullet_target[0],GAME_SCREEN[1]*self.bullet_target[1])
                            self.enemy.orientated_shoot(target_position)
                        self.enemy.shooted = True
                        self.update_time()
                        self.bullet_cnt += 1
                else:
                    if self.enemy.time-self.init_time > self.bullet_break*1000:
                        self.bullet_cnt = 0
                        self.update_time()
            else:
                self.enemy.speed_value = self.init_speed
        # 所有敌人都需删除，场景删除所有敌人并不再更新
        if self.need_to_end:
            self.end()
    def end(self):
        self.enemy.kill()
    @staticmethod
    def create(cls_info:dict,scene_list:list,scene_time:list,background:pygame.Surface,
               hook_player:fighter,hook_global_info:utils.Info,
               hook_enemy_group:pygame.sprite.Group,
               hook_enemyfire_group:pygame.sprite.Group,
               hook_background_group:pygame.sprite.Group,
               init_time=pygame.time.get_ticks(),random_permute=False,random_flip=False):
        assert cls_info['type'] == 'scene2', "types of scene_info and scene dont't fit"
        cnt =  dict(type='scene2',
                    point_list=[[0.5, 0.1], [0.45, 0.11], [0.41, 0.12], [0.38, 0.13], [0.35, 0.15], [0.34, 0.17], [0.36, 0.2], [0.39, 0.21], [0.43, 0.22], [0.48, 0.22], [0.52, 0.21], [0.56, 0.19], [0.6, 0.17], [0.6, 0.15], [0.56, 0.14], [0.52, 0.13], [0.48, 0.13], [0.43, 0.13], [0.39, 0.13], [0.36, 0.15], [0.35, 0.17], [0.37, 0.19], [0.42, 0.19], [0.47, 0.19], [0.5, 0.17], [0.52, 0.15], [0.5, 0.13], [0.45, 0.13], [0.42, 0.14], [0.4, 0.16], [0.41, 0.18], [0.44, 0.18], [0.48, 0.19], [0.53, 0.18], [0.56, 0.17], [0.58, 0.15], [0.59, 0.12], [0.56, 0.11], [0.51, 0.11]],
                    enemy_id='eb0',
                    enemy_fire_id=8,
                    enemy_speed=0.5,
                    enemy_init_speed=1.5,
                    max_iter=1,
                    bullet_speed=1.0,
                    bullet_target=[0,-1],
                    bullet_cd=0.4,
                    bullet_break_cnt=2,
                    bullet_break=2.0,
                    wait_time=0.8,
                    scene_time=0.0,
                    random_permute=False,
                    random_flip=False
               )
        cnt.update(cls_info)
        scene = scene2(myscreen=background,
                       enemy_ID=cnt['enemy_id'],
                       PointList=augment_path(PointList_tran(cnt['point_list']),cnt['random_permute'],cnt['random_flip']),
                       speed=cnt['enemy_speed'],
                       init_speed=cnt['enemy_init_speed'],
                       max_iter=cnt['max_iter'],
                       bullet_speed=cnt['bullet_speed'],
                       bullet_ID=cnt['enemy_fire_id'],
                       bullet_target=cnt['bullet_target'],
                       bullet_cd=cnt['bullet_cd'],
                       bullet_break=cnt['bullet_break'],
                       bullet_break_cnt=cnt['bullet_break_cnt'],
                       hook_global_info=hook_global_info,
                       hook_enemy_group=hook_enemy_group,
                       hook_enemyfire_group=hook_enemyfire_group,
                       hook_player=hook_player,
                       hook_background_group=hook_background_group,
                       init_time=init_time,
                       wait_time=cnt['wait_time'],
                       )
        scene_list.append(scene)
        scene_time.append(cnt['scene_time'])