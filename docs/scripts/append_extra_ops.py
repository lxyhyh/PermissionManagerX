#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""向 perm_descs.xml（英文/中文）追加 Android16 新增 AppOps 的名称/说明/中文名。"""
import re
import os

ROOT = os.path.dirname(os.path.abspath(__file__))

# op -> (英文说明, 中文名, 中文说明)
EXTRA = [
    ("ACCEPT_HANDOVER", "Accept a phone call handover from another device.", "接受通话转接", "接受从其他设备转接过来的通话。"),
    ("ACCESS_ACCESSIBILITY", "Access accessibility features.", "访问无障碍功能", "访问无障碍相关功能。"),
    ("ACCESS_MEDIA_LOCATION", "Read location embedded in media files.", "媒体位置信息", "读取媒体文件中嵌入的位置信息。"),
    ("ACCESS_RESTRICTED_SETTINGS", "Access restricted settings.", "受限设置", "访问受限的系统设置。"),
    ("ACTIVATE_PLATFORM_VPN", "Activate the platform VPN.", "平台 VPN", "激活系统平台 VPN。"),
    ("ACTIVATE_VPN", "Activate VPN.", "VPN", "激活 VPN 连接。"),
    ("ACTIVITY_RECOGNITION_SOURCE", "Use the activity recognition data source.", "身体活动数据源", "使用身体活动识别的数据源。"),
    ("ARCHIVE_ICON_OVERLAY", "Show archived app icon overlay.", "归档图标标记", "在已归档应用的图标上显示标记。"),
    ("CAMERA_SANDBOXED", "Use the camera in sandboxed mode.", "相机（沙箱）", "以沙箱模式使用相机。"),
    ("CAPTURE_CONSENTLESS_BUGREPORT_ON_USERDEBUG_BUILD", "Capture bug report without consent (userdebug builds).", "免确认抓取错误报告", "在 userdebug 版本上无需确认抓取错误报告。"),
    ("COARSE_LOCATION_SOURCE", "Use the coarse location data source.", "大致位置数据源", "使用大致位置的数据源。"),
    ("CONTROL_AUDIO", "Control audio playback.", "控制音频", "控制音频播放。"),
    ("CONTROL_AUDIO_PARTIAL", "Partially control audio playback.", "部分音频控制", "部分控制音频播放。"),
    ("CREATE_ACCESSIBILITY_OVERLAY", "Create accessibility overlays.", "创建无障碍悬浮层", "创建无障碍悬浮层。"),
    ("EMERGENCY_LOCATION", "Access location during emergency.", "紧急位置", "在紧急情况下访问位置。"),
    ("ENABLE_MOBILE_DATA_BY_USER", "Enable mobile data by user action.", "开启移动数据", "由用户操作开启移动数据。"),
    ("ESTABLISH_VPN_MANAGER", "Establish VPN as manager.", "VPN 管理", "以管理者身份建立 VPN。"),
    ("ESTABLISH_VPN_SERVICE", "Establish VPN service.", "VPN 服务", "建立 VPN 服务。"),
    ("EYE_TRACKING_COARSE", "Coarse eye tracking data.", "粗略眼动追踪", "获取粗略的眼动追踪数据。"),
    ("EYE_TRACKING_FINE", "Fine eye tracking data.", "精确眼动追踪", "获取精确的眼动追踪数据。"),
    ("FACE_TRACKING", "Face tracking data.", "面部追踪", "获取面部追踪数据。"),
    ("FINE_LOCATION_SOURCE", "Use the fine location data source.", "精确位置数据源", "使用精确位置的数据源。"),
    ("FOREGROUND_SERVICE_SPECIAL_USE", "Run a special use foreground service.", "特殊用途前台服务", "运行特殊用途的前台服务。"),
    ("HAND_TRACKING", "Hand tracking data.", "手部追踪", "获取手部追踪数据。"),
    ("HEAD_TRACKING", "Head tracking data.", "头部追踪", "获取头部追踪数据。"),
    ("INSTANT_APP_START_FOREGROUND", "Start foreground from an instant app.", "免安装应用前台启动", "免安装（instant）应用启动前台组件。"),
    ("LOADER_USAGE_STATS", "Read usage stats via loader.", "加载器使用统计", "通过数据加载器读取使用情况统计。"),
    ("MANAGE_CREDENTIALS", "Manage credentials.", "管理凭据", "管理设备上的凭据。"),
    ("MANAGE_IPSEC_TUNNELS", "Manage IPsec tunnels.", "管理 IPsec 隧道", "管理 IPsec 隧道。"),
    ("MANAGE_MEDIA", "Manage media.", "管理媒体", "管理设备上的媒体内容。"),
    ("MEDIA_ROUTING_CONTROL", "Control media routing.", "控制媒体路由", "控制媒体输出路由。"),
    ("RANGING", "Use ranging (distance measurement).", "测距", "使用测距功能（距离测量）。"),
    ("RAPID_CLEAR_NOTIFICATIONS_BY_LISTENER", "Rapidly clear notifications via listener.", "快速清除通知", "通过通知监听器快速清除通知。"),
    ("READ_HEART_RATE", "Read heart rate data.", "读取心率", "读取心率数据。"),
    ("READ_MEDIA_VISUAL_USER_SELECTED", "Read user-selected photos and videos.", "读取用户选择的媒体", "读取用户自行选择的照片和视频。"),
    ("READ_OXYGEN_SATURATION", "Read blood oxygen saturation.", "读取血氧", "读取血氧饱和度数据。"),
    ("READ_SKIN_TEMPERATURE", "Read skin temperature.", "读取皮肤温度", "读取皮肤温度数据。"),
    ("READ_SYSTEM_GRAMMATICAL_GENDER", "Read system grammatical gender setting.", "读取语法性别设置", "读取系统语法性别设置。"),
    ("READ_WRITE_HEALTH_DATA", "Read and write health data.", "读写健康数据", "读取和写入健康数据。"),
    ("RECEIVE_AMBIENT_TRIGGER_AUDIO", "Receive ambient trigger audio.", "环境触发音频", "接收环境触发音频。"),
    ("RECEIVE_EXPLICIT_USER_INTERACTION_AUDIO", "Receive explicit user interaction audio.", "用户交互音频", "接收用户显式交互的音频。"),
    ("RECEIVE_SANDBOX_TRIGGER_AUDIO", "Receive sandbox trigger audio.", "沙箱触发音频", "接收沙箱触发音频。"),
    ("RECEIVE_SENSITIVE_NOTIFICATIONS", "Receive sensitive notifications.", "接收敏感通知", "接收敏感内容的通知。"),
    ("RECORD_AUDIO_SANDBOXED", "Record audio in sandboxed mode.", "录制音频（沙箱）", "以沙箱模式录制音频。"),
    ("RECORD_INCOMING_PHONE_AUDIO", "Record incoming phone call audio.", "录制来电音频", "录制来电通话的音频。"),
    ("RUN_USER_INITIATED_JOBS", "Run user-initiated jobs.", "用户发起的任务", "运行由用户发起的后台任务。"),
    ("SCENE_UNDERSTANDING_COARSE", "Coarse scene understanding.", "粗略场景理解", "获取粗略的场景理解数据。"),
    ("SCENE_UNDERSTANDING_FINE", "Fine scene understanding.", "精确场景理解", "获取精确的场景理解数据。"),
    ("SYSTEM_EXEMPT_FROM_DISMISSIBLE_NOTIFICATIONS", "Exempt from dismissible notification restrictions.", "豁免通知关闭限制", "豁免通知可被关闭的限制。"),
    ("SYSTEM_EXEMPT_FROM_HIBERNATION", "Exempt from hibernation.", "豁免休眠", "豁免系统休眠限制。"),
    ("SYSTEM_EXEMPT_FROM_SUSPENSION", "Exempt from suspension.", "豁免挂起", "豁免系统挂起限制。"),
    ("UNARCHIVAL_CONFIRMATION", "Confirm app unarchival.", "确认恢复归档应用"),
    ("USE_FULL_SCREEN_INTENT", "Use full-screen intents.", "全屏通知"),
    ("WRITE_SYSTEM_PREFERENCES", "Write system preferences.", "写入系统偏好"),
]

def insert_into_array(xml, array_name, items):
    # 在指定 string-array 的 </string-array> 前插入 items
    idx = xml.find(f'<string-array name="{array_name}">')
    if idx < 0:
        raise RuntimeError(f"{array_name} not found")
    end = xml.find("</string-array>", idx)
    block = "".join(f"    <item>{x}</item>\n" for x in items)
    return xml[:end] + block + xml[end:]

en = os.path.join(ROOT, "..", "..", "app", "src", "main", "res", "values", "perm_descs.xml")
zh = os.path.join(ROOT, "..", "..", "app", "src", "main", "res", "values-zh-rCN", "perm_descs.xml")

for path in (en, zh):
    xml = open(path, encoding="utf-8").read()
    xml = insert_into_array(xml, "app_op_desc_names", [n for n, *_ in EXTRA])
    if "values-zh-rCN" in path:
        # 中文版说明优先使用中文说明字段（第 4 字段），否则用英文说明
        xml = insert_into_array(xml, "app_op_descs", [t[3] if len(t) > 3 else t[1] for t in EXTRA])
    else:
        xml = insert_into_array(xml, "app_op_descs", [d for _, d, *_ in EXTRA])
    if "values-zh-rCN" in path:
        xml = insert_into_array(xml, "app_op_desc_labels", [l for _, _, l, *_ in EXTRA])
    else:
        xml = insert_into_array(xml, "app_op_desc_labels", [n for n, *_ in EXTRA])
    open(path, "w", encoding="utf-8").write(xml)
    print(f"updated: {path}")

print("完成")
