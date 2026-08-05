# INSTALL_DESIGN_COMMAND_CENTER.ps1
# 目标：把本包内容合并到 D:\All projects\MINIGAME
# 路径有空格，必须使用英文双引号。

$Target = "D:\All projects\MINIGAME"
Write-Host "目标目录: $Target"
if (!(Test-Path $Target)) {
    New-Item -ItemType Directory -Path $Target -Force | Out-Null
    Write-Host "已创建目标目录"
}
Write-Host "请将本包内 MINIGAME 文件夹中的内容复制/合并到：$Target"
Write-Host "如果已经解压到该路径，可忽略此脚本。"
