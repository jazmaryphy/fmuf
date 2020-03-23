import numpy as np

e=1.6021766E-19 # Coulomb = ampere ⋅ second
h=6.6260693e-34 # Js
hbar=h/(2*np.pi) # Js

q1_p=1.1038146751377e+21     # V/m^2
q2_p=1.1378898981548641e+21  # V/m^2

l=3.5    # spin for Vanadium
factor=1.  # can be a steinheimer factor
Q=-0.05e-28   # Quadrupole moment m^-2

electric_quadrupole_interaction=2.924e6  # Hz obtain from buttet 1973
electric_quadrupole_interaction_a=2.924e6  # Hz obtain from buttet 1973
electric_quadrupole_interaction_b=2.924e6  # Hz obtain from buttet 1973

omega_mu1=(3*e*factor*q1_p*Q)/(hbar*4*l*(2*l-1))
omega_mu2=(3*e*factor*q2_p*Q)/(hbar*4*l*(2*l-1))

q_crystal= h * electric_quadrupole_interaction / ( e * Q)   # V/m2

print('electric field gradient of point charge for site 1 and 2')
print('site 1 = ', q1_p, ':', 'site 2 = ',q2_p)

print('crystal electric field gradient of V3Si used from Buttet 1973 paper')
print('crystal efg = ',(q_crystal))

print('ratio = ',abs(q_crystal)/q2_p)
