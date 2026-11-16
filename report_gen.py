#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""报告生成 agent：从命盘 JSON 生成报告 HTML 预览页。
--defect 用于演示：故意漏掉信息条的四柱（真实踩过的坑），让 Kane 抓。
"""
import argparse
import json
from pathlib import Path

BASE = Path(__file__).parent
OUT = BASE / 'out'
OUT.mkdir(exist_ok=True)

BODY = '''一、性格特点
这个盘命宫坐申，廉贞入庙，主星气正。为人外柔内刚，心里有杆秤，认定的事九头牛拉不回。聪明，学东西快，但想得多做得缓，容易内耗。身宫落迁移，注定闲不住，心思一直在"外面"。

二、事业方向
官禄宫武曲天府同坐，又带禄存，是典型的"财权双美"。适合跟钱、账、制度打交道的行当：财政、税务、审计、金融监管、国企财务岗都合。不宜纯技术岗，也不宜自己当老板冲一线，做体系内的实权岗位最稳。

三、外出与发展
身宫落迁移，贪狼化忌同宫。外出是命里带的，早年在出生地附近憋屈，走出去才顺。但化忌在迁移，头几年在外多磕绊，租房、通勤、人际都有学费要交。熬过前三年，路越走越宽。

四、感情婚姻
夫妻宫七杀带火星，另一半性子急、能干、直来直去，不是温柔款。正缘在外地，认识方式偏"路上"：出差、调动、旅途、新圈子。宜迟不宜早，三十前后定最稳。

五、健康
木三局壬水日，注意肝胆和睡眠。思虑重，容易睡不着、睡不实。少熬夜，少吃宵夜，比什么药都强。

六、过去几件事
2017 年前后与家里长辈关系疏远了一层，或家中有变动。2018 年换过环境，住校或搬家。2024 年有了第一份正式收入，但那年经手他人的钱有过损耗。

七、未来十年与近三年
2026 年文昌化科，利考试、签约、露脸的事。2027 年天机化科，思路大开，但巨门化忌，嘴上要严，合同要细看。2028 年起整体上一个台阶。三十三岁后进天梁大限，日子由紧转松。

八、三条建议
第一，钱上三不：不担保、不借贷、不合伙糊涂账。第二，买房别赶早，三十三后再看。第三，每天留半小时给脑子放空，这个盘最大的损耗是神经过劳。
'''


def build(chart: dict, defect: bool = False) -> str:
    lunar = chart.get('农历', {})
    pan = chart.get('盘', {})
    pillars = lunar.get('四柱', '')
    info_items = []
    if not defect:
        info_items.append(f'四柱：{pillars}')
    info_items += [
        f'公历：{chart.get("输入", {}).get("钟表时间", "")}（广东韶关）',
        f'农历：{lunar.get("农历日期", "")}',
        f'五行局：{pan.get("五行局", "")}',
        f'命主{pan.get("命主", "")}·身主{pan.get("身主", "")}',
    ]
    info_html = '　'.join(info_items)
    body_html = '\n'.join(
        f'<h2>{l.split(chr(10))[0]}</h2>' if False else f'<p>{line}</p>'
        for line in BODY.strip().split('\n') if line.strip()
    )
    # 章节标题渲染
    parts = []
    for block in BODY.strip().split('\n\n'):
        lines = block.strip().split('\n')
        parts.append(f'<h2>{lines[0]}</h2>')
        for line in lines[1:]:
            parts.append(f'<p>{line}</p>')
    body_html = '\n'.join(parts)

    return f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>命盘报告 预览</title>
<style>
body {{ background: #fff; color: #111; max-width: 720px; margin: 40px auto; padding: 0 22px;
       font-family: "Songti SC", serif; font-size: 15.5px; line-height: 2.05; }}
h1 {{ color: #8a1f1f; font-size: 22px; }}
h2 {{ color: #8a1f1f; font-size: 17px; border-bottom: 1px solid #c9a0a0; padding-bottom: 4px; }}
.info {{ font-size: 13.5px; color: #333; border: 1px solid #c9a0a0; padding: 8px 12px; }}
p {{ text-indent: 2em; }}
footer {{ margin-top: 48px; font-size: 12px; color: #777; text-align: center; }}
</style></head><body>
<h1>命盘报告</h1>
<div class="info">{info_html}</div>
{body_html}
<footer>本报告仅作传统文化研究与自我认知参考</footer>
</body></html>'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--chart', default=str(BASE / 'sample_chart.json'))
    ap.add_argument('--defect', action='store_true', help='演示用：故意漏掉四柱')
    ap.add_argument('--html-in', help='直接用已有 HTML（修复轮由 qc_loop 传入）')
    args = ap.parse_args()

    if args.html_in:
        html = Path(args.html_in).read_text(encoding='utf-8')
    else:
        chart = json.loads(Path(args.chart).read_text(encoding='utf-8'))
        html = build(chart, defect=args.defect)
    out = OUT / 'report.html'
    out.write_text(html, encoding='utf-8')
    print(out)


if __name__ == '__main__':
    main()
