"""
calc.py

This module contains a collection of implementations of generic RF/Microwave Calculations

Author: Michael Loose
Date: 18. Sep. 2023
Institution: Friedrich-Alexander-Universität Erlangen, Lehrstuhl für technische Elektronik
License: MIT

"""
import numpy as np
import pandas as pd

def dBm(x:float) -> float:
    """
    Alias for w2dBm
    Converts a linear power value to (dBm).
    
    Parameters:
    - x (float): Linear power value.
    
    Returns:
    - float: Logarithmic representation of the power value in decibels (dB).
    """
    return w2dBm(x)


def mag(z):
    """
    Calculates the magnitude (absolute value) of a complex number or array of complex numbers.

    Parameters:
    - z (complex, np.ndarray, or pd.DataFrame): Complex number, array of complex numbers, or DataFrame containing complex numbers.

    Returns:
    - np.ndarray, float, or pd.DataFrame: Magnitude(s) of the complex number(s).
    """
    if isinstance(z, pd.DataFrame):
        return z.applymap(np.abs)
    else:
        return np.abs(z)

def phase(z, deg=True):
    """
    Calculates the angle (phase) of a complex number or array of complex numbers in degrees or radians.

    Parameters:
    - z (complex, np.ndarray, or pd.DataFrame): Complex number, array of complex numbers, or DataFrame containing complex numbers.
    - deg (bool, optional): Return angle in degrees if True, in radians if False. Default is True.

    Returns:
    - np.ndarray, float, or pd.DataFrame: Angle(s) of the complex number(s) in degrees (or radians).
    """
    if isinstance(z, pd.DataFrame):
        return z.applymap(lambda x: np.angle(x, deg=deg))
    else:
        return np.angle(z, deg=deg)

def real(z):
    """
    Extracts the real part of a complex number or array of complex numbers.

    Parameters:
    - z (complex, np.ndarray, or pd.DataFrame): Complex number, array of complex numbers, or DataFrame containing complex numbers.

    Returns:
    - np.ndarray, float, or pd.DataFrame: Real part(s) of the complex number(s).
    """
    if isinstance(z, pd.DataFrame):
        return z.applymap(np.real)
    else:
        return np.real(z)

def imag(z):
    """
    Extracts the imaginary part of a complex number or array of complex numbers.

    Parameters:
    - z (complex, np.ndarray, or pd.DataFrame): Complex number, array of complex numbers, or DataFrame containing complex numbers.

    Returns:
    - np.ndarray, float, or pd.DataFrame: Imaginary part(s) of the complex number(s).
    """
    if isinstance(z, pd.DataFrame):
        return z.applymap(np.imag)
    else:
        return np.imag(z)

def w2dBm(x:float) -> float:
    """
    Converts a linear power value to (dBm).
    
    Parameters:
    - x (float): Linear power value.
    
    Returns:
    - float: Logarithmic representation of the power value in decibels (dB).
    """
    try:
        return 10*np.log10(x*1000)
    except:
        return np.nan
    
def dBm2W(x:float) -> float:
    """
    Converts a logarithmic (dBm) power value to its linear representation
    
    Parameters:
    - x (float): Linear power value.
    
    Returns:
    - float: Logarithmic representation of the power value in decibels (dB).
    """
    try:
        return (10**(x/10))/1000

    except:
        return np.nan
    
def lin2logP(x:float) -> float:
    """
    Converts a linear power value to its logarithmic (dB) representation.
    
    Parameters:
    - x (float): Linear power value.
    
    Returns:
    - float: Logarithmic representation of the power value in decibels (dB).
    """
    try:
        return 10*np.log10(x)
    except:
        return np.nan
    
def lin2logV(x:float) -> float:
    """
    Converts a linear voltage value to its logarithmic (dB) representation.
    
    Parameters:
    - x (float): Linear voltage value.
    
    Returns:
    - float: Logarithmic representation of the voltage value in decibels (dB).
    """
    try:
        return 20*np.log10(x)
    except:
        return np.nan

def log2linP(x:float) -> float:
    """
    Converts a logarithmic (dB) power value to its linear representation.
    
    Parameters:
    - x (float): Logarithmic power value in decibels (dB).
    
    Returns:
    - float: Linear representation of the power value.
    """
    return (10**(x/10))

def log2linV(x:float) -> float:
    """
    Converts a logarithmic (dB) voltage value to its linear representation.
    
    Parameters:
    - x (float): Logarithmic voltage value in decibels (dB).
    
    Returns:
    - float: Linear representation of the voltage value.
    """
    return (10**(x/20))


def ztos(z, z0=50):
    """
    Converts impedance to reflection coefficient.

    Parameters:
    - z (complex or np.ndarray): Impedance (complex number or array of complex numbers).
    - z0 (float, optional): Reference impedance. Default is 50 Ohms.

    Returns:
    - np.ndarray or complex: Reflection coefficient(s).
    """
    #TBD:
    # AD: Z0 im Zähler müsste konjungiert komplex sein. Das mal genauer recherchieren und nachziehen
    z = np.asarray(z)  # Ensure z is a NumPy array for vectorized operations
    return (z - z0) / (z + z0)

def stoz(s, z0=50):
    """
    Converts reflection coefficient to impedance.

    Parameters:
    - s (complex or np.ndarray): Reflection coefficient (complex number or array of complex numbers).
    - z0 (float, optional): Reference impedance. Default is 50 Ohms.

    Returns:
    - np.ndarray or complex: Impedance(s).
    """
    s = np.asarray(s)  # Ensure s is a NumPy array for vectorized operations
    return z0 * (1 + s) / (1 - s)

def ri(z, f="g"):
    """
    Returns a string representation of complex number(s) in rectangular (cartesian) format.

    Parameters:
    - z (complex or np.ndarray): Complex number or array of complex numbers.
    - f (str, optional): Format specifier. Default is "g".

    Returns:
    - str: String representation of the complex number(s) in rectangular format.
    """
    z = np.asarray(z)
    if z.shape:
        return "\n".join(f"{zi.real:{f}} + {zi.imag:{f}}j" for zi in z)
    else:
        return f"{z.real:{f}} + {z.imag:{f}}j"

def ma(z, f="g"):
    """
    Returns a string representation of complex number(s) in polar format (magnitude and angle).

    Parameters:
    - z (complex or np.ndarray): Complex number or array of complex numbers.
    - f (str, optional): Format specifier. Default is "g".

    Returns:
    - str: String representation of the complex number(s) in polar format.
    """
    z = np.asarray(z)
    mag = np.abs(z)
    angle = np.angle(z, deg=True)

    if z.shape:
        return "\n".join(f"{m:{f}} ∠ {a:{f}}°" for m, a in zip(mag, angle))
    else:
        return f"{mag:{f}} ∠ {angle:{f}}°"


def polar(mag, ang, deg=True):
    """
    Converts polar coordinates (magnitude and angle) to a complex number.

    Parameters:
    - mag (float): Magnitude of the complex number.
    - ang (float): Angle of the complex number, in degrees if deg=True, otherwise in radians.
    - deg (bool, optional): Specifies if the angle is in degrees (True) or radians (False). Default is True.

    Returns:
    complex: A complex number corresponding to the given magnitude and angle.
    """
    # Convert angle to radians if it's in degrees
    if deg:
        ang = np.radians(ang)

    # Create complex number from magnitude and angle
    return np.cos(ang) * mag + np.sin(ang) * mag * 1j