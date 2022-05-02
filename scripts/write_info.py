import os
import re
BASE_DIR = os.path.dirname(__file__)
enemy_path = os.path.join(BASE_DIR,'../enemy_png')
enemyfile_path = os.path.join(BASE_DIR,'../enemyfire_png')
bullet_path = os.path.join(BASE_DIR,"../bullet_png")

enemy_files = [file for file in sorted(os.listdir(enemy_path)) if os.path.splitext(file)[1] == '.png']
enemyfile_files = [file for file in sorted(os.listdir(enemyfile_path)) if os.path.splitext(file)[1] == '.png']
bullet_files = [file for file in sorted(os.listdir(bullet_path)) if os.path.splitext(file)[1] == '.png']
HP_dict = dict(tiny=1,small=3,big=8)
enemyfire_damage_list = [0.5,1.0,2.5]
enemyfire_level_list = [0,1,2]
bullet_level_list = [0,1,2]
enemy_gold_list = [2,3,7]
enemy_score_list = [10,15,35]
enemy_diamond_list = [0.01,0.05,0.12]
bullet_dmage_list = [1.0,1.5,2.0,3.0,4.5]
f = open(os.path.join(BASE_DIR,"../data/enemy_info.csv"),'w')
f.write("filename,size,HP,gold,diamond,score\n")
for file in enemy_files:
    size = 'tiny'
    gold = enemy_gold_list[0]
    diamond = enemy_diamond_list[0]
    score = enemy_score_list[0]
    if 'a' in file:
        size = 'small'
        gold = enemy_gold_list[1]
        diamond = enemy_diamond_list[1]
        score = enemy_score_list[1]
    elif 'b' in file:
        size = 'big'
        gold = enemy_gold_list[2]
        diamond = enemy_diamond_list[2]
        score = enemy_score_list[2]
    HP = HP_dict[size]
    info = f'{file},{size},{HP},{gold},{diamond},{score}\n'
    f.write(info)
f.close()
f = open(os.path.join(BASE_DIR,"../data/enemyfire_info.csv"),'w')
f.write("filename,damage,level\n")
for file in enemyfile_files:
    key = re.search("[_]\w*",file).group()  # 匹配.png前面的下划线后面的字符
    damage = enemyfire_damage_list[0]
    level = enemyfire_level_list[0]
    if 'a' in key:
        damage = enemyfire_damage_list[1]
        level = enemyfire_level_list[1]
    elif 'b' in key:
        damage = enemyfire_damage_list[2]
        level = enemyfire_level_list[2]
    info = f'{file},{damage},{level}\n'
    f.write(info)
f.close()
f = open(os.path.join(BASE_DIR,"../data/bullet_info.csv"),'w')
f.write("filename,damage,level\n")
for file in bullet_files:
    key = re.search("[_]\w*",file).group()
    damage = bullet_dmage_list[0]
    level = bullet_level_list[0]
    if 'a' in key:
        damage = bullet_dmage_list[1]
        level = bullet_level_list[1]
    elif 'b' in key:
        damage = bullet_dmage_list[2]
        level = bullet_level_list[2]
    info = f'{file},{damage},{level}\n'
    f.write(info)
f.close()