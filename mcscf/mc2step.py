#!/usr/bin/env python
#
# Author: Qiming Sun <osirpt.sun@gmail.com>
#

import time
import numpy
import scipy.linalg
import pyscf.lib.logger as logger
import pyscf.scf
from pyscf.mcscf import mc1step

def kernel(casscf, mo_coeff, tol=1e-7, macro=30, micro=8, \
           ci0=None, verbose=None, **cikwargs):
    if verbose is None:
        verbose = casscf.verbose
    log = logger.Logger(casscf.stdout, verbose)
    cput0 = (time.clock(), time.time())
    log.debug('Start 2-step CASSCF')

    mo = mo_coeff
    nmo = mo.shape[1]
    ncore = casscf.ncore
    ncas = casscf.ncas
    nocc = ncore + ncas
    eris = casscf.update_ao2mo(mo)
    e_tot, e_ci, fcivec = casscf.casci(mo, ci0, eris, **cikwargs)
    log.info('CASCI E = %.15g', e_tot)
    if ncas == nmo:
        return e_tot, e_ci, fcivec, mo
    elast = e_tot
    conv = False
    toloose = casscf.conv_tol_grad
    totmicro = totinner = 0
    casdm1 = 0

    t2m = t1m = log.timer('Initializing 2-step CASSCF', *cput0)
    for imacro in range(macro):
        ninner = 0
        t3m = t2m
        casdm1_old = casdm1
        for imicro in range(micro):

            casdm1, casdm2 = \
                    casscf.fcisolver.make_rdm12(fcivec, ncas, casscf.nelecas)
            norm_dm1 = numpy.linalg.norm(casdm1 - casdm1_old)
            t3m = log.timer('update CAS DM', *t3m)
            u, dx, g_orb, nin = casscf.rotate_orb(mo, casdm1, casdm2, eris, 0)
            ninner += nin
            norm_t = numpy.linalg.norm(u-numpy.eye(nmo))
            norm_gorb = numpy.linalg.norm(g_orb)
            t3m = log.timer('orbital rotation', *t3m)

            if norm_t < toloose or norm_gorb < toloose:
                if casscf.natorb:
                    natocc, natorb = scipy.linalg.eigh(-casdm1)
                    u[:,ncore:nocc] = numpy.dot(u[:,ncore:nocc], natorb)
                    log.debug1('natural occ = %s', str(natocc))
            mo = numpy.dot(mo, u)
            casscf.save_mo_coeff(mo, imacro, imicro)

            eris = None # to avoid using too much memory
            eris = casscf.update_ao2mo(mo)
            t3m = log.timer('update eri', *t3m)

            log.debug('micro %d, |u-1|=%4.3g, |g[o]|=%4.3g, |dm1|=%4.3g', \
                      imicro, norm_t, norm_gorb, norm_dm1)
            t2m = log.timer('micro iter %d'%imicro, *t2m)
            if norm_t < toloose or norm_gorb < toloose or norm_dm1 < toloose:
                break

        totinner += ninner
        totmicro += imicro+1

        e_tot, e_ci, fcivec = casscf.casci(mo, fcivec, eris, **cikwargs)
        log.info('macro iter %d (%d ah, %d micro), CASSCF E = %.15g, dE = %.8g,',
                 imacro, ninner, imicro+1, e_tot, e_tot-elast)
        log.info('               |grad[o]|=%4.3g, |dm1|=%4.3g',
                 norm_gorb, norm_dm1)
        log.timer('CASCI solver', *t3m)
        t2m = t1m = log.timer('macro iter %d'%imacro, *t1m)

        if (abs(elast - e_tot) < tol and
            norm_gorb < toloose and norm_dm1 < toloose):
            conv = True
            break
        else:
            elast = e_tot

    if conv:
        log.info('2-step CASSCF converged in %d macro (%d ah %d micro) steps',
                 imacro+1, totinner, totmicro)
    else:
        log.info('2-step CASSCF not converged, %d macro (%d ah %d micro) steps',
                 imacro+1, totinner, totmicro)
    log.note('2-step CASSCF, energy = %.15g', e_tot)
    log.timer('2-step CASSCF', *cput0)
    return conv, e_tot, e_ci, fcivec, mo



if __name__ == '__main__':
    from pyscf import gto
    from pyscf import scf

    mol = gto.Mole()
    mol.verbose = 0
    mol.output = None#"out_h2o"
    mol.atom = [
        ['H', ( 1.,-1.    , 0.   )],
        ['H', ( 0.,-1.    ,-1.   )],
        ['H', ( 1.,-0.5   ,-1.   )],
        ['H', ( 0.,-0.5   ,-1.   )],
        ['H', ( 0.,-0.5   ,-0.   )],
        ['H', ( 0.,-0.    ,-1.   )],
        ['H', ( 1.,-0.5   , 0.   )],
        ['H', ( 0., 1.    , 1.   )],
    ]

    mol.basis = {'H': 'sto-3g',
                 'O': '6-31g',}
    mol.build()

    m = scf.RHF(mol)
    ehf = m.scf()
    emc = kernel(mc1step.CASSCF(m, 4, 4), m.mo_coeff, verbose=4)[1]
    print(ehf, emc, emc-ehf)
    print(emc - -3.22013929407)


    mol.atom = [
        ['O', ( 0., 0.    , 0.   )],
        ['H', ( 0., -0.757, 0.587)],
        ['H', ( 0., 0.757 , 0.587)],]
    mol.basis = {'H': 'cc-pvdz',
                 'O': 'cc-pvdz',}
    mol.build()

    m = scf.RHF(mol)
    ehf = m.scf()
    mc = mc1step.CASSCF(m, 6, 4)
    mc.verbose = 4
    mo = m.mo_coeff.copy()
    mo[:,2:5] = m.mo_coeff[:,[4,2,3]]
    emc = mc.mc2step(mo)[0]
    print(ehf, emc, emc-ehf)
    #-76.0267656731 -76.0873922924 -0.0606266193028
    print(emc - -76.0873923174, emc - -76.0926176464)

