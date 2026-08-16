@Suppress("UnstableApiUsage")
dependencyResolutionManagement {
  repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)

  repositories {
    // 同根目录 settings.gradle.kts：aliyun (public/google/gradle-plugin) 国内最快(31-240ms) → 放第一梯队
    mavenLocal()
    maven { url = uri("https://maven.aliyun.com/repository/public") }
    maven { url = uri("https://maven.aliyun.com/repository/google") }
    maven { url = uri("https://maven.aliyun.com/repository/gradle-plugin") }
    mavenCentral()
    gradlePluginPortal()
    maven { setUrl("https://jitpack.io") }
    google()
  }

  versionCatalogs { create("libs") { from(files("../gradle/libs.versions.toml")) } }
}
