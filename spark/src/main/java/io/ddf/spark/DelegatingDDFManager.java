package io.ddf.spark;

import io.ddf.DDF;
import io.ddf.DDFManager;
import io.ddf.exception.DDFException;

import java.util.Map;
import java.util.UUID;

/**
 * A DDFManager that delegate work to another DDFManager.
 * This is used to re-use one single SparkDDFManager with multiple DataSource, so that
 * it appears as each data source has one and only one corresponding DDFManager.
 */
public class DelegatingDDFManager extends DDFManager {

  private final DDFManager manager;
  private final String uri;

  public DelegatingDDFManager(DDFManager manager, String uri) {
    this.uri = uri;
    this.manager = manager;
  }

  @Override
  public DDF transfer(UUID fromEngine, UUID ddfuuid) throws DDFException {
    return manager.transfer(fromEngine, ddfuuid);
  }

  @Override
  public DDF transferByTable(UUID fromEngine, String tableName) throws DDFException {
    return manager.transferByTable(fromEngine, tableName);
  }

  @Override
  public DDF loadTable(String fileURL, String fieldSeparator) throws DDFException {
    return manager.loadTable(fileURL, fieldSeparator);
  }

  @Override
  public DDF getOrRestoreDDFUri(String ddfURI) throws DDFException {
    return manager.getOrRestoreDDFUri(ddfURI);
  }

  @Override
  public DDF getOrRestoreDDF(UUID uuid) throws DDFException {
    return manager.getOrRestoreDDF(uuid);
  }

  @Override
  public DDF createDDF(Map<Object, Object> options) throws DDFException {
    options.put("sourceUri", uri);
    return manager.createDDF(options);
  }

  @Override
  public String getEngine() {
    return null;
  }
}