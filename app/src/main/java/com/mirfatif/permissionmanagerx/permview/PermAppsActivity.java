package com.mirfatif.permissionmanagerx.permview;

import android.app.Activity;
import android.app.AppOpsManager;
import android.content.Intent;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import android.widget.TextView;
import androidx.appcompat.app.AlertDialog;
import androidx.fragment.app.FragmentActivity;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import com.mirfatif.permissionmanagerx.R;
import com.mirfatif.permissionmanagerx.app.App;
import com.mirfatif.permissionmanagerx.base.AlertDialogFragment;
import com.mirfatif.permissionmanagerx.databinding.ActivityPermAppsBinding;
import com.mirfatif.permissionmanagerx.fwk.PermAppsActivityM;
import com.mirfatif.permissionmanagerx.parser.AppOpsParser;
import com.mirfatif.permissionmanagerx.parser.PackageParser;
import com.mirfatif.permissionmanagerx.parser.PermDescProvider;
import com.mirfatif.permissionmanagerx.parser.PermListView;
import com.mirfatif.permissionmanagerx.parser.PermListView.AppEntry;
import com.mirfatif.permissionmanagerx.parser.PermListView.PermListItem;
import com.mirfatif.permissionmanagerx.privs.DaemonHandler;
import com.mirfatif.permissionmanagerx.privs.DaemonIface;
import com.mirfatif.permissionmanagerx.util.UserUtils;
import com.mirfatif.permissionmanagerx.util.bg.UiRunner;
import com.mirfatif.privtasks.util.bg.BgRunner;
import java.util.ArrayList;
import java.util.List;

public class PermAppsActivity {

  private final FragmentActivity mA;
  private ActivityPermAppsBinding mB;
  private String mPermName;
  private boolean mIsAppOp;
  private final List<AppEntry> mEntries = new ArrayList<>();
  private AppAdapter mAdapter;

  public PermAppsActivity(FragmentActivity act) {
    mA = act;
  }

  public static void start(Activity act, String permName, boolean isAppOp) {
    Intent intent = new Intent(App.getCxt(), PermAppsActivityM.class);
    intent.putExtra("perm_name", permName);
    intent.putExtra("is_app_op", isAppOp);
    act.startActivity(intent);
  }

  public void onCreated() {
    mB = ActivityPermAppsBinding.inflate(mA.getLayoutInflater());
    mA.setContentView(mB.getRoot());

    mPermName = mA.getIntent().getStringExtra("perm_name");
    mIsAppOp = mA.getIntent().getBooleanExtra("is_app_op", false);

    CharSequence label = PermDescProvider.INS.getLabel(mPermName);
    mA.setTitle(label != null ? label : mPermName);

    mB.recyclerView.setLayoutManager(new LinearLayoutManager(mA));
    mAdapter = new AppAdapter();
    mB.recyclerView.setAdapter(mAdapter);

    mB.allowAllV.setOnClickListener(v -> batch(true));
    mB.denyAllV.setOnClickListener(v -> batch(false));

    // 包列表刷新完成后自动刷新本页（修复 M1：改完权限界面不刷新）
    PackageParser.INS.getPkgListLive().observe(mA, pkgs -> refresh());

    refresh();
  }

  private void refresh() {
    mEntries.clear();
    for (PermListItem item : PermListView.INS.getList()) {
      if (mPermName.equals(item.name) && item.isAppOp == mIsAppOp) {
        mEntries.addAll(item.apps);
        break;
      }
    }
    mAdapter.notifyDataSetChanged();
  }

  private void batch(boolean grant) {
    BgRunner.execute(
        () -> {
          // 修复 M2'：守护进程不在线时提示并中止，避免“假成功”
          if (!DaemonHandler.INS.isDaemonAlive(true, true)) {
            return;
          }
          int skipped = 0;
          for (AppEntry entry : new ArrayList<>(mEntries)) {
            if (!entry.perm.isChangeable() || !entry.pkg.isChangeable()) {
              skipped++;
              continue;
            }
            if (entry.perm.isAppOp()) {
              Integer op = AppOpsParser.INS.getAppOpCode(mPermName);
              if (op == null) {
                skipped++;
                continue;
              }
              DaemonIface.INS.setAppOpMode(
                  entry.pkg.getUid(),
                  entry.perm.isPerUid() ? null : entry.pkg.getName(),
                  op,
                  grant ? AppOpsManager.MODE_ALLOWED : AppOpsManager.MODE_IGNORED);
            } else {
              DaemonIface.INS.setPermState(
                  grant, entry.pkg.getName(), mPermName, UserUtils.getUserId(entry.pkg.getUid()));
            }
          }

          final int skippedCount = skipped;
          UiRunner.post(
              () -> {
                com.mirfatif.permissionmanagerx.util.UiUtils.showToast(
                    R.string.perm_view_batch_done);
                if (skippedCount > 0) {
                  com.mirfatif.permissionmanagerx.util.UiUtils.showToast(
                      mA.getString(R.string.perm_view_skipped, skippedCount));
                }
                refresh();
                // 触发重解析 → 聚合视图重建 → 主界面列表同步刷新（修复 M1）
                PackageParser.INS.updatePkgList();
              });
        });
  }

  private void setEntry(AppEntry entry, int mode) {
    BgRunner.execute(
        () -> {
          // 修复 M2'：守护进程不在线时提示并中止，避免“假成功”
          if (!DaemonHandler.INS.isDaemonAlive(true, false)) {
            return;
          }
          if (!entry.perm.isChangeable() || !entry.pkg.isChangeable()) {
            return;
          }
          if (entry.perm.isAppOp()) {
            Integer op = AppOpsParser.INS.getAppOpCode(mPermName);
            if (op != null) {
              DaemonIface.INS.setAppOpMode(
                  entry.pkg.getUid(), entry.perm.isPerUid() ? null : entry.pkg.getName(), op, mode);
            }
          } else {
            DaemonIface.INS.setPermState(
                mode != 0, entry.pkg.getName(), mPermName, UserUtils.getUserId(entry.pkg.getUid()));
          }
          UiRunner.post(
              () -> {
                refresh();
                // 触发重解析 → 聚合视图重建 → 本页状态刷新（修复 M1）
                PackageParser.INS.updatePkgList();
              });
        });
  }

  private void showModeDialog(AppEntry entry) {
    List<CharSequence> options = new ArrayList<>();
    List<Integer> modes = new ArrayList<>();

    if (mIsAppOp) {
      options.add(mA.getString(R.string.app_op_mode_allow));
      modes.add(AppOpsManager.MODE_ALLOWED);
      options.add(mA.getString(R.string.app_op_mode_ignore));
      modes.add(AppOpsManager.MODE_IGNORED);
      options.add(mA.getString(R.string.app_op_mode_deny));
      modes.add(AppOpsManager.MODE_ERRORED);
      options.add(mA.getString(R.string.app_op_mode_foreground));
      modes.add(AppOpsManager.MODE_FOREGROUND);
    } else {
      options.add(mA.getString(R.string.perm_mode_granted));
      modes.add(1);
      options.add(mA.getString(R.string.perm_mode_revoked));
      modes.add(0);
    }

    AlertDialog dialog =
        new AlertDialog.Builder(mA)
            .setTitle(entry.pkg.getLabel())
            .setItems(
                options.toArray(new CharSequence[0]),
                (d, which) -> setEntry(entry, modes.get(which)))
            .create();
    AlertDialogFragment.show(mA, dialog, "PERM_VIEW_MODE");
  }

  private class AppAdapter extends RecyclerView.Adapter<AppAdapter.VH> {

    public VH onCreateViewHolder(ViewGroup parent, int viewType) {
      View view =
          LayoutInflater.from(parent.getContext())
              .inflate(R.layout.rv_item_perm_app, parent, false);
      return new VH(view);
    }

    public void onBindViewHolder(VH holder, int position) {
      AppEntry entry = mEntries.get(position);

      try {
        holder.iconV.setImageDrawable(App.getPm().getApplicationIcon(entry.pkg.getName()));
      } catch (Exception e) {
        holder.iconV.setImageResource(R.mipmap.ic_launcher);
      }

      holder.nameV.setText(entry.pkg.getLabel());
      holder.pkgV.setText(entry.pkg.getName());

      CharSequence state = entry.perm.getLocalizedPermStateName();
      holder.stateV.setText(state);

      boolean changeable = entry.perm.isChangeable() && entry.pkg.isChangeable();
      holder.itemView.setAlpha(changeable ? 1f : 0.4f);
      holder.itemView.setOnClickListener(changeable ? v -> showModeDialog(entry) : null);
    }

    public int getItemCount() {
      return mEntries.size();
    }

    class VH extends RecyclerView.ViewHolder {
      final ImageView iconV;
      final TextView nameV, pkgV, stateV;

      VH(View v) {
        super(v);
        iconV = v.findViewById(R.id.icon_v);
        nameV = v.findViewById(R.id.name_v);
        pkgV = v.findViewById(R.id.pkg_v);
        stateV = v.findViewById(R.id.state_v);
      }
    }
  }
}
