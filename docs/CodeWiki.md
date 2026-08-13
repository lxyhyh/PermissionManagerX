# PermissionManagerX 代码 Wiki

> 本 Wiki 基于对仓库源码的分析生成，用于帮助开发者快速理解 `PermissionManagerX`（PMX）的整体架构、模块划分、关键类职责、依赖关系与运行方式。
> 项目定位：Android 上的"扩展权限管理器"，用于查看和设置 **Manifest 权限（清单权限）** 与 **AppOps（应用操作）**。

---

## 目录

1. [项目概览](#1-项目概览)
2. [整体架构](#2-整体架构)
3. [模块划分与职责](#3-模块划分与职责)
4. [关键类与函数说明](#4-关键类与函数说明)
5. [依赖关系](#5-依赖关系)
6. [项目运行方式](#6-项目运行方式)
7. [附录：关键设计机制](#7-附录关键设计机制)

---

## 1. 项目概览

| 项 | 说明 |
|---|---|
| **项目名称** | PermissionManagerX（PMX） |
| **包名 (applicationId)** | `com.mirfatif.permissionmanagerx` |
| **定位** | 查看/授予/撤销 Manifest 权限；查看/设置 AppOps；权限引用状态备份与恢复 |
| **版本** | v1.30（versionCode 130） |
| **SDK** | compileSdk/targetSdk 36，minSdk 24（Android 7），NDK 28.2 |
| **语言** | 主要 Java，少量 Kotlin（`MidReleaseBrokenAPIsDelegate.kt`、`CrashReportActivity.kt`） |
| **构建** | Gradle 9.0 + Kotlin DSL（`build.gradle.kts`）+ 自定义 buildSrc 约定插件 |
| **权限来源** | 设备 **root** 或 **ADB over network**，通过提权守护进程修改系统权限 |
| **开源协议** | AGPL-3.0 |

**核心能力**：对每个已安装 App，单屏查看并管理其 Manifest 权限与 AppOps 权限，并可设置"引用状态（reference）"用于快速备份/恢复，左侧彩色指示条便于快速审查。

### 关键目录结构

```
.
├── app/                主应用模块（UI、解析、守护进程客户端、服务）
├── priv_library/       提权任务库（共享 AIDL 接口、隐藏 API 封装、绑定对象）
├── priv_daemon/        提权守护进程（在 root/ADB 环境中运行的服务器）
├── hidden_apis/        隐藏 Android API 桩（编译期使用，覆盖系统类）
├── native/             原生 C 代码（pmxe 可执行 + pmxd 共享库，JNI）
├── buildSrc/           Gradle 约定插件（复用构建配置）
├── help/               多语言帮助站点（静态 HTML）
├── fastlane/           应用商店元数据
└── docs/               项目文档（含本 Wiki）
```

---

## 2. 整体架构

PMX 采用 **客户端-守护进程（Client–Daemon）** 架构，核心难点在于：普通 App 无法直接修改系统级权限，因此需要借助 root 或 ADB 运行一个**提权守护进程**，由守护进程通过**隐藏系统 API** 完成真正的权限读写，App 再通过 **Binder/AIDL** 与之通信。

```
┌───────────────────────────── 普通 App 进程 (app模块) ────────────────────────────┐
│  UI 层：MainActivity / PackageActivity / PermListActivity / Settings ...        │
│     │                                                                           │
│  解析层：PackageParser / Package / Permission / AppOpsParser（数据模型+LiveData） │
│     │                                                                           │
│  客户端：DaemonHandler / DaemonIface / NativeDaemon / AdbConnManager            │
└───────────────┬─────────────────────────────────────────────────────────────────┘
                │ ① 启动：root(su) 或 ADB shell 拉起原生二进制
                │ ② 握手：TCP 回环 + UUID 口令
                │ ③ 通信：Binder + AIDL（IPrivTasks）经 DaemonRcvSvc 转发
                ▼
┌───────────── 提权守护进程 (priv_daemon 模块, 运行于 root/ADB 环境) ──────────────┐
│  Main → PrivDaemon → Server(回环socket监听) + Callbacks(回调/日志)                │
│  核心：IPrivTasksImpl（实现 IPrivTasks AIDL 接口）                                │
│  AppPrivTasks（枚举AppOps、权限映射） + PrivsStatusReader（权限状态）             │
│  Jni（load libpmxd.so: 重定向stderr / 正则匹配）                                  │
└───────────────┬─────────────────────────────────────────────────────────────────┘
                ▼ 通过隐藏系统 API
┌───────────── Android 系统服务（IAppOpsService / IPackageManager / IPermissionManager ...）─┐
```

### 数据流（一次权限修改）

1. 用户在 UI 修改权限（如勾选 AppOp）。
2. `Permission`/`Package` 数据层调用 `DaemonIface`。
3. `DaemonIface` 通过 `IPrivTasks`（Binder）调用守护进程。
4. 守护进程 `IPrivTasksImpl` 调用 `HiddenAPIs` → `SysSvcFactory` 获取系统服务 Binder → `setMode()/setAppOpMode()`。
5. 结果通过回调返回，UI 刷新（`updatePkgList()`）。

---

## 3. 模块划分与职责

### 3.1 `app` 模块（主应用）

按包组织，职责如下：

| 包 | 职责 |
|---|---|
| `app/` | 全局 `App` 类：初始化上下文、全局异常捕获、语言设置 |
| `main/` | 主界面（应用列表）：`MainActivity`、`PackageAdapter`、启动守护进程 UI、ADB 连接对话框、反馈等 |
| `pkg/` | 单应用页（权限列表）：`PackageActivity`、`PermissionAdapter`、权限详情/长按对话框 |
| `base/` | 基础组件：`BaseActivity`（主题/夜间模式）、通用对话框、列表适配器基类 |
| `prefs/` | 设置：`MySettings`（SharedPreferences 封装）、`AppUpdate`、排除过滤器 `ExcFiltersData`、设置 Fragments |
| `parser/` | 数据解析层：`PackageParser`、`Package`、`Permission`、`AppOpsParser`、`PermGroupsMapping`、`permsdb`（Room 数据库） |
| `privs/` | 守护进程客户端：`DaemonHandler`、`DaemonIface`、`DaemonStarter`、`NativeDaemon`、`AdbConnManager` |
| `svc/` | 前台服务：`DaemonRcvSvc`（接收 Binder）、`AdbConnectSvc`（ADB 连接）、`LogcatSvc`（日志收集） |
| `util/` | 工具：日志、通知、UI、语言、用户、后台任务（`Live*` 系列） |
| `fwk/` | **"M" 包装器**：被 AndroidManifest 注册的 Activity/Service（`*M` 类），委托给同包真实实现 |
| `profile/` | 权限配置备份/恢复（`PermProfileBackupRestore`，当前为占位实现） |
| `zhx/` | **汉化版扩展模块**：`i18n`（权限中文说明）、`design`（外观偏好）、`permview`（权限视图页） |

### 3.2 `priv_library` 模块（提权任务库）

被 `app` 与 `priv_daemon` 共享的库，包含：

| 包 | 职责 |
|---|---|
| `iface/` | **`IPrivTasks`**：手写 AIDL 风格接口 + `Stub`/`Proxy`，客户端与守护进程的通信契约 |
| `hiddenapis/` | **`HiddenAPIs`**（隐藏 API 封装）、**`SysSvcFactory`**（系统服务 Binder 工厂）、`MidReleaseBrokenAPIsDelegate.kt`（版本差异兜底） |
| `bind/` | Binder 传输对象：`AppOpsLists`、`MyPackageOps`、`PrivsStatus`、`DaemonState`、`PermFixedFlags`、`StrIntMap` |
| `util/` | 日志（`MyLog`/`LogUtil`）、锁、非阻塞读、通用工具 |
| `err/` | 异常：`ContainerException`、`HiddenAPIsException` |
| 根 | `AppPrivTasks`（AppOps 枚举与权限映射核心）、`Constants`、`HiddenSdkIntConstants`、`HiddenSdkStringConstants`、`PrivTasksError`（错误码） |
| `aidl/` | AIDL 回调：`ILogCallback`、`IPrivTasksCallback` |

### 3.3 `priv_daemon` 模块（提权守护进程）

运行于 root/ADB 环境的服务器进程：

| 类 | 职责 |
|---|---|
| `Main` | `main()` 入口，构造并启动 `PrivDaemon` |
| `PrivDaemon` | 启动时清理同名残留进程，校验参数（`com.mirfatif.*` + UUID），调用 `Callbacks.talkToApp` 上报，进入 Looper |
| `Server` | 在 `127.0.0.1` 开启回环 `ServerSocket`，监听 App 的 UUID 口令连接 |
| `Callbacks` | 承载 `IPrivTasks` 实例、向 App 发送 Binder Intent、崩溃日志、调试日志回调、退出管理 |
| `IPrivTasksImpl` | **`IPrivTasks.Stub` 实现**：真正执行 AppOps/Permission 操作 |
| `PrivsStatusReader` | 读取守护进程自身权限状态（`checkPermission` 一批系统权限） |
| `Jni` | 加载 `libpmxd.so`，JNI 方法（重定向 stderr、正则匹配） |
| `DaemonLog` | 守护进程日志 |

### 3.4 `hidden_apis` 模块

- 提供 Android 隐藏 framework 类的**桩实现**（`android/os/ServiceManager`、`android/AppOpsManager`、`com/android/internal/app/IAppOpsService` 等）。
- 仅用于**编译期**：让 `priv_library` 能引用隐藏 API。通过 `priv_library/build.gradle.kts` 中的 `createTasksForHiddenAPIs()`，把生成的 `classes.jar` 前置到编译 classpath，**覆盖** Android SDK 同名类。
- 运行时实际走系统真实实现（`compileOnly`）。

### 3.5 `native` 模块（原生 C）

| 文件 | 说明 |
|---|---|
| `pmxe.c` | 编译为**可执行文件** `libpmxe.so`（App 的 `nativeLibraryDir` 下），作为守护进程二进制，由 root/ADB 拉起 |
| `pmxd.c` | 编译为**共享库** `libpmxd.so`，通过 JNI 被 `priv_daemon.Jni` 加载 |
| `build_native.sh` | 用 NDK 交叉编译 4 种 ABI |

`pmxd.c` 提供的 JNI 函数：
- `Java_com_mirfatif_privdaemon_Jni_sendStdErr(int port)`：把守护进程 stderr 重定向到 App 的回环 socket。
- `Java_com_mirfatif_privdaemon_Jni_closeStdErr()`：把 stderr 重定向到 `/dev/null`。
- `Java_com_mirfatif_privdaemon_Jni_matches(...)`：POSIX 正则匹配。

> 注：仓库包含 `libcap` 子模块（`native/libcap`），用于生成 `cap_names.h`，供 pmxe 编译时链接 Linux capabilities 相关代码。

---

## 4. 关键类与函数说明

### 4.1 通信契约：`IPrivTasks`（priv_library/iface）

手写 Binder 接口（非系统 AIDL 生成），关键方法：

| 方法 | 作用 |
|---|---|
| `hello(IBinder cb, String crashLogFile)` | 守护进程向 App 上报运行状态（PID/UID/SELinux 上下文/端口） |
| `sendStdErr(int port, String jniLibPath)` | 让守护进程加载 JNI 库并重定向 stderr |
| `setExitOnAppDeath(boolean)` | 设置 App 退出时守护进程是否随之退出 |
| `getPrivsStatus()` | 获取守护进程权限状态 |
| `setDebug(IBinder logCb)` | 开启/关闭日志回调 |
| `dumpHeap(dir)` | 转储守护进程堆（hprof） |
| `grantAppPrivileges(pkg, uid)` | 授予 App 运行所需特权（后台运行、免电救、GET_APP_OPS_STATS 等） |
| `getAppOpsLists()` | 获取全部 AppOps 名称/模式/映射 |
| `getPermFixedFlags()` | 获取权限固定标志 |
| `getPackagesForUid(uid)` | 按 UID 查包名 |
| `getOpsForPackage(uid, pkg, ops[])` | 查指定包/UID 的 AppOps |
| `getPermFlags(...)` / `setPermState(...)` | 读写 Manifest 权限标志 |
| `setAppOpMode(uid, pkg, op, mode)` | **设置 AppOp 模式（核心写操作）** |
| `resetAppOps(userId, pkg)` | 重置 AppOps |
| `setPkgState(enable, pkg, userId)` | 启用/停用应用 |
| `openAppInfo(pkg, userId)` | 打开系统应用信息页 |
| `stopDaemon()` | 停止守护进程 |

### 4.2 守护进程服务端：`IPrivTasksImpl`（priv_daemon）

实现 `IPrivTasks.Stub`，是真正的执行端：
- `setAppOpMode`：`pkgName==null` 走 `setAppOpUidMode`，否则 `setAppOpMode`（均通过 `HiddenAPIs`→`IAppOpsService`）。
- `setPermState`：`grant`→`grantRuntimePermission`，`revoke`→`revokeRuntimePermission`。
- `grantAppPrivileges`：设置 `OP_RUN_IN_BACKGROUND`/`OP_RUN_ANY_IN_BACKGROUND` 为 ALLOWED、加电源白名单、授予 `GET_APP_OPS_STATS`（Android 13+ 还授 `POST_NOTIFICATIONS`）。

### 4.3 客户端：`DaemonHandler` / `DaemonIface` / `NativeDaemon`（app/privs）

- **`DaemonHandler`**：单例（enum `INS`），守护进程生命周期管理。`startDaemon()` 依次尝试 root→ADB，`isDaemonAlive()` 轮询状态，接收 `hello` 握手并对接 `IPrivTasks`。
- **`DaemonIface`**：对 `IPrivTasks` 的上层封装，供解析层调用，内部检查 `DaemonHandler.INS.isDaemonAlive()`。
- **`NativeDaemon`**：enum `INS_R(root)` / `INS_A(adb)`。`startRootDaemon()` 用 `su` 拉起 `libpmxe.so`；`startAdbDaemon()` 通过 ADB shell 启动；通过回环 socket + UUID 口令通信。
- **`AdbConnManager`**：继承 `AbsAdbConnectionManager`（libadb-android），生成/读取 X509 证书与私钥，建立加密 ADB 连接。

### 4.4 隐藏 API 封装：`HiddenAPIs` / `SysSvcFactory`（priv_library/hiddenapis）

- **`HiddenAPIs`**（enum `INS`）：静态方法包装 `AppOpsManager`（`opToName`、`modeToName`、`permToOpCode`、`opToDefaultMode` 等）+ 实例方法通过 `SysSvcFactory` 调系统服务（`setAppOpMode`、`getOpsForPkg`、`resetAllModes`、`grantRuntimePermission`、`addPowerSaveWhitelistApp` 等）。
- **`SysSvcFactory`**（enum `INS`）：懒加载、缓存下列系统服务 Binder：
  - `getIAppOpsSvc()` → `ServiceManager.getService("appops")`
  - `getIPkgMgr()` → `"package"`
  - `getIPermMgr()` → `"permissionmgr"`（Android 11+）
  - `getIActMgr()` → `"activity"`
  - `getIDevIdleController()` → `"deviceidle"`

### 4.5 数据解析层（app/parser）

- **`PackageParser`**（enum `INS`）：单例，核心数据源。维护 `LiveEvent`（`mPkgListLive`、`mProgMax`、`mProgNow`、`mListCompleted`、`mChangedPkg`）。`updatePkgList()` 触发后台重建应用列表；`updatePkgListWithResult()` 同步返回；`buildRequiredData()` 构建 AppOps/权限映射；`isPkgUpdated()` 增量判断。
- **`Package`**：单个应用的数据模型（标签、包名、UID、系统/框架应用标志、权限列表、权限计数、引用状态）。
- **`Permission`**：单个权限数据模型（保护级别、授予状态、AppOp 模式/访问时间、固定标志、引用状态）。
- **`AppOpsParser`**：AppOps 解析与读写封装（`canReadAppOps()` 判断可读性）。
- **`permsdb`**：Room 数据库（`PermsDb`/`PermissionDao`/`PermissionEntity`/`PermissionDatabase`），持久化权限数据。

### 4.6 设置与持久化：`MySettings`（app/prefs）

- enum 单例，封装 `SharedPreferences` 读写。
- 两类偏好存储：默认（可备份）与 `_no_backup_prefs`（键名以 `_enc` 结尾，如更新时间戳）。
- 提供大量语义化方法：`isDebug()`、`getThemeColorValue()`、`getDarkThemeMode()`、`shouldUseCardStyle()`、`getListDensity()`、`shouldRestartDaemon()`、`getDaemonPort()`、`isRootEnabled()`/`isAdbEnabled()` 等。
- 通过 `mPrefsWatcher`（LiveEvent）通知 UI 偏好变化。

### 4.7 外观与汉化扩展（app/zhx）

- **`UiPrefUtils`**：外观设置唯一读取入口（卡片背景、圆角、列表密度、水波纹、引用指示条、AppOp chip、大标题）。
- **`PermDescProvider`**：权限中文名+说明的翻译入口（系统本地化名 → 内置映射 → 规则翻译三级兜底）。
- **`permview`**：`PermListActivity`（按权限聚合列表）、`PermAppsActivity`（应用列表）、`PermListView`（数据层）。

### 4.8 "M" 包装器（app/fwk）

AndroidManifest 里注册的是 `*M` 类（如 `MainActivityM`、`DaemonRcvSvcM`），它们持有同包真实实现对象（如 `MainActivity mA`），在生命周期回调中**委托**给真实类。这样让核心逻辑类不直接继承 Android 组件，便于解耦与测试。

---

## 5. 依赖关系

### 5.1 模块依赖

```
app ──implementation──► priv_library
app ──runtimeOnly────► priv_daemon
priv_daemon ──implementation──► priv_library
priv_library ──compileOnly──► hidden_apis
```

### 5.2 模块内依赖（核心调用链）

- **UI 启动守护进程**：`MainActivity` → `DaemonStartProg` → `DaemonHandler` → `NativeDaemon`（root/ADB）→ 拉起 `libpmxe.so`。
- **数据传输**：`MainActivity` → `PackageParser`（LiveData）→ `Package`/`Permission` → `DaemonIface` → `DaemonHandler` → `IPrivTasks`(Binder) → `IPrivTasksImpl` → `HiddenAPIs` → `SysSvcFactory` → 系统服务。
- **服务**：守护进程通过 `Callbacks.fireSvcIntent()` 启动 `DaemonRcvSvcM`（转发 Binder）；`AdbConnectSvcM` 负责 ADB 连接；`LogcatSvcM` 收集日志。
- **数据持久化**：`PackageParser` ↔ `permsdb`（Room）；`MySettings` ↔ SharedPreferences。

### 5.3 第三方库（见 `gradle/libs.versions.toml`）

| 库 | 用途 |
|---|---|
| `libadb-android` | ADB-over-network 客户端（`AdbConnManager`） |
| `sun-security-android` | 生成 X509 证书 |
| `hiddenapibypass`（LSPass） | 绕过 Android 隐藏 API 限制 |
| `androidx-appcompat/recyclerview/preference/browser/room/webkit/security-crypto/swiperefreshlayout` | Jetpack 基础库 |
| `material` | Material 组件（SnackBar/NavigationView/CoordinatorLayout） |
| `guava` | 集合工具 |
| `better-link-movement-method` | TextView 超链接点击 |
| `leakcanary` | 内存泄漏检测（仅 debug） |
| `desugar_jdk_nio` | Java 8+ API 脱糖（NDK/JDK NIO） |

---

## 6. 项目运行方式

### 6.1 环境要求

- Linux 环境（`build.gradle` 会调用原生构建脚本）。
- 已安装 Android SDK（含 **NDK 28.2**）与 JDK 17。
- Git 子模块：`native/libcap`（`git clone --recurse-submodules`）。

### 6.2 构建步骤

```bash
# 1. 克隆（含子模块）
git clone --recurse-submodules https://github.com/mirfatif/PermissionManagerX.git

# 2. 配置 SDK 路径
echo "sdk.dir=/path/to/android-sdk" > local.properties

# 3. 构建 release APK（自动触发原生编译）
./gradlew :app:assembleRelease
```

> 仓库自带 `build.sh`（本机 Ubuntu 专用）：会临时修改 `gradle.properties`（aapt2 路径）与 `build_native.sh`（aarch64），构建后用固定 keystore 签名并复制到下载目录，最后还原临时改动。

### 6.3 运行前提（权限来源）

- **root**：设备已 root，应用内勾选 root 选项，通过 `su` 启动守护进程。
- **ADB over network**：在 PC 上执行 `adb tcpip 5555` 等开启网络 ADB，应用内配置 ADB 主机/端口，`AdbConnManager` 建立加密连接。
- 二者缺一不可，否则无法修改 AppOps/权限。

### 6.4 开发调试

```bash
# 代码格式化（spotless）
./gradlew :app:spotlessApply

# debug 构建
./gradlew :app:assembleDebug

# 依赖版本检查
./gradlew dependencyUpdates
```

---

## 7. 附录：关键设计机制

### 7.1 守护进程识别与安全

- 启动参数必须是 `com.mirfatif.*` + **UUID**（`PrivDaemon.start()` 校验），防止任意进程冒充。
- 通信走 `127.0.0.1` 回环 socket + UUID 口令（`Server.readMessage` 校验 `Constants.CMD_CODE_WORD`）。
- Binder 通过 `DaemonRcvSvcM` 中转，`Callbacks.update()` 用 `linkToDeath` 监听 App 死亡，支持"App 退出后守护进程自动退出"。

### 7.2 隐藏 API 访问

- 编译期：`hidden_apis` 提供桩类，覆盖 SDK 类。
- 运行期：`hiddenapibypass`（LSPass）绕过隐藏 API 限制 + `SysSvcFactory` 通过 `ServiceManager.getService()` 获取系统 Binder。
- `MidReleaseBrokenAPIsDelegate.kt` 处理 Android 中间版本破坏性变更。

### 7.3 双模式 UI（汉化版）

- `Theme.AppCompat.DayNight` + `values-night` 资源覆盖实现浅色/深色。
- 颜色 Token 集中在 `colors.xml`，语义色/品牌色放 `values`，背景/文字 Token 在 `values-night` 提供深色值。
- 夜间模式三档（跟随系统/浅色/深色）由 `BaseActivity.setNightTheme()` 应用。

### 7.4 权限引用状态（Reference）

- 用户可为每个可变更权限设置"引用状态"，用于快速备份/恢复。
- `Package`/`Permission` 均含 `mIsReferenced`/`mReference` 字段，`BackupRestore` 实现备份/恢复，左侧彩色指示条标识是否与引用一致。

---

*本文档基于源码分析自动生成，具体实现细节以实际代码为准。*