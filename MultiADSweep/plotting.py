"""
plotting.py


Author: Michael Loose
Date: 18. Sep. 2023
Institution: Friedrich-Alexander-Universität Erlangen, Lehrstuhl für technische Elektronik
License: MIT

"""


from pathlib import Path
import pandas as pd
import numpy as np
import skrf
import matplotlib as mpl
import matplotlib.pyplot as plt


def plot_contours(gamma_points, params, names=None, subdiv=1, filled=False, show_points=False, show_mesh=False, plts = None, contour_kwargs={}, smith_kwargs={}):
    """
    Plots contours on a Smith chart using a Delaunay mesh.
    The points can be in any arbitrary grid, and NaN values are permissible and will be masked.
    The function can handle either a single array of values or multiple arrays as a list/tuple for 'params'.
    If 'names' is not provided, no titles or legends will be created.

    Parameters:
    ---
        gamma_points (array): Complex gamma points for plotting.
        params (array or list/tuple of arrays): Parameters to plot. Each element must be of the same length as gamma_points.
        names (str or list/tuple of str, optional): Names of the parameters. If not provided, no titles or legends are created.
        subdiv (int, optional): Subdivision level for refining the triangulation. Defaults to 1.
        filled (bool, optional): If True, filled contours will be plotted. Defaults to False.
        show_points (bool, optional): If True, points will be shown on the plot. Defaults to False.
        show_mesh (bool, optional): If True, the mesh will be displayed. Defaults to False.
        contour_kwargs (dict, optional): Additional keyword arguments for contour plots. Defaults to {}.
        smith_kwargs (dict, optional): Additional keyword arguments for Smith chart. Defaults to {}.

    Returns:
    ---
        tuple: A tuple consisting of the matplotlib.figure.Figure object and the matplotlib.axes.Axes object of the plot.
    """
    # Ensure 'params' is a list
    if not isinstance(params, (list, tuple)):
        params = [params]

    # Check if names are provided
    create_legend = names is not None
    if create_legend:
        if not isinstance(names, (list, tuple)):
            names = [names]
        # Check lengths of 'params' and 'names'
        if len(params) != len(names):
            raise ValueError("Length of 'names' must match the number of elements in 'params'.")

    # Initialize the plot
    if plts is None:
        f, ax = plt.subplots(figsize=(8, 8))
    else:
        f, ax = plts

    default_smith_kwargs = {'smithR': 1, 'chart_type': 'z', 'draw_labels': False, 'border': False, 'ref_imm': 1.0, 'draw_vswr': None}
    skrf.plotting.smith(ax=ax, **{**default_smith_kwargs, **smith_kwargs})
    ax.set_aspect("equal")
    ax.set_xlim([-1, 1])
    ax.set_ylim([-1, 1])
    
    # Plot points if enabled
    if show_points:
        valid_indices = ~np.isnan(params[0])
        ax.scatter(gamma_points.real[valid_indices], gamma_points.imag[valid_indices], label='Valid Points')
        ax.scatter(gamma_points.real[~valid_indices], gamma_points.imag[~valid_indices], color='red', label='Invalid Points (NaN)')
    
    legends = []

    for idx, param in enumerate(params):
        # Mask NaN values
        valid_indices = ~np.isnan(param)
        gamma_points_real_clean = np.array(gamma_points.real)[valid_indices]
        gamma_points_imag_clean = np.array(gamma_points.imag)[valid_indices]
        param_clean = param[valid_indices]

        # Delaunay triangulation for contouring
        triang_clean = mpl.tri.Triangulation(gamma_points_real_clean, gamma_points_imag_clean)
        refiner = mpl.tri.UniformTriRefiner(triang_clean)
        tri_refi, param_refi = refiner.refine_field(param_clean, subdiv=subdiv)
        
        # Show mesh if enabled
        if show_mesh:
            ax.triplot(tri_refi, color='k', alpha=0.5)

        plot_func = ax.tricontourf if filled else ax.tricontour
        default_contour_kwargs = {
            'cmap': None if len(params) > 1 else 'viridis',
            'colors': mpl.colors.rgb2hex(plt.cm.tab10.colors[idx % len(plt.cm.tab10.colors)]) if len(params) > 1 else None
        }
        cs = plot_func(tri_refi, param_refi, **{**default_contour_kwargs, **contour_kwargs})

        ax.clabel(cs, inline=True, fontsize=10)
        if create_legend and len(params) > 1:
            # Add to legend
            legends.append(mpl.lines.Line2D([0], [0], color=cs.collections[0].get_edgecolor(), label=names[idx]))
    
    if create_legend and len(params) > 1:
        ax.legend(handles=legends)
        title = " and ".join(names) + " Contours"
        ax.set_title(title)
    elif create_legend:
        title = names[0] + " Contours"
        ax.set_title(title)

    return f, ax