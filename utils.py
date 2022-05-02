
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