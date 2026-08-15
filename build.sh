#!/bin/sh
# PMX 汉化版一键构建脚本（本机 Ubuntu 环境专用）
# 用法：cd PermissionManagerX && sh build.sh
cd "$(dirname "$0")" || exit 1

# 1. 构建环境适配（临时生效，构建后自动还原）
grep -q aapt2FromMavenOverride gradle.properties \
  || echo 'android.aapt2FromMavenOverride=/opt/android-sdk/build-tools/37.0.0/aapt2' >> gradle.properties
sed -i 's#prebuilt/linux-x86_64#prebuilt/linux-aarch64#' native/build_native.sh

# 2. 构建
/root/gradle-9.0.0/bin/gradle :app:spotlessApply :app:assembleRelease --no-daemon \
  || { git checkout -- gradle.properties native/build_native.sh; exit 1; }

# 3. 签名（固定签名，覆盖安装不丢数据）
/opt/android-sdk/build-tools/37.0.0/apksigner sign \
  --ks /root/pmx-zh-release.jks --ks-key-alias pmxzh \
  --ks-pass pass:pmxzh123 --key-pass pass:pmxzh123 \
  --out ../PMX-汉化版-release-signed.apk \
  app/build/outputs/apk/release/app-release-unsigned.apk

# 4. 复制到下载目录
cp ../PMX-汉化版-release-signed.apk /storage/emulated/0/Download/

# 5. 还原构建环境临时改动
git checkout -- gradle.properties native/build_native.sh

echo "完成：/sdcard/Download/PMX-汉化版-release-signed.apk"