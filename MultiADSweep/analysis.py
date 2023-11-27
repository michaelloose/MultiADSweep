"""
evaluation.py

This module contains functions for advanced data anylysis.
Author: Michael Loose
Date: 18. Sep. 2023
Institution: Friedrich-Alexander-Universität Erlangen, Lehrstuhl für technische Elektronik
License: MIT

"""


import numpy as np
from scipy.interpolate import Rbf
from scipy.optimize import minimize


def find_2d_max_interp(gamma_points, values):
    """
    Find the global maximum of a 2D scalar field defined by irregularly distributed complex coordinates.

    Parameters:
    ---
    gamma_points (list of complex): The coordinates of the points.
    values (list of float): The scalar values at each point.

    Returns:
    ---
    tuple: A tuple containing the complex coordinate of the global maximum and its value.
    """
    # Convert complex numbers to real and imaginary parts
    x = [p.real for p in gamma_points]
    y = [p.imag for p in gamma_points]

    # Create a radial basis function interpolation
    rbf = Rbf(x, y, values, function='gaussian')

    # Define an objective function for minimization (negative of the maximum)
    def objective_function(point):
        return -rbf(point[0], point[1])

    # Starting point for the optimization (center of the coordinates)
    initial_point = [np.mean(x), np.mean(y)]

    # Minimize the negative interpolated function
    result = minimize(objective_function, initial_point, method='L-BFGS-B')

    # Return the maximum value and the corresponding point
    max_value = -result.fun
    max_point = complex(result.x[0], result.x[1])

    return max_point, max_value