#!/usr/bin/env python
# coding: utf-8
import logging
from qutip import *
import numpy as np
from numpy import pi
from mendeleev import element
from copy import deepcopy
import random as rd

qadd = lambda x : (x[0] + x[1] + x[2]) * 0.33333333333
qdot = lambda x,y : x[0]*y[0] + x[1]*y[1] + x[2]*y[2]
qdot0 = lambda x,y : (x[0]*y[0] + x[1]*y[1] + x[2]*y[2]) * 0.33333333333
qMdotV = lambda x,y : (x[0,0]*y[0] + x[0,1]*y[1] + x[0,2]*y[2],
                        x[1,0]*y[0] + x[1,1]*y[1] + x[1,2]*y[2],
                        x[2,0]*y[0] + x[2,1]*y[1] + x[2,2]*y[2])

# Constants
angtom=1.0e-10 # m
h=6.6260693e-34 # Js
hbar=h/(2*np.pi) # Js
mu_0=(4e-7)*np.pi # Tm A-1
elementary_charge=1.6021766E-19 # Coulomb = ampere ⋅ second

# Conversions
J_to_neV = 6.241508e27 # 1 J = 6.241508e27 neV
planck2pi_neVs = 6.582117e-7 #planck2pi [neV*s]
one_over_plank2pi_neVs = 1. / planck2pi_neVs

def rand_rotation_matrix(deflection=1.0, randnums=None):
    """
    Creates a random rotation matrix.

    deflection: the magnitude of the rotation. For 0, no rotation; for 1, completely random
    rotation. Small deflection => small perturbation.
    randnums: 3 random numbers in the range [0, 1]. If `None`, they will be auto-generated.
    """
    # from http://www.realtimerendering.com/resources/GraphicsGems/gemsiii/rand_rotation.c

    if randnums is None:
        randnums = np.random.uniform(size=(3,))

    theta, phi, z = randnums

    theta = theta * 2.0*deflection*np.pi  # Rotation about the pole (Z).
    phi = phi * 2.0*np.pi  # For direction of pole deflection.
    z = z * 2.0 * deflection  # For magnitude of pole deflection.

    # Compute a vector V used for distributing points over the sphere
    # via the reflection I - V Transpose(V).  This formulation of V
    # will guarantee that if x[1] and x[2] are uniformly distributed,
    # the reflected points will be uniform on the sphere.  Note that V
    # has length sqrt(2) to eliminate the 2 in the Householder matrix.

    r = np.sqrt(z)
    Vx, Vy, Vz = V = (
        np.sin(phi) * r,
        np.cos(phi) * r,
        np.sqrt(2.0 - z)
        )

    st = np.sin(theta)
    ct = np.cos(theta)

    R = np.array(((ct, st, 0), (-st, ct, 0), (0, 0, 1)))

    # Construct the rotation matrix  ( V Transpose(V) - I ) R.

    M = (np.outer(V, V) - np.eye(3)).dot(R)
    return M


class MuonNuclearInteraction(object):

    # Collection of gammas, never really used apart from muon's one.
    gammas = {'mu': 2*np.pi*135.5e6,
              'F' : 2*np.pi*40.053e6,
              'H' : 2*np.pi*42.577e6,
              'V' : 2*np.pi*11.212944e6} # (sT)^-1


    @staticmethod
    def splitIsotope(s):
        return (''.join(filter(str.isdigit, s)) or None,
                ''.join(filter(str.isalpha, s)) or None)

    @staticmethod
    def dipolar_interaction(a_i, a_j):
        gamma_i, p_i, s_i = a_i['Gamma'], a_i['Position'], a_i['Spin']
        gamma_j, p_j, s_j = a_j['Gamma'], a_j['Position'], a_j['Spin']

        d = p_j-p_i
        n_of_d = np.linalg.norm(d)
        u = d/n_of_d

        # dipolar interaction
        Bd=(mu_0*gamma_i*gamma_j*(hbar**2))/(4*np.pi*(n_of_d**3))
        Bd*=6.241508e27 # to neV

        I = a_i['Operators']
        J = a_j['Operators']

        return -Bd * (3*qdot(I,u)*qdot(J,u) - qdot(I,J))

    @staticmethod
    def quadrupolar_interaction(a_i):
        l = a_i['Spin']

        if (l < 0.5001):
            raise RuntimeError("Invalid spin")

        EFG = a_i['EFGTensor']
        Q = a_i['ElectricQuadrupoleMoment']
        I  = a_i['Operators']
        #eta = a_i['eta']
        
        #Q_tensor = np.diag([eta-1., -eta-1. ,2])
        #print('Q_tensor',Q_tensor)
        

        # PAS
        ee, ev = np.linalg.eig(EFG)
        Vxx,Vyy,Vzz = np.sort(np.abs(ee))

        
        # declare just in case EFG is zero
        eta = 0
        if Vzz >= 0.00001:
            eta = (Vxx-Vyy)/Vzz

        E_q = J_to_neV * ( elementary_charge * Q * Vzz / (4*l *(2*l -1)) )

        omega_q = E_q * one_over_plank2pi_neVs

        cost = J_to_neV * (elementary_charge * Q * Vzz /(4*l *(2*l -1)))

        return( \
                cost * (qdot(I, qMdotV(EFG,I))) , \
                (omega_q,  Vzz) \
                )

    @staticmethod
    def quadrupolar_interaction_0(a_i, mu):

        def Vzz_for_unit_charge_at_distance(p_mu, p_N):
            x=p_N-p_mu
            r = np.linalg.norm(x)
            factor=1.
            epsilon0 = 8.8541878E-12 # ampere^2 ⋅ kilogram^−1 ⋅ meter^−3 ⋅ second^4
            elementary_charge=1.6021766E-19 # Coulomb = ampere ⋅ second
            Vzz = factor*(2./(4 * np.pi * epsilon0)) * (elementary_charge / (r**3))
            return Vzz    
     
        def get_V(p_mu, p_N, Vzz):
            x=p_N-p_mu
            n = np.linalg.norm(x)
            x /= n; r = 1. # keeping formula below for clarity
            return -Vzz * ( (3.*np.outer(x,x)-np.eye(3)*(r**2))/r**5 )
            
        l = a_i['Spin']

        if (l < 0.5001):
            raise RuntimeError("Invalid spin")

        #EFG = a_i['EFGTensor']
        Q = a_i['ElectricQuadrupoleMoment']
        I  = a_i['Operators']
        OmegaQI = a_i['OmegaQI']

        n = a_i['Position'] - mu['Position']
        n /= np.linalg.norm(n)

        
        efg=get_V(mu['Position'], a_i['Position'], 2.4185382102322554e+21)
        
        # PAS
        ee, ev = np.linalg.eig(efg)
        Vxx,Vyy,Vzz = np.sort(np.abs(ee))
        
        #Q_tensor = np.diag([eta-1., -eta-1. ,2])
        

        E_q = J_to_neV * ( elementary_charge * Q * Vzz / (4*l *(2*l -1)) )

        omega_q = E_q * one_over_plank2pi_neVs

        # Quadrupole
        cost0 = (J_to_neV * 3 * hbar * ( OmegaQI * h ) ) / ((4*l *(2*l -1) * hbar))   # for V3Ge
        
        cost = J_to_neV * (elementary_charge * Q * Vzz /(4*l *(2*l -1)))

        return( \
                cost * (qdot(I, qMdotV(efg,I))) , \
                (omega_q,  Vzz) \
                )
                
    
    @staticmethod
    def crystal_electric_field_gradient(a_i):
        l = a_i['Spin']

        if (l < 0.5001):
            raise RuntimeError("Invalid spin")

        I  = a_i['Operators']
        eta = a_i['eta']
        OmegaQI = a_i['OmegaQI']
        
        Iplus  = a_i['Plus']
        Iminus = a_i['Minus']
        Iz     = a_i['Z']
        
        Ip = qadd(Iplus)
        Im = qadd(Iminus)
        

        # un comment below for the case of LaCuSrO4
        
        cost0 = J_to_neV * hbar * OmegaQI * 0.5   # for LaCrSrO
        
        # un comment below for the case of LaCuSrO4
        
       # cost0 = (J_to_neV * 3 * hbar * ( OmegaQI * h ) ) / ((4*l *(2*l -1) * hbar))   # for V3Ge
         

        return cost0 * (qdot0(Iz,Iz)  + 0.166666667*eta*(Ip + Im) - 0.33333333333*(l * (l+1)) ) 


    @staticmethod
    def muon_induced_efg(a_i, mu):
    
        def Vzz_for_unit_charge_at_distance(p_mu, p_N):   # EFG point charge
            x=p_N-p_mu
            r = np.linalg.norm(x)
            factor=1.
            epsilon0 = 8.8541878E-12 # ampere^2 ⋅ kilogram^−1 ⋅ meter^−3 ⋅ second^4
            elementary_charge=1.6021766E-19 # Coulomb = ampere ⋅ second
            Vzz = factor*(2./(4 * np.pi * epsilon0)) * (elementary_charge / (r**3))
            return Vzz    
     
        def get_V(p_mu, p_N, Vzz):    # EFGTensor	
            x=p_N-p_mu
            n = np.linalg.norm(x)
            x /= n; r = 1. # keeping formula below for clarity
            return -Vzz * ( (3.*np.outer(x,x)-np.eye(3)*(r**2))/r**5 )

    
        l = a_i['Spin']

        if (l < 0.5001):
            raise RuntimeError("Invalid spin")

        I = a_i['Operators']
        Q = a_i['ElectricQuadrupoleMoment']

        n = a_i['Position'] - mu['Position']
        n /= np.linalg.norm(n)

        
        efg=get_V(mu['Position'], a_i['Position'], Vzz_for_unit_charge_at_distance(mu['Position'], a_i['Position']))
        ee, ev = np.linalg.eig(efg)
        Vxx,Vyy,Vzz = np.sort(np.abs(ee))

        
      #  scale = 2.4301174#3e-1         #  factor 2.4301174  obtain for Copper as ratio of efg of point charge to calculated 
      #  factor=1./scale                # to make same as theoretical value
        
        scale=rd.uniform(1,10)          # if I want to randomly scale Vzz 
        factor=1.
                     
        omega=(3*elementary_charge*factor*Vzz*Q)/(hbar*4*l*(2*l-1))
        
        E_q = planck2pi_neVs * omega
        
        return E_q * ( qdot(n, I) * qdot(n, I) - 0.33333333333*(l * (l+1)))

    @staticmethod
    def custom_term(a_i):
        I = a_i['Operators']
        Ix, Iy, Iz = I
        p = a_i['Position']
        L = a_i['Spin']
        expression = a['CustomHamiltonianTerm']
        return eval(expression)

    @staticmethod
    def external_field(atom, H):

        return - planck2pi_neVs * atom['Gamma'] * qdot(atom['Operators'], H)

    @staticmethod
    def create_hilbert_space(atoms):
        n_nuclei = len(atoms)

        for i in range(n_nuclei):
            Lx = tensor(* [spin_Jx(a_j['Spin']) if j == i else qeye(int(2*a_j['Spin']+1)) for j,a_j in enumerate(atoms)] )
            Ly = tensor(* [spin_Jy(a_j['Spin']) if j == i else qeye(int(2*a_j['Spin']+1)) for j,a_j in enumerate(atoms)] )
            Lz = tensor(* [spin_Jz(a_j['Spin']) if j == i else qeye(int(2*a_j['Spin']+1)) for j,a_j in enumerate(atoms)] )
            atoms[i]['Operators'] = (Lx, Ly, Lz)
            
            L_plus = tensor(* [spin_Jp(a_j['Spin']) if j == i else qeye(int(2*a_j['Spin']+1)) for j,a_j in enumerate(atoms)] )
            L_minu = tensor(* [spin_Jm(a_j['Spin']) if j == i else qeye(int(2*a_j['Spin']+1)) for j,a_j in enumerate(atoms)] )
            L_z =    tensor(* [spin_Jz(a_j['Spin']) if j == i else qeye(int(2*a_j['Spin']+1)) for j,a_j in enumerate(atoms)] )
            atoms[i]['Plus'] =   (L_plus , L_plus , L_plus )   # bizarre way but it works
            atoms[i]['Minus'] = (L_minu , L_minu , L_minu )    # bizarre way but it works
            atoms[i]['Z'] = (L_z , L_z , L_z )                 # bizarre way but it works
           

            # add also observables in the case of muon
            if atoms[i]['Label'] == 'mu':
                Ox = tensor(* [sigmax() if j == i else qeye(int(2*a_j['Spin']+1)) for j,a_j in enumerate(atoms)] )
                Oy = tensor(* [sigmay() if j == i else qeye(int(2*a_j['Spin']+1)) for j,a_j in enumerate(atoms)] )
                Oz = tensor(* [sigmaz() if j == i else qeye(int(2*a_j['Spin']+1)) for j,a_j in enumerate(atoms)] )
                atoms[i]['Observables'] = (Ox, Oy, Oz)

        return Oz.dims

    def __init__(self, atoms, external_field = [0.,0.,0.], logger = None, log_level = ''):

        # Make own copy to avoid overwriting of internal elements
        atoms = deepcopy(atoms)

        self._ext_field = np.array(external_field)

        self.logger = logger or logging.getLogger(__name__)

        if log_level:
            level_config = {'debug': logging.DEBUG, 'info': logging.INFO}
            try:
                self.logger.setLevel(level_config[log_level.lower()])
            except:
                self.logger.warning("Invalid logging level")

        self.Hdim = 1

        for i, atom in enumerate(atoms):
            spin  = atom.get('Spin', None)
            label = atom.get('Label', None)
            pos   = atom.get('Position', None)

            # validation
            if pos is None:
                raise ValueError('Position needed for atom {}'.format(i))

            # assign values
            if label == 'mu':
                if spin:
                    if spin != 0.5:
                        self.logger.warning("Warning, muon spin already set differs from 0.5!!")
                else:
                    atoms[i]['Spin'] = 0.5

                atoms[i]['Gamma'] = self.gammas[label]
            else:
                A, Symbol = self.splitIsotope(label)
                e = element(Symbol)
                if A:
                    A = int(A)
                    for isotope in e.isotopes:
                        if isotope.mass_number == A:
                            break
                    else:
                        raise ValueError('Isotope {} for atom {} not found.'.format(A, Symbol))
                else:

                    max_ab = -1.
                    l = -1
                    for is_n, isotope in enumerate(e.isotopes):
                        if isotope.abundance is None:
                            continue
                        if isotope.abundance > max_ab:
                            l = is_n
                            max_ab = isotope.abundance
                    # Select isotope with highest abundance
                    isotope = e.isotopes[l]

                    level = logging.WARNING if max_ab < 0.99 else logging.INFO
                    self.logger.log(level, 'Using most abundand isotope for {}, i.e. {}{}, {} abundance'.format(label, isotope.mass_number, e.symbol, max_ab))

                # check if overriding spin
                if spin:
                    if spin != isotope.spin:
                        self.logger.warning("Warning, overriding spin for {}".format(label))
                else:
                    atoms[i]['Spin'] = isotope.spin

                atoms[i]['Gamma'] = isotope.g_factor * 7.622593285e6 * 2. * pi  #  \mu_N /h, is 7.622593285(47) MHz/T that in turn is equal to  γ_n / (2 π g_n)

            # increase Hilbert space dimension
            self.Hdim *= (2*atoms[i]['Spin']+1)

        # Check Hilber space dimension makes sense
        if np.abs(self.Hdim - np.rint(self.Hdim)) > 1e-10:
            raise RuntimeError("Something is very bad in the setup")
        else:
            self.Hdim = int(self.Hdim)

        self.logger.info("Hilbert space is {} dimensional".format(self.Hdim))
        self.atoms = atoms

    def set_extfield(self, external_field):
        self._ext_field = np.array(external_field)

    def translate_rotate_sample_vec(self, bring_this_to_z):
        natoms = len(self.atoms)

        # Bring muon to origin
        for a in self.atoms:
            if a['Label'] == 'mu':
                mup = a['Position']
        for i in range(natoms):
            self.atoms[i]['Position'] = self.atoms[i]['Position'] - mup

        def rotation_matrix_from_vectors(vec1, vec2):
            """ Find the rotation matrix that aligns vec1 to vec2
            :param vec1: A 3d "source" vector
            :param vec2: A 3d "destination" vector
            :return mat: A transform matrix (3x3) which when applied to vec1, aligns it with vec2.

            https://stackoverflow.com/a/59204638
            """
            a, b = (vec1 / np.linalg.norm(vec1)).reshape(3), (vec2 / np.linalg.norm(vec2)).reshape(3)
            v = np.cross(a, b)
            c = np.dot(a, b)
            s = np.linalg.norm(v)
            kmat = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
            rotation_matrix = np.eye(3) + kmat + kmat.dot(kmat) * ((1 - c) / (s ** 2))
            return rotation_matrix

        if not np.allclose(bring_this_to_z, np.array([0.,0.,1.])):
            rmat = rotation_matrix_from_vectors(bring_this_to_z, np.array([0.,0.,1.]))
        else:
            rmat = np.eye(3)
        irmat = np.linalg.inv(rmat)

        for i in range(natoms):
            self.atoms[i]['Position'] = rmat.dot(self.atoms[i]['Position'])
            if 'EFGTensor' in self.atoms[i].keys():
                self.atoms[i]['EFGTensor'] = np.dot(rmat, np.dot(self.atoms[i]['EFGTensor'], irmat))

    def create_H(self, cutoff = 10.0E-10):
        """
        cutoff is in Angstrom
        """

        atoms = self.atoms

        # Generate Hilber space and operators
        dims = self.create_hilbert_space(atoms)

        # Empty Hamiltonian
        H = Qobj(dims=dims)

        # Find the muon, used later...
        mu = None
        for a in atoms:
            if a['Label'] == 'mu':
                mu = a

        # Dipolar interaction
        for i, a_i in enumerate(atoms):
            for j, a_j in enumerate(atoms):

                if j <= i:
                    continue

                p_i = a_i['Position']
                p_j = a_j['Position']
                d = p_j-p_i
                n_of_d = np.linalg.norm(d)

                # cutoff for the interaction
                if n_of_d > cutoff:
                    self.logger.info("Skipped interaction between {} and {} with distance {}".format( a_i['Label'], a_j['Label'], n_of_d ) )
                    continue

                self.logger.info("Adding interaction between {} and {} with distance {}".format( a_i['Label'], a_j['Label'], n_of_d ) )


                H += self.dipolar_interaction(a_i, a_j)

                self.logger.info('Dipolar contribution between {}<->{}, r={}'.format(i,j, n_of_d))

        # Quadrupolar interaction
        for i, a_i in enumerate(atoms):

            if (a_i['Spin'] > 0.5):
                EFG = a_i.get('EFGTensor', None)
                Q = a_i.get('ElectricQuadrupoleMoment', None)
                OmegaQI = a_i.get('OmegaQI', None)
                OmegaQmu = a_i.get('OmegaQmu', None)
                eta = a_i.get('eta',None)

                if (not EFG is None) and (not Q is None):
                    Q, strengh = self.quadrupolar_interaction(a_i)
                    Q*=0
                    self.logger.info('Quadrupolar coupling for atom {} {} is {}'.format(i, a_i['Label'], strengh))
                    H += Q
                 
                # trying custom PAS crsytal efg    
                #if (not OmegaQI is None) and (not eta is None):
                if 'eta' in a_i.keys():
                    H += self.crystal_electric_field_gradient(a_i)   

                # Muon induced quadrupolar interaction
                if 'OmegaQmu' in a_i.keys():
                    H += self.muon_induced_efg(a_i, mu) 
                    
                # Another custom CRYSTAL quadrupolar interaction
                if 'OmegaQI' in a_i.keys():
                    Q0, strn = self.quadrupolar_interaction_0(a_i, mu)
                    Q0*=0   # kill this
                    H += Q0


        # External field
        if np.linalg.norm(self._ext_field) > 0.000001:
            for a_i in atoms:
                H += self.external_field(a_i, self._ext_field)

        self.H = H

    def time_evolve_qutip(self, dt, steps):

        atoms = self.atoms
        for atom in atoms:
            if atom['Label'] == 'mu':
                Ox, Oy, Oz = atom['Observables']

        rhox = (1./self.Hdim) * Ox
        rhoy = (1./self.Hdim) * Oy
        rhoz = (1./self.Hdim) * Oz

        dU = (-1j * self.H * one_over_plank2pi_neVs * dt).expm()

        r = np.zeros(steps, dtype=np.complex)
        for i in range(steps):
            U = dU ** i
            r[i] += ( rhox * U.dag() * Ox * U ).tr()
            r[i] += ( rhoy * U.dag() * Oy * U ).tr()
            r[i] += ( rhoz * U.dag() * Oz * U ).tr()

        return np.real_if_close(r/3.)

    def time_evolve_trotter(self, dt, steps, k=3.):
        """
        This subroutine does Trotter expnsion of the matrix
        """
        from time import time
        atoms = self.atoms
        for atom in atoms:
            if atom['Label'] == 'mu':
                Ox, Oy, Oz = atom['Observables']

        rhox = (1./self.Hdim) * Ox
        rhoy = (1./self.Hdim) * Oy
        rhoz = (1./self.Hdim) * Oz

        # compose U operator
        dU = qeye(Oz.dims[0])
        # this is broken!!!
        for h in self.Hs:
            dU *= (-1j * h * one_over_plank2pi_neVs * dt / k).expm()
        dU = dU**k

        r = np.zeros(steps, dtype=np.complex)
        for i in range(steps):
            U = dU**i
            r[i] += ( rhox * U.dag() * Ox * U).tr()
            r[i] += ( rhoy * U.dag() * Oy * U).tr()
            r[i] += ( rhoz * U.dag() * Oz * U).tr()

        return np.real_if_close(r/3.)
        
    def random_three_vector(self,r=1):
        """
        X=r*sin(theta)*cos(phi)
        Y=r*sin(theta)*sin(phi)
        Z=r*cos(theta)
        Generates a random 3D unit vector (direction) with a uniform spherical distribution
        Algo from http://stackoverflow.com/questions/5408276/python-uniform-spherical-distribution
        Equally important site for rejection method of points is
        https://stackoverflow.com/questions/33976911/generate-a-random-sample-of-points-distributed-on-the-surface-of-a-unit-sphere
        :return:
        """
        r=1
        phi = np.random.uniform(0,np.pi*2)
        costheta = np.random.uniform(-1,1)

        theta = np.arccos( costheta )
        x = r*np.sin( theta) * np.cos( phi )
        y = r*np.sin( theta) * np.sin( phi )
        z = r*np.cos( theta )
        
        return (x,y,z)
        

    def celio(self, tlist, k=4, direction=[0.,0.,1.]):
        """
        This implements Celio's approximation as in Phys. Rev. Lett. 56 2720
        """

        def swap(l, p1, p2):
            # given a list of l elements, return a new one where p1 and p2
            # have been swapped.
            a = list(range(0,l))
            a[p1], a[p2] = a[p2], a[p1]
            return a

        # internal copy
        atoms = self.atoms
        n_atoms = len(atoms)

        mu_idx = -1
        for l, atom in enumerate(atoms):
            # record muon position in list. To be used to insert polarized state
            if atom['Label'] == 'mu':
                mu_idx = l
                continue
        if mu_idx < 0:
            raise RuntimeError("Where is the muon!?!")

        Subspaces = []
        for l, atom in enumerate(atoms):
            if l == mu_idx:
                continue

            couple = [atoms[mu_idx].copy(),  atoms[l].copy()]

            dims = self.create_hilbert_space(couple)

            H = self.dipolar_interaction(*couple)

            if (couple[1]['Spin'] > 0.5 and 'EFGTensor' in couple[1].keys()):
                Q, info = self.quadrupolar_interaction(couple[1])
                Q*=0    # I just kill this
                H += Q
                
            if (couple[1]['Spin'] > 0.5 and 'OmegaQI' in couple[1].keys()):
                Q0, info0 = self.quadrupolar_interaction_0(couple[1], couple[0])
                Q0*=0   # I just kill this
                H += Q0
                
            if ( 'OmegaQmu' in couple[1].keys()):
                H += self.muon_induced_efg(couple[1], couple[0])
             
            if ( couple[1]['Spin'] > 0.5 and 'eta' in couple[1].keys()):
                H += self.crystal_electric_field_gradient(couple[1])   

            if np.linalg.norm(self._ext_field) > 0.000001:
                # Add field to atom
                H += self.external_field(couple[1], self._ext_field)
                # Add 1/Nth field to muon
                H += self.external_field(couple[0], self._ext_field/(n_atoms-1))

            # generate maximally mixed state for nuclei (all states populated with random phase)
            NucHdim = int(2*atom['Spin']+1)
            #NuclearPsi = Qobj( np.exp(2.j * np.pi * np.random.rand(NucHdim)), type='ket')

            Subspaces.append({'H': H, 'NucHdim': NucHdim})

        # Convert list of dict to dict of list
        SubspacesInfo = {u: [dic[u] for dic in Subspaces] for u in Subspaces[0]} # https://stackoverflow.com/questions/5558418/list-of-dicts-to-from-dict-of-lists


        def computeU(tt, k):
            # Computer time evolution operator.
            #  we will put the muon as the first particle
            Us = []
            for i, subspace in enumerate(Subspaces):

                other_spins = SubspacesInfo['NucHdim'].copy()
                # current nuclear spin will be in position 0,
                # we'll need to swap it later so we store where original
                # position zero went.
                other_spins[i] = other_spins[0]

                hh = subspace['H']
                # evolution operator on the small matrix
                uu = (-1j * hh * one_over_plank2pi_neVs * tt / k).expm()

                # expand the hilbert space with unitary evolution on other spins
                big_uu = tensor([uu, ] + [qeye(s) for s in other_spins[1:]])

                # swap what is currently position 1 to i-th position and create
                # evolution operator in large hilbert space.
                Us.append( big_uu.permute(swap(n_atoms,1,i+1)) )
            return Us


        r = np.zeros_like(tlist, dtype=np.complex)

        # observe along direction
        direction /= np.linalg.norm(direction)
        if not np.allclose(direction,[0,0,1.]):
            raise RuntimeError("Polarization different from z not yet implemented (but it's easy to implement)")
        o = sigmaz() # this would read qdot((sigmax(), sigmay(), sigmaz()), direction )
        #o = (1./3.)*qdot((sigmax(), sigmay(), sigmaz()), direction )
        


        # Muon observables in big space
        O = tensor(o, *[qeye(S) for S in SubspacesInfo['NucHdim']])

        # Insert muon polarized along positive quantization direction
        #   e, v  = o.eigenstates()
        #   mu_psi = v[1] if e[1] == 1.0 else v[0]
        #
        # Actually below we set it as in basis(2,0), i.e. along z, such that
        # all elements in HdimHalf:2*HdimHalf are zero!

        HdimHalf = np.prod(SubspacesInfo['NucHdim'])
        psi0 = np.zeros(2*HdimHalf, dtype=np.complex)
        psi0[:HdimHalf] = np.exp(2.j * np.pi * np.random.rand(HdimHalf))
        psi = Qobj( psi0, dims=O.dims, type='ket' )

        # Normalize
        Normalization = 1./np.sqrt(HdimHalf)
        psi = psi * Normalization

        dUs = computeU(tlist[1]-tlist[0], k)

        for i, t in enumerate(tlist):
            # measure
            r[i] = (psi.dag() * O * psi)[0,0]
            # Evolve psi
            for _ in range(k):
                for dU in dUs:
                    psi = dU * psi

        return np.real_if_close(r)


    def compute(self, cutoff = 10.0E-10):
        """
        This generates the Hamiltonian and finds eigenstates
        """
        # generate Hamiltonian
        self.create_H(cutoff)

        # find the energy eigenvalues of the composite system
        self.evals, self.ekets = self.H.eigenstates()


    def load_eigenpairs(self, eigenpairs_file):
        """
        This is a helper function to solve or load previous results.
        """

        if load_eigenpairs == False:
            self.logger.info("Diagonalizing matrix...")
            self.compute(cutoff)
            self.logger.info("done...")
            if eigenpairs_file:
                np.savez(save_eigenpairs, evals = self.evals, ekets = self.ekets)

        data = np.load(eigenpairs_file)
        self.evals = data['evals']
        self.ekets = data['ekets']

    def store_eigenpairs(self, eigenpairs_file):
        """
        This is a helper function to solve or load previous results.
        """
        np.savez(save_eigenpairs, evals = self.evals, ekets = self.ekets)


    def sample_spherical(self, direction=[0,0,1]):
        """
        This computes the elements to be later traced. Simple and slow implementation.
        """

        atoms = self.atoms
        for atom in atoms:
            if atom['Label'] == 'mu':
                Ox, Oy, Oz = atom['Observables']

        ekets = self.ekets

        AA = np.zeros([len(ekets),len(ekets)], dtype=np.complex)

        # Chose measuring direction
        if direction != [0,0,1]:
            raise NotImplemented

        O = Oz #qdot( (Ox, Oy, Oz), direction )

        for idx in range(len(ekets)):
            for jdx in range(len(ekets)):
                AA[idx,jdx] += np.abs(O.matrix_element(ekets[idx],ekets[jdx]))**2

        return AA

    def fast_sample_spherical(self, direction=[0,0,1]):
        """
        Same as above, but with numpy vectorized operations.
        """

        atoms = self.atoms
        ekets = self.ekets

        for atom in atoms:
            if atom['Label'] == 'mu':
                Ox, Oy, Oz = atom['Observables']

        self.logger.info('Storing kets in dense matrices')
        allkets = np.matrix(np.zeros((len(ekets),len(ekets)), dtype=np.complex))
        for idx in range(len(ekets)):
            allkets[:,idx] = ekets[idx].data.toarray()[:,0].reshape((len(ekets),1))

        w = np.matrix(np.zeros((len(ekets),len(ekets)), dtype=np.float))

        if direction != [0,0,1]:
            raise NotImplemented

        #qdot( (Ox, Oy, Oz), direction )

        w = np.square(  np.abs(   allkets.conjugate().T*Oz.data.toarray()*allkets  )   ) # AAx = allkets.T*Ox.data.toarray()*allkets

        #
        # This is what is done above...
        #for idx in range(len(ekets)):
        #    for jdx in range(len(ekets)):
        #        AA[idx,jdx,0]=np.abs(Ox.matrix_element(ekets[idx],ekets[jdx]))**2
        #        AA[idx,jdx,1]=np.abs(Oy.matrix_element(ekets[idx],ekets[jdx]))**2
        #        AA[idx,jdx,2]=np.abs(Oz.matrix_element(ekets[idx],ekets[jdx]))**2
        #

        return w


    def polarization(self, tlist, cutoff = 10.0E-10, approximated=False):

        self.compute(cutoff=cutoff)

        w=self.fast_sample_spherical()

        if approximated:
            return self._generate_approximated_signal(tlist, w)
        else:
            return self._generate_signal(tlist, w)

    def _generate_signal(self, tlist, w):
        signal = np.zeros_like(tlist, dtype=np.complex)

        evals = self.evals

        # this does e_i - e_j for all eigenvalues
        ediffs  = np.subtract.outer(evals, evals)
        ediffs *= one_over_plank2pi_neVs

        for idx in range(len(evals)):
            self.logger.info('Adding signal {}...'.format(idx))
            for jdx in range(len(evals)):
                signal += np.exp( 1.j*ediffs[idx,jdx]*tlist ) * w[idx,jdx] # 6.582117e-7 =planck2pi [neV*s]

        return ( np.real_if_close(signal / self.Hdim ) )

    def _generate_approximated_signal(self, tlist, w, weps=1e-18, feps=1e-14):

        evals = self.evals

        factor = 4.0/len(evals)
        weps *= factor
        tmax = np.max(tlist)

        signal = np.zeros_like(tlist, dtype=np.complex)

        # makes the difference of all eigenvalues
        ediffs  = np.subtract.outer(evals, evals)
        ediffs *= one_over_plank2pi_neVs

        order_w = False
        if order_w:
            self.logger.info("Ordering weights")

            idx = np.unravel_index(np.argsort(w, axis=None)[::-1], w.shape)

            _x, _y = idx[0][0], idx[1][0]
        else:
            _x = range(0,len(evals))
            _y = range(0,len(evals))

        for idx in _x:
            self.logger.info('Adding signal...{}'.format(idx))
            for jdx in _y:
                if w[idx,jdx] > weps:
                    if (np.abs(ediffs[idx,jdx]*tmax) > feps ):
                        signal += np.exp( 1.j*ediffs[idx,jdx]*tlist ) * w[idx,jdx] # 6.582117e-7 =planck2pi [neV*s]
                    else:
                        signal += w[idx,jdx]
                        self.logger.info('Skipped (freq) {} {} {}'.format(idx, jdx, ediffs[idx,jdx]*tmax) )
                else:
                    self.logger.info('Skipped (weight) {} {} {}'.format(idx, jdx, w[idx,jdx]) )
        return ( np.real_if_close(signal / self.Hdim ) )


if __name__ == '__main__':
    """
    Here we always use SI in input.
    """
    import matplotlib.pyplot as plt
    angtom=1.0e-10 # m

    # This is a linear F-mu-F along z
    r=1.17 * angtom
    atoms = [
                {'Position': np.array([0.000000  ,  0.  ,  0]),
                'Label': 'F',
                },

                {'Position': np.array([0.000000  ,  0.  ,  r ]),
                'Label': 'mu'
                },

                {'Position': np.array([0.000000  ,  0.  ,  2*r]),
                'Label': 'F',
                }
            ]
    # Time values, in seconds
    tlist = np.linspace(0, 10e-6, 100)

    # Define main class
    NS = MuonNuclearInteraction(atoms, log_level='info')
    # Rotate sample such that axis z used to define the atomic positions
    # is aligned with quantization axis which also happens to be z.
    # Basically the next call will do nothing
    NS.translate_rotate_sample_vec([0,0,1])

    # cutoff the dipolar interaction in order to avoid F-F term
    signal_FmuF = NS.polarization(tlist, cutoff=1.2 * angtom)

    NS = MuonNuclearInteraction(atoms, log_level='info')
    NS.translate_rotate_sample_vec([0,1,0])
    signal_FmuF += NS.polarization(tlist, cutoff=1.2 * angtom)

    NS = MuonNuclearInteraction(atoms, log_level='info')
    NS.translate_rotate_sample_vec([1,0,0])
    signal_FmuF += NS.polarization(tlist, cutoff=1.2 * angtom)

    signal_FmuF /= 3.

    # no cutoff this time
    NS = MuonNuclearInteraction(atoms, log_level='info')
    NS.translate_rotate_sample_vec([0,0,1])
    signal_FmuF_with_Fdip = NS.polarization(tlist)

    NS = MuonNuclearInteraction(atoms, log_level='info')
    NS.translate_rotate_sample_vec([0,1,0])
    signal_FmuF_with_Fdip += NS.polarization(tlist)

    NS = MuonNuclearInteraction(atoms, log_level='info')
    NS.translate_rotate_sample_vec([1,0,0])
    signal_FmuF_with_Fdip += NS.polarization(tlist)

    signal_FmuF_with_Fdip /= 3.

    fig, axes = plt.subplots(1,1)
    axes.plot(tlist, signal_FmuF, label='Computed', linestyle='-')
    axes.plot(tlist, signal_FmuF_with_Fdip, label='Computed, with F-F interaction', linestyle='-.')

    # Generate and plot analytical version for comparison
    def plot_brewer(interval,r):
        from numpy import cos, sin, sqrt
        omegad = (mu_0*NS.gammas['mu']*NS.gammas['F']*(hbar))
        omegad /=(4*np.pi*((r)**3))

        tomegad=interval*omegad
        y = (1./6.)*(3+cos(sqrt(3)*tomegad)+ \
                    (1-1/sqrt(3))*cos(((3-sqrt(3))/2)*tomegad)+ \
                    (1+1/sqrt(3))*cos(((3+sqrt(3))/2)*tomegad))#+0.05*(exp(-x/2.5))**1.5
        return y

    axes.plot(tlist, plot_brewer(tlist, r), label='F-mu-F Brewer', linestyle=':')


    ticks = np.round(axes.get_xticks()*10.**6)
    axes.set_xticklabels(ticks)
    axes.set_xlabel(r'$t (\mu s)$', fontsize=20)
    axes.set_ylabel(r'$\left<P_z\right>$', fontsize=20);
    axes.grid()
    fig.legend()
    plt.show()
