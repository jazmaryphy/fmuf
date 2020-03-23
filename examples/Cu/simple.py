import numpy as np
e=1.6021766E-19 # Coulomb = ampere ⋅ second
h=6.6260693e-34 # Js
hbar=h/(2*np.pi) # Js
Q=(-0.211) * (10**-28) # m^-2
omega_q=3.2e-6   # s^-1

eq=4*hbar*omega_q/(e*Q)

print(eq)
