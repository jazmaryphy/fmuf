#!/usr/bin/env python
# coding: utf-8

# In[1]:


import sys
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import loadmat


# In[2]:


# ## the bamuba function
sys.path.insert(0, '/home/misah/PARMA/WORK/undi-master/examples/v3ge/')
import bamuba as b
from bamuba import plot_bamuba
tlist0 = np.linspace(0, 18, 1000)
yGe=plot_bamuba(tlist0)


# In[3]:


# WITH EXPONENTIAL FUNCS. ADDED
pre='data2'
filename = pre+'.dat'
tlist = np.linspace(0, 18e-6, 200)    # for His is 100
fi1='FirstSite1WithEFG-HIS-Final-Orien-'
fi2='SecondSite11WithEFG-HIS-Final-Orien-'
fi2='FirstSiteNoPowderAverageMYDay3-Orien-'
fi2='SecondSiteNoPowderAverageMYDay3-Orien-'
fi1='FirstSiteNoScaleMYDay3-Orien-'
fi2='SecondSiteNoScaleMYDay3-Orien-'
n1=100                                  # for His is 100
n2=100                                   # for His is 100
file1=np.load(fi1+str(n1)+'.npz')
file2=np.load(fi2+str(n2)+'.npz')

A1=file1['arr_0']
A2=file2['arr_0']



fmat=loadmat('expt.mat')
tmat=fmat['t']
ymat=fmat['y']
t0=tmat[0]
y0=ymat[0]

# for i in range(n):
#     print(A[i])
a0=0.2191# initial asymm for V3Ge

xSi,ySi=np.loadtxt(filename,unpack=True)

y1=a0*( 0.82*A1.sum(axis=0)/float(n1) +         0.18*np.exp(-tlist*100000) )
# y1=1 * ( 0.82*A0.sum(axis=0)/float(n0)  +  \
#         0.18*np.exp(-tlist*0.1)*np.exp(-((tlist*0.1)**2)/2) +  \
#         0.0*np.exp(-tlist*0)*np.exp(-((tlist*0.1)**2)/2) +  \
#         0.0*np.exp(-0.01*tlist**2.5) ) 
        
y2=a0*( 0.82*A2.sum(axis=0)/float(n2) +         0.18*np.exp(-tlist*100000) )
# y2=1 * ( 0.82*A.sum(axis=0)/float(n)  +  \
#         0.18*np.exp(-tlist*0.1)*np.exp(-((tlist*0.)**2)/2) +  \
#         0.0*np.exp(-tlist*0)*np.exp(-((tlist*0.00008)**2)/2) +  \
#         0.0*np.exp(-0.01*tlist**2.5) ) 

fig, axes = plt.subplots(1,1)
#axes.axhline(y=1/3., color='k', ls='--', label='')
axes.plot(tlist,y1,'r--',label='average S1 4V')#+str(n))
axes.plot(tlist,y2,'b--',label='average S2 3V')#+str(n))
axes.plot(xSi*1e-6,ySi, 'k',label='V3Si data ')
axes.plot(tlist0*1e-6,yGe,'g', label='V3Ge data')
# axes.plot(tlist,A[0],'k--',label='1 ')
# axes.plot(tlist,A[-1],'b--',label=str(n))
# for idx, Bmod in enumerate(range(n)):
#     color = list(np.random.choice(range(256), size=3)/256)
#     axes.plot(tlist, A[idx], label='{}d'.format(Bmod), linestyle='-', color=color)
#axes.set_ylim((-0.1,1.1))
axes.set_xlim((0,18e-6))
ticks = np.round(axes.get_xticks()*10.**6)
axes.set_xticklabels(ticks)
axes.set_xlabel(r'$t (\mu s)$', fontsize=20)
axes.set_ylabel(r'$\left<P_z\right>$', fontsize=20);
axes.set_ylabel(r'Asymmetry', fontsize=20);
plt.legend()
plt.show()


# In[7]:


# NO EXPONENTIAL FUNCS. ADDED
pre='data2'
filename = pre+'.dat'
tlist = np.linspace(0, 18e-6, 200)    # for His is 100
fi1='FirstSite1WithEFG-HIS-Final-Orien-'
fi2='SecondSite11WithEFG-HIS-Final-Orien-'
fi2='FirstSiteNoPowderAverageMYDay3-Orien-'
fi2='SecondSiteNoPowderAverageMYDay3-Orien-'
fi1='FirstSiteNoScaleMYDay3-Orien-'
fi2='SecondSiteNoScaleMYDay3-Orien-'
n1=100                                  # for His is 100
n2=100                                   # for His is 100
file1=np.load(fi1+str(n1)+'.npz')
file2=np.load(fi2+str(n2)+'.npz')

A1=file1['arr_0']
A2=file2['arr_0']



fmat=loadmat('expt.mat')
tmat=fmat['t']
ymat=fmat['y']
t0=tmat[0]
y0=ymat[0]

# for i in range(n):
#     print(A[i])
a0=0.2191# initial asymm for V3Ge

xSi,ySi=np.loadtxt(filename,unpack=True)

y1=a0*A1.sum(axis=0)/float(n1)
        
y2=a0*A2.sum(axis=0)/float(n2) 
fig, axes = plt.subplots(1,1)
#axes.axhline(y=1/3., color='k', ls='--', label='')
axes.plot(tlist,y1,'r--',label='average S1 4V')#+str(n))
axes.plot(tlist,y2,'b--',label='average S2 3V')#+str(n))
axes.plot(xSi*1e-6,ySi, 'k',label='V3Si data ')
axes.plot(tlist0*1e-6,yGe,'g', label='V3Ge data')
# axes.plot(tlist,A[0],'k--',label='1 ')
# axes.plot(tlist,A[-1],'b--',label=str(n))
# for idx, Bmod in enumerate(range(n)):
#     color = list(np.random.choice(range(256), size=3)/256)
#     axes.plot(tlist, A[idx], label='{}d'.format(Bmod), linestyle='-', color=color)
#axes.set_ylim((-0.1,1.1))
axes.set_xlim((0,18e-6))
ticks = np.round(axes.get_xticks()*10.**6)
axes.set_xticklabels(ticks)
axes.set_xlabel(r'$t (\mu s)$', fontsize=20)
axes.set_ylabel(r'$\left<P_z\right>$', fontsize=20);
axes.set_ylabel(r'Asymmetry', fontsize=20);
plt.legend()
plt.show()


# In[6]:


# ## the bamuba function
# PLOT without Adding any Function and No Weighting with Initial Asymmetry
sys.path.insert(0, '/home/misah/PARMA/WORK/undi-master/examples/v3ge/')
import bamuba as b
from bamuba import plot_bamuba
tlist0 = np.linspace(0, 18, 1000)
yGe=plot_bamuba(tlist0)
a0=0.2191
fi1='FirstSiteNoScaleMYDay3-Orien-'
fi2='SecondSiteNoScaleMYDay3-Orien-'
n1=100                                  # for His is 100
n2=100                                   # for His is 100
file1=np.load(fi1+str(n1)+'.npz')
file2=np.load(fi2+str(n2)+'.npz')

A1=file1['arr_0']
A2=file2['arr_0']

y1=A1.sum(axis=0)/float(n1)
y2=A2.sum(axis=0)/float(n2)

fig, axes = plt.subplots(1,1)
axes.plot(tlist0*1e-6,yGe/a0, 'g', label='V3Ge data', linestyle='-')
axes.plot(xSi*1e-6,ySi/a0, 'k',label='V3Si data ', linestyle='-')
axes.plot(tlist,y1,'r--',label='average S1 4V')#+str(n))
axes.plot(tlist,y2,'b--',label='average S2 3V')#+str(n))
axes.set_xlim((0.,max(tlist)))
ticks = np.round(axes.get_xticks()*10.**6)
axes.set_xticklabels(ticks)
axes.set_xlabel(r'$t (\mu s)$', fontsize=20)
axes.set_ylabel(r'$\left<P_z\right>$', fontsize=20);
axes.set_ylabel(r'Asymmetry', fontsize=20);
#plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
plt.legend()
plt.show()


# In[ ]:





# In[ ]:




