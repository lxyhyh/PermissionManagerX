package com.mirfatif.permissionmanagerx.fwk;

import android.os.Bundle;
import com.mirfatif.permissionmanagerx.base.BaseActivity;
import com.mirfatif.permissionmanagerx.zhx.permview.PermListActivity;

public class PermListActivityM extends BaseActivity {

  private final PermListActivity mA = new PermListActivity(this);

  protected void onCreated(Bundle savedInstanceState) {
    mA.onCreated();
  }
}
