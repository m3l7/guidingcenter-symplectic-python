# Symplectic integrator for guiding center, explicit 3 (paragraph 6.4.6)
import numpy as np
from integrators.variationalIntegrators.variationalIntegrator import VariationalIntegrator


class SymplecticExplicit3(VariationalIntegrator):
    def __init__(self, config):
        super().__init__(config)

    def legendreRight(self, z0, z1, h):

        field = self.system.fieldBuilder.compute(z1)

        M = np.zeros([4, 4])
        p1 = np.zeros(4)

        # BUILD M
        M[0, 1] = field.Bdag[2]
        M[0, 2] = -field.Bdag[1]
        M[1, 0] = -field.Bdag[2]
        M[1, 2] = field.Bdag[0]
        M[2, 0] = field.Bdag[1]
        M[2, 1] = -field.Bdag[0]
        M[0, 3] = -field.b[0]
        M[1, 3] = -field.b[1]
        M[2, 3] = -field.b[2]
        M[3, 0] = field.b[0]
        M[3, 1] = field.b[1]
        M[3, 2] = field.b[2]
        M[0, 0] = M[1, 1] = M[2, 2] = M[3, 3] = 0

        # qin modified version (explicit 3)
        M[3, 3] = h
        M[0, 3] = M[1, 3] = M[2, 3] = 0
        for i in range(3):
            for j in range(3):
                M[i, j] += 2.*field.b[i]*field.b[j] / h

        M /= 2.

        dq = z1 - z0
        Q = np.dot(M, dq)

        p1[:3] = Q[:3] + field.Adag - h / 2.*self.config.mu*field.Bgrad
        p1[3] = Q[3] - h/2.*z1[3]

        return p1

    def legendreLeftInverse(self, points_z0z1p0p1, h):

        p1 = points_z0z1p0p1.p1
        z1 = points_z0z1p0p1.z1

        field = self.system.fieldBuilder.compute(z1)

        M = np.zeros([4, 4])
        W = np.zeros(4)
        z2 = np.zeros(4)

        # BUILD M
        M[0, 1] = field.Bdag[2]
        M[0, 2] = -field.Bdag[1]
        M[1, 0] = -field.Bdag[2]
        M[1, 2] = field.Bdag[0]
        M[2, 0] = field.Bdag[1]
        M[2, 1] = -field.Bdag[0]
        M[0, 3] = -field.b[0]
        M[1, 3] = -field.b[1]
        M[2, 3] = -field.b[2]
        M[3, 0] = field.b[0]
        M[3, 1] = field.b[1]
        M[3, 2] = field.b[2]
        M[0, 0] = M[1, 1] = M[2, 2] = M[3, 3] = 0

        # qin modified version (explicit 3)
        M[3, 3] = -h
        M[0, 3] = M[1, 3] = M[2, 3] = 0

        for i in range(3):
            for j in range(3):
                M[i, j] -= 2.*field.b[i]*field.b[j] / h

        M /= 2.

        # BUILD W
        W[:3] = h/2.*(self.config.mu*field.Bgrad) + field.Adag - p1[:3]
        W[3] = h/2.*z1[3] - p1[3]

        Q = np.dot(np.linalg.inv(M), W)

        z2 = z1 + Q

        return z2
