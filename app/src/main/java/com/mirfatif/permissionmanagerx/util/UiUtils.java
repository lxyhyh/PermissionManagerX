package com.mirfatif.permissionmanagerx.util;

import android.animation.LayoutTransition;
import android.app.Activity;
import android.app.Dialog;
import android.content.DialogInterface;
import android.content.res.ColorStateList;
import android.content.res.Configuration;
import android.content.res.Resources;
import android.graphics.Color;
import android.graphics.Typeface;
import android.text.style.TextAppearanceSpan;
import android.util.TypedValue;
import android.view.View;
import android.view.ViewGroup;
import android.view.Window;
import android.widget.Button;
import android.widget.Toast;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AlertDialog;
import androidx.core.graphics.ColorUtils;
import androidx.fragment.app.FragmentActivity;
import com.google.android.material.color.MaterialColors;
import com.google.android.material.snackbar.Snackbar;
import com.mirfatif.permissionmanagerx.R;
import com.mirfatif.permissionmanagerx.app.App;
import com.mirfatif.permissionmanagerx.base.DialogBg;
import com.mirfatif.permissionmanagerx.util.bg.UiRunner;
import com.mirfatif.privtasks.util.bg.ThreadUtils;

public class UiUtils {

  private UiUtils() {}

  public static boolean isNightMode(Activity activity) {
    int uiMode = activity.getResources().getConfiguration().uiMode;
    return (uiMode & Configuration.UI_MODE_NIGHT_MASK) == Configuration.UI_MODE_NIGHT_YES;
  }

  public static int dpToPx(float dp) {
    return (int)
        TypedValue.applyDimension(
            TypedValue.COMPLEX_UNIT_DIP, dp, Resources.getSystem().getDisplayMetrics());
  }

  public static String colorIntToRGB(int color, boolean retainAlpha) {
    if (retainAlpha) {
      return String.format("#%08X", color);
    } else {
      return String.format("#%06X", 0xFFFFFF & color);
    }
  }

  public static int getColor(Activity activity, int colorAttrResId) {
    return MaterialColors.getColor(activity, colorAttrResId, Color.TRANSPARENT);
  }

  public static int getBgColor(Activity activity) {
    return getColor(activity, android.R.attr.windowBackground);
  }

  public static int getSharpBgColor(Activity activity) {
    return ColorUtils.blendARGB(
        getBgColor(activity), isNightMode(activity) ? Color.BLACK : Color.WHITE, 0.05f);
  }

  public static int getDimBgColor(Activity activity) {
    return ColorUtils.blendARGB(
        getBgColor(activity), isNightMode(activity) ? Color.WHITE : Color.BLACK, 0.05f);
  }

  public static int getAccentColor() {
    return App.getCxt().getColor(R.color.green);
  }

  public static void onCreateLayout(ViewGroup view) {
    LayoutTransition transition = new LayoutTransition();
    transition.enableTransitionType(LayoutTransition.CHANGING);
    view.setLayoutTransition(transition);
  }

  public static void onCreateDialog(Dialog dialog, Activity activity) {
    Window window = dialog.getWindow();
    if (window == null) {
      return;
    }

    window.setBackgroundDrawable(new DialogBg(activity, true));

    window.setWindowAnimations(android.R.style.Animation_Dialog);
  }

  public static AlertDialog removeButtonPadding(AlertDialog dialog) {
    dialog.setOnShowListener(
        d -> {
          Button b = dialog.getButton(DialogInterface.BUTTON_NEUTRAL);
          int padding = dpToPx(4);
          b.setPadding(b.getPaddingLeft(), padding, padding, padding);
        });
    return dialog;
  }

  public static TextAppearanceSpan getTextHighlightSpan(int colorInt) {
    return new TextAppearanceSpan(
        null,
        Typeface.NORMAL,
        -1,
        new ColorStateList(new int[][] {new int[] {}}, new int[] {colorInt}),
        null);
  }

  public static void showToast(String msg) {
    if (msg != null) {
      UiRunner.post(() -> Toast.makeText(App.getCxt(), msg, Toast.LENGTH_LONG).show());
    }
  }

  public static void showToast(int resId, Object... args) {
    if (resId != 0) {
      showToast(ApiUtils.getString(resId, args));
    }
  }

  public static void showSnackBar(
      FragmentActivity activity, View parent, @Nullable View anchor, String text, int seconds) {
    if (!ThreadUtils.isMainThread()) {
      UiRunner.post(activity, () -> showSnackBar(activity, parent, anchor, text, seconds));
      return;
    }
    var sb = createSnackBar(activity, parent, anchor, text, seconds);
    sb.show();
  }

  public static Snackbar createSnackBar(
      Activity activity, View parent, @Nullable View anchor, String text, int seconds) {
    Snackbar snackBar = Snackbar.make(parent, text, seconds * 1000);
    snackBar.setAnchorView(anchor);

    // L Snackbar 统一品牌化视觉：
    //   1) 文字颜色：sharpText → ink_1（浅=黑/暗=白，与 ink_1 同义，统一用 @color/ink_1 走主题别名覆盖）
    //   2) Action 按钮颜色：原生默认 accentColor → brand 初音绿（浅/深色都用同名 @color/brand）
    //   3) 背景：旧 getSharpBgColor(activity) 纯 accentColor → @drawable/bg_snackbar（card 色+14dp圆角+0.5dp
    // card_stroke 描边，与列表/设置卡片同一 design token）
    //   4) 阴影 elevation 6dp：比列表/设置卡（3dp）高一级但低于底栏（12dp），合理层级
    //   5) margin：left/right = bottom_bar_margin_h (LX=16dp) 与装饰条/底栏对齐；bottom = 88dp = 底栏高度(62) +
    // 底部悬浮(18) + 间隙(8) → 不遮挡底栏
    snackBar.setTextColor(activity.getColor(R.color.ink_1));
    snackBar.setActionTextColor(activity.getColor(R.color.brand));

    View snackView = snackBar.getView();
    snackView.setBackgroundResource(R.drawable.bg_snackbar);
    snackView.setElevation(6 * activity.getResources().getDisplayMetrics().density + 0.5f);
    if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.LOLLIPOP) {
      snackView.setOutlineProvider(android.view.ViewOutlineProvider.BACKGROUND);
      snackView.setClipToOutline(true);
    }

    ViewGroup.LayoutParams lp = snackView.getLayoutParams();
    if (lp instanceof ViewGroup.MarginLayoutParams) {
      ViewGroup.MarginLayoutParams mlp = (ViewGroup.MarginLayoutParams) lp;
      int hMargin = (int) activity.getResources().getDimension(R.dimen.bottom_bar_margin_h);
      int bottomMargin =
          (int)
              TypedValue.applyDimension(
                  TypedValue.COMPLEX_UNIT_DIP, 88, activity.getResources().getDisplayMetrics());
      mlp.leftMargin = hMargin;
      mlp.rightMargin = hMargin;
      mlp.bottomMargin = Math.max(mlp.bottomMargin, bottomMargin);
      snackView.setLayoutParams(mlp);
    }

    return snackBar;
  }
}
