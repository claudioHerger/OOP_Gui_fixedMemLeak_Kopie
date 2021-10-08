#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Helper module for TA data analysis GUI.\n\n
To provide data matrix that is reconstructed as:\n
reduced_data = [left singular vectors] * [singular values] * [right singular vectors].\n
wherein only the SVD components are used as given by the input retained_components
"""

import numpy as np
import scipy

def run(data, retained_components):
    U, sigma, VT = scipy.linalg.svd(data)

    # need the singular values in matrix form too! (for matrix multiplication)
    Sigma = np.diag(sigma)

    # only retain those leftSVs, rightSVs and singular values in Sigma that are given in retained_components
    retained_U = U[:, retained_components]
    retained_VT = VT[retained_components, :]
    retained_Sigma = Sigma[retained_components, :]
    retained_Sigma = retained_Sigma[:, retained_components]

    noise_reduced_data_matrix = np.matmul(np.matmul(retained_U, retained_Sigma), retained_VT)

    return noise_reduced_data_matrix, sigma, U, VT
