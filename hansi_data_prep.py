import os
import numpy as np
import matplotlib.pyplot as plt

from scipy.interpolate import griddata


def grid_data(filename, results_dir):
    data = np.loadtxt(filename)

    time = data[0,1:]
    wave = data[1:,0]+500*0.8
    dat = data[1:,1:]
    si_t = np.size(time)
    si_w = np.size(wave)
    size = 1000j
    siz=1000

    maxt = np.max(time)
    mint = np.min(time)
    maxw = np.max(wave)
    minw = np.min(wave)

    print(mint, maxt, minw, maxw)

    grid_t,grid_w = np.mgrid[mint:maxt:size,minw:maxw:size]

    dat=dat.T
    values=dat.flatten()
    po = np.indices((si_t,si_w))
    poi0 = po[0].flatten()
    poi1 = po[1].flatten()
    point0 = np.zeros(np.size(poi0))
    point1 = np.zeros(np.size(poi1))
    for i in range(np.size(poi0)):
        point0[i]=time[poi0[i]]
        point1[i]=wave[poi1[i]]
    points = np.array((point0,point1)).T

    dat_grid = griddata(points,values, (grid_t, grid_w), method='nearest')

    # fig1, a1 = plt.subplots(1,1)
    # a1.imshow(dat_grid, vmin=0.0,vmax=5000, extent=[mint,maxt,minw,maxw])
    # fig2, a2 = plt.subplots(1,1)
    # a2.imshow(dat, vmin=0.0,vmax=5000)
    # plt.show()

    new_t = grid_t[:,0]
    new_w = grid_w[0,:]

    write_dat = np.zeros((siz+1,siz+1))

    write_dat[1:,1:] = dat_grid
    write_dat[0,1:] = new_t
    write_dat[1:,0] = new_w

    np.savetxt(results_dir+'/gridded_hansi_data.txt', write_dat.T, fmt='%.3f')

if __name__ == "__main__":
    dirName = os.getcwd()
    print(dirName)
    filename = dirName+'/DataFiles/mBDF-TPNlookupc_avg_MV.dat'

    grid_data(filename, dirName+"/DataFiles/")
