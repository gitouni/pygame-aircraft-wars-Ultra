# coding=utf-8
import os
import time
import re
import pygame
# extend import
import pygame.draw
import pygame.mixer
import pygame.sprite
import pygame.time
import pygame.transform
import pygame.image
import pygame.font
import pygame.display

from Game_set import game_set
from Scene_set import scenes
from elements import fighter
import yaml
import utils
from scene import scene1
from utils import Info



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
    def __init__(self,myscreen:pygame.Surface,button_dict:dict,png_dict:dict,bg_img):
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



# 场景函数
"""场景2:
在指定屏幕上生成1个型号为ID的敌机, 每架敌机会从屏幕上边缘飞到path的初始点, 循环围绕path飞行并发射子弹,
直到到达最大循环次数或死亡。子弹类型为bullet_ID,发射速度为bullet_speed,发射频率为1/bullet_cd,发射方向为bullet_target
bullet_target ([0,0]为向下发射子弹，[1,1]为向玩家方向发射子弹)
型号为bullet_ID的子弹。敌机循环运动轨迹依次经过PointList=[(x1,y1),(x2,y2),...,(xn,yn)]个点，
运动速度大小恒为speed, 到达和离开循环路径的速度为init_speed, 两架敌机的出现间隔为dt
# """
# class scene2():
#     def __init__(self,myscreen,t0,enemy_num,enemy_ID,bullet_speed,bullet_ID,speed,PointList,dt,bullet_target):
#         self.screen = myscreen
#         self.N = enemy_num # 场景初始敌机数
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
#         self.bullet_target = bullet_target
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
#             data[3]:敌机的序号，防止kill()方法打乱顺序
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
#         for enemy0 in self.enemy_group.sprites():
#             assert isinstance(enemy0,enemy), "Class must be enemy!"
#             if not enemy0.need_to_remove:
#                 enemy0.update_time()
#                 if enemy0.time - self.init_time > (enemy0.data[3]+1)*self.dt*1000:
#                     enemy0.need_to_move = True
#                 if enemy0.data[0] >= enemy0.data[2] - 1:
#                     enemy0.need_to_remove = True
#         # 对场景中的敌人进行移动
#         for enemy0 in self.enemy_group.sprites():
#             assert isinstance(enemy0,enemy), "Class must be enemy!"
#             if enemy0.need_to_move and not enemy0.need_to_remove:
#                 enemy0.data[0] += 1
#                 if enemy0.data[0] > self.point[enemy0.data[1]]:
#                     enemy0.data[1] += 1
#                     enemy0.rotate(self.speed_dir[enemy0.data[1]])
#                 enemy0.move_to(self.path[enemy0.data[0]])
#                 if self.t0: # 当t0=0或None时不发射子弹
#                     if enemy0.time-self.init_time>self.t0*1000+(enemy0.data[3]+1)*self.dt*1000 and not enemy0.shooted:
#                         if self.bullet_target == [1,1]:  # shoot at player
#                             enemy0.orientated_shoot((player.rect.centerx,player.rect.centery))
#                         elif self.bullet_target == [0,0]:  # shoot at speed direction
#                             enemy0.default_shoot()
#                         else:  # shoot at target position
#                             target_position = (gamescreen_size[0]*self.bullet_target[0],gamescreen_size[1]*self.bullet_target[1])
#                             enemy0.orientated_shoot(target_position)
#                         enemy0.shooted = True
#         # 所有敌人都需删除，场景删除所有敌人并不再更新
#         flag = True
#         for enemy0 in self.enemy_group.sprites():
#             assert isinstance(enemy0,enemy), "Class must be enemy!"
#             flag = flag and enemy0.need_to_remove
#         self.need_to_end = flag
#         if self.need_to_end:
#             self.end()
#     def end(self):
#         for sprite in self.enemy_group.sprites():
#             sprite.kill()
#     @staticmethod
#     def create(cls_info):
#         assert isinstance(cls_info,dict), "scene info must be dict"
#         assert cls_info['type'] == 'scene1', "types of scene_info and scene dont't fit"
#         scene = scene1(myscreen=background,
#                        t0=cls_info['bullet_time'],
#                        enemy_num=cls_info['enemy_num'],
#                        enemy_ID=cls_info['enemy_id'],
#                        bullet_speed=cls_info['bullet_speed'],
#                        bullet_target=cls_info['bullet_target'],
#                        bullet_ID=cls_info['enemy_fire_id'],
#                        speed=cls_info['enemy_speed'],
#                        PointList=utils.PointList_tran(cls_info['point_list'],screen_size),
#                        dt=cls_info['dt'])
#         scene_list.append(scene)
#         scene_time.append(cls_info['scene_time'])


            
   
            

def center_text(out_rect,text_rect):
    x1 = out_rect.left
    y1 = out_rect.top
    dwidth = 1/2*(out_rect.width-text_rect.width)
    dheight = 1/2*(out_rect.height-text_rect.height)
    return (x1+dwidth,y1+dheight) 



def collide_detect():
    myfire_collide = pygame.sprite.groupcollide(enemy_Group,bullet_Group,False,False)
    for unit in myfire_collide.keys():
        hit_bullets = myfire_collide[unit] # 与敌机碰撞的子弹列表
        for blt in hit_bullets:
            collide_xy = pygame.sprite.collide_mask(unit,blt)
            if collide_xy and not utils.transgress_detect(unit.rect):
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
        scene_class[scene_info['type']].create(scene_info,scene_list,scene_time,background,
                                               player,Global_info,enemy_Group,enemyfire_Group,background_Group,init_time)
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
    button_pos = utils.PointList_tran([(0.3,0.7),(0.7,0.7)],screen_size)
    png_pos = utils.PointList_tran([(0.7,0.4)],screen_size)
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
    special_enemyfire_id = [enemyfire_id for enemyfire_id in range(len(enemyfire_dict['filename'])) if 'a' in re.search('[_]\w*',enemyfire_dict['filename'][enemyfire_id]).group()]
    GOLD_POS = (210,5)
    DIAMOND_POS = (300,5)
    SCORE_POS = (350,5)
    pygame.init()  # 初始化背景设置
    pygame.font.init() # 初始化字体设置
    screen = pygame.display.set_mode(screen_size)
    background = pygame.Surface((gamescreen_size[0]+100,gamescreen_size[1]+100))  # blit can receive negative coordinates rather than larger than window size
    pygame.display.set_caption("空中游侠")
    
    bullet_Group = pygame.sprite.Group() # player的子弹群
    enemy_Group = pygame.sprite.Group() # 敌机群
    enemyfire_Group = pygame.sprite.Group() # 敌军的子弹群
    background_Group = pygame.sprite.Group() # 背景动画群
    player = fighter(background,screen,enemy_Group,bullet_Group,background_Group)
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