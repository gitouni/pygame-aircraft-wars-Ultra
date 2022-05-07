import json
import warnings
import os
# 定义按钮
class game_set():
    def __init__(self,file_path='data/game_set0.json'):
        # 保存文件的路径
        self.path = file_path
        # 玩家数据
        self.high_score = 0
        self.gold = 0
        self.diamond = 0        
        # 战机数据
        self.player_HP_level = 5
        self.player_HP_recover = 3
        self.player_energy_level = 3
        self.player_energy_recover_level = 2
        self.player_cooling_level = 3
        self.player_cooling_recover_level = 2
        # 子弹数据
        self.bullet_ID = 1
        self.bullet_shooting_cd_level = 5
        self.missile_num_level = 3
        self.missile_shooting_cd = 100
        self.missile_damage_level = 1
        self.missile_actime_level = 3
        self.missile_flyingtime_level = 4
        # 参数列表
        self.player_HP_list = [5,6.5,7.5,10,15,20,30]  # 7 level
        self.player_HP_recover_list = [0.0005,0.001,0.002,0.005,0.01,0.025,0.05]  # 7 level
        self.player_energy_list = [15,30,45,65,90,120,150]  # 7 level
        self.player_energy_recover_list = [0.03,0.05,0.1,0.18,0.32,0.5,0.75]  # 7
        self.player_cooling_list = [10,16,24,36,50,75,120]  # 7
        self.player_cooling_recover_list = [0.04,0.07,0.14,0.24,0.36,0.5,0.68]  # 7
        self.player_shooting_cd_list = [400,333,285,200,166,100,66]  # 7
        self.missile_num_list = [1,2,4,6,8] # 5
        self.missile_damage_list = [10,12,15,18,24,27,30]  # 7
        self.missile_actime_list = [1.0,0.8,0.65,0.6,0.52,0.45,0.3]  # 7
        self.missile_speed_max_list = [4,5,6,7,8,9,10]  # 7
        self.missile_flyingtime_list = [3,3.5,4,4.5,5,6,7]  # 7
        # 消耗列表
        self.HP_gold = [100,250,500,1500,2500,5000]
        self.HP_recover_gold = [300,700,1750,3500,7000,20000]
        self.energy_gold = [200,550,1250,3000,7000,10000]
        self.energy_recover_gold = [300,800,2000,4000,8000,20000]
        self.cooling_gold = [150,300,700,1500,5000,15000]
        self.cooling_recover_gold = [200,600,1500,3000,6000,12500]
        
        self.bullet_ID_gold = [400,1000,1500,2000,5000]
        self.shooting_cd_gold = [200,500,1000,2000,4500,10000]
        self.missile_num_gold = [300,700,1500,3500]
        self.missile_damage_gold = [150,250,500,1000,2000,3000]
        self.missile_actime_gold = [100,250,350,600,1000,1500]
        self.missile_flyingtime_gold = [150,300,450,800,1250,2000]
        
        self.HP_diamond = [0, 0, 0, 50, 100, 250]
        self.HP_recover_diamond = [0, 0, 0, 100, 250, 500]
        self.energy_diamond = [0, 0, 0, 50, 100, 350]
        self.energy_recover_diamond = [0, 0, 0, 100, 300, 600]
        self.cooling_diamond = [0, 0, 0, 50, 100, 200]
        self.cooling_recover_diamond = [0, 0, 0, 100, 200, 350]
        
        self.bullet_ID_diamond = [0, 0, 0, 50, 150, 400]
        self.shooting_cd_diamond = [0, 0, 0, 100, 250, 500]
        self.missile_num_diamond = [0, 0, 25, 50, 100, 150]
        self.missile_damage_diamond = [0, 0, 25, 50, 100, 200]
        self.missile_actime_diamond = [0, 0, 0, 50, 75, 125]
        self.missile_flyingtime_diamond = [0, 0, 0, 50, 75, 125]
        
    def save(self):
        with open(self.path,'w')as f:
            json.dump(self.__dict__,f)
    def load(self,path=None):
        if path is None:
            path = self.path
        if os.path.exists(path):
            with open(path,'r')as f:
                self.__dict__ = json.load(f)
        else:
            warnings.warn('data file not exists! file path:{}'.format(path))

enemy_data = dict(
    e0=dict(HP_max=1,collide_damage=1),
    e1=dict(HP_max=1,collide_damage=1),
    e2=dict(HP_max=1,collide_damage=1),
    e3=dict(HP_max=1.5,collide_damage=1.5),
    e4=dict(HP_max=1.5,collide_damage=1.5),
    e5=dict(HP_max=1.5,collide_damage=1.5),
    e6=dict(HP_max=2,collide_damage=2),
    e7=dict(HP_max=2,collide_damage=2),
    e8=dict(HP_max=2,collide_damage=2),)
      
            
if __name__ == "__main__":
    game_set0 = game_set()
    game_set0.load()
    game_set1 = game_set()
    gold,diamond,score = game_set0.gold,game_set0.diamond,game_set0.high_score
    game_set1.gold = gold
    game_set1.diamond = diamond
    game_set1.high_score = score
    game_set1.save()
    print(game_set1.__dict__)