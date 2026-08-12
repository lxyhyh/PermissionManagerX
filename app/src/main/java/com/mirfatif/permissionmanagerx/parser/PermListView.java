package com.mirfatif.permissionmanagerx.parser;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** 权限视图的聚合数据：按权限名聚合所有应用的权限条目。 */
public enum PermListView {
  INS;

  public static class PermListItem {
    public final String name;
    public final boolean isAppOp;
    public final List<AppEntry> apps = new ArrayList<>();

    PermListItem(String name, boolean isAppOp) {
      this.name = name;
      this.isAppOp = isAppOp;
    }
  }

  public static class AppEntry {
    public final Package pkg;
    public final Permission perm;

    AppEntry(Package pkg, Permission perm) {
      this.pkg = pkg;
      this.perm = perm;
    }
  }

  private volatile List<PermListItem> mList = Collections.emptyList();

  public List<PermListItem> getList() {
    return mList;
  }

  /** 在包列表刷新完成后调用，重建聚合视图。 */
  public void rebuild(List<Package> pkgs) {
    Map<String, PermListItem> map = new LinkedHashMap<>();

    if (pkgs != null) {
      for (Package pkg : pkgs) {
        List<Permission> perms = pkg.getFullPermsList();
        if (perms == null) {
          continue;
        }
        for (Permission perm : perms) {
          String key = (perm.isAppOp() ? "o:" : "p:") + perm.getName();
          PermListItem item = map.get(key);
          if (item == null) {
            item = new PermListItem(perm.getName(), perm.isAppOp());
            map.put(key, item);
          }
          item.apps.add(new AppEntry(pkg, perm));
        }
      }
    }

    mList = new ArrayList<>(map.values());
  }
}
