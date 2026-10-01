import math, random, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

S = '/tmp/claude-0/-home-user-matreshka/1f984027-563b-5431-a2ee-bc1cba782400/scratchpad'
FF = '/usr/local/lib/python3.11/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2'
VIDEO = sys.argv[1]
OUT = sys.argv[2]
STUDIO = sys.argv[3] if len(sys.argv) > 3 else 'СазоновПитерСтейлз'
TITLE = sys.argv[4] if len(sys.argv) > 4 else 'СЕМЬЯ ЧЕБУРАНО'

W, H, FPS = 1280, 720, 24
PRE = 6.6           # длительность заставки до видео
XF = 0.35           # кроссфейд в видео
SR = 48000
random.seed(7); np.random.seed(7)

# ---------- фон: первый кадр видео, размытый и затемнённый ----------
subprocess.run([FF, '-v', 'error', '-y', '-i', VIDEO, '-vframes', '1', f'{S}/first.png'], check=True)
bg = Image.open(f'{S}/first.png').convert('RGB').resize((W, H), Image.LANCZOS)
bg = bg.filter(ImageFilter.GaussianBlur(7))
bg = ImageEnhance.Brightness(bg).enhance(0.38)
bg_big = bg.resize((W + 40, H + 40), Image.LANCZOS)

# ---------- табличка ----------
f_big = ImageFont.truetype(f'{S}/fonts/pf900.ttf', 62)
f_small = ImageFont.truetype(f'{S}/fonts/pf400i.ttf', 40)
GOLD = (232, 190, 98)

def make_sign():
    tw = f_big.getbbox(STUDIO)[2]
    sw, sh = max(tw + 110, 640), 200
    im = Image.new('RGBA', (sw, sh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # тёмное дерево с золотой рамкой
    for y in range(sh):
        k = 0.75 + 0.25 * math.sin(y * 0.21) * math.sin(y * 0.047)
        d.line([(0, y), (sw, y)], fill=(int(70 * k), int(42 * k), int(24 * k), 255))
    mask = Image.new('L', (sw, sh), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, sw - 1, sh - 1], 26, fill=255)
    im.putalpha(mask)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([8, 8, sw - 9, sh - 9], 20, outline=GOLD, width=4)
    d.rounded_rectangle([18, 18, sw - 19, sh - 19], 14, outline=(150, 112, 50), width=2)
    for x in (40, sw - 40):  # кольца для цепей
        d.ellipse([x - 9, 10, x + 9, 28], outline=GOLD, width=4)
    def ctext(y, txt, font, fill):
        b = font.getbbox(txt); x = (sw - (b[2] - b[0])) / 2 - b[0]
        d.text((x + 3, y + 3), txt, font=font, fill=(20, 10, 5, 200))
        d.text((x, y), txt, font=font, fill=fill)
    ctext(42, STUDIO, f_big, GOLD)
    ctext(122, 'представляет', f_small, (240, 222, 180))
    return im

SIGN = make_sign()
SW, SH = SIGN.size
RINGS = [(40, 19), (SW - 40, 19)]  # точки крепления в координатах таблички

def rot(vx, vy, deg):  # поворот вектора как у PIL.rotate (против часовой визуально)
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    return vx * c + vy * s, -vx * s + vy * c

def place(frame, img, pivot_local, pivot_screen, deg):
    cx, cy = img.size[0] / 2, img.size[1] / 2
    vx, vy = rot(cx - pivot_local[0], cy - pivot_local[1], deg)
    r = img.rotate(deg, resample=Image.BICUBIC, expand=True)
    x = pivot_screen[0] + vx - r.size[0] / 2
    y = pivot_screen[1] + vy - r.size[1] / 2
    frame.alpha_composite(r, (int(round(x)), int(round(y))))

def screen_pt(local, pivot_local, pivot_screen, deg):
    vx, vy = rot(local[0] - pivot_local[0], local[1] - pivot_local[1], deg)
    return pivot_screen[0] + vx, pivot_screen[1] + vy

def chain(d, p0, p1):
    n = max(2, int(math.dist(p0, p1) / 14))
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        a = (p0[0] + (p1[0] - p0[0]) * t0, p0[1] + (p1[1] - p0[1]) * t0)
        b = (p0[0] + (p1[0] - p0[0]) * t1, p0[1] + (p1[1] - p0[1]) * t1)
        d.line([a, b], fill=(120, 120, 125) if i % 2 else (170, 170, 175), width=5 if i % 2 else 3)

# ---------- заголовок ----------
f_title = ImageFont.truetype(f'{S}/fonts/ruslan.ttf', 96)
def make_title():
    b = f_title.getbbox(TITLE)
    tw, th = b[2] - b[0], b[3] - b[1]
    pad = 40
    im = Image.new('RGBA', (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
    glow = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).text((pad - b[0], pad - b[1]), TITLE, font=f_title, fill=(255, 40, 40, 255))
    glow = glow.filter(ImageFilter.GaussianBlur(14))
    im.alpha_composite(glow); im.alpha_composite(glow)
    d = ImageDraw.Draw(im)
    d.text((pad - b[0], pad - b[1]), TITLE, font=f_title, fill=GOLD, stroke_width=4, stroke_fill=(40, 15, 10))
    return im
TITLE_IM = make_title()

# ---------- тайминг ----------
T_DROP, T_SWING_END, T_SNAP_END, T_FALL_END = 0.55, 2.9, 3.55, 4.25
T_TOSS, T_LAND = 4.35, 5.05
PIV = (W / 2, -120)               # точка подвеса над кадром
L = 360                           # от точки подвеса до верха таблички
SIGN_TOP = (SW / 2, 0)

def swing_angle(t):
    tt = t - T_DROP
    return 9 * math.exp(-0.35 * tt) * math.sin(2 * math.pi * 0.62 * tt + 0.9)

rain = [(random.uniform(0, W), random.uniform(0, H), random.uniform(18, 34)) for _ in range(140)]

def render(t):
    shake = 0
    if 4.12 < t < 4.5:
        shake = 14 * math.exp(-(t - 4.12) * 9) * math.sin(t * 90)
    fr = Image.new('RGBA', (W, H))
    fr.paste(bg_big.crop((20 + shake, 20 + shake * 0.6, 20 + shake + W, 20 + shake * 0.6 + H)))
    d = ImageDraw.Draw(fr)
    for i, (x, y, l) in enumerate(rain):  # дождь
        yy = (y + t * 900 + i * 13) % (H + 60) - 60
        xx = (x - t * 120) % W
        d.line([(xx, yy), (xx - 6, yy + l)], fill=(150, 160, 190, 90), width=1)

    if t < T_SNAP_END:
        if t < T_DROP:  # падает сверху и пружинит
            k = t / T_DROP
            yoff = -520 * (1 - k) ** 2 + 18 * math.sin(k * math.pi) * (k > 0.7)
            ang = 0
        else:
            yoff, ang = 0, swing_angle(t)
        if t < T_SWING_END:
            top_screen = (PIV[0], PIV[1] + L + yoff)
            pv_screen = PIV if t >= T_DROP else (PIV[0], PIV[1] + yoff)
            # табличка жёстко висит на подвесе
            s_top = screen_pt((0, L), (0, 0), (0, 0), ang)
            ps = (pv_screen[0] + s_top[0], pv_screen[1] + s_top[1])
            pts = [screen_pt(r, SIGN_TOP, ps, ang) for r in RINGS]
            for k2, p in enumerate(pts):
                chain(d, (W / 2 + (-160 if k2 == 0 else 160), -10), p)
            place(fr, SIGN, SIGN_TOP, ps, ang)
        else:  # левая цепь рвётся: вращение вокруг правого кольца
            a0 = swing_angle(T_SWING_END)
            s_top = screen_pt((0, L), (0, 0), (0, 0), a0)
            ps0 = (PIV[0] + s_top[0], PIV[1] + s_top[1])
            R = screen_pt(RINGS[1], SIGN_TOP, ps0, a0)
            k = (t - T_SWING_END) / (T_SNAP_END - T_SWING_END)
            ang = a0 + (68 - a0) * (1 - math.cos(min(k, 1) * math.pi)) / 2 + 6 * math.sin(k * 9) * (1 - k)
            chain(d, (W / 2 + 160, -10), R)
            # обрывок левой цепи болтается
            chain(d, (W / 2 - 160, -10), (W / 2 - 150 + 20 * math.sin(t * 12), 120))
            place(fr, SIGN, RINGS[1], R, ang)
    elif t < T_FALL_END:  # падение
        a0 = swing_angle(T_SWING_END)
        s_top = screen_pt((0, L), (0, 0), (0, 0), a0)
        ps0 = (PIV[0] + s_top[0], PIV[1] + s_top[1])
        R = screen_pt(RINGS[1], SIGN_TOP, ps0, a0)
        tt = t - T_SNAP_END
        chain(d, (W / 2 + 160, -10), (W / 2 + 165 + 30 * math.sin(t * 10) * math.exp(-tt * 2), 140))
        chain(d, (W / 2 - 160, -10), (W / 2 - 150 + 15 * math.sin(t * 12), 120))
        Rf = (R[0] + 60 * tt, R[1] + 2600 * tt * tt)
        place(fr, SIGN, RINGS[1], Rf, 68 + 50 * tt)
    else:
        for side in (-1, 1):  # пустые цепи ещё качаются
            chain(d, (W / 2 + 160 * side, -10), (W / 2 + 160 * side + 18 * math.sin(t * 8 + side) * math.exp(-(t - 4) * 1.5), 130))

    if t >= T_TOSS:  # заголовок выкидывают снизу
        tt = t - T_TOSS
        D = T_LAND - T_TOSS
        cx, cy = W / 2, H / 2 + 40
        if tt < D:
            k = tt / D
            y = H + 160 - (H + 160 - (cy - 90)) * math.sin(k * math.pi / 2) ** 0.8
            if k > 0.75:
                y = (cy - 90) + 90 * ((k - 0.75) / 0.25) ** 2
            ang = 540 * (1 - k) ** 2 * -1 + 0
            sc = 0.5 + 0.5 * k
        else:
            k2 = tt - D
            y = cy - 22 * math.exp(-k2 * 7) * abs(math.sin(k2 * 18))
            ang = 4 * math.exp(-k2 * 5) * math.sin(k2 * 20)
            sc = 1 + 0.08 * math.exp(-k2 * 8) * math.sin(k2 * 25)
        im = TITLE_IM.resize((int(TITLE_IM.size[0] * sc), int(TITLE_IM.size[1] * sc)), Image.LANCZOS)
        pl = (im.size[0] / 2, im.size[1] / 2)
        place(fr, im, pl, (cx, y), ang)
    return fr.convert('RGB')

# ---------- рендер заставки ----------
p = subprocess.Popen([FF, '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                      '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', f'{S}/pre.mp4'],
                     stdin=subprocess.PIPE)
n = int(round((PRE + XF) * FPS))
for i in range(n):
    p.stdin.write(render(i / FPS).tobytes())
p.stdin.close(); p.wait()

# ---------- звук ----------
N = int((PRE + XF) * SR)
a = np.zeros(N)
def add(sig, t0, gain=1.0):
    i0 = int(t0 * SR); i1 = min(N, i0 + len(sig))
    if i0 < N: a[i0:i1] += gain * sig[:i1 - i0]
def damped(f, dur, decay):
    t = np.arange(int(dur * SR)) / SR
    return np.sin(2 * np.pi * f * t) * np.exp(-t * decay)
def creak(dur, r0, r1, gain=1.0):
    out = np.zeros(int(dur * SR)); t = 0.0
    while t < dur:
        k = t / dur
        rate = r0 + (r1 - r0) * k
        amp = math.sin(math.pi * k) ** 0.5 * (0.6 + 0.4 * random.random())
        burst = damped(780 + 120 * random.random(), 0.02, 400) + 0.5 * damped(1650, 0.02, 500) + 0.3 * damped(320, 0.02, 200)
        i = int(t * SR); j = min(len(out), i + len(burst))
        out[i:j] += amp * burst[:j - i]
        t += (1 / rate) * (0.7 + 0.6 * random.random())
    return out * gain
def noise(dur):
    return np.random.randn(int(dur * SR))
def lowpass(x, k):
    return np.convolve(x, np.ones(k) / k, mode='same')

# дождь
a += lowpass(noise(N / SR), 6) * 0.03 + lowpass(noise(N / SR), 40) * 0.05
# звяк цепей при появлении
for f in (2400, 3150, 4020):
    add(damped(f, 0.5, 9), T_DROP - 0.05, 0.12)
# скрип на каждом крайнем положении качания
half = 1 / (2 * 0.62)
t = T_DROP + 0.15; g = 0.5
while t < T_SWING_END - 0.2:
    add(creak(0.45, 25, 60), t, g); t += half; g *= 0.85
# длинный скрип при обрыве
add(damped(3500, 0.08, 60) + damped(5200, 0.08, 80), T_SWING_END, 0.4)  # щелчок
add(creak(0.7, 18, 90, 0.8), T_SWING_END + 0.02)
# удар об землю
add(damped(55, 0.6, 7), 4.12, 0.8)
add(lowpass(noise(0.3), 30) * np.exp(-np.arange(int(0.3 * SR)) / SR * 15), 4.12, 0.7)
# свист броска
wd = T_LAND - T_TOSS
w = lowpass(noise(wd), 8) * np.sin(np.linspace(0, np.pi, int(wd * SR))) ** 2
add(w, T_TOSS, 0.5)
# «бум» при приземлении заголовка
for f in (73.4, 110, 146.8):
    add(damped(f, 1.6, 2.2), T_LAND, 0.35)
add(lowpass(noise(0.15), 20) * np.exp(-np.arange(int(0.15 * SR)) / SR * 30), T_LAND, 0.5)
a = np.tanh(a * 1.2) * 0.85
fade = np.ones(N); xs = int(XF * SR); fade[-xs:] = np.linspace(1, 0, xs)
a *= fade
with wave.open(f'{S}/pre.wav', 'wb') as wv:
    wv.setnchannels(1); wv.setsampwidth(2); wv.setframerate(SR)
    wv.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())

# ---------- склейка с видео ----------
fc = (f'[1:v]scale={W}:{H}:flags=lanczos,fps={FPS},setsar=1,format=yuv420p,settb=1/24[v1];'
      f'[0:v]fps={FPS},setsar=1,format=yuv420p,settb=1/24[v0];'
      f'[v0][v1]xfade=transition=fadewhite:duration={XF}:offset={PRE}[v];'
      f'[2:a]aresample={SR},aformat=channel_layouts=stereo[a0];'
      f'[1:a]aresample={SR},aformat=channel_layouts=stereo[a1];'
      f'[a0][a1]acrossfade=d={XF}[a]')
subprocess.run([FF, '-v', 'error', '-y', '-i', f'{S}/pre.mp4', '-i', VIDEO, '-i', f'{S}/pre.wav',
                '-filter_complex', fc, '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-crf', '18',
                '-preset', 'medium', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', OUT], check=True)
print('done', OUT)
