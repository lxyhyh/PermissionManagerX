package com.mirfatif.permissionmanagerx.pkg;

import static com.mirfatif.permissionmanagerx.util.ApiUtils.getString;

import android.app.AppOpsManager;
import android.content.Context;
import android.content.res.ColorStateList;
import android.graphics.Color;
import android.text.TextUtils;
import android.text.style.TextAppearanceSpan;
import android.util.TypedValue;
import android.view.LayoutInflater;
import android.view.View;
import android.view.View.OnClickListener;
import android.view.View.OnLongClickListener;
import android.view.ViewGroup;
import android.widget.TextView;
import androidx.core.graphics.ColorUtils;
import androidx.core.view.ViewCompat;
import androidx.lifecycle.LifecycleOwner;
import androidx.recyclerview.widget.DiffUtil;
import androidx.recyclerview.widget.RecyclerView;
import com.mirfatif.permissionmanagerx.R;
import com.mirfatif.permissionmanagerx.base.MyListAdapter;
import com.mirfatif.permissionmanagerx.databinding.RvItemPermBinding;
import com.mirfatif.permissionmanagerx.main.PackageAdapter;
import com.mirfatif.permissionmanagerx.parser.Permission;
import com.mirfatif.permissionmanagerx.pkg.PermissionAdapter.ItemViewHolder;
import com.mirfatif.permissionmanagerx.util.StringUtils;
import com.mirfatif.permissionmanagerx.util.UiUtils;

public class PermissionAdapter extends MyListAdapter<Permission, ItemViewHolder> {

  private static final String TAG = "PermissionAdapter";

  private final PermAdapterCallback mCallback;

  private final Integer mRedTextColor;
  private final TextAppearanceSpan mRedTextSpan;
  private final float mTextSize;

  public PermissionAdapter(Context context, PermAdapterCallback callback, LifecycleOwner owner) {
    super(new DiffUtilItemCallBack(), owner, TAG);
    mCallback = callback;

    TextView tv = new TextView(context);
    mRedTextColor = ColorUtils.blendARGB(tv.getCurrentTextColor(), Color.RED, 0.75f);
    mRedTextSpan = UiUtils.getTextHighlightSpan(mRedTextColor);
    mTextSize = tv.getTextSize();
  }

  public ItemViewHolder onCreateViewHolder(ViewGroup parent, int viewType) {
    LayoutInflater inflater = LayoutInflater.from(parent.getContext());
    RvItemPermBinding b = RvItemPermBinding.inflate(inflater, parent, false);
    return new ItemViewHolder(b);
  }

  public void onBindViewHolder(ItemViewHolder holder, int position) {
    holder.bind(position);
  }

  class ItemViewHolder extends RecyclerView.ViewHolder
      implements OnClickListener, OnLongClickListener {

    private final RvItemPermBinding mB;

    public ItemViewHolder(RvItemPermBinding binding) {
      super(binding.getRoot());
      mB = binding;

      binding.getRoot().setOnClickListener(this);
      binding.getRoot().setOnLongClickListener(this);

      mB.appOpModeV.setTextSize(TypedValue.COMPLEX_UNIT_PX, mTextSize - mTextSize * 10 / 100);
      mB.appOpModeSubV.setTextSize(TypedValue.COMPLEX_UNIT_PX, mTextSize - mTextSize * 20 / 100);
    }

    public void bind(int pos) {
      Permission perm;
      if (pos == RecyclerView.NO_POSITION || (perm = getItem(pos)) == null) {
        return;
      }

      mB.flag.setVisibility(perm.isAppOp() ? View.INVISIBLE : View.VISIBLE);

      mB.appOpsRefStateV.setVisibility(View.GONE);
      if (perm.isReferenced() == null) {
        mB.refIndicationV.setBackgroundColor(PackageAdapter.ORANGE);
      } else if (Boolean.FALSE.equals(perm.isReferenced())) {
        mB.refIndicationV.setBackgroundColor(Color.RED);
        if (perm.isAppOp()) {
          String state = Permission.getLocalizedAppOpModeName(perm.getReference());
          mB.appOpsRefStateV.setText(
              StringUtils.htmlToString(getString(R.string.should_be, state)));
          mB.appOpsRefStateV.setVisibility(View.VISIBLE);
        }
      } else {
        mB.refIndicationV.setBackgroundColor(Color.GREEN);
      }

      mB.iconV.setImageResource(perm.getIconResId());

      CharSequence permName = perm.getLabel();
      if (permName == null) {
        permName = perm.getPermNameString();
      } else if (perm.isAppOp() && perm.hasDependsOnPerm()) {
        permName = TextUtils.concat(permName, " (", perm.getDependsOnName(), ")");
      }
      mB.permNameV.setText(permName);

      // ===== K-3 保护级别胶囊：根据语义染色（Normal灰 / Dangerous红 / Signature绿 / AppOps橙 / 其他=ink_3 中性灰）
      // 染色方案：backgroundTintList，不改动原文字 Spannable（保持对 fixed/privileged 的红高亮效果）。
      CharSequence protLevelCharSeq;
      if (perm.isCritical() && perm.isChangeable()) {
        protLevelCharSeq =
            StringUtils.getHighlightString(
                perm.getLocalizedProtLevelString(),
                mRedTextSpan,
                true,
                getString(R.string.prot_lvl_fixed),
                getString(R.string.prot_lvl_privileged));
      } else {
        protLevelCharSeq = perm.getLocalizedProtLevelString();
      }
      mB.protLevelV.setText(protLevelCharSeq);

      String lvlStr = protLevelCharSeq.toString();
      int capsuleTint;
      Context ctx = mB.protLevelV.getContext();
      if (lvlStr.contains(getString(R.string.prot_lvl_dangerous))) {
        capsuleTint = ctx.getColor(R.color.prot_dangerous_bg);
      } else if (lvlStr.contains(getString(R.string.prot_lvl_signature))) {
        capsuleTint = ctx.getColor(R.color.prot_signature_bg);
      } else if (lvlStr.contains(getString(R.string.prot_lvl_app_ops))) {
        capsuleTint = ctx.getColor(R.color.prot_appops_bg);
      } else if (lvlStr.contains(getString(R.string.prot_lvl_normal))) {
        capsuleTint = ctx.getColor(R.color.prot_normal_bg);
      } else {
        // Internal / Development / Privileged / Fixed / Unknown 等：退化为 ink_3 胶囊底色（中性三级色不抢戏）
        capsuleTint = ctx.getColor(R.color.ink_3);
      }
      ViewCompat.setBackgroundTintList(mB.protLevelV, ColorStateList.valueOf(capsuleTint));

      mB.appOpsTimeV.setVisibility(View.GONE);

      mB.permStateSwitch.setChecked(perm.isGranted());
      mB.permStateSwitch.setEnabled(perm.isChangeable());
      if (perm.isChangeable()) {
        mB.permStateSwitch.setOnClickListener(
            v -> {
              mB.permStateSwitch.setChecked(perm.isGranted());
              mCallback.onPermSwitchToggle(perm);
            });
      } else {
        mB.permStateSwitch.setOnClickListener(null);
      }

      if (perm.isAppOp()) {
        if (perm.hasDependsOnPerm()) {
          mB.permStateCont.setVisibility(View.GONE);
        } else {
          mB.permStateCont.setVisibility(View.VISIBLE);

          int mode = perm.getAppOpMode();

          if (mode != AppOpsManager.MODE_ALLOWED && mode != AppOpsManager.MODE_IGNORED) {
            mB.appOpModeV.setVisibility(View.VISIBLE);
            mB.appOpModeV.setText(perm.getLocalizedPermStateName());
          } else {
            mB.appOpModeV.setVisibility(View.GONE);
          }

          if (perm.hasUnknownOpMode()) {
            mB.appOpModeSubV.setVisibility(View.VISIBLE);
            mB.appOpModeSubV.setText(R.string.app_op_mode_unknown);
          } else if (!perm.isAppOpModeSet()) {
            mB.appOpModeSubV.setVisibility(View.VISIBLE);
            mB.appOpModeSubV.setText(R.string.app_op_mode_not_set);
          } else {
            mB.appOpModeSubV.setVisibility(View.GONE);
          }
        }

        String time = perm.getAppOpAccessTime();
        if (time != null) {
          mB.appOpsTimeV.setText(time);
          mB.appOpsTimeV.setTextColor(mRedTextColor);
          mB.appOpsTimeV.setVisibility(View.VISIBLE);
        }
      } else {
        if (!perm.hasProviderPkg()) {
          mB.permStateCont.setVisibility(View.GONE);
        } else {
          mB.permStateCont.setVisibility(View.VISIBLE);
          mB.appOpModeV.setVisibility(View.GONE);
          mB.appOpModeSubV.setVisibility(View.GONE);
        }
      }
    }

    public void onClick(View v) {
      int pos = getBindingAdapterPosition();
      Permission perm;
      if (pos != RecyclerView.NO_POSITION && (perm = getItem(pos)) != null) {
        int[] location = new int[2];
        v.getLocationInWindow(location);
        mCallback.onPermClick(perm, location[1] - 2 * v.getHeight());
      }
    }

    public boolean onLongClick(View v) {
      int pos = getBindingAdapterPosition();
      Permission perm;
      if (pos != RecyclerView.NO_POSITION && (perm = getItem(pos)) != null) {
        mCallback.onPermLongClick(perm);
      }
      return true;
    }
  }

  private static class DiffUtilItemCallBack extends DiffUtil.ItemCallback<Permission> {

    public boolean areItemsTheSame(Permission oldItem, Permission newItem) {
      return oldItem.getName().equals(newItem.getName());
    }

    public boolean areContentsTheSame(Permission oldItem, Permission newItem) {
      return oldItem.areContentsTheSame(newItem);
    }
  }

  public interface PermAdapterCallback {

    void onPermClick(Permission perm, int yLocation);

    void onPermLongClick(Permission perm);

    void onPermSwitchToggle(Permission perm);
  }
}
