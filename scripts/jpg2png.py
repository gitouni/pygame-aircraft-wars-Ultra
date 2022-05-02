#-*- coding: UTF-8 -*-  
 
from PIL import Image
from PIL.ImageFile import ImageFile
import numpy as np
import os

BASE_DIR = os.path.dirname(__file__)
suffix = '.jpg'
src_dir = "../enemy_jpg"
dst_dir = "../enemy_png"

def toTransparent(img:ImageFile, rgb_threshold=30, factor=0.0):
    img = img.convert('RGBA')
    r_,g_,b_,a_ = map(np.array,img.split())
    a_[r_+g_+b_<rgb_threshold] = factor
    alpha = Image.fromarray(a_,mode='L')
    img.putalpha(alpha)
    return img


jpg_dir = os.path.join(BASE_DIR,src_dir)
png_dir = os.path.join(BASE_DIR,dst_dir)
jpg_files = [file for file in os.listdir(jpg_dir) if os.path.splitext(file)[1] == suffix]
for file in jpg_files:
    full_path = os.path.join(jpg_dir,file)
    img = Image.open(full_path)
    img = toTransparent(img,50,0.0)
    img.save(os.path.join(png_dir,os.path.splitext(file)[0]+'.png'))
    

