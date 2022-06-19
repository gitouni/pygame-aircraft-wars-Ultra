from typing import List
import os
import time
from tkinter import simpledialog
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
import pickle as pkl
from Game_set import game_set
from elements import fighter
import yaml
import utils
from scene import scene1,scene2
import threading

class AutoGameRun:
    def __init__(self,gameset:game_set,globalset:utils.Setting,
                 sim_interval:float,volume:float,config_path='config.yml',log=False):
        self.init_pygame()
        # CONFIG
        with open(config_path,'r')as f:
            self.CONFIG = yaml.load(f,yaml.SafeLoader)
        self.is_log = log  # 是否记录游戏
        # group
        self.enemyfire_Group = pygame.sprite.Group()
        self.enemy_Group = pygame.sprite.Group()
        self.bullet_Group = pygame.sprite.Group()
        self.background_Group = pygame.sprite.Group()
        self.scene_time = []
        self.scene_list = []
        self.scene_class = dict(scene1=scene1,scene2=scene2)
        self.init_time = 0
        # setting
        self.gameset = gameset
        self.globalset = globalset
        self.sim_interval = sim_interval
        self.volume = volume
        self.bg_rollv = self.CONFIG['setting']['bg_rollv']  # rolling speed
        self.screen_size = self.CONFIG['setting']['screen_size'] # 完整屏幕的分辨率
        self.statebar_size = self.CONFIG['setting']['status_bar_size'] # 状态栏分辨率
        self.gamescreen_size = self.CONFIG['setting']['gamescreen_size']
        self.screen_bg_color = self.CONFIG['setting']['background_color']
        
    def init_display(self):
        background_img = pygame.image.load(self.globalset.background_jpg)  # 背景图片
        bg_size = background_img.get_size()
        self.bg_resize = (self.screen_size[0],int(self.screen_size[0]/bg_size[0]*bg_size[1]))
        self.background_img = pygame.transform.scale(background_img,self.bg_resize)
        self.display_font = pygame.font.SysFont('arial', 40, bold=True)
        self.screen = pygame.display.set_mode(self.screen_size)
        self.background = pygame.Surface((self.gamescreen_size[0]+100,self.gamescreen_size[1]+100))  # blit can receive negative coordinates rather than larger than window size
        self.pause_log = pygame.image.load(os.path.join(self.CONFIG['icon']['path'],self.CONFIG['icon']['pause']))
        self.pause_log = pygame.transform.scale(self.pause_log,[40,40])
        self.pause_pos = (self.screen_size[0]//2 - 20, self.screen_size[1]//2 - 20)
    @staticmethod
    def init_pygame():
        if not pygame.get_init():
            pygame.init()  # 初始化背景设置
        if not pygame.font.get_init():
            pygame.font.init() # 初始化字体设置
        if not pygame.mixer.get_init():
            pygame.mixer.init(20000,buffer=1024)  # 音乐初始化
            pygame.mixer.music.set_volume(1)  # 音量初始化
    
    def system_reset_time(self):
        self.init_time = 0
    
    def scene_check(self,now):
        remove_id = []
        for i,scene in enumerate(self.scene_list):
            assert isinstance(scene,(scene1,scene2))
            if not scene.need_to_end:
                if now - self.init_time >= self.scene_time[i]*1000:
                    scene.update()
            else:
                remove_id.append(i)
        if remove_id:
            remove_id.reverse()  # 倒序删除，不影响数组其他元素顺序
            for index in remove_id:
                del self.scene_list[index]  # delete scene and free memory
                del self.scene_time[index]

    def create_scene(self,player:fighter,player_info:utils.Info):
        max_scene_time = 0
        for scene_info in self.globalset.scenes:
            self.scene_class[scene_info['type']].create(scene_info,self.scene_list,self.scene_time,self.background,
                                                hook_player=player,hook_global_info=player_info,
                                                hook_enemy_group=self.enemy_Group,
                                                hook_enemyfire_group=self.enemyfire_Group,
                                                hook_background_group=self.background_Group,
                                                sim_interval=self.sim_interval,
                                                init_time=self.init_time,
                                                volume_multiply=self.volume)
            max_scene_time = max(max_scene_time,scene_info['scene_time'])
        return max_scene_time
    
    
    def clear_sprite(self):
        for sprite in self.enemyfire_Group.sprites():
            sprite.kill()
        for sprite in self.enemy_Group.sprites():
            sprite.kill()
        for sprite in self.bullet_Group.sprites():
            sprite.kill()
        for sprite in self.background_Group.sprites():
            sprite.kill()
                

    def collide_detect(self,player:fighter):
        myfire_collide = pygame.sprite.groupcollide(self.enemy_Group,self.bullet_Group,False,False)
        for unit in myfire_collide.keys():  # enemy
            if utils.transgress_detect(unit.rect):
                continue
            hit_bullets = myfire_collide[unit] # 与敌机碰撞的子弹列表
            for blt in hit_bullets:  # bullet
                collide_xy = pygame.sprite.collide_mask(unit,blt)
                if collide_xy:
                    unit.hurt(blt.damage) # 对敌机造成子弹的伤害
                    blt.dead()  # 组中删除子弹
        if player.alive_:
            enemy_collide = pygame.sprite.spritecollideany(player,self.enemy_Group)
            if enemy_collide:  # enemy
                if not utils.transgress_detect(enemy_collide.rect):
                    if pygame.sprite.collide_mask(player,enemy_collide):            
                        enemy_collide.hurt(player.HP) # 敌军受到玩家撞击伤害
                        player.hurt(enemy_collide.collide_damage) # 玩家受到敌军撞击伤害
            enemyfire_collide = pygame.sprite.spritecollideany(player,self.enemyfire_Group)
            if enemyfire_collide:  # enemyfire
                if pygame.sprite.collide_mask(player,enemyfire_collide):
                    player.hurt(enemyfire_collide.damage) # 玩家受到敌军火力伤害
                    enemyfire_collide.dead() # 删除敌军子弹

    # 事件检查函数
    
    
    def run(self):
        def failed():
            threading.Thread(target=utils.play_music,args=(pygame.mixer.Sound(self.CONFIG['setting']['fail_sound_file']),self.volume)).start()
            
        def succeeded():
            threading.Thread(target=utils.play_music,args=(pygame.mixer.Sound(self.CONFIG['setting']['success_sound_file']),self.volume)).start()
        self.init_display()
        self.globalset.win_open['game'] = True
        self.globalset.has_saved = False
        player_info = utils.Info(self.gameset.gold,self.gameset.diamond)
        player_info.has_success = False
        player_info.has_fail = False
        pygame.display.set_caption("pygame-aircraft-ultra")
        pygame.display.set_icon(pygame.image.load(self.CONFIG['setting']['game_ico']))
        # 渐变显示窗口
        for i in range(11):
            self.screen.fill(tuple([255*(1-i/10) for _ in self.screen_bg_color]))
            time.sleep(0.03)
            pygame.display.flip()
        #开始游戏
        player = fighter(self.background,self.screen,self.enemy_Group,self.bullet_Group,self.background_Group,self.sim_interval,self.volume,self.globalset.player_index)
        player.game_set(self.gameset) # 使用该游戏设置
        player.blitme()
        pygame.display.flip()
        max_scene_time = self.create_scene(player,player_info)
        self.system_reset_time()
        now = self.init_time
        running = True
        pause = False
        blit_ad = 0
        now = self.init_time
        self.globalset.fighter_state.clear()
        clock = pygame.time.Clock()
        while running:
            # 监视屏幕
            running, pause = self.event_check(player,pause)
            while pause and running:
                running, pause = self.event_check(player,pause)
                self.screen.blit(self.pause_log,self.pause_pos)
                pygame.display.flip()
            if not running:
                break
            
            # 让最近绘制的屏幕可见
            now += self.sim_interval
            if self.is_log:
                self.globalset.log_fighter(dict(left=player.moving_left,right=player.moving_right,up=player.moving_up,down=player.moving_down),
                                            player.shooting,
                                            [player.shoot1,player.shoot2,player.shoot3],
                                            player.launching)
            blit_ad += self.sim_interval/1000*self.bg_rollv % self.bg_resize[1]
            blit_ad %= self.bg_resize[1]
            self.background.blit(self.background_img,(0,round(blit_ad)-self.bg_resize[1]+30))
            self.background.blit(self.background_img,(0,round(blit_ad)+30))
            self.scene_check(now)
            self.collide_detect(player)            
            self.bullet_Group.update()
            if player.alive_:
                player.update()    
            self.enemyfire_Group.update()
            self.background_Group.update()
            self.screen.blit(self.background,(0,30))
            self.draw_statebar(player,player_info,now) # 更新状态栏
            if (not player.alive_):
                if not player_info.has_fail:
                    failed()
                    player_info.has_fail = True
                elif (now - self.init_time) % 1000 > 500:
                    display_font_surface = self.display_font.render('Mission Failed',True,[255,0,0])
                    self.screen.blit(display_font_surface,self.CONFIG['setting']['fail_font_pos'])
            else:
                if now - self.init_time > max_scene_time*1000 and len(self.enemy_Group.sprites())==0:
                    if not player_info.has_success:
                        succeeded()
                        player_info.has_success = True
                    elif (now - self.init_time) % 1000 > 500:
                        success_font_surface = self.display_font.render('Mission Accomplished',True,[255,255,255])
                        self.screen.blit(success_font_surface,self.CONFIG['setting']['success_font_pos'])
            pygame.display.flip()  # 更新画面
            clock.tick(1000.0/self.sim_interval)
        self.gameset.gold = int(player_info.gold)
        self.gameset.diamond = int(player_info.diamond)
        self.gameset.high_score = max(self.gameset.high_score,player_info.score)
        self.quit_game()
        
    def draw_statebar(self,player:fighter,player_info:utils.Info,now:int):
        # 分隔线
        pygame.draw.rect(self.screen,(0,0,0),pygame.Rect((0,0),self.statebar_size))
        pygame.draw.line(self.screen,(0,255,0),(0,self.statebar_size[1]-1),\
                        (self.statebar_size[0],self.statebar_size[1]-1),2)
        # 图标参数
        icon_size = (20,20) # 小图标大小
        
        icon_pos = [(5,5),(65,5),(125,5),(185,2),(260,2)] # icon的topleft坐标
        GOLD_POS = (210,5)
        DIAMOND_POS = (285,5)
        SCORE_POS = (340,5)
        TIME_POS = (410,5)
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
            self.screen.blit(icon_list[i],icon_pos[i])    
        rect_pos = [(27,5),(87,5),(147,5)] # 矩形topleft坐标
        Rect_pos = [(26,5),(86,5),(146,5)]
        rect_width = [player.HP/player.HP_max*29,player.energy/player.energy_max*29,\
                    player.cooling/player.cooling_max*29] # 矩形宽度
        rect_color = [(255,0,0),(255,0,255),(200,200,255)]
        for i in range(3):
            if rect_width[i] > 0:# 若矩形宽度不为0
                pygame.draw.rect(self.screen,rect_color[i],pygame.Rect(rect_pos[i],(rect_width[i],20)),0)
            # 填充部分
            pygame.draw.rect(self.screen,(200,200,200),pygame.Rect(Rect_pos[i],(30,20)),1)
            # 外框
        gold_font = pygame.font.SysFont('arial', 15, bold=True)
        diamond_font = pygame.font.SysFont('arial', 15, bold=True)
        score_font = pygame.font.SysFont('arial', 15, bold=True,italic=True)
        time_font = pygame.font.SysFont('arial',15,bold=True)
        gold_font_surface = gold_font.render(utils.pretty_number(player_info.gold),True,[255,255,255])
        diamond_font_surface = diamond_font.render(utils.pretty_number(player_info.diamond),True,[255,255,255])
        score_font_surface = score_font.render(utils.pretty_number(player_info.score),True,[180,255,255])
        time_font_surface = time_font.render("{:.2f}s".format((now-self.init_time)/1000.0),True,[255,100,100])
        self.screen.blit(gold_font_surface,GOLD_POS)
        self.screen.blit(diamond_font_surface,DIAMOND_POS)
        self.screen.blit(score_font_surface,SCORE_POS)
        self.screen.blit(time_font_surface,TIME_POS)
    
    
    @staticmethod
    def event_check(player:fighter,pause:bool) -> tuple:
        running = True
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # 检测到按退出键，实施软退出
                running = False
                return False, pause
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
                    if event.key == pygame.K_p:
                        pause = not pause
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_RIGHT:
                        player.moving_right = False
                    elif event.key == pygame.K_LEFT:
                        player.moving_left = False
                    if event.key == pygame.K_UP:
                        player.moving_up = False
                    elif event.key == pygame.K_DOWN:
                        player.moving_down = False
        return running, pause
    
    def quit_game(self):
        if self.gameset.path:
            self.gameset.save()
        # pygame.mixer.quit()
        # pygame.font.quit()
        # pygame.quit()
        self.globalset.win_open['game'] = False
        self.clear_sprite()
        self.scene_list.clear()
        self.scene_time.clear()  
        if not self.is_log:
            return
        date = time.localtime(time.time())
        date_str = time.strftime(r"%Y-%m-%d-%H-%M-%S",date)
        save_name = simpledialog.askstring('保存录像','请键入保存录像的名称\n空值或Cancel表示不保存。',initialvalue=date_str)
        if not save_name:
            return
        os.makedirs('video',exist_ok=True)
        with open(os.path.join('video',save_name+'.p'),'wb')as f:
            pkl.dump(dict(meta=dict(time=time.strftime(r"%Y-%m-%d %H:%M:%S",date),
                                     sim_interval=self.sim_interval,
                                     scene=self.globalset.scene_path,
                                     player_skin=self.globalset.player_index,
                                     player_dict=self.gameset.__dict__),
                                    state=self.globalset.fighter_state),f)
            
class LogGameRun(AutoGameRun):
    def __init__(self,gameset:game_set,globalset:utils.Setting,
                 sim_interval:float,volume:float,log_path:str,config_path='config.yml'):
        super(LogGameRun,self).__init__(gameset,globalset,
                 sim_interval,volume,config_path)
        with open(log_path,'rb')as f:
            self.log_dict = pkl.load(f)
        with open(self.log_dict['meta']['scene'],'r')as f:
            scene = json.load(f)
        self.sim_interval = self.log_dict['meta']['sim_interval']
        self.gameset.__dict__ = self.log_dict['meta']['player_dict']
        self.globalset.background_jpg = scene['meta']['background']
        self.globalset.scenes = scene['scene']
        self.globalset.player_index = self.log_dict['meta']['player_skin']
        self.index = 0
    
    @staticmethod  
    def event_check(player:fighter,state:dict,pause:bool) -> tuple:
        running = True
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # 检测到按退出键，实施软退出
                running = False
                return False, pause
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    pause = not pause
        if player.alive_: # 玩家阵亡时不再响应控制按键
            player.moving_down = state['moving']['down']
            player.moving_up = state['moving']['up']
            player.moving_left = state['moving']['left']
            player.moving_right = state['moving']['right']
            player.shoot1 = state['shoot_mode'][0]
            player.shoot2 = state['shoot_mode'][1]
            player.shoot3 = state['shoot_mode'][2]
            player.shooting = state['shoot']
            player.launching = state['launch']
        return running, pause
    
    def quit_game(self):
        # pygame.mixer.quit()
        # pygame.font.quit()
        # pygame.quit()
        self.globalset.win_open['game'] = False
        self.clear_sprite()
        self.scene_list.clear()
        self.scene_time.clear() 
     
    def run(self):
        def failed():
            threading.Thread(target=utils.play_music,args=(pygame.mixer.Sound(self.CONFIG['setting']['fail_sound_file']),self.volume)).start()
            
        def succeeded():
            threading.Thread(target=utils.play_music,args=(pygame.mixer.Sound(self.CONFIG['setting']['success_sound_file']),self.volume)).start()
        self.init_display()
        self.globalset.win_open['game'] = True
        self.globalset.has_saved = False
        player_info = utils.Info(self.gameset.gold,self.gameset.diamond)
        player_info.has_success = False
        player_info.has_fail = False
        pygame.display.set_caption("pygame-aircraft-ultra")
        pygame.display.set_icon(pygame.image.load(self.CONFIG['setting']['game_ico']))
        # 渐变显示窗口
        for i in range(11):
            self.screen.fill(tuple([255*(1-i/10) for _ in self.screen_bg_color]))
            time.sleep(0.03)
            pygame.display.flip()
        #开始游戏
        player = fighter(self.background,self.screen,self.enemy_Group,self.bullet_Group,self.background_Group,self.sim_interval,self.volume,self.globalset.player_index)
        player.game_set(self.gameset) # 使用该游戏设置
        player.blitme()
        pygame.display.flip()
        max_scene_time = self.create_scene(player,player_info)
        running = True
        pause = False
        size_state = len(self.log_dict['state'])
        blit_ad = 0
        self.system_reset_time()
        now = self.init_time
        clock = pygame.time.Clock()
        while running:
            # 监视屏幕
            now += self.sim_interval
            if self.index < size_state:
                state = self.log_dict['state'][self.index]
                self.index += 1
            else:
                state = self.log_dict['state'][-1]
                state['shoot'] = False
                state['launch'] = False
                if not player_info.has_success:
                    player.alive_ = False  # 终止飞机互动
            
            running, pause = self.event_check(player,state,pause)
            while pause and running:
                running, pause = self.event_check(player,state,pause)
                self.screen.blit(self.pause_log,self.pause_pos)
                pygame.display.flip()
            if not running:
                break
            # 让最近绘制的屏幕可见
            blit_ad += self.sim_interval/1000*self.bg_rollv % self.bg_resize[1]
            blit_ad %= self.bg_resize[1]
            self.background.blit(self.background_img,(0,round(blit_ad)-self.bg_resize[1]+30))
            self.background.blit(self.background_img,(0,round(blit_ad)+30))
            self.scene_check(now)
            self.collide_detect(player)            
            self.bullet_Group.update()
            if player.alive_:
                player.update()    
            self.enemyfire_Group.update()
            self.background_Group.update()
            self.screen.blit(self.background,(0,30))
            self.draw_statebar(player,player_info,now) # 更新状态栏
            if (not player.alive_):
                if not player_info.has_fail:
                    failed()
                    player_info.has_fail = True
                elif (now - self.init_time) % 1000 > 500 and (not player_info.has_success):
                    display_font_surface = self.display_font.render('Log Finished',True,[255,0,0])
                    self.screen.blit(display_font_surface,self.CONFIG['setting']['fail_font_pos'])
            else:
                if now - self.init_time > max_scene_time*1000 and len(self.enemy_Group.sprites())==0:
                    if not player_info.has_success:
                        succeeded()
                        player_info.has_success = True
                    elif (now - self.init_time) % 1000 > 500:
                        success_font_surface = self.display_font.render('Mission Accomplished',True,[255,255,255])
                        self.screen.blit(success_font_surface,self.CONFIG['setting']['success_font_pos'])
            pygame.display.flip()  # 更新画面
            clock.tick(1000.0/self.sim_interval)
        self.gameset.gold = int(player_info.gold)
        self.gameset.diamond = int(player_info.diamond)
        self.gameset.high_score = max(self.gameset.high_score,player_info.score)
        self.quit_game()
        
class TwoPlayerRun(AutoGameRun):
    def __init__(self,gameset1:game_set,gameset2:game_set,globalset:utils.Setting,
                 sim_interval:float,volume:float,config_path='config.yml'):
        self.init_pygame()
        # CONFIG
        with open(config_path,'r')as f:
            self.CONFIG = yaml.load(f,yaml.SafeLoader)
        # group
        self.enemyfire_Group = pygame.sprite.Group()
        self.enemy_Group = pygame.sprite.Group()
        self.bullet_Group = pygame.sprite.Group()
        self.background_Group = pygame.sprite.Group()
        self.scene_time = []
        self.scene_list = []
        self.scene_class = dict(scene1=scene1,scene2=scene2)
        self.init_time = 0
        # setting
        self.gameset1 = gameset1
        self.gameset2 = gameset2
        self.globalset = globalset
        self.sim_interval = sim_interval
        self.volume = volume
        self.bg_rollv = self.CONFIG['setting']['bg_rollv']  # rolling speed
        self.screen_size = self.CONFIG['setting']['screen_size'] # 完整屏幕的分辨率
        self.statebar_size = self.CONFIG['setting']['status_bar_size'] # 状态栏分辨率
        self.gamescreen_size = self.CONFIG['setting']['gamescreen_size']
        self.screen_bg_color = self.CONFIG['setting']['background_color']
        
    
        
            
