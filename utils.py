from math import sqrt
from typing import Iterable
import pygame
import pygame.mixer
import threading
import time
import yaml
import re
from math import sqrt,cos,sin
import os

with open("config.yml",'r')as f:
    SETTING = yaml.load(f,yaml.SafeLoader)['setting']


class Info:
    def __init__(self,gold=0,diamond=0,score=0):
        self.gold = gold
        self.diamond = diamond
        self.score = score
        self.has_success = False
        self.has_fail = False
        self.lock = threading.Lock()
    def update(self,gold=None,diamond=None,score=None):
        with self.lock:
            if gold is not None: self.gold = gold
            if diamond is not None: self.diamond = diamond
            if score is not None: self.score = score

class Setting:
    def __init__(self):
        # running parameters
        self.has_saved = True
        self.background_jpg = 'background_jpg/img_bg_3.jpg'
        self.scenes = []
        # log parameters
        self.scene_path = ""
        self.fighter_state = []
        self.timestamps = []
    # def log_fighter(self,time:float,x:int,y:int,angle:int,shoot_flag:list(bool,bool,bool),launch_flag:bool):
    #     self.timestamps.append(time)
    #     self.fighter_state.append(dict(x=x,y=y,angle=angle,shoot1=shoot_flag[0],shoot2=shoot_flag[1],shoot3=shoot_flag[2],launch_flag=launch_flag))
        



def pretty_number(num:int)->str:
    if num>1E12:
        return "{:.1f}T".format(num/1E12)
    elif num>1E9:
        return "{:.1f}G".format(num/1E9)
    elif num>1E6:
        return "{:.1f}M".format(num/1E6)
    elif num>1E3:
        return "{:.1f}K".format(num/1E3)
    return str(num)
# 元组差           
def tuple_minus(a,b):           
    return tuple([ax-bx for ax,bx in zip(a,b)])
def tuple_add(a,b):        
    return tuple([ax+bx for ax,bx in zip(a,b)])
# 向量旋转
def vector_rotate(v,phi):
    x1 = v[0]
    x2 = v[1]
    y1 = cos(phi)*x1 - sin(phi)*x2
    y2 = sin(phi)*x1 + cos(phi)*x2
    return (y1,y2)

# 取模函数       
def norm(vector):
    v2 = [i**2 for i in vector]
    return sqrt(sum(v2))

# 计算真实速度的函数
def speed_tran(speed,speed_dir):
    # 向上为正的参考系，主屏幕是向下为正
    V = norm(speed_dir)
    if V < 1e-4:
        return (0,0)
    else:
        return (speed*speed_dir[0]/V,speed*(speed_dir[1])/V)

# 越界补偿
def transgress_xy(rect:pygame.Rect, gamescreen_size:Iterable=SETTING['gamescreen_size']):
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

# 越界检测, 越界：True 
def transgress_detect(rect:pygame.Rect,gamescreen_size:Iterable=SETTING['gamescreen_size']):
    X = gamescreen_size[0]
    Y = gamescreen_size[1]
    if -rect.height < rect.top < Y and -rect.width < rect.left < X:
        return False
    else:
        return True    

# 计算以恒定速度依次到达一个点数组的时间序列和速度方向
def path_cal(PointList:list,speed:float):
    """路径点->轨迹点

    Args:
        PointList (list): [(x1,y1),(x2,y2),...]
        speed (float): speed of track

    Returns:
        (P,Q,V): 
            P: list of resample points [(xa1,ya1),(xa2,ya2),...]\n
            Q: indice of initial points of PointList in P
            V: list of speed (v1,v2) with respect to P
    """
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

def csv2dict(fname:str):
    f = open(fname,'r')
    info_dict = dict()
    keys = f.readline().rstrip().split(',')
    for key in keys:
        info_dict[key] = []
    for line in f.readlines():
        values = line.rstrip().split(',')
        for key,val in zip(info_dict.keys(),values):
            info_dict[key].append(val)
    f.close()
    return info_dict

def path_aug(path:list,inv_index=True,flip=True):
    if inv_index:
        path.reverse()
    if flip:
        for i in range(len(path)):
            path[i][0] = 1.0 - path[i][0]
    return path

# 相对坐标转绝对坐标
def PointList_tran(relative_coordinate,gamscreen_size:Iterable=SETTING['gamescreen_size']):
    # 相对坐标、屏幕尺寸
    n = len(relative_coordinate)
    PointList = list()
    for i in range(n):
        PointList.append((relative_coordinate[i][0]*gamscreen_size[0],relative_coordinate[i][1]*gamscreen_size[1]))
    return PointList


def play_music(sound:pygame.mixer.Sound,volume=None):
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
    
def extract_type(filename_list:list,type='a',pattern:str='[_]\w*[.]'):
    return [index for index in range(len(filename_list)) if re.search(pattern,filename_list[index]) and type in re.search(pattern,filename_list[index]).group()]

def account_sort(account_path:str)->list:
    account_file = os.listdir(account_path)
    if len(account_file)>0:
        account_time = []
        for file in account_file:
            fullpath = os.path.join(account_path,file)
            filetime = os.path.getmtime(fullpath)
            account_time.append(filetime)
        account_tuple = list(zip(account_file,account_time))
        recent_file = sorted(account_tuple,key=lambda ele: ele[1],reverse=True)
        return [item[0] for item in recent_file]
    else:
        return []
    
def scene_statics(scene_list:list)->dict:
    num_dict = dict(scene1=0,scene2=0,e=0,ea=0,eax=0,eb=0,max_speed=0,max_bullet_speed=0)
    for scene in scene_list:
        if scene['type'] == 'scene1':
            num_dict['scene1'] += 1
            if 'ax' in scene['enemy_id']:
                num_dict['eax'] += scene['enemy_num']
            elif 'a' in scene['enemy_id']:
                num_dict['ea'] += scene['enemy_num']
            elif 'b' in scene['enemy_id']:
                num_dict['eb'] += scene['enemy_num']
            else:
                num_dict['e'] += scene['enemy_num']
            num_dict['max_speed'] = max(scene['enemy_speed'],num_dict['max_speed'])
            num_dict['max_bullet_speed'] = max(scene['bullet_speed'],num_dict['max_bullet_speed'])
            
        elif scene['type'] == 'scene2':
            num_dict['scene2'] += 1
            if 'ax' in scene['enemy_id']:
                num_dict['eax'] += 1
            elif 'a' in scene['enemy_id']:
                num_dict['ea'] += 1
            elif 'b' in scene['enemy_id']:
                num_dict['eb'] += 1
            else:
                num_dict['e'] += 1
            num_dict['max_speed'] = max(scene['enemy_speed'],num_dict['max_speed'])
            num_dict['max_bullet_speed'] = max(scene['bullet_speed'],num_dict['max_bullet_speed'])
    return num_dict

