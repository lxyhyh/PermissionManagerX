package com.mirfatif.permissionmanagerx.parser;

import com.mirfatif.permissionmanagerx.R;
import com.mirfatif.permissionmanagerx.app.App;
import java.util.HashMap;
import java.util.Map;

/** 提供 AppOps 与清单权限的中文说明。说明数据位于 res/values(-zh-rCN)/perm_descs.xml。 */
public enum PermDescProvider {
  INS;

  private Map<String, String> mDescs;
  private Map<String, String> mLabels;

  /** 按权限原始名（如 START_FOREGROUND、android.permission.CAMERA）返回说明；查不到返回 null。 */
  public String getDesc(String name) {
    if (name == null) {
      return null;
    }

    if (mDescs == null) {
      synchronized (this) {
        if (mDescs == null) {
          mDescs = buildDescsMap();
        }
      }
    }

    return mDescs.get(name);
  }

  /** 按权限原始名返回内置中文名（系统本地化名缺失时兜底）；查不到返回 null。 */
  public String getLabel(String name) {
    if (name == null) {
      return null;
    }

    if (mLabels == null) {
      synchronized (this) {
        if (mLabels == null) {
          mLabels = buildLabelsMap();
        }
      }
    }

    return mLabels.get(name);
  }

  private Map<String, String> buildDescsMap() {
    Map<String, String> descs = new HashMap<>();

    String[] opNames = App.getCxt().getResources().getStringArray(R.array.app_op_desc_names);
    String[] opDescs = App.getCxt().getResources().getStringArray(R.array.app_op_descs);
    for (int i = 0; i < Math.min(opNames.length, opDescs.length); i++) {
      descs.put(opNames[i], opDescs[i]);
    }

    String[] permNames = App.getCxt().getResources().getStringArray(R.array.perm_desc_names);
    String[] permDescs = App.getCxt().getResources().getStringArray(R.array.perm_desc_descs);
    for (int i = 0; i < Math.min(permNames.length, permDescs.length); i++) {
      descs.put(permNames[i], permDescs[i]);
    }

    return descs;
  }

  private Map<String, String> buildLabelsMap() {
    Map<String, String> labels = new HashMap<>();

    String[] opNames = App.getCxt().getResources().getStringArray(R.array.app_op_desc_names);
    String[] opLabels = App.getCxt().getResources().getStringArray(R.array.app_op_desc_labels);
    for (int i = 0; i < Math.min(opNames.length, opLabels.length); i++) {
      labels.put(opNames[i], opLabels[i]);
    }

    String[] permNames = App.getCxt().getResources().getStringArray(R.array.perm_desc_names);
    String[] permLabels = App.getCxt().getResources().getStringArray(R.array.perm_desc_labels);
    for (int i = 0; i < Math.min(permNames.length, permLabels.length); i++) {
      labels.put(permNames[i], permLabels[i]);
    }

    return labels;
  }
}
