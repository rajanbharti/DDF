"""
Created on Jun 22, 2014

@author: nhanitvn
"""
from __future__ import unicode_literals

from dataframe import DistributedDataFrame
import gateway
import util


class DDFManager(object):
    """
    Main entry point for DDF functionality. A SparkDDFManager can be used
    to create DDFs that are implemented for Spark framework.
    """
    _jdm = None
    _gateway_client = None

    def __init__(self, engine_name):
        """
        Constructor
        :param engine_name: Name of the DDF engine, e.g. 'spark'
        """
        self._gateway_client = gateway.new_gateway_client()
        try:
            engine_type = self._gateway_client.jvm.io.ddf.DDFManager.EngineType.fromString(engine_name)
            self._jdm = self._gateway_client.jvm.io.ddf.DDFManager.get(engine_type)
        except Exception:
            self._gateway_client.close()
            raise

    def load_file(self, path, seperator=' '):
        """
        Load a csv file
        :param path:
        :param seperator:
        :return:
        """
        return DistributedDataFrame(self._jdm.loadFile(path, seperator), self._gateway_client)

    def load_jdbc(self, uri, username, password, table):
        """
        Load a table in JDBC
        (Not tested)

        :param uri:
        :param username:
        :param password:
        :param table:
        :return:
        """
        descriptor = self._gateway_client.jvm.io.ddf.datasource.JDBCDataSourceDescriptor(uri, username, password, table)
        return DistributedDataFrame(self._jdm.load(descriptor), self._gateway_client)

    def list_ddfs(self):
        """
        List all the DDFs

        :return: list of DDF objects
        """
        return [DistributedDataFrame(x, self._gateway_client) for x in list(self._jdm.listDDFs())]

    def get_ddf_by_name(self, ddf_name):
        """
        Get a DDF object using its name
        :param ddf_name: the name of the DDF object to be retrieved
        :return: a DDF object
        """
        return DistributedDataFrame(self._jdm.getDDFByName(ddf_name), self._gateway_client)

    def set_ddf_name(self, ddf, name):
        """
        Set a name for the given DDF

        :param ddf: the DDF object
        :param name: name of the DDF
        :return: nothing
        """
        self._jdm.setDDFName(ddf._jddf, name)

    def sql(self, command, query_on_ddf=True):
        """
        Execute a sql command and return a list of strings
        :param command: the sql command to run
        :param query_on_ddf: whether the query is on ddf or on the origianl engine
        """
        command = command.strip()
        res = self._jdm.sql(command, query_on_ddf)
        if not (command.lower().startswith('create') or command.lower().startswith('load')):
            return util.parse_sql_result(res)
        return res

    def sql2ddf(self, command, query_on_ddf=True):
        """
        Create a DistributedDataFrame from an sql command.
        :param command: the sql command to run
        :param query_on_ddf: whether the query is on ddf or on the origianl engine
        :return: a DDF
        """
        command = command.strip()
        if not command.lower().startswith('select'):
            raise ValueError('Only SELECT query is supported')

        return DistributedDataFrame(self._jdm.sql2ddf(command, query_on_ddf), self._gateway_client)

    def shutdown(self):
        """
        Shut down the DDF Manager
        """
        self._jdm.shutdown()
        self._gateway_client.close()
