#
# Author: Qiming Sun <osirpt.sun@gmail.com>
#

import unittest
import numpy
from functools import reduce
from pyscf import gto
from pyscf import symm
from pyscf.symm import geom


numpy.random.seed(12)
u = numpy.random.random((3,3))
u = numpy.linalg.svd(u)[0]
class KnowValues(unittest.TestCase):
    def test_d5h(self):
        atoms = ringhat(5, u)
        atoms = atoms[5:]
        gpname, orig, axes = geom.detect_symm(atoms)
        self.assertEqual(gpname, 'D5h')

        gpname, axes = geom.subgroup(gpname, axes)
        atoms = geom.shift_atom(atoms, orig, axes)
        self.assertEqual(gpname, 'C2v')
        self.assertTrue(geom.check_given_symm('C2v', atoms))
        self.assertEqual(geom.symm_identical_atoms(gpname, atoms),
                         [[0],[1,4],[2,3],[5,6]])

        atoms = ringhat(5, u)
        atoms = atoms[5:]
        atoms[1][0] = 'C1'
        gpname, orig, axes = geom.detect_symm(atoms, {'C':'ccpvdz','C1':'sto3g','N':'631g'})
        self.assertEqual(gpname, 'C2v')

        gpname, axes = geom.subgroup(gpname, axes)
        atoms = geom.shift_atom(atoms, orig, axes)
        self.assertEqual(gpname, 'C2v')
        self.assertTrue(geom.check_given_symm('C2v', atoms))
        self.assertEqual(geom.symm_identical_atoms(gpname, atoms),
                         [[0,2],[1],[3,4],[5,6]])

    def test_d6h(self):
        atoms = ringhat(6, u)
        atoms = atoms[6:]
        gpname, orig, axes = geom.detect_symm(atoms)
        self.assertEqual(gpname, 'D6h')
        gpname, axes = geom.subgroup(gpname, axes)
        atoms = geom.shift_atom(atoms, orig, axes)
        self.assertEqual(geom.symm_identical_atoms(gpname, atoms),
                         [[0,3],[1,2,4,5],[6,7]])
        self.assertTrue(geom.check_given_symm('D2h', atoms))

    def test_c5h(self):
        atoms = ringhat(5, u)
        gpname, orig, axes = geom.detect_symm(atoms)
        self.assertEqual(gpname, 'C5h')

        gpname, axes = geom.subgroup(gpname, axes)
        atoms = geom.shift_atom(atoms, orig, axes)
        self.assertEqual(gpname, 'Cs')
        self.assertTrue(geom.check_given_symm('Cs', atoms))
        self.assertEqual(geom.symm_identical_atoms(gpname, atoms),
                         [[0], [1], [2], [3], [4], [5], [6], [7], [8], [9], [10,11]])

    def test_c5(self):
        atoms = ringhat(5, u)[:-1]
        gpname, orig, axes = geom.detect_symm(atoms)
        self.assertEqual(gpname, 'C5')
        gpname, axes = geom.subgroup(gpname, axes)
        self.assertEqual(gpname, 'C1')

    def test_c5v(self):
        atoms = ringhat(5, u)[5:-1]
        gpname, orig, axes = geom.detect_symm(atoms)
        self.assertEqual(gpname, 'C5v')

        gpname, axes = geom.subgroup(gpname, axes)
        atoms = geom.shift_atom(atoms, orig, axes)
        self.assertEqual(gpname, 'Cs')
        self.assertTrue(geom.check_given_symm('Cs', atoms))
        self.assertEqual(geom.symm_identical_atoms(gpname, atoms),
                         [[0, 1], [2, 4], [3], [5]])

    def test_ih1(self):
        coords = make60(1.5, 1)
        atoms = [['C', c] for c in coords]
        gpname, orig, axes = geom.detect_symm(atoms)
        self.assertEqual(gpname, 'Ih')

        gpname, axes = geom.subgroup(gpname, axes)
        atoms = geom.shift_atom(atoms, orig, axes)
        self.assertEqual(gpname, 'Cs')
        self.assertTrue(geom.check_given_symm('Cs', atoms))
        self.assertEqual(geom.symm_identical_atoms(gpname, atoms),
                         [[0], [1, 4], [2, 3], [5], [6, 9], [7, 8], [10, 25],
                          [11, 29], [12, 28], [13, 27], [14, 26], [15, 20],
                          [16, 24], [17, 23], [18, 22], [19, 21], [30],
                          [31, 34], [32, 33], [35, 50], [36, 54], [37, 53],
                          [38, 52], [39, 51], [40, 45], [41, 49], [42, 48],
                          [43, 47], [44, 46], [55], [56, 59], [57, 58]])

    def test_ih2(self):
        coords1 = make60(1.5, 3)
        coords2 = make20(1.1)
        atoms = [['C', c] for c in coords1] + [['C', c] for c in coords2]
        gpname, orig, axes = geom.detect_symm(atoms)
        self.assertEqual(gpname, 'Ih')

        gpname, axes = geom.subgroup(gpname, axes)
        atoms = geom.shift_atom(atoms, orig, axes)
        self.assertEqual(gpname, 'Cs')
        self.assertTrue(geom.check_given_symm('Cs', atoms))

    def test_ih3(self):
        coords1 = make20(1.5)
        atoms = [['C', c] for c in coords1]
        gpname, orig, axes = geom.detect_symm(atoms)
        self.assertEqual(gpname, 'Ih')

        gpname, axes = geom.subgroup(gpname, axes)
        atoms = geom.shift_atom(atoms, orig, axes)
        self.assertEqual(gpname, 'Cs')
        self.assertTrue(geom.check_given_symm('Cs', atoms))

    def test_ih4(self):
        coords1 = make12(1.5)
        atoms = [['C', c] for c in coords1]
        gpname, orig, axes = geom.detect_symm(atoms)
        self.assertEqual(gpname, 'Ih')

        gpname, axes = geom.subgroup(gpname, axes)
        atoms = geom.shift_atom(atoms, orig, axes)
        self.assertEqual(gpname, 'Cs')
        self.assertTrue(geom.check_given_symm('Cs', atoms))

    def test_oh1(self):
        coords1 = make6(1.5)
        atoms = [['C', c] for c in coords1]
        gpname, orig, axes = geom.detect_symm(atoms)
        self.assertEqual(gpname, 'Oh')

        gpname, axes = geom.subgroup(gpname, axes)
        atoms = geom.shift_atom(atoms, orig, axes)
        self.assertEqual(gpname, 'D2h')
        self.assertTrue(geom.check_given_symm('D2h', atoms))

    def test_oh2(self):
        coords1 = make8(1.5)
        atoms = [['C', c] for c in coords1]
        gpname, orig, axes = geom.detect_symm(atoms)
        self.assertEqual(gpname, 'Oh')

        gpname, axes = geom.subgroup(gpname, axes)
        atoms = geom.shift_atom(atoms, orig, axes)
        self.assertEqual(gpname, 'D2h')
        self.assertTrue(geom.check_given_symm('D2h', atoms))

    def test_oh3(self):
        coords1 = make8(1.5)
        coords2 = make6(1.5)
        atoms = [['C', c] for c in coords1] + [['C', c] for c in coords2]
        gpname, orig, axes = geom.detect_symm(atoms)
        self.assertEqual(gpname, 'Oh')

        gpname, axes = geom.subgroup(gpname, axes)
        atoms = geom.shift_atom(atoms, orig, axes)
        self.assertEqual(gpname, 'D2h')
        self.assertTrue(geom.check_given_symm('D2h', atoms))

    def test_td1(self):
        coords1 = make4(1.5)
        atoms = [['C', c] for c in coords1]
        gpname, orig, axes = geom.detect_symm(atoms)
        self.assertEqual(gpname, 'Td')

        gpname, axes = geom.subgroup(gpname, axes)
        atoms = geom.shift_atom(atoms, orig, axes)
        self.assertEqual(gpname, 'C2v')
        self.assertTrue(geom.check_given_symm('C2v', atoms))
        self.assertEqual(geom.symm_identical_atoms(gpname, atoms),
                         [[0, 1], [2, 3]])

    def test_td2(self):
        coords1 = make4(1.5)
        coords2 = make4(1.9)
        atoms = [['C', c] for c in coords1] + [['C', c] for c in coords2]
        gpname, orig, axes = geom.detect_symm(atoms)
        self.assertEqual(gpname, 'Td')

        gpname, axes = geom.subgroup(gpname, axes)
        atoms = geom.shift_atom(atoms, orig, axes)
        self.assertEqual(gpname, 'C2v')
        self.assertTrue(geom.check_given_symm('C2v', atoms))
        self.assertEqual(geom.symm_identical_atoms(gpname, atoms),
                         [[0, 1], [2, 3], [4, 5], [6, 7]])

    def test_td3(self):
        coords1 = make4(1.5)
        coords2 = make4(1.9)
        atoms = [['C', c] for c in coords1] + [['C', c] for c in coords2]
        atoms[2][0] = 'C1'
        gpname, orig, axes = geom.detect_symm(atoms)
        self.assertEqual(gpname, 'C3v')

        gpname, axes = geom.subgroup(gpname, axes)
        atoms = geom.shift_atom(atoms, orig, axes)
        self.assertEqual(gpname, 'Cs')
        self.assertTrue(geom.check_given_symm('Cs', atoms))
        self.assertEqual(geom.symm_identical_atoms(gpname, atoms),
                         [[0], [1, 3], [2], [4], [5, 7], [6]])

    def test_Dooh(self):
        atoms = [['H', (0,0,0)], ['H', (0,0,-1)], ['H1', (0,0,1)]]
        basis = {'H':'sto3g'}
        gpname, orig, axes = geom.detect_symm(atoms, basis)
        self.assertEqual(gpname, 'Dooh')

        gpname, axes = geom.subgroup(gpname, axes)
        atoms = geom.shift_atom(atoms, orig, axes)
        self.assertEqual(gpname, 'D2h')
        self.assertTrue(geom.check_given_symm('D2h', atoms, basis))
        self.assertEqual(geom.symm_identical_atoms(gpname, atoms),
                         [[0], [1,2]])

    def test_Coov(self):
        atoms = [['H', (0,0,0)], ['H', (0,0,-1)], ['H1', (0,0,1)]]
        basis = {'H':'sto3g', 'H1':'6-31g'}
        gpname, orig, axes = geom.detect_symm(atoms, basis)
        self.assertEqual(gpname, 'Coov')

        gpname, axes = geom.subgroup(gpname, axes)
        atoms = geom.shift_atom(atoms, orig, axes)
        self.assertEqual(gpname, 'C2v')
        self.assertTrue(geom.check_given_symm('C2v', atoms, basis))
        self.assertEqual(geom.symm_identical_atoms(gpname, atoms),
                         [[0], [1], [2]])

    def test_d5(self):
        coord1 = ring(5)
        coord2 = ring(5, .1)
        coord1[:,2] = 1
        coord2[:,2] =-1
        atoms = [['H', c] for c in numpy.vstack((coord1,coord2))]
        gpname, orig, axes = geom.detect_symm(atoms)
        self.assertEqual(gpname, 'D5')

        gpname, axes = geom.subgroup(gpname, axes)
        atoms = geom.shift_atom(atoms, orig, axes)
        self.assertEqual(gpname, 'C2')
        self.assertTrue(geom.check_given_symm('C2', atoms))
        self.assertEqual(geom.symm_identical_atoms(gpname, atoms),
                         [[0, 9], [1, 8], [2, 7], [3, 6], [4, 5]])

    def test_d5d(self):
        coord1 = ring(5)
        coord2 = ring(5, numpy.pi/5)
        coord1[:,2] = 1
        coord2[:,2] =-1
        atoms = [['H', c] for c in numpy.vstack((coord1,coord2))]
        gpname, orig, axes = geom.detect_symm(atoms)
        self.assertEqual(gpname, 'D5d')

        gpname, axes = geom.subgroup(gpname, axes)
        atoms = geom.shift_atom(atoms, orig, axes)
        self.assertEqual(gpname, 'Cs')
        self.assertTrue(geom.check_given_symm('Cs', atoms))
        self.assertEqual(geom.symm_identical_atoms(gpname, atoms),
                         [[0, 3], [1, 2], [4], [5, 7], [6], [8, 9]])

    def test_detect_symm_c2v(self):
        atoms = [['H' , (1., 0., 2.)],
                 ['He', (0., 1., 0.)],
                 ['H' , (-2.,0.,-1.)],
                 ['He', (0.,-1., 0.)]]
        l, orig, axes = geom.detect_symm(atoms)
        self.assertEqual(l, 'C2v')
        atoms = geom.shift_atom(atoms, orig, axes)
        self.assertTrue(geom.check_given_symm('C2v', atoms))
        self.assertEqual(geom.symm_identical_atoms(l,atoms), [[0,2],[1,3]])

    def test_detect_symm_d2h_a(self):
        atoms = [['He', (0., 1., 0.)],
                 ['H' , (1., 0., 0.)],
                 ['H' , (-1.,0., 0.)],
                 ['He', (0.,-1., 0.)]]
        l, orig, axes = geom.detect_symm(atoms)
        self.assertEqual(l, 'D2h')
        atoms = geom.shift_atom(atoms, orig, axes)
        self.assertTrue(geom.check_given_symm('D2h', atoms))
        self.assertEqual(geom.symm_identical_atoms(l,atoms),
                         [[0, 3], [1, 2]])

    def test_detect_symm_d2h_b(self):
        atoms = [['H' , (1., 0., 2.)],
                 ['He', (0., 1., 0.)],
                 ['H' , (-1.,0.,-2.)],
                 ['He', (0.,-1., 0.)]]
        l, orig, axes = geom.detect_symm(atoms)
        self.assertEqual(l, 'D2h')
        atoms = geom.shift_atom(atoms, orig, axes)
        self.assertTrue(geom.check_given_symm('D2h', atoms))
        self.assertEqual(geom.symm_identical_atoms(l,atoms), [[0,2],[1,3]])

    def test_detect_symm_c2h_a(self):
        atoms = [['H' , (1., 0., 2.)],
                 ['He', (0., 1.,-1.)],
                 ['H' , (-1.,0.,-2.)],
                 ['He', (0.,-1., 1.)]]
        l, orig, axes = geom.detect_symm(atoms)
        atoms = geom.shift_atom(atoms, orig, axes)
        self.assertEqual(l, 'C2h')
        self.assertEqual(geom.symm_identical_atoms(l,atoms), [[0,2],[1,3]])
        self.assertTrue(geom.check_given_symm('C2h', atoms))

    def test_detect_symm_c2h(self):
        atoms = [['H' , (1., 0., 2.)],
                 ['He', (0., 1., 0.)],
                 ['H' , (1., 0., 0.)],
                 ['H' , (-1.,0., 0.)],
                 ['H' , (-1.,0.,-2.)],
                 ['He', (0.,-1., 0.)]]
        l, orig, axes = geom.detect_symm(atoms)
        atoms = geom.shift_atom(atoms, orig, axes)
        self.assertEqual(l, 'C2h')
        self.assertEqual(geom.symm_identical_atoms(l,atoms), [[0,4],[1,5],[2,3]])
        self.assertTrue(geom.check_given_symm('C2h', atoms))

        atoms = [['H' , (1., 0., 1.)],
                 ['H' , (1., 0.,-1.)],
                 ['He', (0., 0., 2.)],
                 ['He', (2., 0.,-2.)],
                 ['Li', (1., 1., 0.)],
                 ['Li', (1.,-1., 0.)]]
        l, orig, axes = geom.detect_symm(atoms)
        atoms = geom.shift_atom(atoms, orig, axes)
        self.assertEqual(l, 'C2h')
        self.assertEqual(geom.symm_identical_atoms(l,atoms),
                         [[0, 1], [2, 3], [4, 5]])
        self.assertTrue(geom.check_given_symm('C2h', atoms))

    def test_detect_symm_d2_a(self):
        atoms = [['H' , (1., 0., 1.)],
                 ['H' , (1., 0.,-1.)],
                 ['He', (0., 0., 2.)],
                 ['He', (2., 0., 2.)],
                 ['He', (1., 1.,-2.)],
                 ['He', (1.,-1.,-2.)]]
        l, orig, axes = geom.detect_symm(atoms)
        self.assertEqual(l, 'D2')
        atoms = geom.shift_atom(atoms, orig, axes)
        self.assertTrue(geom.check_given_symm('D2', atoms))
        self.assertEqual(geom.symm_identical_atoms(l,atoms),
                         [[0, 1], [2, 3, 4, 5]])

    def test_detect_symm_d2_b(self):
        s2 = numpy.sqrt(.5)
        atoms = [['C', (0., 0., 1.)],
                 ['C', (0., 0.,-1.)],
                 ['H', ( 1, 0., 2.)],
                 ['H', (-1, 0., 2.)],
                 ['H', ( s2, s2,-2.)],
                 ['H', (-s2,-s2,-2.)]]
        l, orig, axes = geom.detect_symm(atoms)
        self.assertEqual(l, 'D2')
        atoms = geom.shift_atom(atoms, orig, axes)
        self.assertTrue(geom.check_given_symm('D2', atoms))
        self.assertEqual(geom.symm_identical_atoms(l,atoms),
                         [[0, 1], [2, 3, 4, 5]])

    def test_detect_symm_s4(self):
        atoms = [['H', (-1,-1.,-2.)],
                 ['H', ( 1, 1.,-2.)],
                 ['C', (-.9,-1.,-2.)],
                 ['C', (.9, 1.,-2.)],
                 ['H', ( 1,-1., 2.)],
                 ['H', (-1, 1., 2.)],
                 ['C', ( 1,-.9, 2.)],
                 ['C', (-1, .9, 2.)],]
        l, orig, axes = geom.detect_symm(atoms)
        self.assertEqual(l, 'S4')
        atoms = geom.shift_atom(atoms, orig, axes)
        self.assertTrue(geom.check_given_symm('C2', atoms))
        self.assertEqual(geom.symm_identical_atoms('C2',atoms),
                         [[0, 1], [2, 3], [4, 5], [6, 7]])

    def test_detect_symm_ci(self):
        atoms = [['H' , ( 1., 0., 0.)],
                 ['He', ( 0., 1., 0.)],
                 ['Li', ( 0., 0., 1.)],
                 ['Be', ( .5, .5, .5)],
                 ['H' , (-1., 0., 0.)],
                 ['He', ( 0.,-1., 0.)],
                 ['Li', ( 0., 0.,-1.)],
                 ['Be', (-.5,-.5,-.5)]]
        l, orig, axes = geom.detect_symm(atoms)
        atoms = geom.shift_atom(atoms, orig, axes)
        self.assertEqual(l, 'Ci')
        self.assertTrue(geom.check_given_symm('Ci', atoms))
        self.assertEqual(geom.symm_identical_atoms(l,atoms),
                         [[0, 4], [1, 5], [2, 6], [3, 7]])

    def test_detect_symm_cs1(self):
        atoms = [['H' , (1., 2., 0.)],
                 ['He', (1., 0., 0.)],
                 ['Li', (2.,-1., 0.)],
                 ['Be', (0., 1., 0.)]]
        l, orig, axes = geom.detect_symm(atoms)
        atoms = geom.shift_atom(atoms, orig, axes)
        self.assertEqual(l, 'Cs')
        self.assertTrue(geom.check_given_symm('Cs', atoms))
        self.assertEqual(geom.symm_identical_atoms(l,atoms),
                         [[0], [1], [2], [3]])

    def test_detect_symm_cs2(self):
        atoms = [['H' , (0., 1., 2.)],
                 ['He', (0., 1., 0.)],
                 ['Li', (0., 2.,-1.)],
                 ['Be', (0., 0., 1.)],
                 ['S' , (-3, 1., .5)],
                 ['S' , ( 3, 1., .5)]]
        coord = numpy.dot([a[1] for a in atoms], u)
        atoms = [[atoms[i][0], c] for i,c in enumerate(coord)]
        l, orig, axes = geom.detect_symm(atoms)
        atoms = geom.shift_atom(atoms, orig, axes)
        self.assertEqual(l, 'Cs')
        self.assertTrue(geom.check_given_symm('Cs', atoms))
        self.assertEqual(geom.symm_identical_atoms(l,atoms),
                         [[0], [1], [2], [3], [4, 5]])

    def test_detect_symm_cs3(self):
        atoms = [['H' , ( 2.,1., 0.)],
                 ['He', ( 0.,1., 0.)],
                 ['Li', (-1.,2., 0.)],
                 ['Be', ( 1.,0., 0.)],
                 ['S' , ( .5,1., -3)],
                 ['S' , ( .5,1.,  3)]]
        coord = numpy.dot([a[1] for a in atoms], u)
        atoms = [[atoms[i][0], c] for i,c in enumerate(coord)]
        l, orig, axes = geom.detect_symm(atoms)
        atoms = geom.shift_atom(atoms, orig, axes)
        self.assertEqual(l, 'Cs')
        self.assertTrue(geom.check_given_symm('Cs', atoms))
        self.assertEqual(geom.symm_identical_atoms(l,atoms),
                         [[0], [1], [2], [3], [4, 5]])

    def test_detect_symm_c1(self):
        atoms = [['H' , ( 1., 0., 0.)],
                 ['He', ( 0., 1., 0.)],
                 ['Li', ( 0., 0., 1.)],
                 ['Be', ( .5, .5, .5)]]
        l, orig, axes = geom.detect_symm(atoms)
        atoms = geom.shift_atom(atoms, orig, axes)
        self.assertEqual(l, 'C1')
        self.assertTrue(geom.check_given_symm('C1', atoms))
        self.assertEqual(geom.symm_identical_atoms(l,atoms),
                         [[0], [1], [2], [3]])

    def test_detect_symm_c2(self):
        atoms = [['H' , ( 1., 0., 1.)],
                 ['H' , ( 1., 0.,-1.)],
                 ['He', ( 0.,-3., 2.)],
                 ['He', ( 0., 3.,-2.)]]
        l, orig, axes = geom.detect_symm(atoms)
        atoms = geom.shift_atom(atoms, orig, axes)
        self.assertEqual(l, 'C2')
        self.assertTrue(geom.check_given_symm('C2', atoms))
        self.assertEqual(geom.symm_identical_atoms(l,atoms), [[0,1],[2,3]])


    def test_detect_symm_d3d(self):
        atoms = [
            ['C', ( 1.25740, -0.72596, -0.25666)],
            ['C', ( 1.25740,  0.72596,  0.25666)],
            ['C', ( 0.00000,  1.45192, -0.25666)],
            ['C', (-1.25740,  0.72596,  0.25666)],
            ['C', (-1.25740, -0.72596, -0.25666)],
            ['C', ( 0.00000, -1.45192,  0.25666)],
            ['H', ( 2.04168, -1.17876,  0.05942)],
            ['H', ( 1.24249, -0.71735, -1.20798)],
            ['H', ( 2.04168,  1.17876, -0.05942)],
            ['H', ( 1.24249,  0.71735,  1.20798)],
            ['H', ( 0.00000,  1.43470, -1.20798)],
            ['H', ( 0.00000,  2.35753,  0.05942)],
            ['H', (-2.04168,  1.17876, -0.05942)],
            ['H', (-1.24249,  0.71735,  1.20798)],
            ['H', (-1.24249, -0.71735, -1.20798)],
            ['H', (-2.04168, -1.17876,  0.05942)],
            ['H', ( 0.00000, -1.43470,  1.20798)],
            ['H', ( 0.00000, -2.35753, -0.05942)], ]
        l, orig, axes = geom.detect_symm(atoms)
        self.assertEqual(l, 'D3d')



def ring(n, start=0):
    r = 1. / numpy.sin(numpy.pi/n)
    coord = []
    for i in range(n):
        theta = i * (2*numpy.pi/n)
        coord.append([r*numpy.cos(theta+start), r*numpy.sin(theta+start), 0])
    return numpy.array(coord)

def ringhat(n, u):
    atoms = [['H', c] for c in ring(n)] \
          + [['C', c] for c in ring(n, .1)] \
          + [['N', [0,0, 1.3]],
             ['N', [0,0,-1.3]]]
    c = numpy.dot([a[1] for a in atoms], u)
    return [[atoms[i][0], c[i]] for i in range(len(atoms))]

def rotmatz(ang):
    c = numpy.cos(ang)
    s = numpy.sin(ang)
    return numpy.array((( c, s, 0),
                        (-s, c, 0),
                        ( 0, 0, 1),))
def rotmaty(ang):
    c = numpy.cos(ang)
    s = numpy.sin(ang)
    return numpy.array((( c, 0, s),
                        ( 0, 1, 0),
                        (-s, 0, c),))

def r2edge(ang, r):
    return 2*r*numpy.sin(ang/2)


def make60(b5, b6):
    theta1 = numpy.arccos(1/numpy.sqrt(5))
    theta2 = (numpy.pi - theta1) * .5
    r = (b5*2+b6)/2/numpy.sin(theta1/2)
    rot72 = rotmatz(numpy.pi*2/5)
    s1 = numpy.sin(theta1)
    c1 = numpy.cos(theta1)
    s2 = numpy.sin(theta2)
    c2 = numpy.cos(theta2)
    p1 = numpy.array(( s2*b5,  0, r-c2*b5))
    p9 = numpy.array((-s2*b5,  0,-r+c2*b5))
    p2 = numpy.array(( s2*(b5+b6),  0, r-c2*(b5+b6)))
    rot1 = reduce(numpy.dot, (rotmaty(theta1), rot72, rotmaty(-theta1)))
    p2s = []
    for i in range(5):
        p2s.append(p2)
        p2 = numpy.dot(p2, rot1)

    coord = []
    for i in range(5):
        coord.append(p1)
        p1 = numpy.dot(p1, rot72)
    for pj in p2s:
        pi = pj
        for i in range(5):
            coord.append(pi)
            pi = numpy.dot(pi, rot72)
    for pj in p2s:
        pi = pj
        for i in range(5):
            coord.append(-pi)
            pi = numpy.dot(pi, rot72)
    for i in range(5):
        coord.append(p9)
        p9 = numpy.dot(p9, rot72)
    return numpy.array(coord)


def make12(b):
    theta1 = numpy.arccos(1/numpy.sqrt(5))
    theta2 = (numpy.pi - theta1) * .5
    r = b/2/numpy.sin(theta1/2)
    rot72 = rotmatz(numpy.pi*2/5)
    s1 = numpy.sin(theta1)
    c1 = numpy.cos(theta1)
    p1 = numpy.array(( s1*r,  0,  c1*r))
    p2 = numpy.array((-s1*r,  0, -c1*r))
    coord = [(  0,  0,    r)]
    for i in range(5):
        coord.append(p1)
        p1 = numpy.dot(p1, rot72)
    for i in range(5):
        coord.append(p2)
        p2 = numpy.dot(p2, rot72)
    coord.append((  0,  0,  -r))
    return numpy.array(coord)


def make20(b):
    theta1 = numpy.arccos(numpy.sqrt(5)/3)
    theta2 = numpy.arcsin(r2edge(theta1,1)/2/numpy.sin(numpy.pi/5))
    r = b/2/numpy.sin(theta1/2)
    rot72 = rotmatz(numpy.pi*2/5)
    s2 = numpy.sin(theta2)
    c2 = numpy.cos(theta2)
    s3 = numpy.sin(theta1+theta2)
    c3 = numpy.cos(theta1+theta2)
    p1 = numpy.array(( s2*r,  0,  c2*r))
    p2 = numpy.array(( s3*r,  0,  c3*r))
    p3 = numpy.array((-s3*r,  0, -c3*r))
    p4 = numpy.array((-s2*r,  0, -c2*r))
    coord = []
    for i in range(5):
        coord.append(p1)
        p1 = numpy.dot(p1, rot72)
    for i in range(5):
        coord.append(p2)
        p2 = numpy.dot(p2, rot72)
    for i in range(5):
        coord.append(p3)
        p3 = numpy.dot(p3, rot72)
    for i in range(5):
        coord.append(p4)
        p4 = numpy.dot(p4, rot72)
    return numpy.array(coord)

def make4(b):
    coord = numpy.ones((4,3)) * b*.5
    coord[1,0] = coord[1,1] = -b*.5
    coord[2,2] = coord[2,1] = -b * .5
    coord[3,0] = coord[3,2] = -b * .5
    return coord

def make6(b):
    coord = numpy.zeros((6,3))
    coord[0,0] = coord[1,1] = coord[2,2] = b * .5
    coord[3,0] = coord[4,1] = coord[5,2] =-b * .5
    return coord

def make8(b):
    coord = numpy.ones((8,3)) * b*.5
    n = 0
    for i in range(2):
        for j in range(2):
            for k in range(2):
                coord[n,0] = (-1) ** i * b*.5
                coord[n,1] = (-1) ** j * b*.5
                coord[n,2] = (-1) ** k * b*.5
                n += 1
    return coord



if __name__ == "__main__":
    print("Full Tests geom")
    unittest.main()

