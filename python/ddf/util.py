from __future__ import unicode_literals
import numpy as np
import json

import pandas as pd
from py4j import java_collections


"""
Mapping from DDF types to python types
"""
TYPE_MAPPING = {'integer': int,
                'int': int,
                'tinyint': int,
                'smallint': int,
                'bigint': long,
                'long': long,
                'double': float,
                'float': float,
                # TODO: Find a way to handle decimal better.
                'decimal': float,
                'boolean': bool,
                'logical': bool,
                'string': unicode,
                'array': list,
                'struct': object,
                'timestamp': int,
                'blob': object
                }


NUMERIC_DDF_TYPES = ['int', 'tinyint', 'smallint', 'bigint', 'integer', 'double', 'float', 'decimal']


def is_numeric_ddf_type(t):
    """
    Check if column type t is a numeric type in DDF's set of types
    :param t: column type
    :return: True/False
    """
    return t.lower() in NUMERIC_DDF_TYPES


def to_bool(x):
    """
    Try our best to make x into a boolean value
    :param x: the value to be converted
    :return: a boolean value
    """
    if x is None:
        return None
    if isinstance(x, (bool, np.bool_)):
        return x
    if isinstance(x, (str, unicode)):
        return x.lower() in ['yes', 'true']
    if isinstance(x, (int, long)):
        return x != 0
    if isinstance(x, (float, np.float)):
        return abs(x) > 1e-10
    raise ValueError('Could not convert into bool with value {} of type {}'.format(x, type(x)))


def to_python_type(t):
    tmp = t.split(".")
    t = tmp[len(tmp) - 1]
    return 'str' if t not in TYPE_MAPPING else TYPE_MAPPING[t]


def convert_column_types(df, column_types, raise_on_error=False):
    """
    Convert a dataframe into data types specified in column_types
    :param df: a data frame containing the sampled data
    :type df: pd.DataFrame
    :param column_types: the types of columns, in pE terminology
    :param raise_on_error:
    :return: a correctly typed data frame
    """
    if len(df.columns) != len(column_types):
        raise ValueError('Expect a list of column types of the same length with the number of columns in df')

    for i, c in enumerate(df.columns):
        dest_type = to_python_type(column_types[i])
        if dest_type is bool:
            df[c] = df[c].apply(to_bool)
        elif dest_type is list or column_types[i] == 'struct':
            # json
            df[c] = df[c].apply(lambda x: json.loads(x) if isinstance(x, (str, unicode)) else x)
        elif dest_type is float:
            # NaN is encoded as "null"
            df[c] = df[c].convert_objects(convert_numeric=True)

        # convert type
        df[c] = df[c].astype(dest_type, raise_on_error=raise_on_error)
    return df


"""
Validating column arguments
"""


def validate_column_generic(col_names, column, get_name=True):
    """
    Validate a column name or index, return the column name
    :param col_names: list of column names
    :param column: column name or index
    :param get_name:
    :return: column index
    """
    if type(column) is int:
        if column < 0 or column >= len(col_names):
            raise ValueError('Column index out of range: {}'.format(column))
        return col_names[column] if get_name else column
    elif isinstance(column, (str, unicode)) and column in col_names:
        return column if get_name else col_names.index(column)
    raise ValueError('Column not found: {}'.format(column))


def parse_column_str(col_names, column):
    """
    Validate a column name or index, return the column name
    :param col_names: list of column names
    :param column: column name or index
    :return: column index
    """
    return validate_column_generic(col_names, column, True)


def parse_column(col_names, column):
    """
    Convert a column to index
    :param col_names: list of column names
    :param column: column name or index
    :return: column index
    """
    return validate_column_generic(col_names, column, False)


def to_java_array(ls, java_type, gateway_client):
    """
    Convert python iterable into a java array
    :param ls:
    :param java_type:
    :param gateway_client:
    :return:
    """
    arr = gateway_client.new_array(java_type, len(ls))
    for i in range(0, len(ls)):
        arr[i] = ls[i]
    return arr


def to_java_list(ls, gateway_client):
    """
    Convert a python list into java list
    :param ls: python list to be converted
    :param gateway_client: gateway client object
    :return: java list
    """
    return java_collections.ListConverter().convert([] if ls is None else ls, gateway_client._gateway_client)


def parse_ddf_data(rows, colnames, coltypes):
    n = len(rows)
    data = dict([(c, [None] * n) for c in colnames])
    nulls = ("null", "NULL")
    for i in range(0, n):
        row = str(rows[i]).split('\t')
        for j, c in enumerate(colnames):
            value = row[j].replace('\\\\t', '\t')
            if value not in nulls:
                data[c][i] = value

    return convert_column_types(pd.DataFrame(data=data, columns=colnames), coltypes, raise_on_error=False)


def parse_sql_result(java_result):
    rows = java_result.getRows()
    cols = java_result.getSchema().getColumns()
    coltypes = [str(x.getType().toString()) for x in cols]
    colnames = [str(x.getName()) for x in cols]

    return parse_ddf_data(rows, colnames, coltypes)
