#!/usr/bin/env python
# $Id$
# -*- coding: utf-8

"""
Relativistic Dirac-Hartree-Fock
"""


import numpy
import pyscf.lib
import pyscf.lib.logger as log
from pyscf.scf import _vhf
from pyscf.grad import hf


def grad_elec(mfg, mo_energy=None, mo_coeff=None, mo_occ=None):
    return hf.grad_elec(mfg, mo_energy, mo_coeff, mo_occ)

def grad_nuc(mol):
    return hf.grad_nuc(mol)

def get_hcore(mol):
    n2c = mol.nao_2c()
    n4c = n2c * 2
    c = mol.light_speed

    s  = mol.intor('cint1e_ipovlp', comp=3)
    t  = mol.intor('cint1e_ipkin', comp=3)
    vn = mol.intor('cint1e_ipnuc', comp=3)
    wn = mol.intor('cint1e_ipspnucsp', comp=3)
    h1e = numpy.zeros((3,n4c,n4c), numpy.complex)
    h1e[:,:n2c,:n2c] = vn
    h1e[:,n2c:,:n2c] = t
    h1e[:,:n2c,n2c:] = t
    h1e[:,n2c:,n2c:] = wn * (.25/c**2) - t
    return h1e

def get_ovlp(mol):
    n2c = mol.nao_2c()
    n4c = n2c * 2
    c = mol.light_speed

    s  = mol.intor('cint1e_ipovlp', comp=3)
    t  = mol.intor('cint1e_ipkin', comp=3)
    s1e = numpy.zeros((3,n4c,n4c), numpy.complex)
    s1e[:,:n2c,:n2c] = s
    s1e[:,n2c:,n2c:] = t * (.5/c**2)
    return s1e

def make_rdm1e(mo_energy, mo_coeff, mo_occ):
    return hf.make_rdm1e(mo_energy, mo_coeff, mo_occ)

def matblock_by_atom(mol, atm_id, mat):
    '''extract row band for each atom'''
    shells = mol.atom_shell_ids(atm_id)
    b0, b1 = mol.nao_2c_range(shells[0], shells[-1]+1)
    n2c = mat.shape[1] // 2
    v = numpy.zeros_like(mat)
    v[:,b0:b1,:] = mat[:,b0:b1,:]
    v[:,n2c+b0:n2c+b1,:] = mat[:,n2c+b0:n2c+b1,:]
    return v

def get_veff(mol, dm, level='SSSS'):
    return get_coulomb_hf(mol, dm, level)
def get_coulomb_hf(mol, dm, level='SSSS'):
    '''Dirac-Hartree-Fock Coulomb repulsion'''
    if level.upper() == 'LLLL':
        log.info(mol, 'Compute Gradients: (LL|LL)')
        vj, vk = _call_vhf1_llll(mol, dm)
#L2SL the response of the large and small components on the large component density
#LS2L the response of the large component on the L+S density
#NOSS just exclude SSSS
#TODO    elif level.upper() == 'LS2L':
#TODO        log.info(mol, 'Compute Gradients: (LL|LL) + (SS|dLL)')
#TODO        vj, vk = scf.hf.get_vj_vk(pycint.rkb_vhf_coul_grad_ls2l_o1, mol, dm)
#TODO    elif level.upper() == 'L2SL':
#TODO        log.info(mol, 'Compute Gradients: (LL|LL) + (dSS|LL)')
#TODO        vj, vk = scf.hf.get_vj_vk(pycint.rkb_vhf_coul_grad_l2sl_o1, mol, dm)
#TODO    elif level.upper() == 'NOSS':
#TODO        log.info(mol, 'Compute Gradients: (LL|LL) + (dSS|LL) + (SS|dLL)')
#TODO        vj, vk = scf.hf.get_vj_vk(pycint.rkb_vhf_coul_grad_xss_o1, mol, dm)
    else:
        log.info(mol, 'Compute Gradients: (LL|LL) + (SS|LL) + (SS|SS)')
        vj, vk = _call_vhf1(mol, dm)
    return vj - vk


class UHF(hf.RHF):
    '''Unrestricted Dirac-Hartree-Fock gradients'''
    def __init__(self, scf_method):
        hf.RHF.__init__(self, scf_method)
        if scf_method.with_ssss:
            self.level = 'SSSS'
        else:
            #self.level = 'NOSS'
            self.level = 'LLLL'

    @pyscf.lib.omnimethod
    def get_hcore(self, mol=None):
        if mol is None:
            mol = self.mol
        return get_hcore(mol)

    @pyscf.lib.omnimethod
    def get_ovlp(self, mol=None):
        if mol is None:
            mol = self.mol
        return get_ovlp(mol)

    def _grad_rinv(self, mol, ia):
        n2c = mol.nao_2c()
        n4c = n2c * 2
        c = mol.light_speed
        v = numpy.zeros((3,n4c,n4c), numpy.complex)
        mol.set_rinv_origin_(mol.atom_coord(ia))
        vn = mol.atom_charge(ia) * mol.intor('cint1e_iprinv', comp=3)
        wn = mol.atom_charge(ia) * mol.intor('cint1e_ipsprinvsp', comp=3)
        v[:,:n2c,:n2c] = vn
        v[:,n2c:,n2c:] = wn * (.25/c**2)
        return v

    def get_veff(self, mol, dm):
        return get_coulomb_hf(mol, dm, level=self.level)

    def matblock_by_atom(self, mol, atm_id, mat):
        return matblock_by_atom(mol, atm_id, mat)



def _call_vhf1_llll(mol, dm):
    c1 = .5/mol.light_speed
    n2c = dm.shape[0] // 2
    dmll = dm[:n2c,:n2c].copy()
    vj = numpy.zeros((3,n2c*2,n2c*2), dtype=numpy.complex)
    vk = numpy.zeros((3,n2c*2,n2c*2), dtype=numpy.complex)
    vj[:,:n2c,:n2c], vk[:,:n2c,:n2c] = \
            _vhf.rdirect_mapdm('cint2e_ip1', 's2kl',
                               ('lk->s1ij', 'jk->s1il'), dmll, 3,
                               mol._atm, mol._bas, mol._env)
    return vj, vk

def _call_vhf1(mol, dm):
    c1 = .5/mol.light_speed
    n2c = dm.shape[0] // 2
    dmll = dm[:n2c,:n2c].copy()
    dmls = dm[:n2c,n2c:].copy()
    dmsl = dm[n2c:,:n2c].copy()
    dmss = dm[n2c:,n2c:].copy()
    vj = numpy.zeros((3,n2c*2,n2c*2), dtype=numpy.complex)
    vk = numpy.zeros((3,n2c*2,n2c*2), dtype=numpy.complex)
    vj[:,:n2c,:n2c], vk[:,:n2c,:n2c] = \
            _vhf.rdirect_mapdm('cint2e_ip1', 's2kl',
                               ('lk->s1ij', 'jk->s1il'), dmll, 3,
                               mol._atm, mol._bas, mol._env)
    vj[:,n2c:,n2c:], vk[:,n2c:,n2c:] = \
            _vhf.rdirect_mapdm('cint2e_ipspsp1spsp2', 's2kl',
                               ('lk->s1ij', 'jk->s1il'), dmss, 3,
                               mol._atm, mol._bas, mol._env) * c1**4
    vx = _vhf.rdirect_bindm('cint2e_ipspsp1', 's2kl',
                            ('lk->s1ij', 'jk->s1il'), (dmll, dmsl), 3,
                            mol._atm, mol._bas, mol._env) * c1**2
    vj[:,n2c:,n2c:] += vx[0]
    vk[:,n2c:,:n2c] += vx[1]
    vx = _vhf.rdirect_bindm('cint2e_ip1spsp2', 's2kl',
                            ('lk->s1ij', 'jk->s1il'), (dmss, dmls), 3,
                            mol._atm, mol._bas, mol._env) * c1**2
    vj[:,:n2c,:n2c] += vx[0]
    vk[:,:n2c,n2c:] += vx[1]
    return vj, vk


if __name__ == "__main__":
    from pyscf import gto
    from pyscf import scf

    h2o = gto.Mole()
    h2o.verbose = 0
    h2o.output = None#"out_h2o"
    h2o.atom = [
        ["O" , (0. , 0.     , 0.)],
        [1   , (0. , -0.757 , 0.587)],
        [1   , (0. , 0.757  , 0.587)] ]
    h2o.basis = {"H": '6-31g',
                 "O": '6-31g',}
    h2o.build()
    method = scf.dhf.UHF(h2o)
    print(method.scf())
    g = UHF(method)
    print(g.grad())
#[[ 0   0                0             ]
# [ 0  -4.27565134e-03  -1.20060029e-02]
# [ 0   4.27565134e-03  -1.20060029e-02]]

