package com.mirfatif.permissionmanagerx.zhx.design;

import com.mirfatif.permissionmanagerx.R;
import com.mirfatif.permissionmanagerx.app.App;
import com.mirfatif.permissionmanagerx.prefs.MySettings;

/** 外观设置的统一读取入口：各列表/页面按此工具应用 UI 偏好。 */
public class UiPrefUtils {

  private UiPrefUtils() {}

  public static int dpToPx(float dp) {
    return (int) (dp * App.getCxt().getResources().getDisplayMetrics().density);
  }

  /** 当前列表项背景 drawable；卡片风格关闭时返回分割线列表背景（GeekOS list-item）。 */
  public static int getCardBg() {
    if (!MySettings.INS.shouldUseCardStyle()) {
      return R.drawable.list_item_bg;
    }
    String radius = MySettings.INS.getCardCornerRadius();
    if ("small".equals(radius)) {
      return R.drawable.card_bg_small;
    }
    if ("mid".equals(radius)) {
      return R.drawable.card_bg_mid;
    }
    return R.drawable.card_bg;
  }

  /** 列表项内容内边距（dp）：compact=6 / normal=10 / comfort=14 */
  public static int getItemPaddingDp() {
    String density = MySettings.INS.getListDensity();
    if ("compact".equals(density)) {
      return 6;
    }
    if ("comfort".equals(density)) {
      return 14;
    }
    return 10;
  }

  /** 是否显示水波纹反馈背景。 */
  public static boolean shouldUseRipple() {
    return MySettings.INS.shouldUseRipple();
  }

  /** 是否显示引用状态指示条。 */
  public static boolean shouldShowRefIndicator() {
    return MySettings.INS.shouldShowRefIndicator();
  }

  /** 是否用胶囊 chip 显示 AppOp 模式。 */
  public static boolean shouldUseChip() {
    return MySettings.INS.shouldUseChipStyle();
  }

  /** 顶部标题是否用大字号。 */
  public static boolean shouldUseBigTitle() {
    return MySettings.INS.shouldUseBigTitle();
  }
}
