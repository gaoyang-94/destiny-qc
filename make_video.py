#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 destiny-qc 的演示视频：幻灯片 + piper 英文旁白 + ffmpeg 合成。
排版规则：右侧截图先贴，文字栏宽度按截图左边界动态收缩，保证永不遮挡。
"""
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

EV = Path('/tmp/kane_ev')
OUT = EV / 'video'
OUT.mkdir(exist_ok=True)
W, H = 1280, 720
PAD = 56          # 页边距
GUTTER = 48       # 文字栏与截图的间距
BG = (14, 17, 22)
RED = (196, 62, 52)
GOLD = (217, 164, 65)
GREY = (168, 176, 190)
WHITE = (240, 242, 246)
GREEN = (76, 175, 116)
DIM = (120, 130, 148)

FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FR = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FM = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'

TW = W - 2 * PAD   # 当前文字栏宽度（每页由 layout() 决定）


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
            lines.append(cur)
            cur = w
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


def paste_right(im, src, top=110, max_w=520, max_h=470):
    """贴右侧截图，返回其左边界 x。"""
    s = src.copy()
    ratio = min(max_w / s.width, max_h / s.height)
    s = s.resize((max(1, int(s.width * ratio)), max(1, int(s.height * ratio))), Image.LANCZOS)
    x = W - s.width - PAD
    im.paste(s, (x, top))
    ImageDraw.Draw(im).rectangle([x - 1, top - 1, x + s.width, top + s.height],
                                 outline=(60, 66, 78))
    return x


def layout(img_left=None):
    """设文字栏宽度：有截图就收到截图左边，无截图占满。"""
    global TW
    TW = (img_left - PAD - GUTTER) if img_left else (W - 2 * PAD)
    return TW


def kicker(d, text, y=48):
    d.text((PAD, y), text.upper(), font=f(FM, 17), fill=DIM)


def headline(d, text, y=84, size=40, color=WHITE, width=None):
    return put(d, (PAD, y), text, f(FB, size), color, width=width or TW)


def body(d, lines, y, size=23, color=GREY, width=None, gap=13, bullet=True):
    fnt = f(FR, size)
    wd = (width or TW) - 24 if bullet else (width or TW)
    for ln in lines:
        if bullet:
            d.ellipse([PAD, y + size // 2 - 3, PAD + 6, y + size // 2 + 3], fill=RED)
            y = put(d, (PAD + 24, y), ln, fnt, color, width=wd)
        else:
            y = put(d, (PAD, y), ln, fnt, color, width=wd)
        y += gap
    return y


def verdict_box(d, y, label, text, color=RED, width=None, h=104):
    wd = width or TW
    d.rectangle([PAD, y, PAD + wd, y + h], outline=color, width=2)
    d.text((PAD + 16, y + 12), label, font=f(FM, 16), fill=color)
    put(d, (PAD + 16, y + 38), text, f(FR, 21), WHITE, width=wd - 34, leading=1.3)
    return y + h


# ---------- 幻灯片 ----------

def slide_title():
    im, d = base()
    left = paste_right(im, Image.open(EV / 'chart_after.png'), top=140, max_w=540, max_h=460)
    layout(left)
    d.text((PAD, 170), 'DESTINY', font=f(FB, 74), fill=WHITE)
    d.text((PAD, 246), 'QC', font=f(FB, 74), fill=RED)
    put(d, (PAD, 350), 'AI writes the horoscope. Kane grades it.', f(FR, 26), GOLD, width=TW)
    put(d, (PAD, 440), 'A closed loop between a content agent and a browser-verification layer.',
        f(FR, 20), GREY, width=TW)
    d.text((PAD, 620), 'Kane CLI Online Hackathon · Nov 2026', font=f(FM, 18), fill=DIM)
    return im


def slide_problem():
    im, d = base()
    left = paste_right(im, Image.open(EV / 'report_full.png').crop((0, 0, 1280, 980)),
                       top=120, max_w=480, max_h=450)
    layout(left)
    kicker(d, 'the problem')
    headline(d, 'Open-loop content, sold to customers', size=32)
    body(d, ['3,000-character readings from a chart engine',
             'Only gate: a human glancing at the PDF',
             'The agent never learns if its work is usable'], y=270)
    verdict_box(d, 470, 'WHAT WE NEEDED',
                'A machine-readable verdict the agent can act on.', color=GOLD, h=96)
    return im


def slide_loop():
    im, d = base()
    layout(None)
    kicker(d, 'the loop')
    headline(d, 'Generate → verify → read verdict → fix → re-verify', size=32)
    steps = [('1', 'Content agent generates the report'),
             ('2', 'Kane CLI drives a real browser through the acceptance spec'),
             ('3', 'Failure returns root cause, culprit step, confidence'),
             ('4', 'Agent rewrites the report and resubmits'),
             ('5', 'Max 3 rounds, then escalate to a human')]
    y = 230
    for n, t in steps:
        d.ellipse([PAD, y, PAD + 32, y + 32], fill=RED)
        d.text((PAD + 10, y + 5), n, font=f(FB, 19), fill=WHITE)
        y = put(d, (PAD + 52, y + 3), t, f(FR, 24), WHITE, width=TW - 60) + 18
    d.text((PAD, 640), 'Every run seals an evidence pack: replay, network log, per-step screenshots.',
           font=f(FM, 17), fill=DIM)
    return im


def slide_round1():
    im, d = base()
    left = paste_right(im, Image.open(EV / 'report_full.png').crop((0, 0, 1280, 760)),
                       top=130, max_w=450, max_h=430)
    layout(left)
    kicker(d, 'round 1 · failed')
    headline(d, 'It caught the defect we planted', size=32)
    verdict_box(d, 220, 'VERDICT · report_preview_test',
                'The report header does not show all five required pieces of birth information.', h=130)
    body(d, ['Seeded: the info bar dropped one of five fields',
             'A structured verdict, not a screenshot to squint at'], y=390)
    return im


def slide_round2():
    im, d = base()
    left = paste_right(im, Image.open(EV / 'report_full.png').crop((0, 640, 1280, 1560)),
                       top=130, max_w=450, max_h=430)
    layout(left)
    kicker(d, 'round 2 · failed again')
    headline(d, 'Fixing the header broke the body', size=32)
    verdict_box(d, 220, 'VERDICT · report_preview_test',
                'The report does not meet the required minimum length of 2000 characters.', h=130)
    body(d, ['Verify the output, not the diff',
             'Verdict goes back to the agent again'], y=390)
    return im


def slide_round3():
    im, d = base()
    layout(None)
    kicker(d, 'round 3 · passed')
    d.text((PAD, 150), 'PASSED', font=f(FB, 84), fill=GREEN)
    body(d, ['Three rounds, two real defects, zero human glances',
             'Evidence sealed: replay, console, network, step screenshots',
             'The report ships only now — a gate, not a ritual'], y=300, size=25, width=900)
    d.text((PAD, 610), 'qc_loop.py  ·  report_preview_test.md  ·  2000-char floor  ·  8 sections',
           font=f(FM, 18), fill=DIM)
    return im


def slide_chart():
    im, d = base()
    left = paste_right(im, Image.open(EV / 'chart_after.png'), top=120, max_w=500, max_h=450)
    layout(left)
    kicker(d, 'same rig · the product itself')
    headline(d, 'Seven-step journey test', size=32)
    body(d, ['open · fill form · submit',
             '12-palace grid · four pillars',
             'life master & body master rows'], y=250)
    verdict_box(d, 430, 'RESULT', 'Six passed. Step seven failed.', h=96)
    return im


def slide_bug():
    im, d = base()
    left = paste_right(im, Image.open(EV / 'chart_after.png').crop((700, 700, 1900, 1520)),
                       top=150, max_w=470, max_h=400)
    layout(left)
    kicker(d, 'the real bug it found')
    headline(d, 'Centre cell was missing three fields', size=32)
    body(d, ['four pillars · life master · body master',
             'Patched, rebuilt, re-ran the same test'], y=240)
    d.text((PAD, 370), '7/7', font=f(FB, 96), fill=GREEN)
    d.text((PAD, 490), 'chart_flow_test.md', font=f(FM, 18), fill=DIM)
    return im


def slide_selfaudit():
    im, d = base()
    left = paste_right(im, Image.open(EV / 'chart_after.png').crop((760, 780, 1800, 1440)),
                       top=150, max_w=450, max_h=390)
    layout(left)
    kicker(d, 'bonus · it audited our own spec')
    headline(d, 'A bad test, not a bad app', size=32)
    verdict_box(d, 220, 'VERDICT · family',
                'automation_bug — our step text let two similar labels stand in for each other.', h=140)
    body(d, ['Rewrote the step to assert both rows separately'], y=400)
    return im


def slide_run():
    im, d = base()
    layout(None)
    kicker(d, 'how to run it')
    headline(d, 'Three commands, no framework', size=32)
    lines = ['npm install -g @testmuai/kane-cli',
             'kane-cli login --username $LT_USERNAME --access-key $LT_ACCESS_KEY',
             'python3 qc_loop.py --demo-seed-defect']
    y = 220
    for ln in lines:
        d.rectangle([PAD, y - 10, W - PAD, y + 52], fill=(22, 26, 34))
        d.text((PAD + 18, y), '$ ' + ln, font=f(FM, 22), fill=(150, 220, 170))
        y += 86
    body(d, ['tests/*.md hold the spec in plain English',
             'the loop exits non-zero if unfixed after 3 rounds'], y=520, size=23, width=1000)
    return im


def slide_close():
    im, d = base()
    layout(None)
    d.text((PAD, 170), 'destiny-qc', font=f(FB, 74), fill=WHITE)
    put(d, (PAD, 300), 'Tests are Markdown. Verdicts are JSON. The gate is a script.',
        f(FR, 26), GREY, width=980)
    d.text((PAD, 380), 'github.com/gaoyang-94/destiny-qc', font=f(FM, 24), fill=GOLD)
    d.text((PAD, 440), 'Built with Kane CLI by TestMu AI', font=f(FM, 20), fill=DIM)
    d.text((PAD, 570), 'Thank you.', font=f(FB, 28), fill=GOLD)
    return im


SLIDES = [
    (slide_title, "This is Destiny QC. An AI writes Chinese astrology reports. Kane CLI grades them, in a real browser, and the verdict goes straight back to the agent that wrote them."),
    (slide_problem, "Here is the problem. Our pipeline generates three thousand character readings from a chart engine and sells them to paying customers. The only quality gate was a human glancing at the PDF. That is open loop. The agent has no idea whether its own output is usable."),
    (slide_loop, "So we closed the loop. The agent generates a report. Kane CLI walks the acceptance criteria in a real browser: the birth info bar, eight required sections, banned phrases, and a length floor. On failure, the verdict — root cause, culprit step, confidence — goes back to the agent, which rewrites and resubmits. Three rounds maximum, then it escalates to a human."),
    (slide_round1, "Round one. We deliberately seeded a defect: the report header dropped one of the five required birth fields. Kane caught it on the rendered page, in one plain sentence, pointing at the exact element. Not a screenshot for a human to squint at — a machine readable verdict."),
    (slide_round2, "The agent fixed the header, and broke something else. Round two failed: the body fell under the two thousand character floor. This is exactly why you verify the output, not the diff. Verdict back to the agent."),
    (slide_round3, "Round three. Green. Every run seals an evidence pack: session replay, console, network log, and per-step screenshots. The report ships only now. Verification is a runtime gate, not a human ritual."),
    (slide_chart, "Then we pointed the same rig at the product itself. Seven steps: open the site, fill the birth form, submit, expect a twelve palace grid, then four pillars, five element class, and the life master and body master rows. Six steps passed. Step seven failed."),
    (slide_bug, "It found a real bug. The web chart centre cell was missing the four pillars, plus the life master and body master lines, even though our image renderer already showed them. We patched the component, rebuilt, and re-ran the identical test. Seven of seven."),
    (slide_selfaudit, "One more thing worth showing. On an earlier run, Kane did not blame the app at all. It classified the failure as an automation bug: our step text was vague enough that two similar labels could pass for each other. The verifier audited our specification, not just the product."),
    (slide_run, "Running it takes three commands. Install Kane CLI, log in, and run the loop. The acceptance spec lives in Markdown files a product owner can read, and the loop exits non-zero if the report cannot be fixed in three rounds."),
    (slide_close, "Destiny QC. Tests are Markdown, verdicts are JSON, and the gate is a script. The repository is on GitHub. Built for the Kane CLI hackathon."),
]


def main():
    piper = '/tmp/ttsev/bin/piper'
    voice = str(EV / 'voices' / 'en_US-lessac-medium.onnx')
    segs = []
    for i, (fn, narr) in enumerate(SLIDES, 1):
        img_path = OUT / f'slide{i:02d}.png'
        fn().save(img_path)
        wav = OUT / f'slide{i:02d}.wav'
        subprocess.run([piper, '-m', voice, '--length-scale', '1.13', '--sentence-silence', '0.75',
                        '-f', str(wav)], input=narr, text=True, check=True, capture_output=True)
        dur = float(subprocess.check_output(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0',
             str(wav)]).decode().strip())
        seg = OUT / f'seg{i:02d}.mp4'
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-loop', '1', '-i', str(img_path),
                        '-i', str(wav), '-c:v', 'libx264', '-tune', 'stillimage', '-pix_fmt', 'yuv420p',
                        '-c:a', 'aac', '-b:a', '128k', '-shortest', '-t', f'{dur + 2.0:.2f}',
                        str(seg)], check=True)
        segs.append(seg)
        print(f'slide {i}: {dur:.1f}s', flush=True)

    lst = OUT / 'list.txt'
    lst.write_text(''.join(f"file '{s.name}'\n" for s in segs))
    final = Path('/root/myself/AI/destiny-qc/demo/destiny-qc-demo.mp4')
    final.parent.mkdir(exist_ok=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0',
                    '-i', str(lst), '-c', 'copy', str(final)], cwd=OUT, check=True)
    total = float(subprocess.check_output(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0',
         str(final)]).decode().strip())
    print(f'DONE {final}  {int(total)//60}:{int(total)%60:02d}  {final.stat().st_size/1e6:.1f} MB')


if __name__ == '__main__':
    main()
