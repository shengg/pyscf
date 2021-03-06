#!/usr/bin/env python
#
# Author: Qiming Sun <osirpt.sun@gmail.com>
#

'''
Dirac Hartree-Fock
'''

import ctypes
import _ctypes
import time
from functools import reduce
import numpy
import scipy.linalg
import pyscf.lib
import pyscf.lib.logger as log
from pyscf.lib import logger
from pyscf.scf import hf
from pyscf.scf import diis
from pyscf.scf import chkfile
from pyscf.scf import _vhf


def kernel(mf, conv_tol=1e-9, dump_chk=True, dm0=None):
    '''the modified SCF kernel for Dirac-Hartree-Fock.  In this kernel, the
    SCF is carried out in three steps.  First the 2-electron part is
    approximated by large component integrals (LL|LL); Next, (SS|LL) the
    interaction between large and small components are added; Finally,
    converge the SCF with the small component contributions (SS|SS)
    '''
    mol = mf.mol
    if dm0 is None:
        dm = mf.get_init_guess()
    else:
        dm = dm0

    if dm0 is None and mf._coulomb_now.upper() == 'LLLL':
        scf_conv, hf_energy, mo_energy, mo_coeff, mo_occ \
                = hf.kernel(mf, 4e-3, dump_chk, dm0=dm)
        dm = mf.make_rdm1(mo_coeff, mo_occ)
        mf._coulomb_now = 'SSLL'

    if dm0 is None and (mf._coulomb_now.upper() == 'SSLL' \
                         or mf._coulomb_now.upper() == 'LLSS'):
        scf_conv, hf_energy, mo_energy, mo_coeff, mo_occ \
                = hf.kernel(mf, 4e-4, dump_chk, dm0=dm)
        dm = mf.make_rdm1(mo_coeff, mo_occ)
        mf._coulomb_now = 'SSSS'

    if mf.with_ssss:
        mf._coulomb_now = 'SSSS'
    else:
        mf._coulomb_now = 'SSLL'

    if mf.with_gaunt:
        mf.get_veff = mf.get_vhf_with_gaunt

    return hf.kernel(mf, conv_tol, dump_chk, dm0=dm)

def get_jk_coulomb(mol, dm, hermi=1, coulomb_allow='SSSS',
                   opt_llll=None, opt_ssll=None, opt_ssss=None):
    if coulomb_allow.upper() == 'LLLL':
        log.info(mol, 'Coulomb integral: (LL|LL)')
        j1, k1 = _call_veff_llll(mol, dm, hermi, opt_llll)
        n2c = j1.shape[1]
        vj = numpy.zeros_like(dm)
        vk = numpy.zeros_like(dm)
        vj[...,:n2c,:n2c] = j1
        vk[...,:n2c,:n2c] = k1
    elif coulomb_allow.upper() == 'SSLL' \
      or coulomb_allow.upper() == 'LLSS':
        log.info(mol, 'Coulomb integral: (LL|LL) + (SS|LL)')
        vj, vk = _call_veff_ssll(mol, dm, hermi, opt_ssll)
        j1, k1 = _call_veff_llll(mol, dm, hermi, opt_llll)
        n2c = j1.shape[1]
        vj[...,:n2c,:n2c] += j1
        vk[...,:n2c,:n2c] += k1
    else: # coulomb_allow == 'SSSS'
        log.info(mol, 'Coulomb integral: (LL|LL) + (SS|LL) + (SS|SS)')
        vj, vk = _call_veff_ssll(mol, dm, hermi, opt_ssll)
        j1, k1 = _call_veff_llll(mol, dm, hermi, opt_llll)
        n2c = j1.shape[1]
        vj[...,:n2c,:n2c] += j1
        vk[...,:n2c,:n2c] += k1
        j1, k1 = _call_veff_ssss(mol, dm, hermi, opt_ssss)
        vj[...,n2c:,n2c:] += j1
        vk[...,n2c:,n2c:] += k1
    return vj, vk

def get_jk(mol, dm, hermi=1, coulomb_allow='SSSS'):
    return get_jk_coulomb(mol, dm, hermi=hermi, coulomb_allow=coulomb_allow)


def get_hcore(mol):
    n2c = mol.nao_2c()
    n4c = n2c * 2
    c = mol.light_speed

    s  = mol.intor_symmetric('cint1e_ovlp')
    t  = mol.intor_symmetric('cint1e_spsp') * .5
    vn = mol.intor_symmetric('cint1e_nuc')
    wn = mol.intor_symmetric('cint1e_spnucsp')
    h1e = numpy.empty((n4c, n4c), numpy.complex)
    h1e[:n2c,:n2c] = vn
    h1e[n2c:,:n2c] = t
    h1e[:n2c,n2c:] = t
    h1e[n2c:,n2c:] = wn * (.25/c**2) - t
    return h1e

def get_ovlp(mol):
    n2c = mol.nao_2c()
    n4c = n2c * 2
    c = mol.light_speed

    s = mol.intor_symmetric('cint1e_ovlp')
    t = mol.intor_symmetric('cint1e_spsp') * .5
    s1e = numpy.zeros((n4c, n4c), numpy.complex)
    s1e[:n2c,:n2c] = s
    s1e[n2c:,n2c:] = t * (.5/c**2)
    return s1e

def make_rdm1(mo_coeff, mo_occ):
    return numpy.dot(mo_coeff*mo_occ, mo_coeff.T.conj())

def init_guess_by_minao(mol):
    '''Initial guess in terms of the overlap to minimal basis.'''
    dm = hf.init_guess_by_minao(mol)
    return _proj_dmll(mol, dm, mol)

def init_guess_by_1e(mol):
    '''Initial guess from one electron system.'''
    mf = UHF(mol)
    return mf.init_guess_by_1e(mol)

def init_guess_by_atom(mol):
    '''Initial guess from atom calculation.'''
    dm = hf.init_guess_by_atom(mol)
    return _proj_dmll(mol, dm, mol)

def init_guess_by_chkfile(mol, chkfile_name, project=True):
    from pyscf.scf import addons
    chk_mol, scf_rec = chkfile.load_scf(chkfile_name)

    if numpy.iscomplexobj(scf_rec['mo_coeff']):
        mo = scf_rec['mo_coeff']
        mo_occ = scf_rec['mo_occ']
        if project:
            dm = make_rdm1(addons.project_mo_r2r(chk_mol, mo, mol), mo_occ)
        else:
            dm = make_rdm1(mo, mo_occ)
    else:
        if scf_rec['mo_coeff'].ndim == 2: # nr-RHF
            mo = scf_rec['mo_coeff']
            mo_occ = scf_rec['mo_occ']
            dm = reduce(numpy.dot, (mo*mo_occ, mo.T))
        else: # nr-UHF
            mo = scf_rec['mo_coeff']
            mo_occ = scf_rec['mo_occ']
            dm = reduce(numpy.dot, (mo[0]*mo_occ[0], mo[0].T)) \
               + reduce(numpy.dot, (mo[1]*mo_occ[1], mo[1].T))
        dm = _proj_dmll(chk_mol, dm, mol)
    return dm

def get_init_guess(mol, key='minao'):
    if callable(key):
        return key(mol)
    elif key.lower() == '1e':
        return init_guess_by_1e(mol)
    elif key.lower() == 'atom':
        return init_guess_by_atom(mol)
    elif key.lower() == 'chkfile':
        raise RuntimeError('Call pyscf.scf.hf.init_guess_by_chkfile instead')
    else:
        return init_guess_by_minao(mol)

def time_reversal_matrix(mol, mat):
    n2c = mol.nao_2c()
    tao = mol.time_reversal_map()
    # tao(i) = -j  means  T(f_i) = -f_j
    # tao(i) =  j  means  T(f_i) =  f_j
    taoL = numpy.array([abs(x)-1 for x in tao]) # -1 to fit C-array
    idx = numpy.hstack((taoL, taoL+n2c))
    signL = list(map(lambda x: 1 if x>0 else -1, tao))
    sign = numpy.hstack((signL, signL))

    tmat = numpy.empty_like(mat)
    for j in range(mat.__len__()):
        for i in range(mat.__len__()):
            tmat[idx[i],idx[j]] = mat[i,j] * sign[i]*sign[j]
    return tmat.conjugate()

def analyze(mf, verbose=logger.DEBUG):
    from pyscf.tools import dump_mat
    mo_energy = mf.mo_energy
    mo_occ = mf.mo_occ
    mo_coeff = mf.mo_coeff
    log = logger.Logger(mf.stdout, verbose)
    log.info('**** MO energy ****')
    for i in range(len(mo_energy)):
        if mo_occ[i] > 0:
            log.info('occupied MO #%d energy= %.15g occ= %g', \
                     i+1, mo_energy[i], mo_occ[i])
        else:
            log.info('virtual MO #%d energy= %.15g occ= %g', \
                     i+1, mo_energy[i], mo_occ[i])
#TODO    if mf.verbose >= logger.DEBUG:
#TODO        log.debug(' ** MO coefficients **')
#TODO        label = ['%d%3s %s%-4s' % x for x in mf.mol.spheric_labels()]
#TODO        dump_mat.dump_rec(mf.stdout, mo_coeff, label, start=1)
#TODO    dm = mf.make_rdm1(mo_coeff, mo_occ)
#TODO    return mf.mulliken_pop(mf.mol, dm, mf.get_ovlp(), log)


class UHF(hf.SCF):
    __doc__ = hf.SCF.__doc__ + '''
    Attributes for Dirac-Hartree-Fock
        with_ssss : bool, for Dirac-Hartree-Fock only
            If False, ignore small component integrals (SS|SS).  Default is True.
        with_gaunt : bool, for Dirac-Hartree-Fock only
            If False, ignore Gaunt interaction.  Default is False.

    Examples:

    >>> mol = gto.M(atom='H 0 0 0; H 0 0 1', basis='ccpvdz', verbose=0)
    >>> mf = scf.RHF(mol)
    >>> e0 = mf.scf()
    >>> mf = scf.DHF(mol)
    >>> e1 = mf.scf()
    >>> print('Relativistic effects = %.12f' % (e1-e0))
    Relativistic effects = -0.000008854205
    '''
    def __init__(self, mol):
        hf.SCF.__init__(self, mol)
        self.conv_tol = 1e-8
        self.with_ssss = True
        self._coulomb_now = 'LLLL' # 'SSSS' ~ LLLL+LLSS+SSSS
        self.with_gaunt = False

        self.opt_llll = None
        self.opt_ssll = None
        self.opt_ssss = None
        self._keys = set(self.__dict__.keys())

    def eig(self, h, s):
        e, c = scipy.linalg.eigh(h, s)
        idx = numpy.argmax(abs(c.real), axis=0)
        c[:,c[idx,range(len(e))].real<0] *= -1
        return e, c
        #try:
        #    import pyscf.lib.jacobi
        #    return pyscf.lib.jacobi.zgeeigen(h, s)[:2]
        #except ImportError:
        #    e, c = scipy.linalg.eigh(h, s)
        #    return e, c

    def get_fock(self, h1e, s1e, vhf, dm, cycle=-1, adiis=None):
        f = h1e + vhf
        if 0 <= cycle < self.diis_start_cycle-1:
            f = hf.damping(s1e, dm, f, self.damp_factor)
            f = hf.level_shift(s1e, dm, f, self.level_shift_factor)
        elif 0 <= cycle:
            fac = self.level_shift_factor \
                    * numpy.exp(self.diis_start_cycle-cycle-1)
            f = hf.level_shift(s1e, dm, f, fac)
        if adiis is not None and cycle >= self.diis_start_cycle:
            f = adiis.update(s1e, dm, f)
        return f

    def get_hcore(self, mol=None):
        if mol is None:
            mol = self.mol
        return get_hcore(mol)

    def get_ovlp(self, mol=None):
        if mol is None:
            mol = self.mol
        return get_ovlp(mol)

    def init_guess_by_minao(self, mol=None):
        '''Initial guess in terms of the overlap to minimal basis.'''
        if mol is None: mol = self.mol
        return init_guess_by_minao(mol)

    def init_guess_by_atom(self, mol=None):
        if mol is None: mol = self.mol
        return init_guess_by_atom(mol)

    def init_guess_by_chkfile(self, mol=None, chkfile=None, project=True):
        if mol is None: mol = self.mol
        if chkfile is None: chkfile = self.chkfile
        return init_guess_by_chkfile(mol, chkfile, project=project)

    def build_(self, mol=None):
        if mol is None: mol = self.mol
        mol.check_sanity(self)

        if self.direct_scf:
            def set_vkscreen(opt, name):
                opt._this.contents.r_vkscreen = \
                    ctypes.c_void_p(_ctypes.dlsym(_vhf.libcvhf._handle, name))
            self.opt_llll = _vhf.VHFOpt(mol, 'cint2e', 'CVHFrkbllll_prescreen',
                                        'CVHFrkbllll_direct_scf',
                                        'CVHFrkbllll_direct_scf_dm')
            self.opt_llll.direct_scf_tol = self.direct_scf_tol
            set_vkscreen(self.opt_llll, 'CVHFrkbllll_vkscreen')
            self.opt_ssss = _vhf.VHFOpt(mol, 'cint2e_spsp1spsp2',
                                        'CVHFrkbllll_prescreen',
                                        'CVHFrkbssss_direct_scf',
                                        'CVHFrkbssss_direct_scf_dm')
            self.opt_ssss.direct_scf_tol = self.direct_scf_tol
            set_vkscreen(self.opt_ssss, 'CVHFrkbllll_vkscreen')
            self.opt_ssll = _vhf.VHFOpt(mol, 'cint2e_spsp1',
                                        'CVHFrkbssll_prescreen',
                                        'CVHFrkbssll_direct_scf',
                                        'CVHFrkbssll_direct_scf_dm')
            self.opt_ssll.direct_scf_tol = self.direct_scf_tol
            set_vkscreen(self.opt_ssll, 'CVHFrkbssll_vkscreen')

    def get_occ(self, mo_energy=None, mo_coeff=None):
        if mo_energy is None: mo_energy = self.mo_energy
        mol = self.mol
        n4c = mo_energy.size
        n2c = n4c // 2
        c = mol.light_speed
        mo_occ = numpy.zeros(n2c * 2)
        if mo_energy[n2c] > -1.999 * mol.light_speed**2:
            mo_occ[n2c:n2c+mol.nelectron] = 1
        else:
            n = 0
            for i, e in enumerate(mo_energy):
                if e > -1.999 * mol.light_speed**2 and n < mol.nelectron:
                    mo_occ[i] = 1
                    n += 1
        if self.verbose >= log.INFO:
            log.info(self, 'HOMO %d = %.12g, LUMO %d = %.12g,', \
                     n2c+mol.nelectron, mo_energy[n2c+mol.nelectron-1], \
                     n2c+mol.nelectron+1, mo_energy[n2c+mol.nelectron])
            log.debug(self, 'NES  mo_energy = %s', mo_energy[:n2c])
            log.debug(self, 'PES  mo_energy = %s', mo_energy[n2c:])
        return mo_occ

    # full density matrix for UHF
    def make_rdm1(self, mo_coeff=None, mo_occ=None):
        if mo_coeff is None: mo_coeff = self.mo_coeff
        if mo_occ is None: mo_occ = self.mo_occ
        return make_rdm1(mo_coeff, mo_occ)

#TODO    def get_gaunt_vj_vk(self, mol, dm):
#TODO        '''Dirac-Coulomb-Gaunt'''
#TODO        import pyscf.lib.pycint as pycint
#TODO        log.info(self, 'integral for Gaunt term')
#TODO        vj, vk = hf.get_vj_vk(pycint.rkb_vhf_gaunt, mol, dm)
#TODO        return -vj, -vk
#TODO
#TODO    def get_gaunt_vj_vk_screen(self, mol, dm):
#TODO        '''Dirac-Coulomb-Gaunt'''
#TODO        import pyscf.lib.pycint as pycint
#TODO        log.info(self, 'integral for Gaunt term')
#TODO        vj, vk = hf.get_vj_vk(pycint.rkb_vhf_gaunt_direct, mol, dm)
#TODO        return -vj, -vk

    def get_jk(self, mol=None, dm=None, hermi=1):
        if mol is None: mol = self.mol
        if dm is None: dm = self.make_rdm1()
        t0 = (time.clock(), time.time())
        verbose_bak, mol.verbose = mol.verbose, self.verbose
        stdout_bak,  mol.stdout  = mol.stdout , self.stdout
        vj, vk = get_jk_coulomb(mol, dm, hermi, self._coulomb_now,
                                self.opt_llll, self.opt_ssll, self.opt_ssss)
        mol.verbose = verbose_bak
        mol.stdout  = stdout_bak
        log.timer(self, 'vj and vk', *t0)
        return vj, vk

    def get_veff(self, mol=None, dm=None, dm_last=0, vhf_last=0, hermi=1):
        '''Dirac-Coulomb'''
        if mol is None: mol = self.mol
        if dm is None: dm = self.make_rdm1()
        if self.direct_scf:
            ddm = numpy.array(dm, copy=False) - numpy.array(dm_last, copy=False)
            vj, vk = self.get_jk(mol, ddm, hermi=hermi)
            return numpy.array(vhf_last, copy=False) + vj - vk
        else:
            vj, vk = self.get_jk(mol, dm, hermi=hermi)
            return vj - vk

#TODO    def get_veff_with_gaunt(self, mol, dm, dm_last=0, vhf_last=0):
#TODO        if self.direct_scf:
#TODO            ddm = dm - dm_last
#TODO            vj, vk = self.get_coulomb_vj_vk(mol, ddm, self._coulomb_now)
#TODO            vj1, vk1 = self.get_gaunt_vj_vk_screen(mol, ddm)
#TODO            return vhf_last + vj0 + vj1 - vk0 - vk1
#TODO        else:
#TODO            vj, vk = self.get_coulomb_vj_vk(mol, dm, self._coulomb_now)
#TODO            vj1, vk1 = self.get_gaunt_vj_vk(mol, dm)
#TODO            return vj0 + vj1 - vk0 - vk1

    def scf(self, dm0=None):
        cput0 = (time.clock(), time.time())

        self.build()
        self.dump_flags()
        self.converged, self.hf_energy, \
                self.mo_energy, self.mo_coeff, self.mo_occ \
                = kernel(self, self.conv_tol, dm0=dm0)

        log.timer(self, 'SCF', *cput0)
        self.dump_energy(self.hf_energy, self.converged)
        #if self.verbose >= logger.INFO:
        #    self.analyze(self.verbose)
        return self.hf_energy

    def analyze(self, verbose=logger.DEBUG):
        return analyze(self, verbose)

class HF1e(UHF):
    def scf(self, *args):
        log.info(self, '\n')
        log.info(self, '******** 1 electron system ********')
        self.converged = True
        h1e = self.get_hcore(self.mol)
        s1e = self.get_ovlp(self.mol)
        self.mo_energy, self.mo_coeff = self.eig(h1e, s1e)
        self.mo_occ = numpy.zeros_like(self.mo_energy)
        n2c = self.mo_occ.size // 2
        self.mo_occ[n2c] = 1
        self.hf_energy = self.mo_energy[n2c] + self.mol.energy_nuc()
        return self.hf_energy

class RHF(UHF):
    '''Dirac-RHF'''
    def __init__(self, mol):
        if mol.nelectron.__mod__(2) != 0:
            raise ValueError('Invalid electron number %i.' % mol.nelectron)
        UHF.__init__(self, mol)

    # full density matrix for RHF
    def make_rdm1(self, mo_coeff=None, mo_occ=None):
        '''D/2 = \psi_i^\dag\psi_i = \psi_{Ti}^\dag\psi_{Ti}
        D(UHF) = \psi_i^\dag\psi_i + \psi_{Ti}^\dag\psi_{Ti}
        RHF average the density of spin up and spin down:
        D(RHF) = (D(UHF) + T[D(UHF)])/2
        '''
        if mo_coeff is None: mo_coeff = self.mo_coeff
        if mo_occ is None: mo_occ = self.mo_occ
        dm = make_rdm1(mo_coeff, mo_occ)
        return (dm + time_reversal_matrix(self.mol, dm)) * .5

    def get_occ(self, mo_energy=None, mo_coeff=None):
        if mo_energy is None: mo_energy = self.mo_energy
        mol = self.mol
        n4c = mo_energy.size
        n2c = n4c // 2
        c = mol.light_speed
        mo_occ = numpy.zeros(n2c * 2)
        if mo_energy[n2c] > -1.999 * mol.light_speed**2:
            mo_occ[n2c:n2c+mol.nelectron] = 1
        else:
            n = 0
            for i, e in enumerate(mo_energy):
                if e > -1.999 * mol.light_speed**2 and n < mol.nelectron:
                    mo_occ[i] = 1
                    n += 1
        if self.verbose >= log.INFO:
            log.info(self, 'HOMO %d = %.12g, LUMO %d = %.12g,', \
                     (n2c+mol.nelectron)//2, mo_energy[n2c+mol.nelectron-1], \
                     (n2c+mol.nelectron)//2+1, mo_energy[n2c+mol.nelectron])
            log.debug(self, 'NES  mo_energy = %s', mo_energy[:n2c])
            log.debug(self, 'PES  mo_energy = %s', mo_energy[n2c:])
        return mo_occ


def _jk_triu_(vj, vk, hermi):
    if hermi == 0:
        if vj.ndim == 2:
            vj = pyscf.lib.hermi_triu(vj, 1)
        else:
            for i in range(vj.shape[0]):
                vj[i] = pyscf.lib.hermi_triu(vj[i], 1)
    else:
        if vj.ndim == 2:
            vj = pyscf.lib.hermi_triu(vj, hermi)
            vk = pyscf.lib.hermi_triu(vk, hermi)
        else:
            for i in range(vj.shape[0]):
                vj[i] = pyscf.lib.hermi_triu(vj[i], hermi)
                vk[i] = pyscf.lib.hermi_triu(vk[i], hermi)
    return vj, vk


def _call_veff_llll(mol, dm, hermi=1, mf_opt=None):
    if isinstance(dm, numpy.ndarray) and dm.ndim == 2:
        n2c = dm.shape[0] // 2
        dms = dm[:n2c,:n2c].copy()
    else:
        n2c = dm[0].shape[0] // 2
        dms = []
        for dmi in dm:
            dms.append(dmi[:n2c,:n2c].copy())
    vj, vk = _vhf.rdirect_mapdm('cint2e', 's8',
                                ('ji->s2kl', 'jk->s1il'), dms, 1,
                                mol._atm, mol._bas, mol._env, mf_opt)
    return _jk_triu_(vj, vk, hermi)

def _call_veff_ssll(mol, dm, hermi=1, mf_opt=None):
    if isinstance(dm, numpy.ndarray) and dm.ndim == 2:
        n_dm = 1
        n2c = dm.shape[0] // 2
        dmll = dm[:n2c,:n2c].copy()
        dmsl = dm[n2c:,:n2c].copy()
        dmss = dm[n2c:,n2c:].copy()
        dms = (dmll, dmss, dmsl)
    else:
        n_dm = len(dm)
        n2c = dm[0].shape[0] // 2
        dms = []
        for dmi in dm:
            dms.append(dmi[:n2c,:n2c].copy())
        for dmi in dm:
            dms.append(dmi[n2c:,n2c:].copy())
        for dmi in dm:
            dms.append(dmi[n2c:,:n2c].copy())
    jks = ('lk->s2ij',) * n_dm \
        + ('ji->s2kl',) * n_dm \
        + ('jk->s1il',) * n_dm
    c1 = .5/mol.light_speed
    vx = _vhf.rdirect_bindm('cint2e_spsp1', 's4', jks, dms, 1,
                            mol._atm, mol._bas, mol._env, mf_opt) * c1**2
    vj = numpy.zeros((n_dm,n2c*2,n2c*2), dtype=numpy.complex)
    vk = numpy.zeros((n_dm,n2c*2,n2c*2), dtype=numpy.complex)
    vj[:,n2c:,n2c:] = vx[      :n_dm  ,:,:]
    vj[:,:n2c,:n2c] = vx[n_dm  :n_dm*2,:,:]
    vk[:,n2c:,:n2c] = vx[n_dm*2:      ,:,:]
    if n_dm == 1:
        vj = vj.reshape(vj.shape[1:])
        vk = vk.reshape(vk.shape[1:])
    return _jk_triu_(vj, vk, hermi)

def _call_veff_ssss(mol, dm, hermi=1, mf_opt=None):
    c1 = .5/mol.light_speed
    if isinstance(dm, numpy.ndarray) and dm.ndim == 2:
        n2c = dm.shape[0] // 2
        dms = dm[n2c:,n2c:].copy()
    else:
        n2c = dm[0].shape[0] // 2
        dms = []
        for dmi in dm:
            dms.append(dmi[n2c:,n2c:].copy())
    vj, vk = _vhf.rdirect_mapdm('cint2e_spsp1spsp2', 's8',
                                ('ji->s2kl', 'jk->s1il'), dms, 1,
                                mol._atm, mol._bas, mol._env, mf_opt) * c1**4
    return _jk_triu_(vj, vk, hermi)

def _proj_dmll(mol_nr, dm_nr, mol):
    from pyscf.scf import addons
    proj = addons.project_mo_nr2r(mol_nr, 1, mol)

    n2c = proj.shape[0]
    n4c = n2c * 2
    dm = numpy.zeros((n4c,n4c), dtype=complex)
    # *.5 because alpha and beta are summed in project_mo_nr2r
    dm_ll = reduce(numpy.dot, (proj, dm_nr*.5, proj.T.conj()))
    dm[:n2c,:n2c] = (dm_ll + time_reversal_matrix(mol, dm_ll)) * .5
    return dm


if __name__ == '__main__':
    import pyscf.gto
    mol = pyscf.gto.Mole()
    mol.verbose = 5
    mol.output = 'out_dhf'

    mol.atom.extend([['He', (0.,0.,0.)], ])
    mol.basis = {
        'He': [(0, 0, (1, 1)),
               (0, 0, (3, 1)),
               (1, 0, (1, 1)), ]}
    mol.build()

##############
# SCF result
    method = UHF(mol)
    energy = method.scf() #-2.38146942868
    print(energy)
