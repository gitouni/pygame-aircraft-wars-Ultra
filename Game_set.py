import json
import warnings
import os
# 定义按钮
class game_set():
    def __init__(self,file_path=''):
        # 保存文件的路径
        self.path = file_path
        # 玩家数据
        self.high_score = 0
        self.gold = 0
        self.diamond = 0        
        self.setting = dict()
        # 战机数据
        self.player_HP_level = 0
        self.player_HP_recover = 0
        self.player_energy_level = 0
        self.player_energy_recover_level = 0
        self.player_cooling_level = 0
        self.player_cooling_recover_level = 0
        # 子弹数据
        self.bullet_ID = 0
        self.bullet_shooting_cd_level = 0
        self.missile_num_level = 0
        self.missile_shooting_cd = 300
        self.missile_damage_level = 0
        self.missile_actime_level = 0
        self.missile_flyingtime_level = 0
        # 参数列表
        self.player_HP_list = [5,6.5,7.5,10,15,20,30,50,90,160]  # 10 level
        self.player_HP_recover_list = [0.0005,0.0008,0.00125,0.002,0.004,0.007,0.01,0.015,0.02,0.03]  # 10 level
        self.player_energy_list = [22,35,50,80,120,185,230,300,415,550]  # 10 level
        self.player_energy_recover_list = [0.02,0.03,0.05,0.08,0.2,0.3,0.4,0.5,0.6,0.7]  # 10
        self.player_cooling_list = [10,14,20,35,55,90,140,200,300,450]  # 10 level
        self.player_cooling_recover_list = [0.01,0.02,0.035,0.05,0.09,0.135,0.18,0.25,0.35,0.5]  # 10
        self.player_shooting_cd_list = [390,330,270,210,150,90,60,30]  # 8
        self.missile_num_list = [1,2,4,6,8] # 5
        self.missile_damage_list = [5,6,7,8.2,9.5,11,13,15,18]  # 8
        self.missile_actime_list = [0.8,0.7,0.65,0.6,0.52,0.45,0.3]  # 7
        self.missile_speed_max_list = [5,5.7,6.5,7.3,9,12,15]  # 7
        self.missile_flyingtime_list = [4,4.5,5,5.5,6.8,9,12.0]  # 7
        # 消耗列表
        self.HP_gold = [250,600,1200,2000,4000,6000,9000,12500,20000] # 9
        self.HP_recover_gold = [300,700,1600,3000,5500,8000,12000,22500,30000] # 9 
        self.energy_gold = [400,800,2000,5000,8000,11000,15000,17500,22500]  # 9
        self.energy_recover_gold = [600,1000,2500,4000,6000,9000,12000,17500,30000] # 9
        self.cooling_gold = [300,600,1400,2000,4500,7000,10000,12500,15000]  # 9
        self.cooling_recover_gold = [400,700,1400,3000,5000,8500,12000,17500,22500] # 9
        
        self.bullet_ID_gold = [200,400,1000,2500,5000]
        self.shooting_cd_gold = [300,600,1800,3500,8000,15000,25000] # 7
        self.missile_num_gold = [350,800,2000,4000]
        self.missile_damage_gold = [200,500,900,2000,4000,10000,18000]  # 7
        self.missile_actime_gold = [100,250,500,1200,2500,5000]  # 6
        self.missile_flyingtime_gold = [150,300,600,1500,3500,6000]  # 6
        
        self.HP_diamond = [0, 0, 0, 0, 25, 50, 100, 150, 200] # 9
        self.HP_recover_diamond = [0, 0, 0, 0, 50, 100, 150, 200, 300] # 9
        self.energy_diamond = [0, 0, 0, 0, 25, 50, 100, 150, 250] # 9
        self.energy_recover_diamond = [0, 0, 0, 0, 25 ,50, 100, 200, 300]  # 9
        self.cooling_diamond = [0, 0, 0, 0, 25, 50, 75, 100, 150]  # 9
        self.cooling_recover_diamond = [0, 0, 0, 0, 25, 50, 75, 150, 250] # 9
        
        self.bullet_ID_diamond = [0, 0, 25, 50, 100] # 5
        self.shooting_cd_diamond = [0, 0, 25, 75, 200, 300, 400, 500] 
        self.missile_num_diamond = [0, 0, 50, 100]
        self.missile_damage_diamond = [0, 0, 0, 50, 100, 200, 300] # 7
        self.missile_actime_diamond = [0, 0, 0, 50, 75, 150] # 6
        self.missile_flyingtime_diamond = [0, 0, 0, 50, 100, 200]  # 6
        if self.path:
            self.load(self.path)
        
    def save(self):
        if self.path and os.path.isfile(self.path):
            with open(self.path,'w')as f:
                json.dump(self.__dict__,f)
        else:
            warnings.warn('save file path not valid:{}'.format(self.path))
    def load(self,path=None):
        if path is None:
            path = self.path
        if os.path.exists(path):
            with open(path,'r')as f:
                self.__dict__ = json.load(f)
        else:
            warnings.warn('data file not exists! file path:{}'.format(path))

class basic_set():
    def __init__(self):
   
        # 参数列表
        self.player_HP_list = [5,6.5,7.5,10,15,20,30,50,90,160]  # 10 level
        self.player_HP_recover_list = [0.0005,0.0008,0.00125,0.002,0.004,0.007,0.01,0.015,0.02,0.03]  # 10 level
        self.player_energy_list = [22,35,50,80,120,185,230,300,415,550]  # 10 level
        self.player_energy_recover_list = [0.02,0.03,0.05,0.08,0.2,0.3,0.4,0.5,0.6,0.7]  # 10
        self.player_cooling_list = [10,14,20,35,55,90,140,200,300,450]  # 10 level
        self.player_cooling_recover_list = [0.01,0.02,0.035,0.05,0.09,0.135,0.18,0.25,0.35,0.5]  # 10
        self.player_shooting_cd_list = [390,330,270,210,150,90,60,30]  # 8
        self.missile_num_list = [1,2,4,6,8] # 5
        self.missile_damage_list = [5,6,7,8.2,9.5,11,13,15,18]  # 8
        self.missile_actime_list = [0.8,0.7,0.65,0.6,0.52,0.45,0.3]  # 7
        self.missile_speed_max_list = [5,5.7,6.5,7.3,9,12,15]  # 7
        self.missile_flyingtime_list = [4,4.5,5,5.5,6.8,9,12.0]  # 7
        # 消耗列表
        self.HP_gold = [250,600,1200,2000,4000,6000,9000,12500,20000] # 9
        self.HP_recover_gold = [300,700,1600,3000,5500,8000,12000,22500,30000] # 9 
        self.energy_gold = [400,800,2000,5000,8000,11000,15000,17500,22500]  # 9
        self.energy_recover_gold = [600,1000,2500,4000,6000,9000,12000,17500,30000] # 9
        self.cooling_gold = [300,600,1400,2000,4500,7000,10000,12500,15000]  # 9
        self.cooling_recover_gold = [400,700,1400,3000,5000,8500,12000,17500,22500] # 9
        
        self.bullet_ID_gold = [200,400,1000,2500,5000]
        self.shooting_cd_gold = [300,600,1800,3500,8000,15000,25000] # 7
        self.missile_num_gold = [350,800,2000,4000]
        self.missile_damage_gold = [200,500,900,2000,4000,10000,18000]  # 7
        self.missile_actime_gold = [100,250,500,1200,2500,5000]  # 6
        self.missile_flyingtime_gold = [150,300,600,1500,3500,6000]  # 6
        
        self.HP_diamond = [0, 0, 0, 0, 25, 50, 100, 150, 200] # 9
        self.HP_recover_diamond = [0, 0, 0, 0, 50, 100, 150, 200, 300] # 9
        self.energy_diamond = [0, 0, 0, 0, 25, 50, 100, 150, 250] # 9
        self.energy_recover_diamond = [0, 0, 0, 0, 25 ,50, 100, 200, 300]  # 9
        self.cooling_diamond = [0, 0, 0, 0, 25, 50, 75, 100, 150]  # 9
        self.cooling_recover_diamond = [0, 0, 0, 0, 25, 50, 75, 150, 250] # 9
        
        self.bullet_ID_diamond = [0, 0, 25, 50, 100] # 5
        self.shooting_cd_diamond = [0, 0, 25, 75, 200, 300, 400, 500] 
        self.missile_num_diamond = [0, 0, 50, 100]
        self.missile_damage_diamond = [0, 0, 0, 50, 100, 200, 300] # 7
        self.missile_actime_diamond = [0, 0, 0, 50, 75, 150] # 6
        self.missile_flyingtime_diamond = [0, 0, 0, 50, 100, 200]  # 6
        
    def save(self,file_path=''):
        if file_path and os.path.exists(os.path.dirname(os.path.abspath(file_path))):
            with open(file_path,'w')as f:
                json.dump(self.__dict__,f)
        else:
            warnings.warn('save file path not valid:{}'.format(file_path))

      
            
if __name__ == "__main__":
    basicset = basic_set()
    basicset.save('data/basic_setting.json')