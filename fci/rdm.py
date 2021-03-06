#!/usr/bin/env python

import os
import ctypes
import _ctypes
import numpy
import pyscf.lib
from pyscf.fci import cistring

librdm = pyscf.lib.load_library('libmcscf')

'''FCI 1, 2, 3, 4-particle density matrices.

Note the index difference to the mean-field density matrix.  Here,
        dm[p,q,r,s,...] = <p^+ q r^+ s ... >
rather than the mean-field DM
        dm[p,q] = < q^+ p >
'''

def reorder_rdm(rdm1, rdm2, inplace=False):
    nmo = rdm1.shape[0]
    if not inplace:
        rdm2 = rdm2.copy()
    for k in range(nmo):
        rdm2[:,k,k,:] -= rdm1
    #return rdm1, rdm2
    rdm2 = pyscf.lib.transpose_sum(rdm2.reshape(nmo*nmo,-1), inplace=True) * .5
    return rdm1, rdm2.reshape(nmo,nmo,nmo,nmo)

# dm_pq = <|p^+ q|>
def make_rdm1_ms0(fname, cibra, ciket, norb, nelec, link_index=None):
    if isinstance(nelec, (int, numpy.integer)):
        neleca = nelec//2
    else:
        neleca, nelecb = nelec
        assert(neleca == nelecb)
    if link_index is None:
        link_index = cistring.gen_linkstr_index(range(norb), neleca)
    na,nlink,_ = link_index.shape
    rdm1 = numpy.empty((norb,norb))
    fn = getattr(librdm, fname)
    fn(rdm1.ctypes.data_as(ctypes.c_void_p),
       cibra.ctypes.data_as(ctypes.c_void_p),
       ciket.ctypes.data_as(ctypes.c_void_p),
       ctypes.c_int(norb),
       ctypes.c_int(na), ctypes.c_int(na),
       ctypes.c_int(nlink), ctypes.c_int(nlink),
       link_index.ctypes.data_as(ctypes.c_void_p),
       link_index.ctypes.data_as(ctypes.c_void_p))
    return rdm1

# NOTE the rdm2 is calculated as <p^+ q r^+ s>, call reorder_rdm to transform
# to the normal rdm2, which is defined as <p^+ r^+ q s>
# symm = 1: bra, ket symmetry
# symm = 2: particle permutation symmetry
def make_rdm12_ms0(fname, cibra, ciket, norb, nelec, link_index=None, symm=0):
    if isinstance(nelec, (int, numpy.integer)):
        neleca = nelec//2
    else:
        neleca, nelecb = nelec
        assert(neleca == nelecb)
    if link_index is None:
        link_index = cistring.gen_linkstr_index(range(norb), neleca)
    link_index = (link_index, link_index)
    return make_rdm12_spin1(fname, cibra, ciket, norb, nelec, link_index, symm)

def make_rdm1(fname, cibra, ciket, norb, nelec, link_index=None):
    return make_rdm1_ms0(fname, cibra, ciket, norb, nelec, link_index)

def make_rdm12(fname, cibra, ciket, norb, nelec, link_index=None, symm=0):
    return make_rdm12_ms0(fname, cibra, ciket, norb, nelec, link_index, symm)

###################################################
#
# nelec and link_index are tuples of (alpha,beta)
#
def make_rdm1_spin1(fname, cibra, ciket, norb, nelec, link_index=None):
    if isinstance(nelec, (int, numpy.integer)):
        neleca = nelecb = nelec//2
    else:
        neleca, nelecb = nelec
    if link_index is None:
        link_indexa = cistring.gen_linkstr_index(range(norb), neleca)
        link_indexb = cistring.gen_linkstr_index(range(norb), nelecb)
    else:
        link_indexa, link_indexb = link_index
    na,nlinka = link_indexa.shape[:2]
    nb,nlinkb = link_indexb.shape[:2]
    rdm1 = numpy.empty((norb,norb))
    fn = getattr(librdm, fname)
    fn(rdm1.ctypes.data_as(ctypes.c_void_p),
       cibra.ctypes.data_as(ctypes.c_void_p),
       ciket.ctypes.data_as(ctypes.c_void_p),
       ctypes.c_int(norb),
       ctypes.c_int(na), ctypes.c_int(nb),
       ctypes.c_int(nlinka), ctypes.c_int(nlinkb),
       link_indexa.ctypes.data_as(ctypes.c_void_p),
       link_indexb.ctypes.data_as(ctypes.c_void_p))
    return rdm1

# NOTE the rdm2 is calculated as <p^+ q r^+ s>, call reorder_rdm to transform
# to the normal rdm2, which is defined as <p^+ r^+ q s>
# symm = 1: bra, ket symmetry
# symm = 2: particle permutation symmetry
def make_rdm12_spin1(fname, cibra, ciket, norb, nelec, link_index=None, symm=0):
    if isinstance(nelec, (int, numpy.integer)):
        neleca = nelecb = nelec//2
    else:
        neleca, nelecb = nelec
    if link_index is None:
        link_indexa = cistring.gen_linkstr_index(range(norb), neleca)
        link_indexb = cistring.gen_linkstr_index(range(norb), nelecb)
    else:
        link_indexa, link_indexb = link_index
    na,nlinka = link_indexa.shape[:2]
    nb,nlinkb = link_indexb.shape[:2]
    rdm1 = numpy.empty((norb,norb))
    rdm2 = numpy.empty((norb,norb,norb,norb))
    fn = _ctypes.dlsym(librdm._handle, fname)
    librdm.FCIrdm12_drv(ctypes.c_void_p(fn),
                        rdm1.ctypes.data_as(ctypes.c_void_p),
                        rdm2.ctypes.data_as(ctypes.c_void_p),
                        cibra.ctypes.data_as(ctypes.c_void_p),
                        ciket.ctypes.data_as(ctypes.c_void_p),
                        ctypes.c_int(norb),
                        ctypes.c_int(na), ctypes.c_int(nb),
                        ctypes.c_int(nlinka), ctypes.c_int(nlinkb),
                        link_indexa.ctypes.data_as(ctypes.c_void_p),
                        link_indexb.ctypes.data_as(ctypes.c_void_p),
                        ctypes.c_int(symm))
    return rdm1, rdm2


##############################
#
# 3-particle and 4-particle density matrix for RHF-FCI wfn
#
def make_dm123(fname, cibra, ciket, norb, nelec):
    if isinstance(nelec, (int, numpy.integer)):
        neleca = nelecb = nelec//2
    else:
        neleca, nelecb = nelec
    link_indexa = cistring.gen_linkstr_index(range(norb), neleca)
    link_indexb = cistring.gen_linkstr_index(range(norb), nelecb)
    na,nlinka = link_indexa.shape[:2]
    nb,nlinkb = link_indexb.shape[:2]
    rdm1 = numpy.empty((norb,)*2)
    rdm2 = numpy.empty((norb,)*4)
    rdm3 = numpy.empty((norb,)*6)
    kernel = _ctypes.dlsym(librdm._handle, fname)
    librdm.FCIrdm3_drv(ctypes.c_void_p(kernel),
                       rdm1.ctypes.data_as(ctypes.c_void_p),
                       rdm2.ctypes.data_as(ctypes.c_void_p),
                       rdm3.ctypes.data_as(ctypes.c_void_p),
                       cibra.ctypes.data_as(ctypes.c_void_p),
                       ciket.ctypes.data_as(ctypes.c_void_p),
                       ctypes.c_int(norb),
                       ctypes.c_int(na), ctypes.c_int(nb),
                       ctypes.c_int(nlinka), ctypes.c_int(nlinkb),
                       link_indexa.ctypes.data_as(ctypes.c_void_p),
                       link_indexb.ctypes.data_as(ctypes.c_void_p))
    rdm3 = _complete_dm3_(rdm2, rdm3)
    return rdm1, rdm2, rdm3
def _complete_dm3_(dm2, dm3):
# fci_4pdm.c assumed symmetry p >= r >= t for 3-pdm <p^+ q r^+ s t^+ u>
# Using E^r_sE^p_q = E^p_qE^r_s - \delta_{qr}E^p_s + \delta_{ps}E^r_q to
# complete the full 3-pdm
    def transpose01(ijk, i, j, k):
        jik = ijk.transpose(1,0,2)
        jik[:,j] -= dm2[i,:,k,:]
        jik[i,:] += dm2[j,:,k,:]
        dm3[j,:,i,:,k,:] = jik
        return jik
    def transpose12(ijk, i, j, k):
        ikj = ijk.transpose(0,2,1)
        ikj[:,:,k] -= dm2[i,:,j,:]
        ikj[:,j,:] += dm2[i,:,k,:]
        dm3[i,:,k,:,j,:] = ikj
        return ikj

# ijk -> jik -> jki -> kji -> kij -> ikj
    norb = dm2.shape[0]
    for i in range(norb):
        for j in range(i+1):
            for k in range(j+1):
                tmp = transpose01(dm3[i,:,j,:,k,:].copy(), i, j, k)
                tmp = transpose12(tmp, j, i, k)
                tmp = transpose01(tmp, j, k, i)
                tmp = transpose12(tmp, k, j, i)
                tmp = transpose01(tmp, k, i, j)
    return dm3

def make_dm1234(fname, cibra, ciket, norb, nelec):
    if isinstance(nelec, (int, numpy.integer)):
        neleca = nelecb = nelec//2
    else:
        neleca, nelecb = nelec
    link_indexa = cistring.gen_linkstr_index(range(norb), neleca)
    link_indexb = cistring.gen_linkstr_index(range(norb), nelecb)
    na,nlinka = link_indexa.shape[:2]
    nb,nlinkb = link_indexb.shape[:2]
    rdm1 = numpy.empty((norb,)*2)
    rdm2 = numpy.empty((norb,)*4)
    rdm3 = numpy.empty((norb,)*6)
    rdm4 = numpy.empty((norb,)*8)
    librdm.FCIrdm4_drv(ctypes.c_void_p(_ctypes.dlsym(librdm._handle, fname)),
                       rdm1.ctypes.data_as(ctypes.c_void_p),
                       rdm2.ctypes.data_as(ctypes.c_void_p),
                       rdm3.ctypes.data_as(ctypes.c_void_p),
                       rdm4.ctypes.data_as(ctypes.c_void_p),
                       cibra.ctypes.data_as(ctypes.c_void_p),
                       ciket.ctypes.data_as(ctypes.c_void_p),
                       ctypes.c_int(norb),
                       ctypes.c_int(na), ctypes.c_int(nb),
                       ctypes.c_int(nlinka), ctypes.c_int(nlinkb),
                       link_indexa.ctypes.data_as(ctypes.c_void_p),
                       link_indexb.ctypes.data_as(ctypes.c_void_p))
    rdm3 = _complete_dm3_(rdm2, rdm3)
    rdm4 = _complete_dm4_(rdm3, rdm4)
    return rdm1, rdm2, rdm3, rdm4
def _complete_dm4_(dm3, dm4):
# fci_4pdm.c assumed symmetry p >= r >= t >= v for 4-pdm <p^+ q r^+ s t^+ u v^+ w>
# Using E^r_sE^p_q = E^p_qE^r_s - \delta_{qr}E^p_s + \delta_{ps}E^r_q to
# complete the full 4-pdm
    def transpose01(ijkl, i, j, k, l):
        jikl = ijkl.transpose(1,0,2,3)
        jikl[:,j] -= dm3[i,:,k,:,l,:]
        jikl[i,:] += dm3[j,:,k,:,l,:]
        dm4[j,:,i,:,k,:,l,:] = jikl
        return jikl
    def transpose12(ijkl, i, j, k, l):
        ikjl = ijkl.transpose(0,2,1,3)
        ikjl[:,:,k] -= dm3[i,:,j,:,l,:]
        ikjl[:,j,:] += dm3[i,:,k,:,l,:]
        dm4[i,:,k,:,j,:,l,:] = ikjl
        return ikjl
    def transpose23(ijkl, i, j, k, l):
        ijlk = ijkl.transpose(0,1,3,2)
        ijlk[:,:,:,l] -= dm3[i,:,j,:,k,:]
        ijlk[:,:,k,:] += dm3[i,:,j,:,l,:]
        dm4[i,:,j,:,l,:,k,:] = ijlk
        return ijlk
    def chain(ijkl, i, j, k, l):
        tmp = transpose23(ijkl, i, j, k, l)
        tmp = transpose12(tmp, i, j, l, k)
        tmp = transpose23(tmp, i, l, j, k)
        tmp = transpose12(tmp, i, l, k, j)
        tmp = transpose23(tmp, i, k, l, j)
        return tmp

# ijkl -> ijlk -> iljk -> ilkj -> iklj -> ikjl
#      -> jikl -> jilk -> jlik -> jlki -> jkli -> jkil
#(ikjl)-> kijl -> kilj -> klij -> klji -> kjli -> kjil
#(iljk)-> lijk -> likj -> lkij -> lkji -> ljki -> ljik
    norb = dm3.shape[0]
    for i in range(norb):
        for k in range(i+1):
            for j in range(k+1):
                for l in range(j+1):
                    tmp = chain(dm4[i,:,j,:,k,:,l,:].copy(), i, j, k, l)
                    tmp = transpose01(tmp, i, k, j, l)
                    tmp = chain(tmp, k, i, j, l)
                    tmp = transpose01(dm4[i,:,j,:,k,:,l,:].copy(), i, j, k, l)
                    tmp = chain(tmp, j, i, k, l)
                    tmp = transpose01(dm4[i,:,l,:,j,:,k,:].copy(), i, l, j, k)
                    tmp = chain(tmp, l, i, j, k)
    return dm4

# <p^+ q r^+ s t^+ u> => <p^+ r^+ t^+ u s q>
# rdm2 is the (reordered) standard 2-pdm
def reorder_rdm3(rdm1, rdm2, rdm3, inplace=True):
    if not inplace:
        rdm3 = rdm3.copy()
    norb = rdm1.shape[0]
    for p in range(norb):
        for q in range(norb):
            for s in range(norb):
                rdm3[p,q,q,s] += -rdm2[p,s]
            for u in range(norb):
                rdm3[p,q,:,:,q,u] += -rdm2[p,u]
            for s in range(norb):
                rdm3[p,q,:,s,s,:] += -rdm2[p,q]
    for q in range(norb):
        for s in range(norb):
            rdm3[:,q,q,s,s,:] += -rdm1
    return rdm3

# <p^+ q r^+ s t^+ u w^+ v> => <p^+ r^+ t^+ w^+ v u s q>
# rdm2, rdm3 are the (reordered) standard 2-pdm and 3-pdm
def reorder_rdm4(rdm1, rdm2, rdm3, rdm4, inplace=True):
    raise RuntimeError('TODO')

