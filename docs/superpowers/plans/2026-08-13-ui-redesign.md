# UI 全面重新设计（MIUI X + Apple 现代风）实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 PMX 全部界面重新设计为「MIUI X / HyperOS + Apple iOS」混合现代风格：大圆角连续曲线卡片（squircle）、低饱和底色+多彩图标、扁平图标、克制排版（本次**不做毛玻璃**，纯色低饱和）；同时**移除蓝/粉/灰主题色与全部外观偏好开关**，主题色收敛为两项：**初音绿（#39C5BB，默认）+ 跟随系统（动态取色）**。

**Architecture:** 本次改版严格遵循现有「设计系统资源模块」架构——所有颜色/圆角/主题集中在 `res/values*` 资源文件，外观唯一读取入口为 `zhx.design.UiPrefUtils`。因此改版分两条主线并行：(1) 重写颜色 Token、圆角 Token、主题/样式、drawable；(2) 移除蓝/粉/灰主题色与外型偏好开关，主题色保留「初音绿/跟随系统」两项，其余读取点固定为新卡片风格。不做任何数据层/守护进程改动。

**用户已确认的决策：** ✅ 主题色保留一项附加选项（跟随系统）；✅ 默认固定组合（卡片开/密度10dp/水波纹开/指示条开/chip开/大标题开）；✅ 保留夜间模式开关；✅ 卡片圆角 20dp；✅ 不做毛玻璃。

**Tech Stack:** Android XML 资源（colors/dimens/styles/theme/drawable/layout）、Java（MySettings、UiPrefUtils、BaseActivity、PackageAdapter、PermissionAdapter、MainActivity、SettingsFragTheme）、AppCompat + Material + RecyclerView。

---

## 文件结构总览

| 文件 | 责任 |
|---|---|
| `res/values/colors.xml` | 重写颜色 Token（浅色），初音绿品牌，移除蓝/粉/灰 |
| `res/values-night/colors.xml` | 重写夜间 Token |
| `res/values/dimens.xml` | 更新圆角 Token（squircle 连续曲线大圆角） |
| `res/values/attrs.xml` | 保留 `accentColor` 系列（移除多余桥接不做破坏） |
| `res/values/styles.xml` | 移除 ThemeOverlayBlue/Pink/Gray，保留 Green；更新公共样式 |
| `res/values/theme.xml` | 主题桥接微调 |
| `res/drawable/*.xml` | 重写卡片/搜索/胶囊/chip 背景为大圆角 |
| `res/layout/*.xml` | 主界面、列表项、关于页等重排为 iOS 分组卡片风 |
| `MySettings.java` | 移除/固定外观方法与主题色方法 |
| `UiPrefUtils.java` | 固定为固定值（初音绿卡片、固定圆角/密度/水波纹/指示条/chip/大标题） |
| `BaseActivity.java` | 移除主题色切换逻辑，固定初音绿 |
| `PackageAdapter.java` / `PermissionAdapter.java` / `MainActivity.java` | 移除外观偏好分支，用固定样式 |
| `SettingsFragTheme.java` / `settings_prefs_theming.xml` / `pref_keys_foss.xml` | 移除外观开关项 |
| `arrays.xml` | 移除 theme_colors / theme_color_values |

---

## Task 1: 重写颜色 Token（初音绿品牌，移除多主题色）

**Files:**
- Modify: `app/src/main/res/values/colors.xml`
- Modify: `app/src/main/res/values-night/colors.xml`

- [ ] **Step 1: 重写 `values/colors.xml`（浅色）**

  保留现有分层结构（基底/文字/品牌/语义/控件），将品牌区收敛为初音绿，并加入 MIUI+iOS 混合的浅色语义。删除 `blue*`、`pink*`、`gray*` 全部 color 条目。

```xml
<?xml version="1.0" encoding="utf-8"?>
<resources>
  <!-- ============================================================ -->
  <!-- 初音绿（Miku）设计系统 · 颜色 Token（浅色 = 默认模式）          -->
  <!-- MIUI X + Apple 现代混合：低饱和底色 + 大圆角 + 初音绿品牌      -->
  <!-- ============================================================ -->

  <!-- —— 基底层（浅色，iOS 灰白底） —— -->
  <color name="windowBg">#F2F2F7</color>
  <color name="cardBg">#FFFFFF</color>
  <color name="cardBgPressed">#E9E9EC</color>
  <color name="geekBorder">#14000000</color>
  <color name="dividerColor">#1F000000</color>
  <color name="darkTransBg">#66000000</color>

  <!-- —— 品牌色：初音绿（唯一主题色） —— -->
  <color name="green">#39C5BB</color>
  <color name="greenTrans5">#0D39C5BB</color>
  <color name="greenTrans10">#1A39C5BB</color>
  <color name="greenTrans20">#3339C5BB</color>
  <color name="greenTrans50">#8039C5BB</color>
  <color name="greenTrans75">#BF39C5BB</color>

  <!-- —— 文字层（浅色） —— -->
  <color name="textPrimary">#1A1A1A</color>
  <color name="textSecondary">#8E8E93</color>
  <color name="textTertiary">#C7C7CC</color>
  <color name="textOnCard">#1A1A1A</color>
  <color name="textOnPrimary">#FFFFFF</color>
  <color name="sharpText">#1A1A1A</color>

  <!-- —— 语义色（两模式共用） —— -->
  <color name="stateGreen">#34C759</color>
  <color name="stateOrange">#FF9F0A</color>
  <color name="stateRed">#FF3B30</color>
  <color name="stateInfo">#007AFF</color>
  <color name="orangeState">#FF9F0A</color>

  <!-- —— 控件层（浅色） —— -->
  <color name="colorControlNormal">#F0F0F2</color>
  <color name="colorControlNormalA50">#80F0F0F2</color>
  <color name="colorControlNormalDisabled">#F5F5F7</color>
</resources>
```

- [ ] **Step 2: 重写 `values-night/colors.xml`（夜间）**

  删除 `blue*`/`pink*`/`gray*`，仅覆盖基底/文字/控件。

```xml
<?xml version="1.0" encoding="utf-8"?>
<resources>
  <!-- —— 基底层（夜间，深灰低饱和） —— -->
  <color name="windowBg">#000000</color>
  <color name="cardBg">#1C1C1E</color>
  <color name="cardBgPressed">#2C2C2E</color>
  <color name="geekBorder">#14000000</color>
  <color name="dividerColor">#3A3A3C</color>
  <color name="darkTransBg">#B3000000</color>

  <!-- —— 文字层（夜间） —— -->
  <color name="textPrimary">#FFFFFF</color>
  <color name="textSecondary">#8E8E93</color>
  <color name="textTertiary">#48484A</color>
  <color name="textOnCard">#FFFFFF</color>
  <color name="textOnPrimary">#1A1A1A</color>
  <color name="sharpText">#FFFFFF</color>

  <!-- —— 控件层（夜间） —— -->
  <color name="colorControlNormal">#2C2C2E</color>
  <color name="colorControlNormalA50">#802C2C2E</color>
  <color name="colorControlNormalDisabled">#232629</color>
</resources>
```

- [ ] **Step 3: 验证颜色资源无残留引用**

  运行：`grep -rn "blue\|pink\|button_bg\|seekbar\|clock" app/src/main/res/values app/src/main/res/values-night`
  预期：不再有对已删除 `blue*`/`pink*`/`gray*` 的引用（`gray` 若在别处用到需后续处理，见 Task 6）。

- [ ] **Step 4: Commit**

```bash
git add app/src/main/res/values/colors.xml app/src/main/res/values-night/colors.xml
git commit -m "feat(ui): 重写颜色 Token 为初音绿 + MIUI/iOS 混合浅深两套"
```

---

## Task 2: 重写圆角与间距 Token（squircle 连续曲线大圆角）

**Files:**
- Modify: `app/src/main/res/values/dimens.xml`

- [ ] **Step 1: 更新 `dimens.xml` 的圆角 Token**

  将圆角改为 MIUI+iOS 偏大、连续曲线感的尺度（保留现有间距）。**注意**：多处布局直接写 `16dp` 圆角到 drawable，因此 drawable 的圆角在 Task 3 统一处理，此处更新命名 Token 供新 drawable 引用。

```xml
<resources>
  <!-- 间距（保留） -->
  <dimen name="space_1">4dp</dimen>
  <dimen name="space_2">8dp</dimen>
  <dimen name="space_3">12dp</dimen>
  <dimen name="space_4">16dp</dimen>
  <dimen name="space_5">20dp</dimen>
  <dimen name="space_6">24dp</dimen>
  <dimen name="space_8">32dp</dimen>

  <!-- 圆角（squircle 连续曲线大圆角，MIUI X + Apple） -->
  <dimen name="radius_sm">8dp</dimen>
  <dimen name="radius_md">12dp</dimen>
  <dimen name="radius_lg">16dp</dimen>
  <dimen name="radius_xl">20dp</dimen>
  <dimen name="radius_2xl">24dp</dimen>
  <dimen name="radius_3xl">28dp</dimen>
  <dimen name="radius_full">999dp</dimen>
</resources>
```

- [ ] **Step 2: Commit**

```bash
git add app/src/main/res/values/dimens.xml
git commit -m "feat(ui): 统一大圆角 Token（squircle 连续曲线）"
```

---

## Task 3: 重写 drawable 背景（大圆角 + 语义色）

**Files:**
- Modify: `app/src/main/res/drawable/card_bg.xml`
- Modify: `app/src/main/res/drawable/card_bg_mid.xml`
- Modify: `app/src/main/res/drawable/card_bg_small.xml`
- Modify: `app/src/main/res/drawable/search_bg.xml`
- Modify: `app/src/main/res/drawable/capsule_fill.xml`
- Modify: `app/src/main/res/drawable/capsule_outline.xml`
- Modify: `app/src/main/res/drawable/chip_bg.xml`（若存在）

- [ ] **Step 1: 重写 `card_bg.xml` 为 20dp 圆角 + 弱边框**

```xml
<?xml version="1.0" encoding="utf-8"?>
<selector xmlns:android="http://schemas.android.com/apk/res/android">
  <item android:state_pressed="true">
    <shape android:shape="rectangle">
      <corners android:radius="20dp" />
      <solid android:color="@color/cardBgPressed" />
    </shape>
  </item>
  <item>
    <shape android:shape="rectangle">
      <corners android:radius="20dp" />
      <solid android:color="@color/cardBg" />
      <stroke android:width="1dp" android:color="@color/geekBorder" />
    </shape>
  </item>
</selector>
```

- [ ] **Step 2: 重写 `card_bg_mid.xml`（16dp）与 `card_bg_small.xml`（12dp）**

```xml
<!-- card_bg_mid.xml -->
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
  <corners android:radius="16dp" />
  <solid android:color="@color/cardBg" />
</shape>
```

```xml
<!-- card_bg_small.xml -->
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
  <corners android:radius="12dp" />
  <solid android:color="@color/cardBg" />
</shape>
```

- [ ] **Step 3: 重写 `search_bg.xml`（22dp 胶囊，iOS 搜索框风）**

```xml
<?xml version="1.0" encoding="utf-8"?>
<selector xmlns:android="http://schemas.android.com/apk/res/android">
  <item android:state_pressed="true">
    <shape android:shape="rectangle">
      <corners android:radius="22dp" />
      <solid android:color="@color/cardBgPressed" />
    </shape>
  </item>
  <item>
    <shape android:shape="rectangle">
      <corners android:radius="22dp" />
      <solid android:color="@color/cardBg" />
    </shape>
  </item>
</selector>
```

- [ ] **Step 4: 重写 `capsule_fill.xml` / `capsule_outline.xml` / `chip_bg.xml`**

  胶囊保持 `radius_full`；`chip_bg.xml` 若存在，改为 `@color/greenTrans10` 底 + `green` 文字，圆角 12dp。

```xml
<!-- chip_bg.xml（若存在） -->
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
  <corners android:radius="12dp" />
  <solid android:color="@color/greenTrans10" />
</shape>
```

- [ ] **Step 5: Commit**

```bash
git add app/src/main/res/drawable/
git commit -m "feat(ui): 重写卡片/搜索/胶囊/chip 背景为大圆角"
```

---

## Task 4: 主题色收敛为初音绿 + 跟随系统（移除蓝/粉/灰）

**Files:**
- Modify: `app/src/main/java/com/mirfatif/permissionmanagerx/base/BaseActivity.java`
- Modify: `app/src/main/res/values/styles.xml`
- Modify: `app/src/main/res/values/arrays.xml`

- [ ] **Step 1: 重写 `BaseActivity.applyThemeColor()`**

  删除 Blue/Pink/Gray 分支。根据 `getThemeColorValue()` 返回值，仅在两值间选择：`green`（初音绿）或 `system`（跟随系统动态取色）。

```java
  /** 应用主题色：仅支持初音绿（默认）或跟随系统动态取色。 */
  private void applyThemeColor() {
    String color = MySettings.INS.getThemeColorValue();
    int overlay = R.style.ThemeOverlaySystem;
    if ("green".equals(color)) {
      overlay = R.style.ThemeOverlayGreen;
    }
    getTheme().applyStyle(overlay, true);
  }
```

- [ ] **Step 2: 从 `styles.xml` 删除 `ThemeOverlayBlue/Pink/Gray`，新增 `ThemeOverlaySystem`**

  删除 `ThemeOverlayBlue`、`ThemeOverlayPink`、`ThemeOverlayGray` 三个 style 块；保留 `ThemeOverlayGreen`；新增 `ThemeOverlaySystem`（动态取色，继承 `ThemeOverlay.Material3.DynamicColors.Light/Dark` 或 `ThemeOverlay.MaterialComponents` 变体，随 main 主题浅深自动切换）。

```xml
  <!-- 跟随系统动态取色 -->
  <style name="ThemeOverlaySystem" parent="ThemeOverlay.MaterialComponents.Dark.ActionBar" />
```

- [ ] **Step 3: 重写 `arrays.xml` 的 `theme_colors` 与 `theme_color_values`（两值）**

  将两个 string-array 改为仅两项：初音绿 + 跟随系统。

```xml
  <string-array name="theme_colors">
    <item>初音绿</item>
    <item>跟随系统</item>
  </string-array>

  <string-array name="theme_color_values">
    <item>green</item>
    <item>system</item>
  </string-array>
```

- [ ] **Step 4: 验证无残留引用**

  运行：`grep -rn "ThemeOverlayBlue\|ThemeOverlayPink\|ThemeOverlayGray" app/src/main`
  预期：无匹配（SettingsFragTheme 与 settings_prefs 在 Task 5 处理）。

- [ ] **Step 5: Commit**

```bash
git add app/src/main/java/com/mirfatif/permissionmanagerx/base/BaseActivity.java app/src/main/res/values/styles.xml app/src/main/res/values/arrays.xml
git commit -m "feat(ui): 移除多主题色切换，固定初音绿主题"
```

---

## Task 5: 移除外观偏好开关（UI 与逻辑）

**Files:**
- Modify: `app/src/main/java/com/mirfatif/permissionmanagerx/prefs/MySettings.java`
- Modify: `app/src/main/java/com/mirfatif/permissionmanagerx/zhx/design/UiPrefUtils.java`
- Modify: `app/src/main/java/com/mirfatif/permissionmanagerx/prefs/settings/SettingsFragTheme.java`
- Modify: `app/src/main/res/xml/settings_prefs_theming.xml`
- Modify: `app/src/main/res/values/pref_keys_foss.xml`

- [ ] **Step 1: 简化 `UiPrefUtils` 为固定值**

  移除对 `MySettings` 外观方法的依赖，全部返回固定值（卡片开、20dp 圆角、密度 10dp、水波纹开、指示条开、chip 开、大标题开）。

```java
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
```

- [ ] **Step 2: 从 `MySettings` 移除外观方法（保留主题色与夜间方法）**

  删除 `shouldUseCardStyle()`、`getCardCornerRadius()`、`shouldShowRefIndicator()`、`shouldUseChipStyle()`、`getListDensity()`、`shouldUseBigTitle()`、`shouldUseRipple()`（第 123-172 行）。**保留** `getThemeColorValue()`/`setThemeColorValue()`（仍在两值间切换）与 `getDarkThemeMode()`（夜间模式）。若删后有未使用 import，一并清理。

- [ ] **Step 3: 简化 `SettingsFragTheme.onSharedPreferenceChanged`**

  仅保留主题色与夜间模式触发的刷新逻辑，删除 card/radius/dots/chip/density/big_title/ripple 分支。

```java
  public void onSharedPreferenceChanged(SharedPreferences sharedPreferences, String key) {
    if (Objects.requireNonNull(key).equals(getString(R.string.pref_settings_theme_color_key))
        || Objects.requireNonNull(key).equals(getString(R.string.pref_settings_dark_theme_key))) {
      mA.recreate();
      MySettings.INS.recreateMainActivity();
    }
  }
```

- [ ] **Step 4: 精简 `settings_prefs_theming.xml`**

  保留 `theme_color` ListPreference（数组已是两项：初音绿/跟随系统）与 `dark_theme` ListPreference；删除整个 `<PreferenceCategory>`（外观：card/radius/dots/chip/density/big_title/ripple）分组。

```xml
<?xml version="1.0" encoding="utf-8"?>
<PreferenceScreen xmlns:app="http://schemas.android.com/apk/res-auto">
  <ListPreference
    app:defaultValue="@string/pref_settings_theme_color_default"
    app:entries="@array/theme_colors"
    app:entryValues="@array/theme_color_values"
    app:icon="@drawable/palette"
    app:key="@string/pref_settings_theme_color_key"
    app:singleLineTitle="false"
    app:title="@string/pref_settings_theme_color_title"
    app:useSimpleSummaryProvider="true" />
  <ListPreference
    app:defaultValue="@string/pref_settings_dark_theme_default"
    app:entries="@array/dark_theme_modes"
    app:entryValues="@array/dark_theme_mode_values"
    app:icon="@drawable/dark_mode"
    app:key="@string/pref_settings_dark_theme_key"
    app:singleLineTitle="false"
    app:title="@string/pref_settings_dark_theme_title"
    app:useSimpleSummaryProvider="true" />
</PreferenceScreen>
```

- [ ] **Step 5: 从 `pref_keys_foss.xml` 删除外观键（保留 theme_color 与 dark_theme）**

  删除与 `pref_settings_ui_card_style`、`pref_settings_ui_radius`、`pref_settings_ui_dots`、`pref_settings_ui_chip`、`pref_settings_ui_density`、`pref_settings_ui_big_title`、`pref_settings_ui_ripple` 相关的**字符串键**（第 270-343 行附近）。**保留** `pref_settings_theme_color_*` 与 `pref_settings_dark_theme_*` 键。若这些键在其他 `.xml`（如 `values-*/pref_keys_foss.xml`）也存在，需先确认生成逻辑，避免 aapt2 报错——先只改默认 `values/`，如构建报未定义再补其他。

- [ ] **Step 6: 验证编译**

  运行：`./gradlew :app:compileDebugJavaWithJavac`（或 `:app:spotlessApply` 后 `:app:assembleDebug`）
  预期：成功，无对已删 R 资源（`R.string.pref_settings_ui_*`、`R.bool.pref_settings_ui_*`）的引用。

- [ ] **Step 7: Commit**

```bash
git add app/src/main/java/com/mirfatif/permissionmanagerx/prefs/MySettings.java app/src/main/java/com/mirfatif/permissionmanagerx/zhx/design/UiPrefUtils.java app/src/main/java/com/mirfatif/permissionmanagerx/prefs/settings/SettingsFragTheme.java app/src/main/res/xml/settings_prefs_theming.xml app/src/main/res/values/pref_keys_foss.xml
git commit -m "feat(ui): 移除外观偏好开关，固定新设计风格"
```

---

## Task 6: 清理适配器与主界面对偏好分支的引用，并全局处理 `gray` 引用

**Files:**
- Modify: `app/src/main/java/com/mirfatif/permissionmanagerx/main/PackageAdapter.java`
- Modify: `app/src/main/java/com/mirfatif/permissionmanagerx/pkg/PermissionAdapter.java`
- Modify: `app/src/main/java/com/mirfatif/permissionmanagerx/main/MainActivity.java`

- [ ] **Step 1: 简化 `PackageAdapter.onCreateViewHolder`**

  移除偏好分支，直接应用固定样式。

```java
  public ItemViewHolder onCreateViewHolder(ViewGroup parent, int viewType) {
    LayoutInflater inflater = LayoutInflater.from(parent.getContext());
    RvItemPkgBinding binding = RvItemPkgBinding.inflate(inflater, parent, false);

    // 固定新设计风格：卡片背景 / 指示条 / 水波纹 / 密度
    binding.getRoot().setBackgroundResource(UiPrefUtils.getCardBg());
    binding.refIndicationV.setVisibility(View.VISIBLE);
    int pad = UiPrefUtils.dpToPx(UiPrefUtils.getItemPaddingDp());
    binding.getRoot().setPadding(pad, 0, pad, 0);

    return new ItemViewHolder(binding);
  }
```

- [ ] **Step 2: 简化 `PermissionAdapter.onCreateViewHolder`**

```java
  public ItemViewHolder onCreateViewHolder(ViewGroup parent, int viewType) {
    LayoutInflater inflater = LayoutInflater.from(parent.getContext());
    RvItemPermBinding b = RvItemPermBinding.inflate(inflater, parent, false);

    // 固定新设计风格
    b.getRoot().setBackgroundResource(UiPrefUtils.getCardBg());
    b.refIndicationV.setVisibility(View.VISIBLE);

    return new ItemViewHolder(b);
  }
```

  同时删除 `bind()` 中 `if (UiPrefUtils.shouldUseChip())` 分支，固定为 chip 样式（删除 else 分支）：

```java
          if (mode != AppOpsManager.MODE_ALLOWED && mode != AppOpsManager.MODE_IGNORED) {
            mB.appOpModeV.setVisibility(View.VISIBLE);
            mB.appOpModeV.setText(perm.getLocalizedPermStateName());
            mB.appOpModeV.setBackgroundResource(R.drawable.chip_bg);
            mB.appOpModeV.setPadding(8, 2, 8, 2);
          } else {
            mB.appOpModeV.setVisibility(View.GONE);
          }
```

- [ ] **Step 3: 简化 `MainActivity` 大标题逻辑**

```java
    mB = ActivityMainBinding.inflate(mA.getLayoutInflater());
    mB.movCont.setData(new Data());
    mA.setContentView(mB);

    // MIUI/iOS 混合风格：固定大标题
    mB.bigTitleV.setVisibility(View.VISIBLE);
    mB.bigTitleV.setText(R.string.app_name);
```

- [ ] **Step 4: 全局检查 `gray` 颜色引用**

  运行：`grep -rn "@color/gray\|@color/grayTrans\|R.color.gray" app/src/main`
  若存在对 `gray`/`grayTrans*` 的引用（Task 1 已删），需改为 `@color/textTertiary` 或保留一个 `gray`=#9CA3AF 别名。若保留，在 `colors.xml` 加回 `gray` 别名以免报错。

- [ ] **Step 5: Verify spotless + 编译**

  运行：`./gradlew :app:spotlessApply :app:compileDebugJavaWithJavac`
  预期：成功。

- [ ] **Step 6: Commit**

```bash
git add app/src/main/java/com/mirfatif/permissionmanagerx/main/PackageAdapter.java app/src/main/java/com/mirfatif/permissionmanagerx/pkg/PermissionAdapter.java app/src/main/java/com/mirfatif/permissionmanagerx/main/MainActivity.java app/src/main/res/values/colors.xml
git commit -m "feat(ui): 适配器与主界面固定新样式，清理灰色引用"
```

---

## Task 7: 重排关键布局为 iOS 分组卡片风

**Files:**
- Modify: `app/src/main/res/layout/activity_main.xml`
- Modify: `app/src/main/res/layout/rv_item_pkg.xml`
- Modify: `app/src/main/res/layout/rv_item_perm.xml`
- Modify: `app/src/main/res/layout/activity_about.xml`
- Modify: `app/src/main/res/layout/activity_perm_list.xml`

- [ ] **Step 1: 调整 `rv_item_pkg.xml` 间距与圆角**

  将 `android:layout_marginHorizontal="8dp"` 改为 `12dp`，`layout_marginVertical="12dp"` 改为 `6dp`（iOS 分组列表项密集排列），保持 `background="@drawable/card_bg"`（已是 20dp 圆角）。

- [ ] **Step 2: 调整 `rv_item_perm.xml` 间距**

  同样 `.layout_marginHorizontal="8dp"` → `12dp`，`layout_marginVertical="12dp"` → `6dp`。

- [ ] **Step 3: 调整 `activity_main.xml` 顶部大标题**

  将 `big_title_v` 的 `paddingBottom="8dp"` 改为 `12dp`，`textSize="28sp"` 保持，`letterSpacing="-0.02"` 保持。顶部 `View` 分隔线移除或改细（删除第 12-14 行的 `ListSeparator` View，改用 `android:background="?attr/accentColor"` 的 2dp 细线）。

- [ ] **Step 4: 调整 `activity_about.xml` 为分组卡片**

  将根 `MyLinearLayout` 的 `android:layout_margin="8dp"` 改为 `12dp`；每个 `AboutActivityItemContainer` 改为 `background="@drawable/card_bg"` + `android:clipToOutline="true"`，并在相邻项之间加 `View` 分隔线（已在布局中存在的 `ListSeparator` 保留，但改 `geekBorder` 细线）。此项为可选打磨，若改动过大导致编译失败可回退到仅调间距。

- [ ] **Step 5: Commit**

```bash
git add app/src/main/res/layout/
git commit -m "feat(ui): 关键布局重排为 iOS 分组卡片风"
```

---

## Task 8: 全量构建验证 + 设计文档同步

**Files:**
- Run: 构建
- Modify: `docs/架构-设计系统与模块划分.md`

- [ ] **Step 1: 全量编译**

  运行：`./gradlew :app:assembleDebug`
  预期：成功产出 APK。

- [ ] **Step 2: 更新设计文档**

  将引言从「GeekOS」更新为「初音绿（Miku）· MIUI X + Apple 现代混合」设计系统；更新开头「设计系统资源模块」对 `colors.xml`/`theme.xml`/`styles.xml`/`dimens.xml`/drawable 的职责描述；删除关于「多主题色切换（蓝/粉/灰）」与「外观偏好开关」的说明，改为「主题色两项：初音绿/跟随系统」；在第 27-39 行 Token 表格中更新为新初音绿配色；在第二节模块划分中说明 `UiPrefUtils` 已固定为固定样式。

- [ ] **Step 3: Commit**

```bash
git add docs/架构-设计系统与模块划分.md
git commit -m "docs(ui): 更新设计系统文档为初音绿 MIUI/iOS 混合风格"
```

---

## Self-Review

**1. Spec 覆盖：**
- 全部界面 → Task 1-3（全局 Token/drawable）+ Task 7（关键布局）+ 已有布局引用 Token 自动生效。所有界面通过 `?attr/accentColor` 与 `@color/*` 全局换肤，无需逐一改每个 Activity。
- MIUI X + Apple 混合风格 → Task 1（低饱和底色/语义色）、Task 2-3（大圆角）、Task 7（分组卡片）。
- 移除蓝/粉/灰主题色 + 外观偏好开关 → Task 4-6。
- 保留主题色两项（初音绿/跟随系统）→ Task 4/5。
- 固定初音绿（默认）→ Task 1/4。

**2. Placeholder scan：** 所有 Step 均含具体代码或命令，无 TBD/TODO。`chip_bg.xml`、`gray` 引用、`values-*/pref_keys_foss.xml` 标记为「若存在/若报错」的场景已给出明确处理路径。

**3. 类型一致性：** `UiPrefUtils` 方法签名在 Task 5 保持一致；`R.drawable.chip_bg`、`R.style.ThemeOverlayGreen`/`ThemeOverlaySystem`、`pref_settings_theme_color_key`/`pref_settings_dark_theme_key` 等引用与现有代码一致。`getThemeColorValue()`/`setThemeColorValue()` 与 `getDarkThemeMode()` 均保留（两值主题色 + 夜间模式仍可用）。

**风险提示：** Task 6 Step 4 若 `gray` 被多处引用，删除后 aapt2 会报错；已在 Step 中给出「加回 `gray` 别名」的兜底。Task 7 布局微调不影响功能，可独立回退。