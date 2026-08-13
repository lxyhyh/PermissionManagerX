package com.mirfatif.permissionmanagerx.zhx.i18n;

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

    String label = mLabels.get(name);
    if (label == null) {
      label = translateOpName(name);
    }
    return label;
  }

  private static final String[] OP_WORDS =
      new String[] {
        "READ",
        "读取",
        "WRITE",
        "写入",
        "RECEIVE",
        "接收",
        "SEND",
        "发送",
        "GET",
        "获取",
        "SET",
        "设置",
        "MANAGE",
        "管理",
        "USE",
        "使用",
        "REQUEST",
        "请求",
        "CHANGE",
        "更改",
        "MONITOR",
        "监视",
        "PROJECT",
        "投影",
        "PLAY",
        "播放",
        "RECORD",
        "录制",
        "TAKE",
        "占用",
        "START",
        "启动",
        "RUN",
        "运行",
        "POST",
        "发布",
        "ACCESS",
        "访问",
        "BIND",
        "绑定",
        "MUTE",
        "静音",
        "TURN",
        "打开",
        "CONTROL",
        "控制",
        "ACTIVATE",
        "激活",
        "ESTABLISH",
        "建立",
        "ENABLE",
        "开启",
        "ANSWER",
        "接听",
        "CALL",
        "拨打",
        "CREATE",
        "创建",
        "CAPTURE",
        "抓取",
        "CONFIRM",
        "确认",
        "RANGING",
        "测距",
        "AUDIO",
        "音频",
        "CAMERA",
        "相机",
        "MICROPHONE",
        "麦克风",
        "CONTACTS",
        "联系人",
        "CALENDAR",
        "日历",
        "SMS",
        "短信",
        "MMS",
        "彩信",
        "CALL_LOG",
        "通话记录",
        "WAP_PUSH",
        "WAP推送",
        "CELL_BROADCASTS",
        "小区广播",
        "ICC_SMS",
        "SIM卡短信",
        "CLIPBOARD",
        "剪贴板",
        "EXTERNAL_STORAGE",
        "外部存储",
        "MEDIA_AUDIO",
        "媒体音频",
        "MEDIA_IMAGES",
        "媒体图片",
        "MEDIA_VIDEO",
        "媒体视频",
        "MEDIA_LOCATION",
        "媒体位置信息",
        "PHONE_STATE",
        "电话状态",
        "PHONE_NUMBERS",
        "电话号码",
        "PHONE_CALL",
        "通话",
        "ACCOUNTS",
        "账户",
        "VOICEMAIL",
        "语音留言",
        "USAGE_STATS",
        "使用情况统计",
        "INSTALL_PACKAGES",
        "安装应用",
        "DELETE_PACKAGES",
        "卸载应用",
        "QUERY_ALL_PACKAGES",
        "查询所有应用",
        "WIFI_SCAN",
        "扫描Wi-Fi",
        "WIFI_STATE",
        "Wi-Fi状态",
        "BLUETOOTH_SCAN",
        "蓝牙扫描",
        "BLUETOOTH_CONNECT",
        "蓝牙连接",
        "BLUETOOTH_ADVERTISE",
        "蓝牙广播",
        "NEARBY_WIFI_DEVICES",
        "附近Wi-Fi设备",
        "LOCATION",
        "位置",
        "COARSE",
        "大致",
        "FINE",
        "精确",
        "BACKGROUND",
        "后台",
        "FOREGROUND",
        "前台",
        "AUDIO_FOCUS",
        "音频焦点",
        "MEDIA_BUTTONS",
        "媒体按键",
        "NOTIFICATION",
        "通知",
        "NOTIFICATIONS",
        "通知",
        "OUTGOING_CALLS",
        "外拨电话",
        "ANSWER_PHONE_CALLS",
        "接听来电",
        "CALL_PHONE",
        "拨打电话",
        "INTERNET",
        "互联网",
        "NETWORK_STATE",
        "网络状态",
        "ALARM",
        "闹钟",
        "EXACT_ALARM",
        "精确闹钟",
        "BOOT_COMPLETED",
        "开机自启",
        "BATTERY_OPTIMIZATIONS",
        "电池优化",
        "FULL_SCREEN_INTENT",
        "全屏通知",
        "DEVICE_ADMIN",
        "设备管理器",
        "NOTIFICATION_LISTENER_SERVICE",
        "通知使用权",
        "ACCESSIBILITY_SERVICE",
        "无障碍服务",
        "VPN",
        "VPN",
        "DEVICE_IDENTIFIERS",
        "设备标识符",
        "ICC_AUTH",
        "SIM认证",
        "SENSORS",
        "传感器",
        "BODY_SENSORS",
        "身体传感器",
        "ACTIVITY_RECOGNITION",
        "身体活动识别",
        "SCREEN",
        "屏幕",
        "SCREENSHOT",
        "截屏",
        "STRUCTURE",
        "结构",
        "WALLPAPER",
        "壁纸",
        "SETTINGS",
        "设置",
        "SECURE_SETTINGS",
        "安全设置",
        "ALERT_WINDOW",
        "悬浮窗",
        "PICTURE_IN_PICTURE",
        "画中画",
        "LEGACY_STORAGE",
        "旧版存储访问",
        "SYSTEM_ALERT_WINDOW",
        "悬浮窗",
        "WAKE_LOCK",
        "唤醒锁",
        "VIBRATE",
        "振动",
        "TOAST_WINDOW",
        "显示Toast",
        "PACKAGES",
        "应用",
        "DATA",
        "数据",
        "SOURCE",
        "数据源",
        "SANDBOXED",
        "沙箱",
        "TRACKING",
        "追踪",
        "HEART_RATE",
        "心率",
        "OXYGEN_SATURATION",
        "血氧",
        "SKIN_TEMPERATURE",
        "皮肤温度",
        "HEALTH_DATA",
        "健康数据",
        "CREDENTIALS",
        "凭据",
        "IPSEC_TUNNELS",
        "IPsec隧道",
        "MEDIA",
        "媒体",
        "ROUTING",
        "路由",
        "EMERGENCY",
        "紧急",
        "MOBILE_DATA",
        "移动数据",
        "USER",
        "用户",
        "INSTANT_APP",
        "免安装应用",
        "LOADER",
        "加载器",
        "JOBS",
        "任务",
        "SCENE_UNDERSTANDING",
        "场景理解",
        "EXEMPT_FROM",
        "豁免",
        "HIBERNATION",
        "休眠",
        "SUSPENSION",
        "挂起",
        "DISMISSIBLE",
        "可关闭的",
        "RESTRICTED_SETTINGS",
        "受限设置",
        "HANDOVER",
        "转接",
        "ARCHIVE",
        "归档",
        "ICON_OVERLAY",
        "图标标记",
        "UNARCHIVAL",
        "恢复归档",
        "CONFIRMATION",
        "确认",
        "HOTWORD",
        "唤醒词",
        "OUTPUT",
        "输出",
        "SIP",
        "SIP",
        "UWB",
        "UWB",
        "GPS",
        "GPS",
        "NFC",
        "NFC",
        "BIOMETRIC",
        "生物识别",
        "FINGERPRINT",
        "指纹",
        "SENSITIVE",
        "敏感",
        "AMBIENT",
        "环境",
        "TRIGGER",
        "触发",
        "EXPLICIT",
        "显式",
        "INTERACTION",
        "交互",
        "INCOMING",
        "来电",
        "PHONE",
        "电话",
        "VISUAL_USER_SELECTED",
        "用户选择的",
        "GRAMMATICAL_GENDER",
        "语法性别",
        "SPECIAL_USE",
        "特殊用途",
        "OVERRIDE",
        "覆盖",
        "POLICY",
        "策略",
        "FIXED",
        "固定",
        "PLATFORM",
        "平台",
        "RESTRICTED",
        "受限",
        "SANDBOX",
        "沙箱",
        "TESTING",
        "测试",
        "HISTORICAL",
        "历史",
        "WINDOW",
        "窗口",
        "SCREEN_ON",
        "点亮屏幕",
        "DEVICE",
        "设备",
        "SERVICE",
        "服务",
        "LISTENER",
        "监听器",
        "MANAGER",
        "管理器",
        "INSECURE",
        "不安全",
        "SECURE",
        "安全"
      };

  /** 规则兜底：静态映射查不到时，按驼峰单词表生成中文名。 */
  private String translateOpName(String name) {
    if (name == null || name.isEmpty()) {
      return null;
    }
    StringBuilder sb = new StringBuilder();
    String[] parts = name.split("_");
    for (String part : parts) {
      String zh = null;
      for (int i = 0; i < OP_WORDS.length; i += 2) {
        if (OP_WORDS[i].equals(part)) {
          zh = OP_WORDS[i + 1];
          break;
        }
      }
      if (zh == null) {
        return null; // 有未识别单词时放弃规则翻译，避免产生奇怪结果
      }
      sb.append(zh);
    }
    return sb.length() == 0 ? null : sb.toString();
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
