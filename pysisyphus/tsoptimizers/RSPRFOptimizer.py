#!/usr/bin/env python3

# See [1] https://pubs.acs.org/doi/pdf/10.1021/j100247a015
#         Banerjee, 1985
#     [2] https://aip.scitation.org/doi/abs/10.1063/1.2104507
#         Heyden, 2005
#     [3] https://onlinelibrary.wiley.com/doi/abs/10.1002/jcc.540070402
#         Baker, 1985
#     [4] https://link.springer.com/article/10.1007/s002140050387
#         Besalu, 1998


import numpy as np

from pysisyphus.tsoptimizers.TSHessianOptimizer import TSHessianOptimizer


class RSPRFOptimizer(TSHessianOptimizer):

    def optimize(self):
        energy, gradient, H, eigvals, eigvecs = self.housekeeping()
        self.update_ts_mode(eigvals, eigvecs)

        # Transform gradient to eigensystem of hessian
        gradient_trans = eigvecs.T.dot(gradient)

        # Minimize energy along all modes, except the TS-mode
        min_indices = [i for i in range(gradient_trans.size) if i != self.root]
        min_mat = np.asarray(np.bmat((
            (np.diag(eigvals[min_indices]), gradient_trans[min_indices,None]),
            (gradient_trans[None,min_indices], [[0]])
        )))
        # Maximize energy along the chosen TS mode. The matrix is hardcoded
        # as 2x2, so only first-order saddle point searches are supported.
        max_mat = np.array(((eigvals[self.root], gradient_trans[self.root]),
                           (gradient_trans[self.root], 0)))

        min_diag_indices = np.diag_indices(min_mat.shape[0])

        """In the RS-(P)RFO method we have to scale the matrices with alpha.
        Unscaled matrix (Eq. 8) in [1]:
            (H  g) (x)          (S 0) (x)
                       = lambda
            (g+ 0) (1)          (0 1) (1)
        with
            S = alpha * Identity matrix
        and multiplying from the left with the inverse of the scaling matrix
            (1/alpha 0)

            (0       1)
        we get
            (1/alpha 0) (H  g) (x)          (x)
                                   = lambda
            (0       1) (g+ 0) (1)          (1)
        eventually leading to the scaled matrix:
            (H/alpha  g/alpha) (x)          (x)
                                   = lambda     .
            (g+             0) (1)          (1)
        """
        alpha = self.alpha0
        for mu in range(self.max_micro_cycles):
            self.log(f"RS-PRFO micro cycle {mu:02d}, alpha={alpha:.6f}")
            max_mat_scaled = max_mat.copy()
            # Create the scaled max. matrix
            max_mat_scaled[0, 0] /= alpha
            max_mat_scaled[0, 1] /= alpha
            step_max, eigval_max, nu_max = self.solve_rfo(max_mat_scaled, "max")
            step_max = step_max[0]
            # Create the scaled min. matrix
            scaled_min_eigenvalues = np.zeros_like(eigvals)
            scaled_min_eigenvalues[:-1] = eigvals[min_indices] / alpha
            min_mat_scaled = min_mat.copy()
            min_mat_scaled[min_diag_indices] = scaled_min_eigenvalues
            min_mat_scaled[:-1,-1] /= alpha
            step_min, eigval_min, nu_min = self.solve_rfo(min_mat_scaled, "min")

            # Calculate overlap between directions over the course of the micro cycles
            # if mu == 0:
                # TODO: convert back to original space
                # ref_step_max = step_max.copy()
                # ref_step_min = step_min.copy()
            min_norm = np.linalg.norm(step_min)
            max_norm = np.linalg.norm(step_max)
            self.log(f"norm(step_max)={max_norm:.6f}")
            self.log(f"norm(step_min)={min_norm:.6f}")
            self.log(f"norm(step_max)/norm(step_min)={max_norm/min_norm:.2%}")
            # Calculate overlaps with originally proposed step in mu == 0
            # TODO: convert back to original space
            # max_ovlp = ref_step_max @ step_max
            # min_ovlp = ref_step_min @ step_min

            # As of Eq. (8a) of [4] max_eigval and min_eigval also
            # correspond to:
            # max_eigval = -forces_trans[self.root] * max_step
            # min_eigval = -forces_trans[min_indices].dot(min_step)

            # Create the full PRFO step
            step = np.zeros_like(gradient_trans)
            step[self.root] = step_max
            step[min_indices] = step_min
            step_norm = np.linalg.norm(step)
            self.log(f"norm(step)={step_norm:.6f}")

            inside_trust = step_norm <= self.trust_radius
            if inside_trust:
                self.log( "Restricted step satisfies trust radius of "
                         f"{self.trust_radius:.6f}")
                self.log(f"Micro-cycles converged in cycle {mu:02d} with "
                         f"alpha={alpha:.6f}!")
                break

            # Derivative of the squared step w.r.t. alpha
            # max subspace
            dstep2_dalpha_max = (2*eigval_max/(1+step_max**2 * alpha)
                                 * gradient_trans[self.root]**2
                                 / (eigvals[self.root] - eigval_max * alpha)**3
            )
            # min subspace
            dstep2_dalpha_min = (2*eigval_min/(1+step_min.dot(step_min) * alpha)
                                 * np.sum(gradient_trans[min_indices]**2
                                          / (eigvals[min_indices] - eigval_min * alpha)**3
                                 )
            )
            dstep2_dalpha = dstep2_dalpha_max + dstep2_dalpha_min
            # Update alpha
            alpha_step = (2*(self.trust_radius*step_norm - step_norm**2)
                          / dstep2_dalpha
            )
            alpha += alpha_step
            assert alpha > 0, "alpha must not be negative!"

        # Right now the step is still given in the Hessians eigensystem. We
        # transform it back now.
        step = eigvecs.dot(step)
        step_norm = np.linalg.norm(step)

        # With max_micro_cycles = 1 the RS part is disabled and the step
        # probably isn't scaled correctly in the one micro cycle.
        # In this case we use a naive scaling if the step is too big.
        if (self.max_micro_cycles == 1) and (step_norm > self.trust_radius):
            step = step / step_norm * self.trust_radius
        self.log(f"norm(step)={np.linalg.norm(step):.6f}")

        # Eq. (6) from [4] seems erronous ... the prediction is usually only ~50%
        # of the actual change ...
        # predicted_energy_change = 1/2 * (eigval_max / nu_max**2 + eigval_min / nu_min**2)
        # self.predicted_energy_changes.append(predicted_energy_change)

        quadratic_prediction = step @ gradient + 0.5 * step @ self.H @ step
        rfo_prediction = quadratic_prediction / (1 + step @ step)
        self.predicted_energy_changes.append(rfo_prediction)

        self.log("")
        return step
