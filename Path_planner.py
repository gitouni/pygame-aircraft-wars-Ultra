# -*- coding: utf-8 -*-
import tkinter as tk
from scipy.interpolate import splrep,splev
import numpy as np
import json
import os

class Path_Planner():
    def __init__(self,painter_size=(310,400),rectangle=(50,30,270,360),save='cycle_path'):
        self.root = tk.Tk()
        self.F1 = tk.Frame(self.root)
        self.F2 = tk.Frame(self.root)
        tk.Label(self.root, text="请画出敌机的轨迹（矩形框为屏幕边界）", font=('songti',14)).pack()
        self.F1.pack()
        self.F2.pack()
        tk.Button(self.F1, text="插值",font=('songti',14), command=self.get_path).pack(side='left')
        tk.Button(self.F1, text="清空",font=("songti",14),command=self.clear_painter).pack(side="left")
        tk.Button(self.F1, text="保存",font=("songti",14),command=self.save).pack(side='left')
        self.scale = tk.Scale(self.F1,cursor='circle',length=150,orient=tk.HORIZONTAL,showvalue=1,from_=3,to=100,resolution=1)
        self.scale.pack(side='right')
        self.scale.set(30)
        self.Painter = tk.Canvas(self.F2, width=painter_size[0], height=painter_size[1], borderwidth=2,background="#BBBBBB")
        self.Painter.bind("<Button-1>", self.get_msg)
        self.Painter.bind("<B1-Motion>",  self.paint)
        self.Painter.pack()
        self.Painter.create_rectangle(*rectangle)
        self.painter_rect = rectangle
        self.painter_size = (rectangle[2]-rectangle[0],rectangle[3]-rectangle[1])
        self.mx = 0
        self.my = 0
        self.m_path = []
        self.xlist = None
        self.ylist = None
        self.save_name = save
        
    def get_msg(self,event):
        self.mx = event.x
        self.my = event.y
        
    def paint(self,event):
        x,y = event.x, event.y
        self.Painter.create_line(self.mx, self.my, x, y, fill="black",smooth='True',width=3)
        self.mx, self.my = x, y
        self.m_path.append((x,y))
        
    def clear_painter(self):
        self.Painter.delete("all")
        self.m_path.clear()
        self.Painter.create_rectangle(*self.painter_rect)
        
    def get_path(self):
        xy_path = np.array(self.m_path)  # (N,2)
        i_list = np.arange(0,len(self.m_path))
        ii_list= np.linspace(0,i_list.size,num=self.scale.get())
        x_list = xy_path[:,0]
        y_list = xy_path[:,1]
        xeval = splrep(i_list,x_list,k=3)
        yeval = splrep(i_list,y_list,k=3)
        xx_list = splev(ii_list,xeval)
        yy_list = splev(ii_list,yeval)
        self.Painter.delete('all')
        self.Painter.create_rectangle(*self.painter_rect)
        for x,y in zip(xx_list,yy_list):
            self.Painter.create_oval(x-2,y-2,x+2,y+2,fill="#476042")
        x0,y0 = xx_list[0],yy_list[0]
        for x1,y1 in zip(xx_list[1:],yy_list[1:]):
            self.Painter.create_line(x0,y0,x1,y1)
            x0,y0 = x1,y1
        self.xlist = (xx_list-self.painter_rect[0])/self.painter_size[0]
        self.ylist = (yy_list-self.painter_rect[1])/self.painter_size[1]
    def save(self):
        path = [(round(x,2),round(y,2)) for x,y in zip(self.xlist,self.ylist)]
        with open(os.path.join(self.save_name,"path.json"),'w')as f:
            json.dump(path,f)
        
  
    
    
if __name__ == '__main__':
    path_planeer = Path_Planner()
    path_planeer.root.mainloop()
    
