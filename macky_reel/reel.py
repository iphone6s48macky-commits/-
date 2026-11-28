"""macky's car shop 施工紹介リール — 共通スタイル & レンダラー

RAV4 センチュリーホーン動画のフォーマットを再現:
  - 縦型 1080x1920 / 30fps / ハードカット + ゆっくりズーム
  - タイトル: 赤ピル(車種) + 極太白文字 + 黄色サブ
  - 本編: 左上「● macky's car shop」バッジ、紺半透明ボックス+赤縦ラインのテロップ
  - 紺背景の説明カード、紺背景のエンドカード
  - 横長写真はぼかし背景 + 横幅フィット

使い方は jobs/*.py を参照。1 ジョブ = シーンのリストを render() に渡すだけ。
"""
import os, shutil, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps

W, H, FPS = 1080, 1920, 30
LIB = os.path.dirname(os.path.abspath(__file__))

NAVY = (16, 30, 73)
RED = (220, 22, 40)
YELLOW = (255, 204, 40)
WHITE = (255, 255, 255)
SHOP = "macky's car shop"


def font(weight, size):
    name = {"medium": "500Medium", "bold": "700Bold", "xbold": "800ExtraBold",
            "black": "900Black"}[weight]
    return ImageFont.truetype(os.path.join(LIB, "fonts", f"NotoSansJP_{name}.ttf"), size)


def tsize(text, f):
    b = ImageDraw.Draw(Image.new("L", (1, 1))).textbbox((0, 0), text, font=f)
    return b[2] - b[0], b[3] - b[1], b[0], b[1]


def draw_text(lay, xy, text, f, fill=WHITE, shadow=True, stroke=0, stroke_fill=(0, 0, 0)):
    """xy = 見た目の左上。ドロップシャドウ付き"""
    w, h, ox, oy = tsize(text, f)
    x, y = xy[0] - ox, xy[1] - oy
    if shadow:
        sh = Image.new("RGBA", lay.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((x + 4, y + 6), text, font=f, fill=(0, 0, 0, 150),
                                stroke_width=stroke + 2, stroke_fill=(0, 0, 0, 150))
        lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    ImageDraw.Draw(lay).text((x, y), text, font=f, fill=fill,
                             stroke_width=stroke, stroke_fill=stroke_fill)
    return w, h


def rrect(lay, box, r, fill):
    o = Image.new("RGBA", lay.size, (0, 0, 0, 0))
    ImageDraw.Draw(o).rounded_rectangle(box, r, fill=fill)
    lay.alpha_composite(o)


# ------------------------------------------------------------------ 部品
def badge(lay):
    f = font("bold", 40)
    w, h, _, _ = tsize(SHOP, f)
    x0, y0, ph = 56, 168, 74
    rrect(lay, (x0, y0, x0 + 34 + 26 + w + 34, y0 + ph), ph // 2, NAVY + (175,))
    d = ImageDraw.Draw(lay)
    cx, cy = x0 + 40, y0 + ph // 2
    d.ellipse((cx - 13, cy - 13, cx + 13, cy + 13), fill=RED)
    draw_text(lay, (cx + 30, cy - h // 2 - 2), SHOP, f, shadow=False)


def pill(lay, cx, y, text, f, bg=RED, fg=WHITE, padx=34, ph=None):
    w, h, _, _ = tsize(text, f)
    ph = ph or h + 34
    rrect(lay, (cx - w // 2 - padx, y, cx + w // 2 + padx, y + ph), ph // 2, bg + (255,))
    draw_text(lay, (cx - w // 2, y + (ph - h) // 2 - 2), text, f, fill=fg, shadow=False)
    return ph


def caption(lay, y, main, sub=None, align="center"):
    """紺半透明ボックス + 赤縦ライン。main は 1〜2 行 (list 可)"""
    lines = main if isinstance(main, list) else [main]
    f = font("black", 64)
    fs = font("xbold", 44)
    for i, t in enumerate(lines):
        w, h, _, _ = tsize(t, f)
        bw, bh = w + 90, 112
        x = (W - bw) // 2 if align == "center" else 48
        rrect(lay, (x, y, x + bw, y + bh), 8, NAVY + (190,))
        ImageDraw.Draw(lay).rectangle((x, y, x + 12, y + bh), fill=RED)
        draw_text(lay, (x + 50, y + (bh - h) // 2 - 3), t, f)
        y += bh + 14
    if sub:
        w, h, _, _ = tsize(sub, fs)
        bw, bh = w + 70, 84
        x = (W - bw) // 2 if align == "center" else 48
        rrect(lay, (x, y, x + bw, y + bh), 8, NAVY + (190,))
        ImageDraw.Draw(lay).rectangle((x, y, x + 10, y + bh), fill=RED)
        draw_text(lay, (x + 40, y + (bh - h) // 2 - 3), sub, fs)


# ------------------------------------------------------------------ 背景プレート
def _grade(im):
    im = ImageEnhance.Contrast(im).enhance(1.06)
    return ImageEnhance.Color(im).enhance(1.05)


def photo_plate(path, fx=0.5, fy=0.5, crop=None, blur_boxes=(), mode="fill", scale=1.2):
    """写真→ 9:16 プレート (scale 倍の解像度で返す: ズーム用)
    mode='fill' : 画面いっぱいに切り抜き
    mode='fit'  : 横幅フィット + ぼかし背景 (横長写真用)
    crop=(x0,y0,x1,y1): 先に部分切り出し
    blur_boxes: モザイクをかける矩形 (元画像座標)"""
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    for b in blur_boxes:
        reg = im.crop(b)
        small = reg.resize((max(1, reg.width // 24), max(1, reg.height // 24)))
        im.paste(small.resize(reg.size, Image.NEAREST), b)
    if crop:
        im = im.crop(crop)
    im = _grade(im)
    BW, BH = int(W * scale), int(H * scale)
    iw, ih = im.size
    if mode == "fill":
        r = max(BW / iw, BH / ih)
        nw, nh = int(iw * r + 0.5), int(ih * r + 0.5)
        big = im.resize((nw, nh), Image.LANCZOS)
        x0 = int((nw - BW) * fx); y0 = int((nh - BH) * fy)
        return big.crop((x0, y0, x0 + BW, y0 + BH))
    # fit
    r = max(BW / iw, BH / ih)
    bg = im.resize((int(iw * r) + 1, int(ih * r) + 1), Image.LANCZOS)
    bg = bg.crop(((bg.width - BW) // 2, (bg.height - BH) // 2,
                  (bg.width - BW) // 2 + BW, (bg.height - BH) // 2 + BH))
    bg = ImageEnhance.Brightness(bg.filter(ImageFilter.GaussianBlur(40))).enhance(0.55)
    r = BW / iw
    fg = im.resize((BW, int(ih * r)), Image.LANCZOS)
    bg.paste(fg, (0, int(BH * fy - fg.height / 2)))
    return bg


def navy_plate():
    return Image.new("RGB", (W, H), NAVY)


# ------------------------------------------------------------------ シーン別テロップ
def title_overlay(car, lines, sub):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # 薄い白帯 (RAV4 と同じ: 上 1/7〜半分)
    band = Image.new("RGBA", (W, 760), (255, 255, 255, 60))
    lay.alpha_composite(band, (0, 270))
    pill(lay, W // 2, 330, car, font("xbold", 40), ph=72)
    y = 460
    f = font("black", 118 if max(len(t) for t in lines) <= 7 else 104)
    for t in lines:
        w, h, _, _ = tsize(t, f)
        draw_text(lay, ((W - w) // 2, y), t, f, stroke=3, stroke_fill=(60, 60, 60))
        y += h + 34
    fs = font("black", 54)
    w, h, _, _ = tsize(sub, fs)
    draw_text(lay, ((W - w) // 2, y + 26), sub, fs, fill=YELLOW, stroke=2,
              stroke_fill=(80, 60, 0))
    return lay


def caption_overlay(main, sub=None, y=1150, tag=None, tag_color=RED):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    badge(lay)
    if tag:
        pill(lay, W // 2, 420, tag, font("black", 58), bg=tag_color, ph=96, padx=36)
    caption(lay, y, main, sub)
    return lay


def card_overlay(heading, subhead, points=(), note=None):
    """紺背景カード (RAV4 の「移植元：〜」カード)"""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    badge(lay)
    f = font("black", 62)
    w, h, _, _ = tsize(heading, f)
    y = 420
    ImageDraw.Draw(lay).rectangle((44, y - 10, 56, y + h + 90), fill=RED)
    draw_text(lay, ((W - w) // 2, y), heading, f, shadow=False)
    fs = font("bold", 46)
    w2, h2, _, _ = tsize(subhead, fs)
    draw_text(lay, ((W - w2) // 2, y + h + 30), subhead, fs, shadow=False)
    # 下部ポイント
    y = 1300
    fp = font("bold", 46)
    for p in points:
        w, h, _, _ = tsize(p, fp)
        bw = w + 110
        x = (W - bw) // 2
        rrect(lay, (x, y, x + bw, y + 92), 46, (255, 255, 255, 28))
        d = ImageDraw.Draw(lay)
        d.ellipse((x + 34, y + 36, x + 54, y + 56), fill=RED)
        draw_text(lay, (x + 74, y + (92 - h) // 2 - 3), p, fp, shadow=False)
        y += 116
    if note:
        fn = font("medium", 30)
        w, h, _, _ = tsize(note, fn)
        draw_text(lay, ((W - w) // 2, y + 10), note, fn, fill=(200, 205, 220), shadow=False)
    return lay


def card_plate(image_path, crop, box=(36, 640, 1044, 1210)):
    """紺背景 + 白角丸カード内に写真"""
    pl = navy_plate().convert("RGBA")
    x0, y0, x1, y1 = box
    rrect(pl, box, 22, WHITE + (255,))
    im = _grade(ImageOps.exif_transpose(Image.open(image_path)).convert("RGB").crop(crop))
    iw, ih = x1 - x0 - 24, y1 - y0 - 24
    r = min(iw / im.width, ih / im.height)
    im = im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, im.width, im.height), 14, fill=255)
    pl.paste(im, (x0 + (x1 - x0 - im.width) // 2, y0 + (y1 - y0 - im.height) // 2), mask)
    return pl.convert("RGB")


def end_overlay(tagline, area="対応エリア：大阪府全域"):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rectangle((0, 500, W, 506), fill=RED)
    d.rectangle((0, 1410, W, 1416), fill=RED)
    def center(t, f, y, fill=WHITE):
        w, h, _, _ = tsize(t, f)
        draw_text(lay, ((W - w) // 2, y), t, f, fill=fill, shadow=False)
        return h
    center(tagline, font("black", 56), 600)
    center(SHOP, font("bold", 76), 716)
    center("ご予約・ご相談は", font("bold", 44), 960)
    pill(lay, W // 2, 1060, "プロフィールのリンクから", font("black", 54), ph=104, padx=70)
    center(area, font("bold", 40), 1270)
    return lay


# ------------------------------------------------------------------ レンダー
def render(scenes, out_dir, bgm_cfg=None, name="reel"):
    """scenes: dict(plate=Image(scale倍), overlay=RGBA, dur=秒, zoom=(z0,z1),
                     anim='static'|'slide', label=str)"""
    media = os.path.join(out_dir, "media")
    frames = os.path.join(out_dir, "_frames")
    os.makedirs(media, exist_ok=True)
    shutil.rmtree(frames, ignore_errors=True)
    os.makedirs(frames)

    t = 0
    for i, s in enumerate(scenes, 1):
        s["start"] = t
        s["n"] = int(round(s["dur"] * FPS))
        t += s["n"]
        s["plate"].resize((W, H), Image.LANCZOS).save(os.path.join(media, f"plate_{i:02d}_{s['label']}.png"))
        s["overlay"].save(os.path.join(media, f"telop_{i:02d}_{s['label']}.png"))
    total = t

    fr = 0
    for s in scenes:
        big = s["plate"]
        bw, bh = big.size
        sc = bw / W
        z0, z1 = s.get("zoom", (1.0, 1.0))
        for k in range(s["n"]):
            p = k / max(1, s["n"] - 1)
            p = p * p * (3 - 2 * p) * 0.3 + p * 0.7      # ほぼ等速、端だけ少しなめらか
            z = z0 + (z1 - z0) * p
            # big は sc 倍の解像度。z=1 で全体、z>1 で中央を拡大
            cw, ch = int(bw / z), int(bh / z)
            x0, y0 = (bw - cw) // 2, (bh - ch) // 2
            img = big.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.BILINEAR).convert("RGBA")
            ov = s["overlay"]
            anim = s.get("anim", "slide")
            if anim == "slide":
                a = min(1.0, max(0.0, (k - 3) / 8))
                e = 1 - (1 - a) ** 3
                if e > 0:
                    o = ov if e >= 1 else _fade(ov, e, int((1 - e) * 60))
                    img.alpha_composite(o)
            else:
                img.alpha_composite(ov)
            img.convert("RGB").save(os.path.join(frames, f"{fr:04d}.jpg"), quality=93)
            fr += 1

    silent = os.path.join(out_dir, "_silent.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS),
                    "-i", os.path.join(frames, "%04d.jpg"), "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "slow", silent], check=True)
    shutil.rmtree(frames)

    out = os.path.join(out_dir, f"{name}.mp4")
    if bgm_cfg is not None:
        from bgm import make_bgm
        cuts = [s["start"] / FPS for s in scenes[1:]]
        wav = os.path.join(media, "bgm.wav")
        make_bgm(wav, total / FPS, cuts, **bgm_cfg)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", wav,
                        "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000",
                        "-c:a", "aac", "-b:a", "192k", "-shortest",
                        "-movflags", "+faststart", out], check=True)
        os.remove(silent)
    else:
        os.replace(silent, out)
    write_xml(scenes, total, os.path.join(out_dir, f"{name}.xml"), name, bgm_cfg is not None)
    return out


def _fade(ov, e, dx):
    r, g, b, a = ov.split()
    a = a.point(lambda v: int(v * e))
    o = Image.merge("RGBA", (r, g, b, a))
    shifted = Image.new("RGBA", ov.size, (0, 0, 0, 0))
    shifted.alpha_composite(o, (0, dx))
    return shifted


# ------------------------------------------------------------------ Premiere XML
def write_xml(scenes, total, path, name, with_bgm):
    rate = f"<rate><timebase>{FPS}</timebase><ntsc>FALSE</ntsc></rate>"

    def clip(cid, fname, st, n, z=None):
        motion = ""
        if z and z != (1.0, 1.0):
            motion = f"""
            <filter><effect><name>Basic Motion</name><effectid>basic</effectid>
              <effectcategory>motion</effectcategory><effecttype>motion</effecttype><mediatype>video</mediatype>
              <parameter><parameterid>scale</parameterid><name>Scale</name><valuemin>0</valuemin><valuemax>1000</valuemax>
                <value>{z[0]*100:.1f}</value>
                <keyframe><when>0</when><value>{z[0]*100:.1f}</value></keyframe>
                <keyframe><when>{n}</when><value>{z[1]*100:.1f}</value></keyframe>
              </parameter></effect></filter>"""
        return f"""
          <clipitem id="{cid}"><name>{fname}</name><enabled>TRUE</enabled><duration>{n}</duration>{rate}
            <start>{st}</start><end>{st+n}</end><in>0</in><out>{n}</out>
            <file id="f-{cid}"><name>{fname}</name><pathurl>media/{fname}</pathurl>{rate}
              <media><video><samplecharacteristics><width>{W}</width><height>{H}</height></samplecharacteristics></video></media>
            </file>{motion}
          </clipitem>"""

    v1 = "".join(clip(f"plate-{i}", f"plate_{i:02d}_{s['label']}.png", s["start"], s["n"], s.get("zoom"))
                 for i, s in enumerate(scenes, 1))
    v2 = "".join(clip(f"telop-{i}", f"telop_{i:02d}_{s['label']}.png", s["start"], s["n"])
                 for i, s in enumerate(scenes, 1))
    audio = ""
    if with_bgm:
        audio = f"""
        <track>
          <clipitem id="bgm"><name>bgm.wav</name><enabled>TRUE</enabled><duration>{total}</duration>{rate}
            <start>0</start><end>{total}</end><in>0</in><out>{total}</out>
            <file id="f-bgm"><name>bgm.wav</name><pathurl>media/bgm.wav</pathurl>{rate}<duration>{total}</duration>
              <media><audio><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics>
                <channelcount>2</channelcount></audio></media></file>
            <sourcetrack><mediatype>audio</mediatype><trackindex>1</trackindex></sourcetrack>
          </clipitem>
        </track>"""
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE xmeml>
<xmeml version="4">
  <sequence id="seq"><name>{name}</name><duration>{total}</duration>{rate}
    <media>
      <video>
        <format><samplecharacteristics>{rate}<width>{W}</width><height>{H}</height>
          <pixelaspectratio>square</pixelaspectratio><fielddominance>none</fielddominance></samplecharacteristics></format>
        <track>{v1}
        </track>
        <track>{v2}
        </track>
      </video>
      <audio>
        <numOutputChannels>2</numOutputChannels>
        <format><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics></format>{audio}
      </audio>
    </media>
  </sequence>
</xmeml>
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(xml)
