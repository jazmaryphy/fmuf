import numpy as np

e=1.6021766E-19 # Coulomb = ampere ⋅ second
h=6.6260693e-34 # Js
hbar=h/(2*np.pi) # Js

q1_p=0     # V/m^2
q2_p=0  # V/m^2

l_Cu=1.5    # spin for Copper
l_La=3.5
factor=1.  # can be a steinheimer factor
Q_Cu=-0.211e-28  # m^-2    # Quadrupole moment m^-2
Q_La=0.22e-28  # m^-2 

electric_quadrupole_interaction_Cu=OmegaQI_Cu=2*np.pi*34.0e6#213.6e6 #2*np.pi*34.0e0   #  213.6e6 or 194.8e6 # Hz
electric_quadrupole_interaction_La=40.2e6 #2*np.pi*6.4e0   #   40.2e6

Q=0
l=1
factor=0
omega_Q_Cu= (3*e*factor*q1_p*Q)/(hbar*4*l*(2*l-1))
omega_Q_La=(3*e*factor*q2_p*Q)/(hbar*4*l*(2*l-1))

q_Cu= (hbar*4*l_Cu*(2*l_Cu-1))/(3*e*Q_Cu) * electric_quadrupole_interaction_Cu * 0.5   # V/m^2
q_La= (hbar*4*l_La*(2*l_La-1))/(3*e*Q_La) * electric_quadrupole_interaction_La * 0.5  # V/m^2

print('electric field gradient of of the paper')
print('for Cu = ',abs(q_Cu))
print('for La = ',abs(q_La))

