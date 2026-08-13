package com.mirfatif.permissionmanagerx.zhx.permview;

import android.app.Activity;
import android.content.Intent;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import android.widget.TextView;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import com.mirfatif.permissionmanagerx.R;
import com.mirfatif.permissionmanagerx.app.App;
import com.mirfatif.permissionmanagerx.base.BaseActivity;
import com.mirfatif.permissionmanagerx.databinding.ActivityPermListBinding;
import com.mirfatif.permissionmanagerx.fwk.PermListActivityM;
import com.mirfatif.permissionmanagerx.parser.PackageParser;
import com.mirfatif.permissionmanagerx.zhx.i18n.PermDescProvider;
import com.mirfatif.permissionmanagerx.zhx.permview.PermListView.PermListItem;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

public class PermListActivity {
  private final BaseActivity mA;
  private ActivityPermListBinding mB;
  private final List<PermListItem> mFiltered = new ArrayList<>();
  private PermAdapter mAdapter;

  public PermListActivity(BaseActivity act) {
    mA = act;
  }

  public static void start(Activity act) {
    act.startActivity(new Intent(App.getCxt(), PermListActivityM.class));
  }

  public void onCreated() {
    mB = ActivityPermListBinding.inflate(mA.getLayoutInflater());
    // 走 BaseActivity.setContentView(ViewBinding)：Android 15+ edge-to-edge 状态栏适配
    mA.setContentView(mB);
    mA.setTitle(R.string.perm_view_title);

    mB.recyclerView.setLayoutManager(new LinearLayoutManager(mA));
    mAdapter = new PermAdapter();
    mB.recyclerView.setAdapter(mAdapter);
    mB.searchV.addTextChangedListener(
        new TextWatcher() {
          public void beforeTextChanged(CharSequence s, int a, int b, int c) {}

          public void onTextChanged(CharSequence s, int a, int b, int c) {
            refresh();
          }

          public void afterTextChanged(Editable s) {}
        });

    // 包列表加载/刷新完成后自动刷新本页（修复：权限视图不显示权限列表）
    PackageParser.INS.getPkgListLive().observe(mA, pkgs -> refresh());

    refresh();
  }

  private void refresh() {
    String q = mB.searchV.getText().toString().trim().toLowerCase(Locale.ROOT);

    mFiltered.clear();
    for (PermListItem item : PermListView.INS.getList()) {
      String label = PermDescProvider.INS.getLabel(item.name);
      if (label == null) {
        label = item.name;
      }
      if (q.isEmpty()
          || item.name.toLowerCase(Locale.ROOT).contains(q)
          || label.toLowerCase(Locale.ROOT).contains(q)) {
        mFiltered.add(item);
      }
    }

    mAdapter.notifyDataSetChanged();
    mB.emptyV.setVisibility(mFiltered.isEmpty() ? View.VISIBLE : View.GONE);
  }

  private class PermAdapter extends RecyclerView.Adapter<PermAdapter.VH> {

    public VH onCreateViewHolder(ViewGroup parent, int viewType) {
      View view =
          LayoutInflater.from(parent.getContext())
              .inflate(R.layout.rv_item_perm_list, parent, false);
      return new VH(view);
    }

    public void onBindViewHolder(VH holder, int position) {
      PermListItem item = mFiltered.get(position);

      CharSequence label = PermDescProvider.INS.getLabel(item.name);
      if (label == null) {
        label = item.name;
      }
      holder.nameV.setText(label);

      if (!item.apps.isEmpty() && item.apps.get(0).perm.getIconResId() != 0) {
        holder.iconV.setImageResource(item.apps.get(0).perm.getIconResId());
      }

      String protLevel = "";
      if (!item.apps.isEmpty() && item.apps.get(0).perm.getLocalizedProtLevelString() != null) {
        protLevel = item.apps.get(0).perm.getLocalizedProtLevelString().toString();
      }
      String sub =
          item.name
              + (protLevel.isEmpty() ? "" : "  |  " + protLevel)
              + "  |  "
              + mA.getResources()
                  .getQuantityString(R.plurals.apps_count, item.apps.size(), item.apps.size());
      holder.subV.setText(sub);

      holder.itemView.setOnClickListener(v -> PermAppsActivity.start(mA, item.name, item.isAppOp));
    }

    public int getItemCount() {
      return mFiltered.size();
    }

    class VH extends RecyclerView.ViewHolder {
      final ImageView iconV;
      final TextView nameV, subV;

      VH(View v) {
        super(v);
        iconV = v.findViewById(R.id.icon_v);
        nameV = v.findViewById(R.id.name_v);
        subV = v.findViewById(R.id.sub_v);
      }
    }
  }
}
