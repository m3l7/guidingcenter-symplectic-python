from emFields.eqdskReader.eqdskReader import EqdskReader
from emFields.AB_dBfields.AB_dBfield import AB_dB_FieldBuilder, ABdBGuidingCenter
import numpy as np
import sys


def cyl2cart(v, x):
    r = np.sqrt(x[0]*x[0] + x[1]*x[1])
    ret = np.zeros(3)
    ret[0] = (v[0]*x[0] - v[1]*x[1]) / r
    ret[1] = (v[0]*x[1] + v[1]*x[0]) / r
    ret[2] = v[2]
    return ret


class GradShafranov_Spline_ABdB(AB_dB_FieldBuilder):
    def __init__(self, config):
        self.eqdsk = EqdskReader(config.eqdskFile, config.psi_degree, config.f_degree)
        self.R0 = config.R0
        self.B0 = config.B0
        self.hx = config.hx
        self.c = 2.998E8
        self.A0 = config.m*self.c/config.q  # 1.7E-3, A_norm = A / A0

        print("EQDSK: range r: {} {}".format(self.eqdsk.r_min, self.eqdsk.r_max))
        print("EQDSK: range z: {} {}".format(self.eqdsk.z_min, self.eqdsk.z_max))
        print("EQDSK: range psi: {} {}".format(self.eqdsk.simag, self.eqdsk.sibry))

    def B_Hessian_num(self, z):
        ret = np.zeros([3, 3])
        for j in range(3):
            z0 = np.array(z)
            z1 = np.array(z)
            z0[j] -= self.hx
            z1[j] += self.hx
            field1 = self.compute(z1)
            field0 = self.compute(z0)
            ret[:, j] = 0.5*(field1.Bgrad - field0.Bgrad) / self.hx

        return ret

    def B_dB_cyl(self, R, Z):

        # interpolate psi and derivatives
        psi = self.eqdsk.psi_spl(x=R, y=Z)[0][0]
        dpsi_dR = self.eqdsk.psi_spl(x=R, y=Z, dx=1, dy=0, grid=True)[0][0]
        dpsi_dz = self.eqdsk.psi_spl(x=R, y=Z, dx=0, dy=1, grid=True)[0][0]
        d2psi_dR2 = self.eqdsk.psi_spl(x=R, y=Z, dx=2, dy=0, grid=True)[0][0]
        d2psi_dRdz = self.eqdsk.psi_spl(x=R, y=Z, dx=1, dy=1, grid=True)[0][0]
        d2psi_dz2 = self.eqdsk.psi_spl(x=R, y=Z, dx=0, dy=2, grid=True)[0][0]
        d3psi_d2Rdz = self.eqdsk.psi_spl(x=R, y=Z, dx=2, dy=1, grid=True)[0][0]
        d3psi_dRd2z = self.eqdsk.psi_spl(x=R, y=Z, dx=1, dy=2, grid=True)[0][0]
        d3psi_d3z = self.eqdsk.psi_spl(x=R, y=Z, dx=0, dy=3, grid=True)[0][0]
        d3psi_d3R = self.eqdsk.psi_spl(x=R, y=Z, dx=3, dy=0, grid=True)[0][0]

        if psi > max(self.eqdsk.sibry, self.eqdsk.simag) or psi < min(self.eqdsk.sibry, self.eqdsk.simag) \
           or Z > self.eqdsk.sepmaxz or Z < self.eqdsk.sepminz:
            print("WARNING: outside main plasma. psi: {}, Z: {}, R: {}".format(psi, Z, R))

            sys.exit(0)

        # evaluate the magnetic field
        BR = -dpsi_dz/R
        Bp = self.B0 * self.R0 / R
        Bz = dpsi_dR/R
        # evaluate the derivatives
        dBR_dR = dpsi_dz/(R**2)-d2psi_dRdz/R
        dBR_dp = 0.
        dBR_dz = -d2psi_dz2/R
        dBp_dR = - self.B0 * self.R0 / (R**2)
        dBp_dp = 0.
        dBp_dz = 0.
        dBz_dR = -dpsi_dR/(R**2) + d2psi_dR2/R
        dBz_dp = 0.
        dBz_dz = d2psi_dRdz/R

        d2BR_d2R = -2 * dpsi_dz / (R**3) + 2 * d2psi_dRdz / (R**2) - d3psi_d2Rdz / R
        d2BR_dRdz = d2psi_dz2 / (R**2) - d3psi_dRd2z / R
        d2BR_d2z = -d3psi_d3z / R
        d2Bp_d2R = 2 * self.B0 * self.R0 / (R**3)
        d2Bp_dRdz = 0.
        d2Bp_d2z = 0.
        d2Bz_d2R = 2 * dpsi_dR / (R**3) - 2 * d2psi_dR2 / (R**2) + d3psi_d3R / R
        d2Bz_dRdz = -d2psi_dRdz / (R**2) + d3psi_d2Rdz / R
        d2Bz_d2z = d3psi_dRd2z / R

        return np.array([BR, Bp, Bz,
                         dBR_dR, dBR_dp, dBR_dz,
                         dBp_dR, dBp_dp, dBp_dz,
                         dBz_dR, dBz_dp, dBz_dz,
                         d2BR_d2R, d2BR_dRdz, d2BR_d2z,
                         d2Bp_d2R, d2Bp_dRdz, d2Bp_d2z,
                         d2Bz_d2R, d2Bz_dRdz, d2Bz_d2z]) / self.A0

    def A(self, x):
        r = np.sqrt(x[0]**2 + x[1]**2)
        z = x[2]
        sintheta = x[1] / r
        costheta = x[0] / r

        psi = self.eqdsk.psi_spl(x=r, y=z)[0][0]
        dpsi_dR = self.eqdsk.psi_spl(x=r, y=z, dx=1, dy=0, grid=True)[0][0]
        dpsi_dz = self.eqdsk.psi_spl(x=r, y=z, dx=0, dy=1, grid=True)[0][0]

        Acyl = np.array([0, psi/r, - self.B0 * self.R0 * np.log(r / self.R0)])
        A = cyl2cart(Acyl, x)

        # compute Ajac
        dAx_dr = psi / r**2 * sintheta - dpsi_dR / r * sintheta
        dAx_dp = - psi / r**2 * costheta
        dAx_dz = - dpsi_dz / r * sintheta
        dAy_dr = - psi / r**2 * costheta + dpsi_dR / r * costheta
        dAy_dp = - psi / r**2 * sintheta
        dAy_dz = dpsi_dz / r * costheta
        dAz_dr = -self.B0 * self.R0 / r
        dAz_dp = 0
        dAz_dz = 0
        Ajac = np.zeros([3, 3])
        Ajac[0, :] = cyl2cart(np.array([dAx_dr, dAx_dp, dAx_dz]), x)
        Ajac[1, :] = cyl2cart(np.array([dAy_dr, dAy_dp, dAy_dz]), x)
        Ajac[2, :] = cyl2cart(np.array([dAz_dr, dAz_dp, dAz_dz]), x)
        return [A / self.A0, Ajac / self.A0]

    """Compute the third derivative of the magnetic field at the given 4D position

    Returns:
        [numpy.array([3, 3, 3])]
    """
    def d3B(self, z):
        ret = np.zeros([3, 3, 3])

        for i in range(3):
            # print("i " + str(i))
            z1 = np.array(z)
            z0 = np.array(z)
            z1[i] += self.hx
            z0[i] -= self.hx
            BdB1 = self.compute(z1)
            BdB0 = self.compute(z0)
            for j in range(3):
                for k in range(3):
                    ret[i, j, k] = 0.5 * (BdB1.BHessian[j, k] - BdB0.BHessian[j, k]) / self.hx

        # print("\n\n===== D3B")
        # print(ret)
        # # print(ret[1,0,0])
        # # print(ret[0,1,0])
        # print("=====\n\n")
        return ret

    """Compute the magnetic field and first and second derivatives at the given 4D position

    Returns:
        [ABdBGuidingCenter]
    """
    def compute(self, z):
        x = z[:3]
        r = np.sqrt(x[0]**2 + x[1]**2)
        u = z[3]
        # theta = np.arctan(x[1]/x[0])
        sintheta = x[1] / r
        costheta = x[0] / r

        BdB = self.B_dB_cyl(r, x[2])
        Bcyl = np.array([BdB[0], BdB[1], BdB[2]])

        # build B, B and |B| (cartesian)
        B = cyl2cart(Bcyl, x)
        Bnorm = np.linalg.norm(B)
        b = B / Bnorm

        A_Ajac = self.A(x)
        A = A_Ajac[0]
        Ajac = A_Ajac[1]
        Adag = A + u * b

        # build curl B (cyl and cartesian)
        Bcurl_cyl = np.zeros(3)
        Bcurl_cyl[0] = - BdB[8]
        Bcurl_cyl[1] = BdB[5] - BdB[9]
        Bcurl_cyl[2] = Bcyl[1] / r + BdB[6]
        Bcurl = cyl2cart(Bcurl_cyl, x)

        # build grad|B| (cyl and cartesian)
        dB_dR = np.array([BdB[3], BdB[6], BdB[9]])
        dB_dz = np.array([BdB[5], BdB[8], BdB[11]])
        gradB_cyl = np.zeros(3)
        gradB_cyl[0] = np.dot(Bcyl, dB_dR)
        gradB_cyl[1] = 0
        gradB_cyl[2] = np.dot(Bcyl, dB_dz)
        gradB_cyl /= Bnorm
        B_grad = cyl2cart(gradB_cyl, x)

        # build grad(1/|B|) and Bdag
        grad1_B = - B_grad / Bnorm**2
        Bdag = B + u * Bcurl / Bnorm + u * np.cross(grad1_B, B)

        # compute Bjac
        dBx_dr = BdB[3] * costheta - BdB[6] * sintheta
        dBx_dp = - BdB[0] * sintheta / r - BdB[1] * costheta / r
        dBx_dz = BdB[5] * costheta - BdB[8] * sintheta / r
        dBy_dr = BdB[3] * sintheta + BdB[6] * costheta
        dBy_dp = + BdB[0] * costheta / r - BdB[1] * sintheta / r
        dBy_dz = BdB[5] * sintheta + BdB[8] * costheta / r
        dBz_dr = BdB[9]
        dBz_dp = 0
        dBz_dz = BdB[11]
        Bjac = np.zeros([3, 3])
        Bjac[0, :] = cyl2cart(np.array([dBx_dr, dBx_dp, dBx_dz]), x)
        Bjac[1, :] = cyl2cart(np.array([dBy_dr, dBy_dp, dBy_dz]), x)
        Bjac[2, :] = cyl2cart(np.array([dBz_dr, dBz_dp, dBz_dz]), x)

        Adag_jac = Ajac + u * Bjac / Bnorm
        Adag_jac[0, :] += u * B[0] * np.transpose(grad1_B)
        Adag_jac[1, :] += u * B[1] * np.transpose(grad1_B)
        Adag_jac[2, :] += u * B[2] * np.transpose(grad1_B)

        # compute |B| hessian
        d2B_d2R = np.array([BdB[12], BdB[15], BdB[18]])
        d2B_dRdz = np.array([BdB[13], BdB[16], BdB[19]])
        d2B_d2z = np.array([BdB[14], BdB[17], BdB[20]])
        d2modB_d2R = - np.dot(Bcyl, dB_dR)**2 / (Bnorm**2) + np.dot(dB_dR, dB_dR) + np.dot(Bcyl, d2B_d2R)
        d2modB_dRdz = - np.dot(Bcyl, dB_dR)*np.dot(Bcyl, dB_dz) / (Bnorm**2) + np.dot(dB_dR, dB_dz) +\
            np.dot(Bcyl, d2B_dRdz)
        d2modB_d2z = - np.dot(Bcyl, dB_dz)**2 / (Bnorm**2) + np.dot(dB_dz, dB_dz) + np.dot(Bcyl, d2B_d2z)
        d2modB_d2R /= Bnorm
        d2modB_dRdz /= Bnorm
        d2modB_d2z /= Bnorm

        gradCyl_dmodB_dx = np.array([d2modB_d2R * costheta, -gradB_cyl[0] * sintheta / r,
                                    d2modB_dRdz * costheta])
        gradCyl_dmodB_dy = np.array([d2modB_d2R * sintheta, gradB_cyl[0] * costheta / r,
                                    d2modB_dRdz * sintheta])
        gradCyl_dmodB_dz = np.array([d2modB_dRdz, 0, d2modB_d2z])

        BHessian = np.zeros([3, 3])
        BHessian[0, :] = cyl2cart(gradCyl_dmodB_dx, x)
        BHessian[1, :] = cyl2cart(gradCyl_dmodB_dy, x)
        BHessian[2, :] = cyl2cart(gradCyl_dmodB_dz, x)

        # print("\n\n===== Bhessian")
        # print(BHessian)
        # print("=====\n\n")

        return ABdBGuidingCenter(Adag_jac=Adag_jac, A=A, Adag=Adag,
                                 B=B, Bgrad=B_grad, b=b, Bnorm=Bnorm, BHessian=BHessian, Bdag=Bdag)
