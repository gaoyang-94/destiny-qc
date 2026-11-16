#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""闭环守门员：生成报告 → Kane 浏览器验收 → 失败则把 verdict 喂给修复 agent → 复验（≤3 轮）。
用法:
  python3 qc_loop.py                 # 正常一轮
  python3 qc_loop.py --demo-seed-defect   # 演示：先埋缺陷，看 Kane 抓到、agent 修复、复验转绿
"""
import argparse
import json
import re
import subprocess
import sys
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import requests

BASE = Path(__file__).parent
OUT = BASE / 'out'
PREVIEW_PORT = 8610
MAX_ROUNDS = 3


def start_server():
    OUT.mkdir(exist_ok=True)
    handler = partial(SimpleHTTPRequestHandler, directory=str(OUT))
    srv = ThreadingHTTPServer(('127.0.0.1', PREVIEW_PORT), handler)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def log(msg):
    print(f'[qc] {msg}', flush=True)


def kane_verify(preview_url: str) -> dict:
    """跑 Kane 报告验收用例，返回 run_end 解析结果。"""
    cmd = [
        'kane-cli', 'testmd', 'run', str(BASE / 'tests' / 'report_preview_test.md'),
        '--headless', '--timeout', '420', '--local',
        '--variables', json.dumps({'preview_url': {'value': preview_url}}),
    ]
    log('Kane 验收中（真实浏览器）…')
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=460, cwd=BASE)
    text = r.stdout + r.stderr
    run_end = None
    for line in text.splitlines():
        line = line.strip()
        if line.startswith('{') and '"type":"run_end"' in line.replace(' ', ''):
            run_end = json.loads(line)
    if run_end is None:
        return {'status': 'error', 'raw_tail': text[-1500:]}
    verdict = run_end.get('verdict') or {}
    return {
        'status': run_end.get('status'),
        'root_cause': verdict.get('root_cause') or run_end.get('reason') or '',
        'suggestion': verdict.get('suggestion') or '',
        'one_liner': verdict.get('one_liner') or run_end.get('one_liner', ''),
        'test_url': run_end.get('test_url', ''),
        'evidence': run_end.get('session_dir', ''),
        'credits': run_end.get('credits_consumed'),
    }


def agent_fix(root_cause: str, html_path: Path) -> None:
    """修复 agent：读 Kane 的失败归因，直接改写报告 HTML。"""
    html = html_path.read_text(encoding='utf-8')
    chart = json.loads((BASE / 'sample_chart.json').read_text(encoding='utf-8'))
    lunar = chart.get('农历', {})
    pan = chart.get('盘', {})
    facts = {
        '四柱': lunar.get('四柱', ''),
        '公历': chart.get('输入', {}).get('钟表时间', ''),
        '农历': lunar.get('农历日期', ''),
        '五行局': pan.get('五行局', ''),
        '命主身主': f"命主{pan.get('命主', '')}·身主{pan.get('身主', '')}",
    }
    prompt = f'''你是报告修复员。一份紫微命盘报告的 HTML 预览页未通过自动验收。

【验收失败归因（来自 Kane CLI verdict)】
{root_cause}

【报告可用的事实字段（JSON)】
{json.dumps(facts, ensure_ascii=False)}

【当前 HTML】
{html[:8000]}

请修复这份 HTML 使其满足验收标准：信息条必须含干支四柱/公历生日/农历生日/五行局/命主身主五项；
不得出现「判词/加注/此节可验/此节可回对/生成于/AI 生成」；正文八个章节齐全；页脚只保留
「本报告仅作传统文化研究与自我认知参考」。保留原有 <style> 不变。
只输出完整修复后的 HTML，不要任何解释。'''
    env = {}
    for line in Path('/root/myself/AI/AI写电子书/重生1988/.env').read_text().splitlines():
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            env[k.strip()] = v.strip()
    r = requests.post(
        f"{env.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')}/chat/completions",
        headers={'Authorization': f"Bearer {env['DEEPSEEK_API_KEY']}"},
        json={'model': env.get('DEEPSEEK_MODEL', 'deepseek-chat'), 'max_tokens': 8000,
              'temperature': 0.2, 'messages': [{'role': 'user', 'content': prompt}]},
        timeout=300)
    r.raise_for_status()
    fixed = r.json()['choices'][0]['message']['content']
    m = re.search(r'<!DOCTYPE html.*</html>', fixed, re.S | re.I)
    if m:
        fixed = m.group(0)
    html_path.write_text(fixed, encoding='utf-8')
    log('修复 agent 已改写报告 HTML')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--demo-seed-defect', action='store_true')
    args = ap.parse_args()

    log('第 0 步：生成报告')
    cmd = [sys.executable, str(BASE / 'report_gen.py')]
    if args.demo_seed_defect:
        cmd.append('--defect')
        log('（演示模式：故意埋入「信息条缺四柱」缺陷）')
    html_path = Path(subprocess.check_output(cmd, text=True).strip())

    srv = start_server()
    preview_url = f'http://127.0.0.1:{PREVIEW_PORT}/report.html'
    log(f'预览页：{preview_url}')

    try:
        for rnd in range(1, MAX_ROUNDS + 1):
            log(f'—— 第 {rnd} 轮验收 ——')
            res = kane_verify(preview_url)
            if res['status'] == 'passed':
                log('✅ 验收通过，报告放行')
                if res.get('test_url'):
                    log(f"证据：{res['test_url']}")
                return 0
            if res['status'] == 'error':
                log('⚠️ Kane 调用异常'); print(res.get('raw_tail', '')[-800:])
                return 2
            log(f"❌ 验收未过：{res.get('one_liner') or res['root_cause'][:120]}")
            if rnd == MAX_ROUNDS:
                log('已达最大修复轮次，升级人工处理')
                return 1
            agent_fix(res['root_cause'] + '\n' + res.get('suggestion', ''), html_path)
        return 1
    finally:
        srv.shutdown()


if __name__ == '__main__':
    sys.exit(main())
