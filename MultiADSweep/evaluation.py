"""
evaluation.py

This module contains a collection of utility functions designed to simplify the process of working with 
Advanced Design System (ADS) simulation data in python using pandas (pd) Dataframes

Author: Michael Loose
Date: 18. Sep. 2023
Institution: Friedrich-Alexander-Universität Erlangen, Lehrstuhl für technische Elektronik
License: MIT

"""
import numpy as np
import pandas as pd
import warnings
import keysight.pwdatatools as pwdt

def block_to_dataframe(block):
    """
    Converts a data block to a pandas DataFrame with indexed independent variables.

    Parameters:
    block (Block): The block to convert to DataFrame.

    Returns:
    pd.DataFrame: A DataFrame with the data from the block, indexed by its independent variables.
    """
    independent_var_names = list(block.ivarnames)
    return block.data.set_index(independent_var_names)



def get_block_containing_variable(dataset, variable_name):
    """
    Retrieves the first block in a dataset containing the specified variable.

    Parameters:
    dataset (Group): The dataset to search for the variable.
    variable_name (str): The name of the variable to search for.

    Returns:
    Block: The first block containing the specified variable.

    Raises:
    AttributeError: If the variable is not found in the dataset.
    """
    found_blocks = dataset.find_blocks_with_varname(variable_name)
    if len(found_blocks) == 0:
        raise AttributeError(f"\"{variable_name}\" not found within Dataset")
    elif len(found_blocks) > 1:
        warnings.warn(f"\"{variable_name}\" found multiple times within Dataset. Using first occurrence", UserWarning) 
    return block_to_dataframe(found_blocks[0])

def extract_variable_as_dataframe(ds, variable_name, unstack = None, fill_value=np.nan):
    """
    Extracts a specified variable from a dataset, block, or DataFrame, and optionally pivots it.

    Parameters:
    ds (Group or Block or pd.DataFrame): The data source to extract the variable from.
    variable_name (str): The name of the variable to extract.
    unstack (list of str or None): Independent variable names to unstack (make columns)

    Returns:
    pd.DataFrame: A DataFrame or pivot table containing the extracted variable.
    """
    if isinstance(ds, pwdt.Group):
        df = get_block_containing_variable(ds, variable_name)
    elif isinstance(ds, pwdt.Block):
        df = block_to_dataframe(ds)
    elif isinstance(ds, pd.DataFrame):
        df = ds
    else:
        raise ValueError(f"Dataset of unknown type {type(df)}")

    if unstack:
        return pd.DataFrame(get_block_containing_variable(ds, variable_name)[variable_name]).unstack(unstack)
    else:
        return pd.DataFrame(get_block_containing_variable(ds, variable_name)[variable_name])

def lookup(data_df, lookup_df):
    """
    Performs a lookup in data_df based on indices in lookup_df. 
    If lookup_df is a pd.Series, returns a pd.Series with values corresponding to each index in lookup_df. 
    If lookup_df is a pd.DataFrame, performs the lookup for each non-index column in lookup_df 
    and returns a pd.DataFrame with corresponding values for each column.

    Parameters:
    data_df (pd.DataFrame): The DataFrame from which values are to be retrieved.
    lookup_df (pd.Series or pd.DataFrame): The Series or DataFrame containing the lookup values.

    Returns:
    pd.Series or pd.DataFrame: A Series or DataFrame containing the retrieved values, 
                               indexed like lookup_df or with corresponding columns.
    """
    # Melt the DataFrame
    data_df_melted = data_df.melt(ignore_index=False).reset_index()

    if isinstance(lookup_df, pd.Series):
        # Prepare index names for merging
        idx_names = lookup_df.index.names + data_df.index.names

        # Prepare lookup DataFrame for merging
        lookup_df_melted = lookup_df.reset_index()
        lookup_df_melted.columns = idx_names

        # Merge and return as a Series
        merged = pd.merge(data_df_melted, lookup_df_melted, on=idx_names)
        return merged.set_index(lookup_df.index.names)['value']

    elif isinstance(lookup_df, pd.DataFrame):
        # Prepare index names for merging
        idx_names = lookup_df.index.names + data_df.index.names

        # Initialize an empty DataFrame to store results
        result_df = pd.DataFrame(index=lookup_df.index)

        # Perform lookup for each non-index column
        for col in lookup_df.columns.difference(lookup_df.index.names):
            lookup_series = lookup_df[col]
            lookup_series_melted = lookup_series.reset_index()
            lookup_series_melted.columns = idx_names

            # Merge and extract values
            merged = pd.merge(data_df_melted, lookup_series_melted, on=idx_names)
            result_df[col] = merged.set_index(lookup_df.index.names)['value']

        return result_df

    else:
        raise ValueError("Unsupported data type for lookup_df")