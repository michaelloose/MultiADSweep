"""
utilities.py

This module provides a collection of utility functions being used
within this library but can also be helpful for external applications.
These functions offer various helper functionalities to streamline common tasks.

Author: Michael Loose
Date: 18. Sep. 2023
Institution: Friedrich-Alexander-Universität Erlangen, Lehrstuhl für technische Elektronik
License: MIT

"""

import numpy as np
import re
import subprocess
import os
from typing import Optional, Union
from pathlib import Path
from scipy.spatial import KDTree



def robust_byte_decode(byte_str:bytes, format="utf-8") -> str:
    """
    Decodes a byte string into a string using the specified encoding (default is UTF-8). 
    If there are any non-decodable characters, they are replaced with their hex representation.
    
    Parameters:
    ---
    - byte_str (bytes): The byte string to decode.
    - format (str): The encoding format to use for decoding. Default is "utf-8".
    
    Returns:
    ---
    - str: The decoded string with non-decodable characters replaced by their hex representation.
    """
    # Try to decode the byte string
    try:
        return byte_str.decode(format)
    except UnicodeDecodeError as e:
        # If an error occurs, replace the non-decodable character with its hex value and process the subsequent string recursively
        faulty_byte = byte_str[e.start:e.end]
        replacement = r'\x' + faulty_byte.hex()
        return byte_str[:e.start].decode(format) + replacement + robust_byte_decode(byte_str[e.end:], format=format)

# With Option to exclude Datasets. Not fully validated
# def fast_copy_dir(src: Path, dst: Path, exclude_datasets=False):
#     """
#     Copies the contents of the source directory to the destination directory quickly,
#     with an option to exclude .ds files. It first tries to use rsync, then falls back
#     to shutil if rsync is not available.

#     If the destination directory exists, it is first removed to ensure a clean copy.

#     Parameters:
#     - src (pathlib.Path): Path to the source directory.
#     - dst (pathlib.Path): Path to the destination directory.
#     - exclude_datasets (bool): If True, exclude .ds files from copying (only works with rsync).
#     """
#     # Ensure the parent directory of the destination exists
#     os.makedirs(dst.parent, exist_ok=True)
    
#     # If the destination directory exists, remove it
#     if os.path.exists(dst):
#         shutil.rmtree(dst)

#     # Check if rsync is available
#     if shutil.which("rsync"):
#         rsync_command = ["rsync", "-a"]
#         if exclude_datasets:
#             rsync_command += ["--exclude", "*.ds"]
#         rsync_command += [str(src) + "/", str(dst)+"/"]
#         subprocess.run(rsync_command,stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

#     # Fallback to shutil
#     else:
#         ignore = shutil.ignore_patterns('*.ds') if exclude_datasets else None
#         shutil.copytree(src, dst, ignore=ignore)


def fast_copy_dir(src: Path, dst: Path, exclude_datasets=False):
    """
    Copies the contents of the source directory to the destination directory using shell.
    
    If the destination directory exists, it is first removed to ensure a clean copy.
    The function uses shell commands for faster performance.
    
    Parameters:
    ---
    - src (pathlib.Path): Path to the source directory.
    - dst (pathlib.Path): Path to the destination directory.
    
    Note:
    ---
    This function requires the subprocess module and assumes that the 'cp' and 'rm' 
    shell commands are available on the system.
    """
    
    # Ensure the parent directory of the destination exists
    os.makedirs(dst.parent, exist_ok=True)
    
    # If the destination directory exists, remove it
    if os.path.exists(dst):
        subprocess.run(["rm", "-rf", dst])
    
    # Use shell command for faster copying
    subprocess.run(["cp", "-r", src, dst])

def modify_netlist(path:Path, vars_dict:dict):
    """
    Modifies the netlist file at the given path by updating variable values.
    
    This function reads the netlist file line by line and checks if a line starts 
    with a variable name followed by an equals sign. If such a line is found, 
    the value of the variable is updated based on the provided vars_dict.
    
    Parameters:
    ---
    - path (pathlib.Path): Path to the netlist file.
    - vars_dict (dict): Dictionary containing variable names as keys and their 
                        desired values as values.
    
    """
    
    # Read the file lines into a list
    with open(path, 'r') as file:
        lines = file.readlines()
    
    modified_lines = []
    
    # Iterate over each line in the file
    for line in lines:
        # Check each variable in the provided dictionary
        for var_name, var_value in vars_dict.items():
            # If the line starts with the variable name and an equals sign, update its value
            if line.startswith(f"{var_name}="):
                line = f"{var_name}={var_value}\n"
            elif line.startswith(f"global {var_name}="):
                line = f"global {var_name}={var_value}\n"
        modified_lines.append(line)

    # Write the modified lines back to the file
    with open(path, 'w') as file:
        file.writelines(modified_lines)

def get_cell_name_from_netlist(path:Path):
    """
    Extracts and returns the cell name from an ADS netlist file

    
    Parameters:
    ---
    - path (pathlib.Path): Path to the netlist file.
    
    Returns:
    ---
    - str: The extracted cell name from the netlist file.
    
    Note:
    The function expects the first line of the netlist file to contain a hierarchy 
    in the format "some:value:cell_name:last_value".
    """
     
    # The first line of the netlist contains the hierarchy. 
    # The cell name is the second last value in this hierarchy.
    with open(path, 'r') as file:
        # In der ersten Zeile der Netlist steht die Hierarchie. Der vorletzte Wert ist hier der Zellenname
        hierarchy = re.findall('"([^"]*)"', file.readline())[0].split(":")
    return hierarchy[-2]
                

def generate_complex_points(
    mode: str = "circular", 
    center: complex = complex(0, 0), 
    radius: float = 1, 
    point_spacing: Optional[float] = None, 
    num_points_per_direction: Optional[int] = None, 
    flat_direction: str = "re", 
    rounding_precision: Union[str, int, None] = "auto"
) -> np.ndarray:
    """
    Generate complex sampling points based on the specified mode and parameters.

    Parameters:
    ---
    - mode (str): Sampling mode. 
        "rectangular": Generates points within a rectangular region defined by the center and radius.
        "circular_scaled": Generates points in a circular pattern by scaling a square grid. This mode will not include points for the maximum extent either in the real or imaginary direction, based on the flat_direction parameter.
        "circular": Generates points within a circle defined by radius. Note: Using this mode will result in an irregular matrix over which ADS might not be able to contour.
    - center (complex): Center of the sampling region.
    - radius (float): Radius for circular sampling or half the side length for rectangular sampling.
    - point_spacing (float, optional): Spacing between points. If provided, num_points is ignored.
    - num_points_per_direction (int, optional): Number of points in one dimension (either rows or columns, whichever is greater). Used only if point_spacing is not provided.
    - flat_direction (str, optional): Direction in which the space is flatly cut off in "circular_scaled" mode. Can be "re" or "im".
    - rounding_precision (str, int, None, optional): Specifies the precision for rounding the complex sampling points.
        "auto" (default): Automatically determines the precision based on the point_spacing.
        int: Specifies the number of decimal places for rounding
        None: No rounding: Use maximum float precision

    Returns:
    ---
    - numpy.ndarray: Array of complex sampling points.
    """
    
    if point_spacing is None and num_points_per_direction is not None:
        x = np.linspace(center.real - radius, center.real + radius, num_points_per_direction)
        y = np.linspace(center.imag - radius, center.imag + radius, num_points_per_direction)    
        if mode == "circularScaled":
            if flat_direction == "re":
                y = np.linspace(center.imag - radius, center.imag + radius, num_points_per_direction+2)  
            else:
                x = np.linspace(center.real - radius, center.real + radius, num_points_per_direction+2)
        point_spacing = 2 * radius / (num_points_per_direction-1)

    else:
        x = np.arange(center.real - radius, center.real + radius + point_spacing, point_spacing)
        y = np.arange(center.imag - radius, center.imag + radius + point_spacing, point_spacing)
    X, Y = np.meshgrid(x, y)
   
    if mode == "rectangular":
        complex_points = X.ravel() + 1j * Y.ravel()
    
    elif mode == "circular":
        complex_points = X.ravel() + 1j * Y.ravel()
        complex_points = complex_points[np.abs(complex_points - center) < radius*1.01]
        
         
    elif mode == "circular_scaled":
        
        if flat_direction == "re":
            # Remove the first and last rows
            Y = Y[1:-1]
            X = X[1:-1]
            # Scale rows
            for i in range(Y.shape[0]):
                scale_factor = np.sqrt(radius**2 - Y[i, 0]**2) / radius
                X[i, :] *= scale_factor
        else:
            # Remove the first and last columns
            X = X[:, 1:-1]
            Y = Y[:, 1:-1]
            # Scale columns
            for i in range(X.shape[1]):
                scale_factor = np.sqrt(radius**2 - X[0, i]**2) / radius
                Y[:, i] *= scale_factor       
        complex_points = X.ravel() + 1j * Y.ravel()
        decimals = len(str(point_spacing).split('.')[1])+1


    else:
        raise ValueError("Invalid mode specified.")
    
    if rounding_precision == "auto":
        decimals = len(str(point_spacing).split('.')[1])
        complex_points = np.round(complex_points.real, decimals) + 1j * np.round(complex_points.imag, decimals)

    elif type(rounding_precision) == int:
        decimals = rounding_precision
        complex_points = np.round(complex_points.real, decimals) + 1j * np.round(complex_points.imag, decimals)

    return complex_points


def nudge_points_apart(points, min_distance):
    """
    Adjust a set of points to ensure that each point is at least a specified minimum distance from every other point.

    Parameters:
    ---
    points (numpy.ndarray): A 2D NumPy array of shape (n, 2), where each row represents the coordinates (x, y) of a point.
    min_distance (float): The minimum allowed distance between any two points.

    Returns:
    ---
    numpy.ndarray: A 2D NumPy array of the same shape as `points`, where each point has been adjusted to ensure the minimum distance.
    """
    tree = KDTree(points)
    adjusted_coordinates = points.copy()

    for i, point in enumerate(points):
        indices = tree.query_ball_point(point, min_distance)

        for j in indices:
            if i != j:
                point_j = adjusted_coordinates[j]
                diff = point_j - point
                distance = np.linalg.norm(diff)

                # Handling of identical points
                if distance < np.finfo(float).eps:
                    # Adding a small random nudge
                    adjustment = np.random.normal(0, np.finfo(float).eps, size=point.shape)
                    adjusted_coordinates[i] -= adjustment
                    adjusted_coordinates[j] += adjustment
                    continue

                if distance < min_distance:
                    direction = diff / distance
                    overlap = min_distance - distance
                    adjustment = direction * overlap / 2
                    adjusted_coordinates[i] -= adjustment
                    adjusted_coordinates[j] += adjustment

    return adjusted_coordinates


def generate_smith_diagram_points(points_per_segment=100, r_values=[0, 0.2, 0.5, 1, 2, 5], x_values=[0, 0.2, 0.5, 1, 2, 5], scale_factor=0.95, chart_type='impedance', minimum_distance=0.0001):
    """
    Generate complex points in the shape of a Smith chart.

    Parameters:
    ---
    points_per_segment (int): Number of points to generate for each segment of the chart.
    r_values (list of floats): List of resistance values for which to generate points.
    x_values (list of floats): List of reactance values for which to generate points.
    scale_factor (float): Scaling factor to apply to the points.
    chart_type (str): Type of Smith chart ('impedance' or 'admittance').
    minimum_distance (float): Minimum distance between any two points.

    Returns:
    ---
    numpy.ndarray: A 2D NumPy array of shape (n, 2), where each row represents the coordinates (x, y) of a point on the Smith chart.
    """
    resistance_points = []
    for resistance in r_values:
        angles = np.linspace(0, 2 * np.pi, points_per_segment)
        x_coords = resistance / (resistance + 1) + (1 / (resistance + 1)) * np.cos(angles)
        y_coords = (1 / (resistance + 1)) * np.sin(angles)
        resistance_points.extend(zip(x_coords, y_coords))

    reactance_points = []
    for reactance in x_values:
        if reactance == 0:
            reactance_points.extend(zip(np.linspace(-1, 1, points_per_segment), np.zeros(points_per_segment)))
            continue

        max_angle = np.arctan(1/reactance) * 2
        angles = np.linspace(0, max_angle, points_per_segment)
        x_coords = 1 - reactance * np.sin(angles)
        y_coords = reactance - reactance * np.cos(angles)
        reactance_points.extend(zip(x_coords, y_coords))
        reactance_points.extend(zip(x_coords, -y_coords))

    all_points = np.array(resistance_points + reactance_points)
    scaled_points = all_points * scale_factor

    if chart_type == 'admittance':
        scaled_points[:, 0] *= -1
    
    if minimum_distance:
        scaled_points = nudge_points_apart(scaled_points, minimum_distance)

    return scaled_points
