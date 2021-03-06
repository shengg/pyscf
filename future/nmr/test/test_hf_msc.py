#!/usr/bin/env python

import unittest
import numpy
from pyscf import gto
from pyscf import scf
from pyscf import nmr

mol = gto.Mole()
mol.verbose = 5
mol.output = '/dev/null'

mol.atom = [
    [1   , (0. , 0. , .917)],
    ["F" , (0. , 0. , 0.)], ]
#mol.nucmod = {"F":2, "H":2}
mol.basis = {"H": 'cc_pvdz',
             "F": 'cc_pvdz',}
mol.build()

nrhf = scf.RHF(mol)
nrhf.conv_tol = 1e-12
nrhf.scf()

rhf = scf.dhf.RHF(mol)
nrhf.conv_tol = 1e-12
rhf.scf()

def finger(mat):
    return abs(mat).sum()

class KnowValues(unittest.TestCase):
    def test_nr_common_gauge_ucpscf(self):
        m = nmr.hf.NMR(nrhf)
        m.cphf = False
        m.gauge_orig = (1,1,1)
        msc = m.shielding()
        self.assertAlmostEqual(finger(msc), 1636.7415677000859, 7)

    def test_nr_common_gauge_cpscf(self):
        m = nmr.hf.NMR(nrhf)
        m.cphf = True
        m.gauge_orig = (1,1,1)
        msc = m.shielding()
        self.assertAlmostEqual(finger(msc), 1562.3861950975397, 7)

    def test_nr_giao_ucpscf(self):
        m = nmr.hf.NMR(nrhf)
        m.cphf = False
        m.gauge_orig = None
        msc = m.shielding()
        self.assertAlmostEqual(finger(msc), 1488.0951043100554, 7)

    def test_nr_giao_cpscf(self):
        m = nmr.hf.NMR(nrhf)
        m.cphf = True
        m.gauge_orig = None
        msc = m.shielding()
        self.assertAlmostEqual(finger(msc), 1358.9828057660634, 7)

    def test_rmb_common_gauge_ucpscf(self):
        m = nmr.dhf.NMR(rhf)
        m.cphf = False
        m.gauge_orig = (1,1,1)
        msc = m.shielding()
        self.assertAlmostEqual(finger(msc), 1642.1875348839881, 6)

    def test_rmb_common_gauge_cpscf(self):
        m = nmr.dhf.NMR(rhf)
        m.cphf = True
        m.gauge_orig = (1,1,1)
        msc = m.shielding()
        self.assertAlmostEqual(finger(msc), 1569.0408649904268, 6)

    def test_rmb_giao_ucpscf(self):
        m = nmr.dhf.NMR(rhf)
        m.cphf = False
        m.gauge_orig = None
        msc = m.shielding()
        self.assertAlmostEqual(finger(msc), 1493.7232313499048, 6)

    def test_rmb_giao_cpscf(self):
        m = nmr.dhf.NMR(rhf)
        m.cphf = True
        m.gauge_orig = None
        msc = m.shielding()
        self.assertAlmostEqual(finger(msc), 1365.4686105975627, 6)

    def test_rkb_giao_cpscf(self):
        m = nmr.dhf.NMR(rhf)
        m.mb = 'RKB'
        m.cphf = True
        m.gauge_orig = None
        msc = m.shielding()
        self.assertAlmostEqual(finger(msc), 1923.9100429530872, 6)

    def test_rkb_common_gauge_cpscf(self):
        m = nmr.dhf.NMR(rhf)
        m.mb = 'RKB'
        m.cphf = True
        m.gauge_orig = (1,1,1)
        msc = m.shielding()
        self.assertAlmostEqual(finger(msc), 1980.1184526183633, 6)

    def test_make_h10(self):
        numpy.random.seed(1)
        nao = mol.nao_nr()
        dm0 = numpy.random.random((nao,nao))
        dm0 = dm0 + dm0.T
        h1 = nmr.hf.make_h10(mol, dm0)
        self.assertAlmostEqual(numpy.linalg.norm(h1), 14.8641461638, 8)
        h1 = nmr.hf.make_h10(mol, dm0, gauge_orig=(0,0,0))
        self.assertAlmostEqual(numpy.linalg.norm(h1), 3.61014387186, 8)
        h1 = nmr.dhf.make_h10(mol, rhf.make_rdm1())
        self.assertAlmostEqual(numpy.linalg.norm(h1), 13.261106469, 8)
        h1 = nmr.dhf.make_h10(mol, rhf.make_rdm1(), gauge_orig=(0,0,0), mb='RKB')
        self.assertAlmostEqual(numpy.linalg.norm(h1), 6.2623637195, 8)



if __name__ == "__main__":
    print("Full Tests of RHF-MSC DHF-MSC for HF")
    unittest.main()
    import sys; sys.exit()
