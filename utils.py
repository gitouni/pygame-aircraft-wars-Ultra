from math import sqrt
from typing import Iterable
import pygame
import pygame.mixer
import threading
import time
import yaml
import re
from math import sqrt,cos,sin

with open("config.yml",'r')as f:
    SETTING = yaml.load(f,yaml.SafeLoader)['setting']


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
