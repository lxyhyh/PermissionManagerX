package com.mirfatif.permissionmanagerx.zhx.design;

import com.mirfatif.permissionmanagerx.R;
import com.mirfatif.permissionmanagerx.app.App;

/** 外观统一读取入口：自 UI 全面改版后固定为新设计风格，不再跟随用户偏好开关。 */
public class UiPrefUtils {

  private UiPrefUtils() {}

  public static int dpToPx(float dp) {
    return (int) (dp * App.getCxt().getResources().getDisplayMetrics().density);
  }

  /** 固定为卡片风格（20dp 圆角）。 */
  public static int getCardBg() {
    return R.drawable.card_bg;
  }

  /** 固定列表项内边距（dp）。 */
  public static int getItemPaddingDp() {
    return 10;
  }

  /** 固定显示水波纹反馈。 */
  public static boolean shouldUseRipple() {
    return true;
  }

  /** 固定显示引用状态指示条。 */
  public static boolean shouldShowRefIndicator() {
    return true;
  }

  /** 固定用胶囊 chip 显示 AppOp 模式。 */
  public static boolean shouldUseChip() {
    return true;
  }

  /** 固定用大标题。 */
  public static boolean shouldUseBigTitle() {
    return true;
  }
}
