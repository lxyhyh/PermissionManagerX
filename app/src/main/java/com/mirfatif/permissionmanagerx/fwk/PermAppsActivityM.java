package com.mirfatif.permissionmanagerx.fwk;

import android.os.Bundle;
import com.mirfatif.permissionmanagerx.base.BaseActivity;
import com.mirfatif.permissionmanagerx.permview.PermAppsActivity;

public class PermAppsActivityM extends BaseActivity {

  private final PermAppsActivity mA = new PermAppsActivity(this);

  protected void onCreated(Bundle savedInstanceState) {
    mA.onCreated();
  }
}
