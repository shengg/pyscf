#!/usr/bin/env python
# File: gen_grid.py
# Author: Qiming Sun <osirpt.sun@gmail.com>
#

'''
Generate DFT grids and weights, based on the code provided by Gerald Knizia <>
'''


import os
import ctypes
from functools import reduce
import numpy
import pyscf.lib
from pyscf import gto
from pyscf.dft import radi

libdft = pyscf.lib.load_library('libdft')

# ~= (L+1)**2/3
SPHERICAL_POINTS_ORDER = {
      0:    1,
      3:    6,
      5:   14,
      7:   26,
      9:   38,
     11:   50,
     13:   74,
     15:   86,
     17:  110,
     19:  146,
     21:  170,
     23:  194,
     25:  230,
     27:  266,
     29:  302,
     31:  350,
     35:  434,
     41:  590,
     47:  770,
     53:  974,
     59: 1202,
     65: 1454,
     71: 1730,
     77: 2030,
     83: 2354,
     89: 2702,
     95: 3074,
    101: 3470,
    107: 3890,
    113: 4334,
    119: 4802,
    125: 5294,
    131: 5810
}

# SG0
# S. Chien and P. Gill,  J. Comput. Chem. 27 (2006) 730-739.

# P.M.W. Gill, B.G. Johnson, J.A. Pople, Chem. Phys. Letters 209 (1993) 506-512
SG1RADII = numpy.array((
    0,
    1.0000,                                                 0.5882,
    3.0769, 2.0513, 1.5385, 1.2308, 1.0256, 0.8791, 0.7692, 0.6838,
    4.0909, 3.1579, 2.5714, 2.1687, 1.8750, 1.6514, 1.4754, 1.3333))


def sg1_prune(nuc, rads, n_ang):
    '''SG1, CPL, 209, 506'''
# In SG1 the ang grids for the five regions
#            6  38 86  194 86
    leb_ngrid = numpy.array([6, 38, 86, 194, 86])
    alphas = numpy.array((
        (0.25  , 0.5, 1.0, 4.5),
        (0.1667, 0.5, 0.9, 3.5),
        (0.1   , 0.4, 0.8, 2.5)))
    if nuc <= 2: # H, He
       place = ((rads/SG1RADII[nuc]).reshape(-1,1) > alphas[0]).sum(axis=1)
    elif nuc <= 10: # Li - Ne
       place = ((rads/SG1RADII[nuc]).reshape(-1,1) > alphas[1]).sum(axis=1)
    else:
       place = ((rads/SG1RADII[nuc]).reshape(-1,1) > alphas[2]).sum(axis=1)
    return leb_ngrid[place]

def nwchem_prune(nuc, rads, n_ang):
    '''NWChem'''
    alphas = numpy.array((
        (0.25  , 0.5, 1.0, 4.5),
        (0.1667, 0.5, 0.9, 3.5),
        (0.1   , 0.4, 0.8, 2.5)))
    leb_ngrid = numpy.array(
        [38,  50,  74 , 86,  110, 146, 170, 194, 230, 266, 302, 350,
         434, 590, 770, 974, 1202,1454,1730,2030,2354,2702,3074,3470,
         3890,4334,4802,5294,5810])
    if n_ang < 50:
        angs = numpy.empty(len(rads), dtype=int)
        angs[:] = n_ang
        return angs
    elif n_ang == 50:
        leb_l = numpy.array([1, 2, 2, 2, 1])
    else:
        idx = numpy.where(leb_ngrid==n_ang)[0][0]
        leb_l = numpy.array([1, 3, idx-1, idx, idx-1])

    if nuc <= 2: # H, He
       place = ((rads/SG1RADII[nuc]).reshape(-1,1) > alphas[0]).sum(axis=1)
    elif nuc <= 10: # Li - Ne
       place = ((rads/SG1RADII[nuc]).reshape(-1,1) > alphas[1]).sum(axis=1)
    else:
       place = ((rads/SG1RADII[nuc]).reshape(-1,1) > alphas[2]).sum(axis=1)
    angs = leb_l[place]
    angs = leb_ngrid[angs]
    return angs

# Prune scheme JCP 102, 346
def treutler_prune(nuc, rads, n_ang):
    '''Treutler-Ahlrichs'''
    nr = len(rads)
    leb_ngrid = numpy.empty(nr, dtype=int)
    leb_ngrid[:nr//3] = 14 # l=5
    leb_ngrid[nr//3:nr//2] = 50 # l=11
    leb_ngrid[nr//2:] = n_ang
    return leb_ngrid



###########################################################
# Becke partitioning

# Stratmann, Scuseria, Frisch. CPL, 257, 213 (1996), eq.11
def stratmann(g):
    '''Stratmann, Scuseria, Frisch. CPL, 257, 213 (1996)'''
    a = .64 # comment after eq. 14, 
    if isinstance(g, numpy.ndarray):
        ma = g/a
        ma2 = ma * ma
        g1 = (1/16.)*(ma*(35 + ma2*(-35 + ma2*(21 - 5 *ma2))))
        g1[g<=-a] = -1
        g1[g>= a] =  1
        return g1
    else:
        if g <= -a:
            g = -1
        elif g >= a:
            g = 1
        else:
            ma = g/a
            ma2 = ma*ma
            g = (1/16.)*(ma*(35 + ma2*(-35 + ma2*(21 - 5 *ma2))))
        return g

def original_becke(g):
    '''Becke, JCP, 88, 2547 (1988)'''
    g = (3 - g**2) * g * .5
    g = (3 - g**2) * g * .5
    g = (3 - g**2) * g * .5
    return g

def gen_atomic_grids(mol, mol_grids={}, radi_method=radi.gauss_chebyshev,
                     level=3, prune_scheme=treutler_prune):
    atom_grids_tab = {}
    for ia in range(mol.natm):
        symb = mol.atom_symbol(ia)

        if symb not in atom_grids_tab:
            chg = mol.atom_charge(ia)
            if symb in mol_grids:
                n_rad, n_ang = mol_grids[symb]
                assert(n_ang in SPHERICAL_POINTS_ORDER.values())
            else:
                n_rad = _default_rad(chg, level)
                n_ang = _default_ang(chg, level)
            rad, rad_weight = radi_method(n_rad)
            # atomic_scale = 1
            # rad *= atomic_scale
            # rad_weight *= atomic_scale

            if callable(prune_scheme):
                angs = prune_scheme(chg, rad, n_ang)
            else:
                angs = [n_ang] * n_rad
            pyscf.lib.logger.debug1(mol, 'atom %s rad-grids = %d, ang-grids = %s',
                                    symb, n_rad, angs)

            angs = numpy.array(angs)
            coords = []
            vol = []
            for n in set(angs):
                grid = numpy.empty((n,4))
                libdft.MakeAngularGrid(grid.ctypes.data_as(ctypes.c_void_p),
                                       ctypes.c_int(n))
                coords.append(numpy.einsum('i,jk->ijk',rad[angs==n],
                                           grid[:,:3]).reshape(-1,3))
                vol.append(numpy.einsum('i,j->ij', rad_weight[angs==n],
                                        grid[:,3]).ravel())
            atom_grids_tab[symb] = (numpy.vstack(coords), numpy.hstack(vol))
    return atom_grids_tab


def gen_partition(mol, atom_grids_tab, atomic_radii_adjust=None,
                  becke_scheme=original_becke):
    atm_coords = numpy.array([mol.atom_coord(i) for i in range(mol.natm)])
    atm_dist = radi._inter_distance(mol)
    def gen_grid_partition(coords):
        ngrid = coords.shape[0]
        grid_dist = numpy.empty((mol.natm,ngrid))
        for ia in range(mol.natm):
            dc = coords - atm_coords[ia]
            grid_dist[ia] = numpy.sqrt(numpy.einsum('ij,ij->i',dc,dc))
        pbecke = numpy.ones((mol.natm,ngrid))
        for i in range(mol.natm):
            for j in range(i):
                g = 1/atm_dist[i,j] * (grid_dist[i]-grid_dist[j])
                if atomic_radii_adjust is not None:
                    g = atomic_radii_adjust(i, j, g)
                g = becke_scheme(g)
                pbecke[i] *= .5 * (1-g)
                pbecke[j] *= .5 * (1+g)

        return pbecke

    coords_all = []
    weights_all = []
    for ia in range(mol.natm):
        coords, vol = atom_grids_tab[mol.atom_symbol(ia)]
        coords = coords + atm_coords[ia]
        pbecke = gen_grid_partition(coords)
        weights = vol * pbecke[ia] / pbecke.sum(axis=0)
        coords_all.append(coords)
        weights_all.append(weights)
    return numpy.vstack(coords_all), numpy.hstack(weights_all)



class Grids(object):
    def __init__(self, mol):
        self.mol = mol
        self.stdout = mol.stdout
        self.verbose = mol.verbose
        self.atomic_radii = radi.treutler_atomic_radii_adjust(mol, radi.BRAGG_RADII)
        #self.atomic_radii = radi.becke_atomic_radii_adjust(mol, radi.BRAGG_RADII)
        #self.atomic_radii = radi.becke_atomic_radii_adjust(mol, radi.COVALENT_RADII)
        #self.atomic_radii = None # to switch off atomic radii adjustment
        self.radi_method = radi.treutler
        #self.radi_method = radi.gauss_chebyshev
        #self.becke_scheme = stratmann
        self.becke_scheme = original_becke
        self.level = 3
        self.prune_scheme = treutler_prune
        self.symmetry = mol.symmetry

        self.coords  = None
        self.weights = None

    def dump_flags(self):
        try:
            pyscf.log.info(self, 'radial grids: %s', self.radi_method.__doc__)
            pyscf.log.info(self, 'becke partition: %s', self.becke_scheme.__doc__)
            pyscf.log.info(self, 'pruning grids: %s', self.prune_scheme.__doc__)
            pyscf.log.info(self, 'grids dens level: %d', self.level)
            pyscf.log.info(self, 'symmetrized grids: %d', self.symmetry)
            if self.atomic_radii is not None:
                pyscf.log.info(self, 'adjust function', self.atomic_radii.__doc__)
        except:
            pass

    def setup_grids(self, mol=None):
        return self.setup_grids_(mol)
    def setup_grids_(self, mol=None):
        if mol is None: mol = self.mol
        atom_grids_tab = self.gen_atomic_grids(mol, mol_grids=mol.grids,
                                               radi_method=self.radi_method,
                                               level=self.level,
                                               prune_scheme=self.prune_scheme)
        self.coords, self.weights = \
                self.gen_partition(mol, atom_grids_tab, self.atomic_radii,
                                   self.becke_scheme)
        pyscf.lib.logger.info(self, 'tot grids = %d', len(self.weights))
        return self.coords, self.weights

    def gen_atomic_grids(self, mol, mol_grids=None, radi_method=None,
                         level=None, prune_scheme=None):
        if mol_grids is None: mol_grids = mol.grids
        if radi_method is None: radi_method = mol.radi_method
        if level is None: level = self.level
        if prune_scheme is None: prune_scheme = self.prune_scheme
        return gen_atomic_grids(mol, mol_grids, self.radi_method, level,
                                prune_scheme)

    def gen_partition(self, mol, atom_grids_tab, atomic_radii=None,
                      becke_scheme=original_becke):
        return gen_partition(mol, atom_grids_tab, atomic_radii,
                             becke_scheme)



def _default_rad(nuc, level=3):
    tab   = numpy.array( (2 , 10, 18, 36, 54, 86, 118))
    grids = numpy.array(((20, 25, 35, 40, 50, 60, 70 ),
                         (25, 30, 40, 45, 55, 65, 75 ),
                         (30, 35, 45, 50, 60, 70, 80 ),
                         (35, 40, 50, 55, 65, 75, 85 ),
                         (40, 45, 55, 60, 70, 80, 90 ),
                         (45, 50, 60, 65, 75, 85, 95 ),))
    period = (nuc > tab).sum()
    return grids[level,period]

def _default_ang(nuc, level=3):
    tab   = numpy.array( (2 , 10, 18, 36, 54, 86, 118))
    order = numpy.array(((15, 17, 17, 17, 17, 17, 17 ),
                         (17, 23, 23, 23, 23, 23, 23 ),
                         (23, 29, 29, 29, 29, 29, 29 ),
                         (29, 35, 35, 35, 35, 35, 35 ),
                         (35, 41, 41, 41, 41, 41, 41 ),
                         (41, 47, 47, 47, 47, 47, 47 ),))
    period = (nuc > tab).sum()
    return SPHERICAL_POINTS_ORDER[order[level,period]]





if __name__ == '__main__':
    import gto
    h2o = gto.Mole()
    h2o.verbose = 0
    h2o.output = None#"out_h2o"
    h2o.atom.extend([
        ['O' , (0. , 0.     , 0.)],
        ['H' , (0. , -0.757 , 0.587)],
        ['H' , (0. , 0.757  , 0.587)] ])

    h2o.basis = {"H": '6-31g',
                 "O": '6-31g',}
    h2o.grids = {"H": (50, 302),
                 "O": (50, 302),}
    h2o.build()
    import time
    t0 = time.clock()
    g = Grids(h2o)
    g.setup_grids()
    print(g.coords.shape)
    print(time.clock() - t0)

