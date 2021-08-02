#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Helper module for TA data analysis GUI.\n\n
Used e.g. for SVD_GlobalFit data reconstruction.\n
* data = TA data after time zero\n
* retained_components = selected/retained components for data reconstruction.\n
Returns: the retained right and left singular vectors and the retained singular values.
"""

import scipy

def run(data, retained_components):
    U, sigma, VT = scipy.linalg.svd(data)

    # only retain those leftSVs, rightSVs and singular values as given by retained_components
    retained_U = U[:, retained_components]
    retained_VT = VT[retained_components, :]
    retained_sigma = sigma[retained_components]
    # print(f"retained components: {retained_components}")
    # print(f'retained sing_values: {retained_sigma}')

    return retained_VT, retained_U, retained_sigma