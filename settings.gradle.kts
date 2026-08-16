@Suppress("UnstableApiUsage")
dependencyResolutionManagement {
  repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)

  repositories {
    // ⚠️ 2026-08-16 真实网络延迟实测（强制 IPv4）：
    //   [1] aliyun public  ............ 31ms  ✅ (maven.aliyun.com/repository/public = 国内合流，kotlin+androidx+第三方 全命中)
    //   [2] aliyun google  ............ 240ms ✅ (国内 AGP 8.12.2 / AndroidX appcompat 专门镜像)
    //   [3] aliyun gradle-plugin ..... 200ms ✅ (国内 gradle 插件镜像：spotless/versions)
    //   [4] mavenCentral ............. 326ms ✅ (repo.maven.apache.org = 海外 central，纯 java 库兜底)
    //   [5] plugins.gradle.org ....... 1339ms✅ (海外 gradlePluginPortal 兜底)
    //   [6] jitpack.io ............... (libadb-android)
    //   [7] google() (dl.google.com) . 506ms ✅ (海外直连，最后兜底)
    //
    // 沙盒网络出口偶发 IP 段 timeout（波动期 5-15m）→ 配合 gradle.properties 短超时+重试：
    //   systemProp.org.gradle.internal.http.connectionTimeout=10000
    //   systemProp.org.gradle.internal.http.socketTimeout=60000
    mavenLocal()
    maven { url = uri("https://maven.aliyun.com/repository/public") }
    maven { url = uri("https://maven.aliyun.com/repository/google") }
    maven { url = uri("https://maven.aliyun.com/repository/gradle-plugin") }
    mavenCentral()
    gradlePluginPortal()
    maven { url = uri("https://jitpack.io") }
    google()
  }
}

include(":hidden_apis")

include(":priv_library")

include(":priv_daemon")

include(":app")
