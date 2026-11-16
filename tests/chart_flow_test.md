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

## 验证命盘渲染
Wait for the chart to render.
Verify a 12-palace grid (十二宫) is displayed.
Verify the center cell shows 四柱 (four pillars), 五行局, 命主 and 身主.
