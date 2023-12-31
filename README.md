# MultiADSweep
A Python library for controlling Pathwave ADS Simulation out of python with multithreading capability and data evaluation tools.

## Version
- **MultiADSweep**: 0.1

## Author
- **Name**: Michael Loose <[michael.loose@fau.de](mailto:michael.loose@fau.de)>
- **Affiliation**: Lehrstuhl für technische Elektronik, Friedrich-Alexander-Universität Erlangen-Nürnberg

## Tested Environment
- **Keysight ADS Version**: 2022 rev2, 2023 rev2

## Python Version
- **Required**: Python 3.10.13

## Required Python Packages
- `numpy` (Version 1.22.4)
- `scipy` (Version 1.11.3)
- `pandas` (Version 1.4.4)
- `scikit-rf` (Version 0.29.1)
- `matplotlib` (Version 3.5.3)
- `tqdm` (Version 4.65.0)

## Keysight Packages
**Important Note**: The following Keysight packages are not publicly available but are provided with the installation of Keysight ADS. These packages must be installed manually from the supplied wheel files.

Install the following packages from the wheels supplied with Keysight ADS:
- `keysight_pwdatatools` (Version 0.5.0)
  - Wheel: `keysight_pwdatatools-0.5.0-cp310-cp310-manylinux2014_x86_64.manylinux_2_17_x86_64.whl`
- `keysight_cdm` (Version 1.0.1)
  - Wheel: `keysight_cdm-1.0.1-py3-none-any.whl`
- `keysight_ads_dataset` (Version 0.9.1)
  - Wheel: `keysight_ads_dataset-0.9.1-cp310-cp310-linux_x86_64.whl`
- `keysight_ads_datalink` (Version 5.1)
  - Wheel: `keysight_ads_datalink-5.1-py3-none-any.whl`

## Recommended Python Packages
For enhanced functionality and user experience, the following packages are recommended:
- `ipykernel`
  - For support in Jupyter notebooks.
- `IPython`
  - For interactive Python sessions.
- `celluloid`
  - For simple animated plots. Note: `ffmpeg` is required for generating output files.
- `jupyter-notebook` or `jupyterlab`
  - For running notebooks in a web browser or in Visual Studio Code.
- `ipympl`
  - For interactive matplotlib plots in Jupyter notebooks.
- `ipywidgets`
  - For interactive widgets in Jupyter notebooks.
- `mplcursors`
  - For interactive cursors in Jupyter notebooks.
