/*
 *
 */

#include <stdlib.h>
#include <string.h>
#include <math.h>
//#include <omp.h>
#include "config.h"
#include "cvhf.h"
#include "np_helper/np_helper.h"
#include "fblas.h"

/*
 * J
 */
void CVHFnrs8_ij_s2kl_o0(double *eri, double *dm, double *vj,
                         int nao, int ic, int jc)
{
        int i, j, ij;
        double dm_ij;
        double *vj_ij = &vj[ic*nao+jc];

        if (ic > jc) {
                dm_ij = dm[ic*nao+jc] + dm[jc*nao+ic];
        } else if (ic == jc) {
                dm_ij = dm[ic*nao+ic];
        } else {
                return;
        }

        for (i = 0, ij = 0; i < ic; i++) {
                for (j = 0; j < i; j++, ij++) {
                        *vj_ij += eri[ij] *(dm[i*nao+j]+dm[j*nao+i]);
                        vj[i*nao+j] += eri[ij] * dm_ij;
                }
                *vj_ij += eri[ij] * dm[i*nao+i];
                vj[i*nao+i] += eri[ij] * dm_ij;
                ij++;
        }
        // i == ic
        for (j = 0; j < jc; j++, ij++) {
                *vj_ij += eri[ij] *(dm[i*nao+j]+dm[j*nao+i]);
                vj[i*nao+j] += eri[ij] * dm_ij;
        }
        *vj_ij += eri[ij] * dm_ij;
}

void CVHFnrs4_ij_s2kl_o0(double *eri, double *dm, double *vj,
                         int nao, int ic, int jc)
{
        int i, j, ij;
        double dm_ij;

        if (ic > jc) {
                dm_ij = dm[ic*nao+jc] + dm[jc*nao+ic];
        } else if (ic == jc) {
                dm_ij = dm[ic*nao+ic];
        } else {
                return;
        }

        for (i = 0, ij = 0; i < nao; i++) {
                for (j = 0; j <= i; j++, ij++) {
                        vj[i*nao+j] += eri[ij] * dm_ij;
                }
        }
}

void CVHFnrs2kl_kl_s1ij_o0(double *eri, double *dm, double *vj,
                           int nao, int ic, int jc)
{
        int i, j, ij;
        double *vj_ij = &vj[ic*nao+jc];
        for (i = 0, ij = 0; i < nao; i++) {
                for (j = 0; j < i; j++, ij++) {
                        *vj_ij += eri[ij] *(dm[i*nao+j]+dm[j*nao+i]);
                }
                *vj_ij += eri[ij] * dm[i*nao+i];
                ij++;
        }
}



/*
 * K
 */
void CVHFnrs8_jk_s1il_o0(double *eri, double *dm, double *vk,
                         int nao, int ic, int jc)
{
        int k, l, kl;
        if (ic > jc) {
                for (k = 0, kl = 0; k < ic; k++) {
                        for (l = 0; l < k; l++, kl++) {
                                vk[jc*nao+l] += eri[kl] * dm[ic*nao+k];
                                vk[ic*nao+l] += eri[kl] * dm[jc*nao+k];
                                vk[jc*nao+k] += eri[kl] * dm[ic*nao+l];
                                vk[ic*nao+k] += eri[kl] * dm[jc*nao+l];
                                vk[l*nao+jc] += eri[kl] * dm[k*nao+ic];
                                vk[k*nao+jc] += eri[kl] * dm[l*nao+ic];
                                vk[l*nao+ic] += eri[kl] * dm[k*nao+jc];
                                vk[k*nao+ic] += eri[kl] * dm[l*nao+jc];
                        }
                        vk[jc*nao+k] += eri[kl] * dm[ic*nao+k];
                        vk[ic*nao+k] += eri[kl] * dm[jc*nao+k];
                        vk[k*nao+jc] += eri[kl] * dm[k*nao+ic];
                        vk[k*nao+ic] += eri[kl] * dm[k*nao+jc];
                        kl++;
                }
                k = ic;
                for (l = 0; l < jc; l++, kl++) { // l<k
                        vk[jc*nao+l] += eri[kl] * dm[ic*nao+k];
                        vk[ic*nao+l] += eri[kl] * dm[jc*nao+k];
                        vk[jc*nao+k] += eri[kl] * dm[ic*nao+l];
                        vk[ic*nao+k] += eri[kl] * dm[jc*nao+l];
                        vk[l*nao+jc] += eri[kl] * dm[k*nao+ic];
                        vk[k*nao+jc] += eri[kl] * dm[l*nao+ic];
                        vk[l*nao+ic] += eri[kl] * dm[k*nao+jc];
                        vk[k*nao+ic] += eri[kl] * dm[l*nao+jc];
                }
                // ic = k, jc = l;
                vk[jc*nao+jc] += eri[kl] * dm[ic*nao+ic];
                vk[ic*nao+jc] += eri[kl] * dm[jc*nao+ic];
                vk[jc*nao+ic] += eri[kl] * dm[ic*nao+jc];
                vk[ic*nao+ic] += eri[kl] * dm[jc*nao+jc];
        } else if (ic == jc) {
                for (k = 0, kl = 0; k < ic; k++) {
                        for (l = 0; l < k; l++, kl++) {
                                vk[ic*nao+l] += eri[kl] * dm[ic*nao+k];
                                vk[ic*nao+k] += eri[kl] * dm[ic*nao+l];
                                vk[l*nao+ic] += eri[kl] * dm[k*nao+ic];
                                vk[k*nao+ic] += eri[kl] * dm[l*nao+ic];
                        }
                        vk[ic*nao+k] += eri[kl] * dm[ic*nao+k];
                        vk[k*nao+ic] += eri[kl] * dm[k*nao+ic];
                        kl++;
                }
                k = ic;
                for (l = 0; l < k; l++, kl++) { // l<k
                        vk[ic*nao+l] += eri[kl] * dm[ic*nao+ic];
                        vk[ic*nao+ic] += eri[kl] * dm[ic*nao+l];
                        vk[l*nao+ic] += eri[kl] * dm[ic*nao+ic];
                        vk[ic*nao+ic] += eri[kl] * dm[l*nao+ic];
                }
                // ic = jc = k = l
                vk[ic*nao+ic] += eri[kl] * dm[ic*nao+ic];
        }
}

void CVHFnrs8_jk_s2il_o0(double *eri, double *dm, double *vk,
                         int nao, int ic, int jc)
{
        int k, l;
        if (ic > jc) {
                // k < jc
                for (k=0; k < jc; k++) {
                        for (l = 0; l < k; l++) {
                                vk[jc*nao+l] += eri[l] * dm[ic*nao+k];
                                vk[jc*nao+k] += eri[l] * dm[ic*nao+l];
                                vk[ic*nao+l] += eri[l] * dm[jc*nao+k];
                                vk[ic*nao+k] += eri[l] * dm[jc*nao+l];
                        }
                        // l = k
                        vk[jc*nao+k] += eri[k] * dm[ic*nao+k];
                        vk[ic*nao+k] += eri[k] * dm[jc*nao+k];
                        eri += k + 1;
                }
                // k = jc
                for (l = 0; l < k; l++) {
                        vk[jc*nao+l] += eri[l] * dm[ic*nao+jc];
                        vk[jc*nao+jc] += eri[l] *(dm[ic*nao+l] + dm[l*nao+ic]);
                        vk[ic*nao+l] += eri[l] * dm[jc*nao+jc];
                        vk[ic*nao+jc] += eri[l] * dm[jc*nao+l];
                }
                // l = k = jc
                vk[jc*nao+jc] += eri[l] *(dm[ic*nao+jc] + dm[jc*nao+ic]);
                vk[ic*nao+jc] += eri[l] * dm[jc*nao+jc];
                eri += k + 1;
                // k > jc
                for (k=jc+1; k < ic; k++) {
                        // l < jc
                        for (l = 0; l < jc; l++) {
                                vk[jc*nao+l] += eri[l] * dm[ic*nao+k];
                                vk[ic*nao+l] += eri[l] * dm[jc*nao+k];
                                vk[ic*nao+k] += eri[l] * dm[jc*nao+l];
                                vk[k*nao+jc] += eri[l] * dm[l*nao+ic];
                        }
                        // l = jc
                        vk[jc*nao+jc] += eri[l] *(dm[ic*nao+k] + dm[k*nao+ic]);
                        vk[ic*nao+jc] += eri[l] * dm[jc*nao+k];
                        vk[ic*nao+k] += eri[l] * dm[jc*nao+jc];
                        vk[k*nao+jc] += eri[l] * dm[jc*nao+ic];
                        //eri += jc+1;
                        // l > jc
                        for (l = jc+1; l < k; l++) {
                                vk[ic*nao+l] += eri[l] * dm[jc*nao+k];
                                vk[ic*nao+k] += eri[l] * dm[jc*nao+l];
                                vk[l*nao+jc] += eri[l] * dm[k*nao+ic];
                                vk[k*nao+jc] += eri[l] * dm[l*nao+ic];
                        }
                        // l = k
                        vk[jc*nao+k] += eri[l] * dm[ic*nao+k];
                        vk[ic*nao+k] += eri[l] * dm[jc*nao+k];
                        vk[k*nao+jc] += eri[l] * dm[k*nao+ic];
                        eri += k + 1;
                }
                // k = ic
                for (l = 0; l < jc; l++) {
                        vk[jc*nao+l] += eri[l] * dm[ic*nao+ic];
                        vk[ic*nao+l] += eri[l] * dm[jc*nao+ic];
                        vk[ic*nao+ic] += eri[l] *(dm[jc*nao+l] + dm[l*nao+jc]);
                        vk[ic*nao+jc] += eri[l] * dm[l*nao+ic];
                }
                // ic = k, jc = l;
                vk[jc*nao+jc] += eri[l] * dm[ic*nao+ic];
                vk[ic*nao+jc] += eri[l] * dm[jc*nao+ic];
                vk[ic*nao+ic] += eri[l] * dm[jc*nao+jc];
                eri += jc + 1;
        } else if (ic == jc) {
                for (k = 0; k < ic-1; k+=2) {
                        for (l = 0; l < k; l++) {
                                vk[ic*nao+l] += eri[l] * dm[ic*nao+k];
                                vk[ic*nao+k] += eri[l] * dm[ic*nao+l];
                                vk[ic*nao+l  ] += eri[l+k+1] * dm[ic*nao+k+1];
                                vk[ic*nao+k+1] += eri[l+k+1] * dm[ic*nao+l  ];
                        }
                        vk[ic*nao+k] += eri[k] * dm[ic*nao+k];
                        eri += k+1;
                        vk[ic*nao+k  ] += eri[k] * dm[ic*nao+k+1];
                        vk[ic*nao+k+1] += eri[k] * dm[ic*nao+k  ];
                        vk[ic*nao+k+1] += eri[k+1] * dm[ic*nao+k+1];
                        eri += k+2;
                }
                for (; k < ic; k++) {
                        for (l = 0; l < k; l++) {
                                vk[ic*nao+l] += eri[l] * dm[ic*nao+k];
                                vk[ic*nao+k] += eri[l] * dm[ic*nao+l];
                        }
                        vk[ic*nao+k] += eri[k] * dm[ic*nao+k];
                        eri += k+1;
                }
                for (l = 0; l < k; l++) { // l<k
                        vk[ic*nao+l] += eri[l] * dm[ic*nao+ic];
                        vk[ic*nao+ic] += eri[l] *(dm[ic*nao+l] + dm[l*nao+ic]);
                }
                // ic = jc = k = l
                vk[ic*nao+ic] += eri[l] * dm[ic*nao+ic];
                eri += k + 1;
        }
}

void CVHFnrs4_jk_s1il_o0(double *eri, double *dm, double *vk,
                         int nao, int ic, int jc)
{
        int k, l, kl;
        if (ic > jc) {
                for (k = 0, kl = 0; k < nao; k++) {
                        for (l = 0; l < k; l++, kl++) {
                                vk[jc*nao+l] += eri[kl] * dm[ic*nao+k];
                                vk[jc*nao+k] += eri[kl] * dm[ic*nao+l];
                                vk[ic*nao+l] += eri[kl] * dm[jc*nao+k];
                                vk[ic*nao+k] += eri[kl] * dm[jc*nao+l];
                        }
                        vk[jc*nao+k] += eri[kl] * dm[ic*nao+k];
                        vk[ic*nao+k] += eri[kl] * dm[jc*nao+k];
                        kl++;
                }
        } else if (ic == jc) {
                for (k = 0, kl = 0; k < nao; k++) {
                        for (l = 0; l < k; l++, kl++) {
                                vk[ic*nao+l] += eri[kl] * dm[ic*nao+k];
                                vk[ic*nao+k] += eri[kl] * dm[ic*nao+l];
                        }
                        vk[ic*nao+k] += eri[kl] * dm[ic*nao+k];
                        kl++;
                }
        }
}

void CVHFnrs4_il_s1jk_o0(double *eri, double *dm, double *vk,
                         int nao, int ic, int jc)
{
        CVHFnrs4_jk_s1il_o0(eri, dm, vk, nao, ic, jc);
}

void CVHFnrs4_jk_s2il_o0(double *eri, double *dm, double *vk,
                         int nao, int ic, int jc)
{
        int k, l, kl;
        if (ic > jc) {
                for (k = 0, kl = 0; k <= jc; k++) {
                        for (l = 0; l < k; l++, kl++) {
                                vk[jc*nao+l] += eri[kl] * dm[ic*nao+k];
                                vk[jc*nao+k] += eri[kl] * dm[ic*nao+l];
                                vk[ic*nao+l] += eri[kl] * dm[jc*nao+k];
                                vk[ic*nao+k] += eri[kl] * dm[jc*nao+l];
                        }
                        vk[jc*nao+k] += eri[kl] * dm[ic*nao+k];
                        vk[ic*nao+k] += eri[kl] * dm[jc*nao+k];
                        kl++;
                }
                for (k = jc+1; k <= ic; k++) {
                        for (l = 0; l <= jc; l++, kl++) {
                                vk[jc*nao+l] += eri[kl] * dm[ic*nao+k];
                                vk[ic*nao+l] += eri[kl] * dm[jc*nao+k];
                                vk[ic*nao+k] += eri[kl] * dm[jc*nao+l];
                        }
                        for (l = jc+1; l < k; l++, kl++) {
                                vk[ic*nao+l] += eri[kl] * dm[jc*nao+k];
                                vk[ic*nao+k] += eri[kl] * dm[jc*nao+l];
                        }
                        vk[ic*nao+k] += eri[kl] * dm[jc*nao+k];
                        kl++;
                }
                for (k = ic+1; k < nao; k++) {
                        for (l = 0, kl = k*(k+1)/2; l <= jc; l++, kl++) {
                                vk[jc*nao+l] += eri[kl] * dm[ic*nao+k];
                                vk[ic*nao+l] += eri[kl] * dm[jc*nao+k];
                        }
                        for (l = jc+1; l <= ic; l++, kl++) {
                                vk[ic*nao+l] += eri[kl] * dm[jc*nao+k];
                        }
                }
        } else if (ic == jc) {
                for (k = 0, kl = 0; k <= ic; k++) {
                        for (l = 0; l < k; l++, kl++) {
                                vk[ic*nao+l] += eri[kl] * dm[ic*nao+k];
                                vk[ic*nao+k] += eri[kl] * dm[ic*nao+l];
                        }
                        vk[ic*nao+k] += eri[kl] * dm[ic*nao+k];
                        kl++;
                }
                for (k = ic+1; k < nao; k++) {
                        for (l = 0, kl = k*(k+1)/2; l <= ic; l++, kl++) {
                                vk[ic*nao+l] += eri[kl] * dm[ic*nao+k];
                        }
                }
        }
}

void CVHFnrs4_il_s2jk_o0(double *eri, double *dm, double *vk,
                         int nao, int ic, int jc)
{
        CVHFnrs4_jk_s2il_o0(eri, dm, vk, nao, ic, jc);
}



/*
 * einsum ijkl,ij->(s2)kl
 * 8-fold symmetry for eri: i>=j,k>=l,ij>=kl
 * input address eri of the first element for pair ij=ic*(ic+1)/2+jc
 * i.e. ~ &eri_ao[ij*(ij+1)/2]
 * dm can be non-Hermitian,
 * output vk might not be Hermitian
 *
 * NOTE all _s2kl (nrs8_, nrs4_, nrs2kl_) assumes the tril part of eri
 * being stored in C-order *contiguously*.  so call CVHFunpack_nrblock2tril
 * to generate eris
 */
void CVHFnrs8_ij_s2kl(double *eri, double *dm, double *vj,
                      int nao, int ic, int jc)
{
        CVHFnrs8_ij_s2kl_o0(eri, dm, vj, nao, ic, jc);
}
// tri_dm: fold upper triangular dm to lower triangle,
// tri_dm[i*(i+1)/2+j] = dm[i*nao+j] + dm[j*nao+i]  for i > j
void CVHFnrs8_tridm_vj(double *eri, double *tri_dm, double *vj,
                       int nao, int ic, int jc)
{
        int i, j, ij;
        double dm_ijc = tri_dm[ic*(ic+1)/2+jc];
        double *vj_ij = &vj[ic*nao+jc];

        for (i = 0, ij = 0; i < ic; i++) {
                for (j = 0; j <= i; j++, ij++) {
                        *vj_ij += eri[ij] * tri_dm[ij];
                        vj[i*nao+j] += eri[ij] * dm_ijc;
                }
        }
        // i == ic
        for (j = 0; j < jc; j++, ij++) {
                *vj_ij += eri[ij] * tri_dm[ij];
                vj[i*nao+j] += eri[ij] * dm_ijc;
        }
        *vj_ij += eri[ij] * dm_ijc;
}
void CVHFnrs8_jk_s1il(double *eri, double *dm, double *vk,
                      int nao, int ic, int jc)
{
        CVHFnrs8_jk_s1il_o0(eri, dm, vk, nao, ic, jc);
}
/*
 * einsum ijkl,jk->(s2)il
 * output vk should be Hermitian
 */
void CVHFnrs8_jk_s2il(double *eri, double *dm, double *vk,
                      int nao, int ic, int jc)
{
        CVHFnrs8_jk_s2il_o0(eri, dm, vk, nao, ic, jc);
}


/*
 * einsum ijkl,jk->il
 * 4-fold symmetry for eri: i>=j,k>=l
 */
void CVHFnrs4_jk_s1il(double *eri, double *dm, double *vk,
                      int nao, int ic, int jc)
{
        CVHFnrs4_jk_s1il_o0(eri, dm, vk, nao, ic, jc);
}
void CVHFnrs4_il_s1jk(double *eri, double *dm, double *vk,
                      int nao, int ic, int jc)
{
        CVHFnrs4_jk_s1il_o0(eri, dm, vk, nao, ic, jc);
}
/*
 * output vk should be Hermitian
 */
void CVHFnrs4_jk_s2il(double *eri, double *dm, double *vk,
                      int nao, int ic, int jc)
{
        CVHFnrs4_jk_s2il_o0(eri, dm, vk, nao, ic, jc);
}
void CVHFnrs4_il_s2jk(double *eri, double *dm, double *vk,
                      int nao, int ic, int jc)
{
        CVHFnrs4_jk_s2il_o0(eri, dm, vk, nao, ic, jc);
}
void CVHFnrs4_ij_s2kl(double *eri, double *dm, double *vj,
                      int nao, int ic, int jc)
{
        CVHFnrs4_ij_s2kl_o0(eri, dm, vj, nao, ic, jc);
}
void CVHFnrs4_kl_s2ij(double *eri, double *dm, double *vj,
                      int nao, int ic, int jc)
{
        if (ic >= jc) {
                CVHFnrs2kl_kl_s1ij_o0(eri, dm, vj, nao, ic, jc);
        }
}


void CVHFnrs1_ij_s1kl(double *eri, double *dm, double *vj,
                      int nao, int ic, int jc)
{
        int i;
        double dm_ij = dm[ic*nao+jc];
        for (i = 0; i < nao*nao; i++) {
                vj[i] += eri[i] * dm_ij;
        }
}
void CVHFnrs1_kl_s1ij(double *eri, double *dm, double *vj,
                      int nao, int ic, int jc)
{
        const int INC1 = 1;
        int nn = nao * nao;
        vj[ic*nao+jc] += ddot_(&nn, eri, &INC1, dm, &INC1);
}
void CVHFnrs1_jk_s1il(double *eri, double *dm, double *vk,
                      int nao, int ic, int jc)
{
        int k, l, kl;
        for (k = 0, kl = 0; k < nao; k++) {
        for (l = 0; l < nao; l++, kl++) {
                vk[ic*nao+l] += eri[kl] * dm[jc*nao+k];
        } }
}
void CVHFnrs1_il_s1jk(double *eri, double *dm, double *vk,
                      int nao, int ic, int jc)
{
        int k, l, kl;
        for (k = 0, kl = 0; k < nao; k++) {
        for (l = 0; l < nao; l++, kl++) {
                vk[jc*nao+k] += eri[kl] * dm[ic*nao+l];
        } }
}


void CVHFnrs2ij_ij_s1kl(double *eri, double *dm, double *vj,
                        int nao, int ic, int jc)
{
        int i;
        double dm_ij;
        if (ic > jc) {
                dm_ij = dm[ic*nao+jc] + dm[jc*nao+ic];
        } else if (ic == jc) {
                dm_ij = dm[ic*nao+ic];
        } else {
                return;
        }

        for (i = 0; i < nao*nao; i++) {
                vj[i] += eri[i] * dm_ij;
        }
}
void CVHFnrs2ij_kl_s2ij(double *eri, double *dm, double *vj,
                        int nao, int ic, int jc)
{
        if (ic < jc) {
                return;
        }
        CVHFnrs1_kl_s1ij(eri, dm, vj, nao, ic, jc);
}
void CVHFnrs2ij_jk_s1il(double *eri, double *dm, double *vk,
                        int nao, int ic, int jc)
{
        int k, l, kl;
        if (ic > jc) {
                for (k = 0, kl = 0; k < nao; k++) {
                        for (l = 0; l < nao; l++, kl++) {
                                vk[jc*nao+l] += eri[kl] * dm[ic*nao+k];
                                vk[ic*nao+l] += eri[kl] * dm[jc*nao+k];
                        }
                }
        } else if (ic == jc) {
                for (k = 0, kl = 0; k < nao; k++) {
                        for (l = 0; l < nao; l++, kl++) {
                                vk[ic*nao+l] += eri[kl] * dm[ic*nao+k];
                        }
                }
        }
}
void CVHFnrs2ij_il_s1jk(double *eri, double *dm, double *vk,
                        int nao, int ic, int jc)
{
        int k, l, kl;
        if (ic > jc) {
                for (k = 0, kl = 0; k < nao; k++) {
                        for (l = 0; l < nao; l++, kl++) {
                                vk[jc*nao+k] += eri[kl] * dm[ic*nao+l];
                                vk[ic*nao+k] += eri[kl] * dm[jc*nao+l];
                        }
                }
        } else if (ic == jc) {
                for (k = 0, kl = 0; k < nao; k++) {
                        for (l = 0; l < nao; l++, kl++) {
                                vk[ic*nao+k] += eri[kl] * dm[ic*nao+l];
                        }
                }
        }
}


void CVHFnrs2kl_ij_s2kl(double *eri, double *dm, double *vj,
                        int nao, int ic, int jc)
{
        int i, j, ij;
        double dm_ij = dm[ic*nao+jc];
        for (i = 0, ij = 0; i < nao; i++) {
                for (j = 0; j <= i; j++, ij++) {
                        vj[i*nao+j] += eri[ij] * dm_ij;
                }
        }
}
void CVHFnrs2kl_kl_s1ij(double *eri, double *dm, double *vj,
                        int nao, int ic, int jc)
{
        CVHFnrs2kl_kl_s1ij_o0(eri, dm, vj, nao, ic, jc);
}
void CVHFnrs2kl_jk_s1il(double *eri, double *dm, double *vk,
                        int nao, int ic, int jc)
{
        int k, l, kl;
        for (k = 0, kl = 0; k < nao; k++) {
                for (l = 0; l < k; l++, kl++) {
                        vk[ic*nao+l] += eri[kl] * dm[jc*nao+k];
                        vk[ic*nao+k] += eri[kl] * dm[jc*nao+l];
                }
                vk[ic*nao+k] += eri[kl] * dm[jc*nao+k];
                kl++;
        }
}
void CVHFnrs2kl_il_s1jk(double *eri, double *dm, double *vk,
                        int nao, int ic, int jc)
{
        int k, l, kl;
        for (k = 0, kl = 0; k < nao; k++) {
                for (l = 0; l < k; l++, kl++) {
                        vk[jc*nao+l] += eri[kl] * dm[ic*nao+k];
                        vk[jc*nao+k] += eri[kl] * dm[ic*nao+l];
                }
                vk[jc*nao+k] += eri[kl] * dm[ic*nao+k];
                kl++;
        }
}


/**************************************************
 * s8   8-fold symmetry: i>=j,k>=l,ij>=kl
 * s4   4-fold symmetry: i>=j,k>=l
 * s2ij 2-fold symmetry: i>=j
 * s2kl 2-fold symmetry: k>=l
 * s1   no permutation symmetry
 **************************************************/
void CVHFnrs8_incore_drv(double *eri, double *dmj, double *vj,
                         double *dmk, double *vk,
                         int n, void (*const fvj)(), void (*const fvk)())
{
        const int npair = n*(n+1)/2;
        double *vj_priv, *vk_priv;
        int i, j;
        size_t ij, off;

        memset(vj, 0, sizeof(double)*n*n);
        memset(vk, 0, sizeof(double)*n*n);

#pragma omp parallel default(none) \
        shared(eri, dmj, dmk, vj, vk, n) \
        private(ij, i, j, off, vj_priv, vk_priv)
        {
                vj_priv = malloc(sizeof(double)*n*n);
                vk_priv = malloc(sizeof(double)*n*n);
                memset(vj_priv, 0, sizeof(double)*n*n);
                memset(vk_priv, 0, sizeof(double)*n*n);
#pragma omp for nowait schedule(dynamic, 4)
                for (ij = 0; ij < npair; ij++) {
                        i = (int)(sqrt(2*ij+.25) - .5 + 1e-7);
                        j = ij - i*(i+1)/2;
                        off = ij*(ij+1)/2;
                        (*fvj)(eri+off, dmj, vj_priv, n, i, j);
                        (*fvk)(eri+off, dmk, vk_priv, n, i, j);
                }
#pragma omp critical
                {
                        for (i = 0; i < n*n; i++) {
                                vj[i] += vj_priv[i];
                                vk[i] += vk_priv[i];
                        }
                }
                free(vj_priv);
                free(vk_priv);
        }
}

void CVHFnrs4_incore_drv(double *eri, double *dmj, double *vj,
                         double *dmk, double *vk,
                         int n, void (*const fvj)(), void (*const fvk)())
{
        const int npair = n*(n+1)/2;
        double *vj_priv, *vk_priv;
        int i, j;
        size_t ij, off;

        memset(vj, 0, sizeof(double)*n*n);
        memset(vk, 0, sizeof(double)*n*n);

#pragma omp parallel default(none) \
        shared(eri, dmj, dmk, vj, vk, n) \
        private(ij, i, j, off, vj_priv, vk_priv)
        {
                vj_priv = malloc(sizeof(double)*n*n);
                vk_priv = malloc(sizeof(double)*n*n);
                memset(vj_priv, 0, sizeof(double)*n*n);
                memset(vk_priv, 0, sizeof(double)*n*n);
#pragma omp for nowait schedule(dynamic, 4)
                for (ij = 0; ij < npair; ij++) {
                        i = (int)(sqrt(2*ij+.25) - .5 + 1e-7);
                        j = ij - i*(i+1)/2;
                        off = ij * npair;
                        (*fvj)(eri+off, dmj, vj_priv, n, i, j);
                        (*fvk)(eri+off, dmk, vk_priv, n, i, j);
                }
#pragma omp critical
                {
                        for (i = 0; i < n*n; i++) {
                                vj[i] += vj_priv[i];
                                vk[i] += vk_priv[i];
                        }
                }
                free(vj_priv);
                free(vk_priv);
        }
}

void CVHFnrs2ij_incore_drv(double *eri, double *dmj, double *vj,
                           double *dmk, double *vk,
                           int n, void (*const fvj)(), void (*const fvk)())
{
        const int npair = n*(n+1)/2;
        double *vj_priv, *vk_priv;
        int i, j;
        size_t ij, off;

        memset(vj, 0, sizeof(double)*n*n);
        memset(vk, 0, sizeof(double)*n*n);

#pragma omp parallel default(none) \
        shared(eri, dmj, dmk, vj, vk, n) \
        private(ij, i, j, off, vj_priv, vk_priv)
        {
                vj_priv = malloc(sizeof(double)*n*n);
                vk_priv = malloc(sizeof(double)*n*n);
                memset(vj_priv, 0, sizeof(double)*n*n);
                memset(vk_priv, 0, sizeof(double)*n*n);
#pragma omp for nowait schedule(dynamic, 4)
                for (ij = 0; ij < npair; ij++) {
                        i = (int)(sqrt(2*ij+.25) - .5 + 1e-7);
                        j = ij - i*(i+1)/2;
                        off = ij * n * n;
                        (*fvj)(eri+off, dmj, vj_priv, n, i, j);
                        (*fvk)(eri+off, dmk, vk_priv, n, i, j);
                }
#pragma omp critical
                {
                        for (i = 0; i < n*n; i++) {
                                vj[i] += vj_priv[i];
                                vk[i] += vk_priv[i];
                        }
                }
                free(vj_priv);
                free(vk_priv);
        }
}

void CVHFnrs2kl_incore_drv(double *eri, double *dmj, double *vj,
                           double *dmk, double *vk,
                           int n, void (*const fvj)(), void (*const fvk)())
{
        const int npair = n*(n+1)/2;
        double *vj_priv, *vk_priv;
        int i, j;
        size_t ij, off;

        memset(vj, 0, sizeof(double)*n*n);
        memset(vk, 0, sizeof(double)*n*n);

#pragma omp parallel default(none) \
        shared(eri, dmj, dmk, vj, vk, n) \
        private(ij, i, j, off, vj_priv, vk_priv)
        {
                vj_priv = malloc(sizeof(double)*n*n);
                vk_priv = malloc(sizeof(double)*n*n);
                memset(vj_priv, 0, sizeof(double)*n*n);
                memset(vk_priv, 0, sizeof(double)*n*n);
#pragma omp for nowait schedule(dynamic, 4)
                for (ij = 0; ij < n*n; ij++) {
                        i = ij / n;
                        j = ij - i * n;
                        off = ij * npair;
                        (*fvj)(eri+off, dmj, vj_priv, n, i, j);
                        (*fvk)(eri+off, dmk, vk_priv, n, i, j);
                }
#pragma omp critical
                {
                        for (i = 0; i < n*n; i++) {
                                vj[i] += vj_priv[i];
                                vk[i] += vk_priv[i];
                        }
                }
                free(vj_priv);
                free(vk_priv);
        }
}

void CVHFnrs1_incore_drv(double *eri, double *dmj, double *vj,
                         double *dmk, double *vk,
                         int n, void (*const fvj)(), void (*const fvk)())
{
        double *vj_priv, *vk_priv;
        int i, j;
        size_t ij, off;

        memset(vj, 0, sizeof(double)*n*n);
        memset(vk, 0, sizeof(double)*n*n);

#pragma omp parallel default(none) \
        shared(eri, dmj, dmk, vj, vk, n) \
        private(ij, i, j, off, vj_priv, vk_priv)
        {
                vj_priv = malloc(sizeof(double)*n*n);
                vk_priv = malloc(sizeof(double)*n*n);
                memset(vj_priv, 0, sizeof(double)*n*n);
                memset(vk_priv, 0, sizeof(double)*n*n);
#pragma omp for nowait schedule(dynamic, 4)
                for (ij = 0; ij < n*n; ij++) {
                        i = ij / n;
                        j = ij - i * n;
                        off = ij * n * n;
                        (*fvj)(eri+off, dmj, vj_priv, n, i, j);
                        (*fvk)(eri+off, dmk, vk_priv, n, i, j);
                }
#pragma omp critical
                {
                        for (i = 0; i < n*n; i++) {
                                vj[i] += vj_priv[i];
                                vk[i] += vk_priv[i];
                        }
                }
                free(vj_priv);
                free(vk_priv);
        }
}

