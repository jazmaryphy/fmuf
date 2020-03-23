import numpy as np
from matplotlib import pyplot as plt 

def plot_bamuba(t):
    #from numpy import *
      
    muAmp=0.0932;
    muGau=7.18;
    muPhi=0;  
    muDeLo=0;  
    muDeGa=0.398;

    MU_TABLE=0.01355;   


	## f= muprecessio
    f_mu=muAmp*np.cos(2*np.pi*(MU_TABLE*muGau*t+muPhi/360))* \
	      np.exp(-t*muDeLo)*np.exp(-((t*muDeGa)**2)/2);

	    
    baAmp_01=0.1215; 
    baDeLo_01=0.0098;
    baDeGa_01=0;

    baAmp_02=0.0044;  
    baDeLo_02=0;  
    baDeGa_02=0.00008; 

	#f_ba1 = mubackground with first parameter sets
    f_ba1=baAmp_01*np.exp(-t*baDeLo_01)*np.exp(-((t*baDeGa_01)**2)/2.);


	#f_ba2 = mubackground with second parameter sets
    f_ba2=baAmp_02*np.exp(-t*baDeLo_02)*np.exp(-((t*baDeGa_02)**2)/2.);

    bamuba = f_mu + f_ba1 + f_ba2
    y=bamuba
    return y

#interval = 18 ;
#t = np.linspace(0,interval, 1000);
#y=plot_bamuba(t)
#plt.plot(t,y)
#plt.grid()

#plt.show()
