---
mode: testing
---

# 命盘生成全流程

## 打开排盘首页
Open http://127.0.0.1:8600/ .
Verify the 「立即起盘」 button is visible.

## 进入排盘表单
Click 「立即起盘」.
Verify the birth-data form appears with fields for birth date, birth time, gender and birthplace.

## 填写生辰并起盘
Fill in birth date as 1990-01-01, birth time as 12:30, select gender 男, set birthplace to 北京.
Submit the form.

## 验证十二宫格
Wait for the chart to render.
Verify a 12-palace grid (十二宫) is displayed, with at least 12 palace cells.

## 验证中心格四柱
Verify the center cell of the chart contains a line of four two-character pillars (干支四柱), i.e. four space-separated pairs such as 癸未 丁巳 壬午 己酉.

## 验证中心格五行局
Verify the center cell shows a 五行局 label such as 木三局 / 水二局 / 土五局.

## 验证中心格命主与身主是独立两行
Verify the center cell has a row whose label is exactly 命主 followed by a star name, and a separate row whose label is exactly 身主 followed by a star name.
Do not accept 命宫 or 身宫 rows as substitutes for 命主 or 身主.
