#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 destiny-qc 的 3 分钟演示视频：幻灯片 + piper 英文旁白 + ffmpeg 合成。"""
import json
import subprocess
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

EV = Path('/tmp/kane_ev')
OUT = EV / 'video'
OUT.mkdir(exist_ok=True)
W, H = 1280, 720
BG = (14, 17, 22)
RED = (196, 62, 52)
GOLD = (217, 164, 65)
GREY = (168, 176, 190)
WHITE = (240, 242, 246)
GREEN = (76, 175, 116)

FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FR = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FM = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
CJK = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'


def f(path, size):
    return ImageFont.truetype(path, size)


def base():
    im = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 6], fill=RED)
    return im, d


def wrap(d, text, font, width):
    lines, cur = [], ''
    for w in text.split():
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=font) <= width:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


def put(d, xy, text, font, fill, width=None, leading=1.35):
    x, y = xy
    lines = wrap(d, text, font, width) if width else [text]
    for ln in lines:
        d.text((x, y), ln, font=font, fill=fill)
        y += int(font.size * leading)
    return y


def shot(path, box=None, scale=1.0):
    im = Image.open(path).convert('RGB')
    if box:
        im = im.crop(box)
    if scale != 1.0:
        im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
    return im


def paste_right(im, src, top=60, max_w=640, border=True):
    s = src.copy()
    ratio = min(max_w / s.width, (H - 2 * top) / s.height)
    s = s.resize((int(s.width * ratio), int(s.height * ratio)), Image.LANCZOS)
    x = W - s.width - 48
    im.paste(s, (x, top))
    if border:
        d = ImageDraw.Draw(im)
        d.rectangle([x - 1, top - 1, x + s.width, top + s.height], outline=(60, 66, 78))


def kicker(d, text, y=54):
    d.text((64, y), text.upper(), font=f(FM, 18), fill=(120, 130, 148))


def headline(d, text, y=96, size=44, color=WHITE, width=720):
    return put(d, (64, y), text, f(FB, size), color, width=width)


def body(d, lines, y, size=24, color=GREY, width=760, gap=14, bullet=False):
    fnt = f(FR, size)
    for ln in lines:
        if bullet:
            d.ellipse([64, y + size // 2 - 3, 70, y + size // 2 + 3], fill=RED)
            y = put(d, (86, y), ln, fnt, color, width=width - 22)
        else:
            y = put(d, (64, y), ln, fnt, color, width=width)
        y += gap
    return y


def verdict_box(d, y, label, text, color=RED):
    d.rectangle([64, y, 64 + 700, y + 96], outline=color, width=2)
    d.text((80, y + 14), label, font=f(FM, 17), fill=color)
    put(d, (80, y + 42), text, f(FR, 22), WHITE, width=660, leading=1.25)


def slide_title():
    im, d = base()
    d.text((64, 210), 'DESTINY QC', font=f(FB, 104), fill=WHITE)
    d.text((68, 340), 'AI writes the horoscope. Kane grades it.', font=f(FR, 34), fill=GOLD)
    d.text((68, 400), 'A closed loop between a content agent and a browser-verification layer',
           font=f(FR, 22), fill=GREY)
    d.text((68, 560), 'Kane CLI Online Hackathon · November 2026', font=f(FM, 20), fill=(120, 130, 148))
    shot_img = shot(EV / 'chart_after.png')
    paste_right(im, shot_img, top=150, max_w=520)
    return im


def slide_problem():
    im, d = base()
    kicker(d, 'the problem')
    headline(d, 'Open-loop content, sold to customers', width=640)
    body(d, ['3,000-character readings generated from a chart engine',
             'The only quality gate: a human glancing at the PDF',
             'The agent never learns whether its own output is usable'], y=230, width=620, bullet=True)
    verdict_box(d, 470, 'WHAT WE NEEDED', 'A machine-readable verdict the agent can act on, per run.', color=GOLD)
    paste_right(im, shot(EV / 'report_full.png', box=(0, 0, 1280, 900)), top=120, max_w=560)
    return im


def slide_loop():
    im, d = base()
    kicker(d, 'the loop')
    headline(d, 'Generate → verify → read verdict → fix → re-verify', size=38, width=1100)
    steps = [('1', 'Content agent generates the report'),
             ('2', 'Kane CLI drives a real browser through the acceptance spec'),
             ('3', 'Failure returns root cause, culprit step, confidence'),
             ('4', 'Agent rewrites the report and resubmits'),
             ('5', 'Max 3 rounds, then escalate to a human')]
    y = 220
    for n, t in steps:
        d.ellipse([64, y, 96, y + 32], fill=RED)
        d.text((74, y + 5), n, font=f(FB, 19), fill=WHITE)
        y = put(d, (116, y + 3), t, f(FR, 25), WHITE if n in '345' else GREY, width=1060) + 20
    d.text((64, 640), 'Every run seals an evidence pack: session video, replay, network log, per-step screenshots.',
           font=f(FM, 18), fill=(120, 130, 148))
    return im


def slide_round1():
    im, d = base()
    kicker(d, 'round 1 · failed')
    headline(d, 'Kane caught a defect we planted — and named the element', size=36, width=620)
    verdict_box(d, 250, 'VERDICT · report_preview_test', 'The report header does not show all five required pieces of birth information.')
    body(d, ['Seeded: the info bar dropped one of five required fields (four pillars)',
             'The verdict is structured JSON — not a screenshot for a human to squint at'], y=380, width=600, bullet=True)
    paste_right(im, shot(EV / 'report_full.png', box=(0, 0, 1280, 760)), top=120, max_w=540)
    return im


def slide_round2():
    im, d = base()
    kicker(d, 'round 2 · failed again')
    headline(d, 'The agent fixed the header and broke something else', size=36, width=620)
    verdict_box(d, 250, 'VERDICT · report_preview_test', 'The generated report does not meet the required minimum length of 2000 Chinese characters.')
    body(d, ['Verify the output, not the diff',
             'Verdict goes back to the agent again — it rewrites, and we re-run'], y=380, width=600, bullet=True)
    paste_right(im, shot(EV / 'report_full.png', box=(0, 700, 1280, 1600)), top=120, max_w=540)
    return im


def slide_round3():
    im, d = base()
    kicker(d, 'round 3 · passed')
    d.text((64, 190), 'PASSED', font=f(FB, 96), fill=GREEN)
    body(d, ['Three rounds, two real defects, zero human glances',
             'Sealed evidence pack: replay, console, network, per-step screenshots',
             'The report ships only now — verification is a runtime gate, not a ritual'], y=340, width=1080, bullet=True)
    d.text((64, 620), 'qc_loop.py  ·  report_preview_test.md  ·  2,000-char floor  ·  8 required sections',
           font=f(FM, 18), fill=(120, 130, 148))
    return im


def slide_chart():
    im, d = base()
    kicker(d, 'same rig, the product itself')
    headline(d, 'Seven-step journey test on the charting app', size=38, width=620)
    body(d, ['open the site · enter the form · submit',
             '12-palace grid · four pillars · five-element class',
             'life master and body master as separate rows'], y=230, width=600, bullet=True)
    verdict_box(d, 440, 'RESULT', 'Six steps passed. The seventh failed.', color=RED)
    paste_right(im, shot(EV / 'chart_after.png'), top=110, max_w=600)
    return im


def slide_bug():
    im, d = base()
    kicker(d, 'the real bug it found')
    headline(d, 'Centre cell was missing three fields the renderer already had', size=34, width=620)
    body(d, ['four pillars  ·  life master  ·  body master',
             'Patched the component, rebuilt, re-ran the same test',
             '7 of 7 passed — and the product got better'], y=300, width=600, bullet=True)
    d.text((64, 470), '7/7', font=f(FB, 120), fill=GREEN)
    d.text((64, 600), 'chart_flow_test.md  ·  evidence sealed', font=f(FM, 18), fill=(120, 130, 148))
    paste_right(im, shot(EV / 'chart_after.png', box=(700, 700, 1900, 1500)), top=140, max_w=560)
    return im


def slide_selfaudit():
    im, d = base()
    kicker(d, 'bonus · it audited our own spec')
    headline(d, 'Kane classified one failure as a bad test, not a bad app', size=34, width=660)
    verdict_box(d, 250, 'VERDICT · family', 'automation_bug / agent_misstep — our step text let two similar labels stand in for each other',
                color=GOLD)
    body(d, ['Rewrote the step to assert the two rows separately',
             'The verification layer audits the specification, not just the product'], y=390, width=1140, bullet=True)
    paste_right(im, shot(EV / 'chart_after.png', box=(760, 780, 1800, 1420)), top=150, max_w=520)
    return im


def slide_run():
    im, d = base()
    kicker(d, 'how to run it')
    headline(d, 'Three commands, no framework', size=38, width=1100)
    lines = [
        'npm install -g @testmuai/kane-cli',
        'kane-cli login --username $LT_USERNAME --access-key $LT_ACCESS_KEY',
        'python3 qc_loop.py --demo-seed-defect',
    ]
    y = 240
    for ln in lines:
        d.rectangle([64, y - 10, 1210, y + 54], fill=(22, 26, 34))
        d.text((84, y), '$ ' + ln, font=f(FM, 24), fill=(150, 220, 170))
        y += 90
    body(d, ['tests/*.md hold the acceptance spec in plain English',
             'qc_loop.py runs generate → verify → fix → verify and exits non-zero if unfixed'], y=530, width=1120, bullet=True)
    return im


def slide_close():
    im, d = base()
    d.text((64, 180), 'destiny-qc', font=f(FB, 84), fill=WHITE)
    body(d, ['Tests are Markdown. Verdicts are JSON. The gate is a script.',
             'github.com/gaoyang-94/destiny-qc',
             'Built with Kane CLI by TestMu AI'], y=310, size=28, width=1100, bullet=False)
    d.text((64, 560), 'Thank you.', font=f(FB, 30), fill=GOLD)
    return im


SLIDES = [
    (slide_title, 'This is Destiny QC. An AI writes Chinese astrology reports. Kane CLI grades them, in a real browser, and the verdict goes straight back to the agent that wrote them.'),
    (slide_problem, 'Here is the problem. Our pipeline generates three thousand character readings from a chart engine and sells them to paying customers. The only quality gate was a human glancing at the PDF. That is open loop. The agent has no idea whether its own output is usable.'),
    (slide_loop, 'So we closed the loop. The agent generates a report. Kane CLI walks the acceptance criteria in a real browser: the birth info bar, eight required sections, banned phrases, and a length floor. On failure, the verdict — root cause, culprit step, confidence — goes back to the agent, which rewrites and resubmits. Three rounds maximum, then it escalates to a human.'),
    (slide_round1, 'Round one. We deliberately seeded a defect: the report header dropped one of the five required birth fields. Kane caught it on the rendered page, in one plain sentence, pointing at the exact element. Not a screenshot for a human to squint at — a machine readable verdict.'),
    (slide_round2, 'The agent fixed the header, and broke something else. Round two failed: the body fell under the two thousand character floor. This is exactly why you verify the output, not the diff. Verdict back to the agent.'),
    (slide_round3, 'Round three. Green. Every run seals an evidence pack: session replay, console, network log, and per-step screenshots. The report ships only now. Verification is a runtime gate, not a human ritual.'),
    (slide_chart, 'Then we pointed the same rig at the product itself. Seven steps: open the site, fill the birth form, submit, expect a twelve palace grid, then four pillars, five element class, and the life master and body master rows. Six steps passed. Step seven failed.'),
    (slide_bug, 'It found a real bug. The web chart centre cell was missing the four pillars, plus the life master and body master lines, even though our image renderer already showed them. We patched the component, rebuilt, and re-ran the identical test. Seven of seven.'),
    (slide_selfaudit, 'One more thing worth showing. On an earlier run, Kane did not blame the app at all. It classified the failure as an automation bug: our step text was vague enough that two similar labels could pass for each other. The verifier audited our specification, not just the product. We rewrote the step and it has been stable since.'),
    (slide_run, 'Running it takes three commands. Install Kane CLI, log in, and run the loop. The acceptance spec lives in Markdown files that a product owner can read, and the loop exits non-zero if the report cannot be fixed in three rounds.'),
    (slide_close, 'Destiny QC. Tests are Markdown, verdicts are JSON, and the gate is a script. The repository is on GitHub. Built for the Kane CLI hackathon.'),
]


def main():
    piper = '/tmp/ttsev/bin/piper'
    voice = str(EV / 'voices' / 'en_US-lessac-medium.onnx')
    segs = []
    for i, (fn, narr) in enumerate(SLIDES, 1):
        img_path = OUT / f'slide{i:02d}.png'
        fn().save(img_path)
        wav = OUT / f'slide{i:02d}.wav'
        subprocess.run([piper, '-m', voice, '--length-scale', '1.13', '--sentence-silence', '0.75', '-f', str(wav)], input=narr, text=True,
                       check=True, capture_output=True)
        dur = float(subprocess.check_output(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(wav)]).decode().strip())
        seg = OUT / f'seg{i:02d}.mp4'
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-loop', '1', '-i', str(img_path),
                        '-i', str(wav), '-c:v', 'libx264', '-tune', 'stillimage', '-pix_fmt', 'yuv420p',
                        '-c:a', 'aac', '-b:a', '128k', '-shortest', '-t', f'{dur + 2.0:.2f}', str(seg)], check=True)
        segs.append(seg)
        print(f'slide {i}: {dur:.1f}s', flush=True)

    lst = OUT / 'list.txt'
    lst.write_text(''.join(f"file '{s.name}'\n" for s in segs))
    final = Path('/root/myself/AI/destiny-qc/demo/destiny-qc-demo.mp4')
    final.parent.mkdir(exist_ok=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0',
                    '-i', str(lst), '-c', 'copy', str(final)], cwd=OUT, check=True)
    total = float(subprocess.check_output(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(final)]).decode().strip())
    size = final.stat().st_size / 1e6
    print(f'DONE {final}  {total/60:.2f} min  {size:.1f} MB')


if __name__ == '__main__':
    main()
