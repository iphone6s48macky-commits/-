#!/usr/bin/env python3
"""Mercedes-Benz 新型Sクラス レーダー探知機取付 — 15秒 縦型紹介動画ビルダー

出力:
  media/plate_XX.png   … V1 用 写真プレート (1080x1920, 9:16 に切り抜き済み)
  media/telop_XX.png   … V2 用 テロップ (1080x1920, 透過PNG)
  preview.mp4          … 完成プレビュー (H.264, 30fps, 15秒)
  sclass_radar_15s.xml … Premiere Pro 読み込み用シーケンス (FCP7 XML)

使い方: python3 build.py <写真フォルダ> <フォントフォルダ>
"""
import os, sys, subprocess, shutil
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
TOTAL = 15 * FPS          # 450 frames
XF = 8                    # クロスディゾルブのフレーム数
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1]
FONTDIR = sys.argv[2]
RED = (226, 35, 45)

def font(weight, size):
    return ImageFont.truetype(os.path.join(FONTDIR, f"NotoSansJP_{weight}.ttf"), size)

# ---------------------------------------------------------------- 構成
# file, 開始frame, 長さ, 横方向の注目位置(0-1), ズーム(開始,終了), パン(dx), テロップ
SHOTS = [
    dict(f="03189a45-image.jpg", name="IMG_8532", start=0,   dur=75, fx=0.55, z=(1.00, 1.10),
         kind="title",
         lines=["Mercedes-Benz", "新型 Sクラス", "レーダー探知機 取付"]),
    dict(f="7d13778f-image.jpg", name="IMG_8537", start=75,  dur=60, fx=0.50, z=(1.08, 1.00),
         kind="caption", lines=["Yupiteru", "SUPER CAT ZK3200"], cy=300),
    dict(f="42da2429-image.jpg", name="IMG_8535", start=135, dur=60, fx=0.58, z=(1.00, 1.08),
         kind="caption", lines=["内装パネルを外して", "見えない配線処理"], blur_vin=True),
    dict(f="d0aef517-image.jpg", name="IMG_8533", start=195, dur=60, fx=0.50, z=(1.00, 1.08),
         kind="caption", lines=["リア周りも", "丁寧に脱着"]),
    dict(f="1b7358e9-image.jpg", name="IMG_8534", start=255, dur=60, fx=0.45, z=(1.08, 1.00),
         kind="caption", lines=["アンビエントライトも", "純正どおり復元"]),
    dict(f="a4151586-image.jpg", name="IMG_8536", start=315, dur=45, fx=0.45, z=(1.00, 1.08),
         kind="caption", lines=["取付位置を", "ミリ単位でチェック"]),
    dict(f="3f24cca6-image.jpg", name="IMG_8538", start=360, dur=90, fx=0.56, z=(1.00, 1.12),
         kind="end", lines=["取付完了！", "macky's car shop"]),
]

# ---------------------------------------------------------------- 写真プレート
def make_plate(s):
    im = Image.open(os.path.join(SRC, s["f"])).convert("RGB")
    if s.get("blur_vin"):
        # 右下の車台番号ラベルをぼかす
        box = (1120, 1700, 1400, 2016)
        region = im.crop(box).filter(ImageFilter.GaussianBlur(28))
        im.paste(region, box)
    iw, ih = im.size
    # 9:16 に切り抜き (高さ基準)
    cw = int(ih * W / H)
    if cw > iw:
        cw, ch = iw, int(iw * H / W)
    else:
        ch = ih
    cx = int(s["fx"] * iw)
    x0 = max(0, min(iw - cw, cx - cw // 2))
    y0 = (ih - ch) // 2
    crop = im.crop((x0, y0, x0 + cw, y0 + ch))
    # ズーム用に 1.2 倍の解像度で保持
    big = crop.resize((int(W * 1.2), int(H * 1.2)), Image.LANCZOS)
    plate = big.resize((W, H), Image.LANCZOS)
    # 軽いグレーディング（コントラスト↑、黒締め）
    from PIL import ImageEnhance
    big = ImageEnhance.Contrast(big).enhance(1.08)
    plate = ImageEnhance.Contrast(plate).enhance(1.08)
    return big, plate

# ---------------------------------------------------------------- テロップ
def text_w(d, t, f):
    b = d.textbbox((0, 0), t, font=f)
    return b[2] - b[0], b[3] - b[1], b[1]

def shadowed(layer, xy, t, f, fill=(255, 255, 255), stroke=6):
    d = ImageDraw.Draw(layer)
    d.text(xy, t, font=f, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0, 230))

def make_telop(s, progress=1.0):
    """progress: 0→1 でスライドイン (0 = 非表示)"""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    ease = 1 - (1 - min(1, max(0, progress))) ** 3
    alpha = int(255 * ease)
    off = int((1 - ease) * 120)

    if s["kind"] == "title":
        # 上部グラデ帯 + 3段タイトル
        grad = Image.new("RGBA", (W, 900), (0, 0, 0, 0))
        gd = ImageDraw.Draw(grad)
        for y in range(900):
            gd.line([(0, y), (W, y)], fill=(0, 0, 0, int(190 * (1 - y / 900) * ease)))
        lay.alpha_composite(grad, (0, 0))
        f1, f2, f3 = font("500Medium", 58), font("900Black", 128), font("800ExtraBold", 76)
        y = 230
        for t, f, col in [(s["lines"][0], f1, (235, 235, 235)),
                          (s["lines"][1], f2, (255, 255, 255)),
                          (s["lines"][2], f3, (255, 255, 255))]:
            tw, th, ty = text_w(d, t, f)
            shadowed(lay, ((W - tw) // 2 - off, y - ty), t, f, fill=col + (alpha,), stroke=5)
            y += th + 40
        # 赤ライン
        lw = int(520 * ease)
        d.rectangle([(W - lw) // 2, y + 10, (W + lw) // 2, y + 20], fill=RED + (alpha,))

    elif s["kind"] == "caption":
        # 下部: 赤アクセント + 黒半透明ボックス
        f1, f2 = font("700Bold", 66), font("900Black", 86)
        t1, t2 = s["lines"]
        w1, h1, o1 = text_w(d, t1, f1)
        w2, h2, o2 = text_w(d, t2, f2)
        bw = max(w1, w2) + 120
        bh = h1 + h2 + 110
        bx = 60 - off
        by = s.get("cy", H - 520)
        box = Image.new("RGBA", (bw, bh), (0, 0, 0, int(165 * ease)))
        lay.alpha_composite(box, (max(0, bx), by))
        d.rectangle([max(0, bx), by, max(0, bx) + 16, by + bh], fill=RED + (alpha,))
        shadowed(lay, (bx + 60, by + 35 - o1), t1, f1, fill=(255, 255, 255, alpha), stroke=3)
        shadowed(lay, (bx + 60, by + 35 + h1 + 30 - o2), t2, f2, fill=(255, 255, 255, alpha), stroke=3)

    elif s["kind"] == "end":
        grad = Image.new("RGBA", (W, 1000), (0, 0, 0, 0))
        gd = ImageDraw.Draw(grad)
        for y in range(1000):
            gd.line([(0, y), (W, y)], fill=(0, 0, 0, int(215 * (y / 1000) * ease)))
        lay.alpha_composite(grad, (0, H - 1000))
        f1, f2 = font("900Black", 150), font("700Bold", 62)
        t1, t2 = s["lines"]
        w1, h1, o1 = text_w(d, t1, f1)
        w2, h2, o2 = text_w(d, t2, f2)
        y = H - 560 + off // 2
        shadowed(lay, ((W - w1) // 2, y - o1), t1, f1, fill=(255, 255, 255, alpha), stroke=6)
        lw = int(600 * ease)
        d.rectangle([(W - lw) // 2, y + h1 + 40, (W + lw) // 2, y + h1 + 50], fill=RED + (alpha,))
        shadowed(lay, ((W - w2) // 2, y + h1 + 90 - o2), t2, f2, fill=(255, 255, 255, alpha), stroke=3)
    return lay

# ---------------------------------------------------------------- フレーム生成
def kb_frame(big, t, z):
    """Ken Burns: t 0→1, ズーム z0→z1 (中央基準)"""
    zz = z[0] + (z[1] - z[0]) * t
    bw, bh = big.size
    cw, ch = int(bw / zz), int(bh / zz)
    x0, y0 = (bw - cw) // 2, (bh - ch) // 2
    return big.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.BILINEAR)

def main():
    media = os.path.join(HERE, "media")
    frames = os.path.join(HERE, "_frames")
    os.makedirs(media, exist_ok=True)
    shutil.rmtree(frames, ignore_errors=True)
    os.makedirs(frames)

    bigs = []
    for i, s in enumerate(SHOTS, 1):
        big, plate = make_plate(s)
        plate.save(os.path.join(media, f"plate_{i:02d}_{s['name']}.png"))
        make_telop(s, 1.0).save(os.path.join(media, f"telop_{i:02d}.png"))
        bigs.append(big)

    for fr in range(TOTAL):
        canvas = None
        for i, s in enumerate(SHOTS):
            st, du = s["start"], s["dur"]
            end = st + du + (XF if i < len(SHOTS) - 1 else 0)
            if not (st <= fr < end):
                continue
            t = (fr - st) / (du + XF)
            img = kb_frame(bigs[i], t, s["z"]).convert("RGBA")
            # テロップ: ショット開始 4f 後から 10f でイン
            p = (fr - st - 4) / 10
            if s["kind"] == "end":
                p = (fr - st - 12) / 14
            if p > 0:
                img.alpha_composite(make_telop(s, p))
            if canvas is None:
                canvas = img
            else:
                a = (fr - st) / XF  # 新ショットのフェードイン
                canvas = Image.blend(canvas, img, min(1, max(0, a)))
        # ラスト 10f はフェードアウト
        if fr >= TOTAL - 10:
            k = (TOTAL - fr) / 10
            canvas = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), canvas, k)
        canvas.convert("RGB").save(os.path.join(frames, f"{fr:04d}.jpg"), quality=92)
        if fr % 50 == 0:
            print("frame", fr)

    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS),
                    "-i", os.path.join(frames, "%04d.jpg"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                    "-preset", "slow", "-movflags", "+faststart",
                    os.path.join(HERE, "preview.mp4")], check=True)
    shutil.rmtree(frames)
    write_xml()
    print("done")

# ---------------------------------------------------------------- Premiere 用 XML
def write_xml():
    def clip(cid, name, path, start, end, fid, scale=None, fade_in=False):
        motion = ""
        if scale:
            dur = end - start
            motion = f"""
            <filter><effect><name>Basic Motion</name><effectid>basic</effectid>
              <effectcategory>motion</effectcategory><effecttype>motion</effecttype><mediatype>video</mediatype>
              <parameter><parameterid>scale</parameterid><name>Scale</name><valuemin>0</valuemin><valuemax>1000</valuemax>
                <value>{scale[0]*100:.1f}</value>
                <keyframe><when>0</when><value>{scale[0]*100:.1f}</value></keyframe>
                <keyframe><when>{dur}</when><value>{scale[1]*100:.1f}</value></keyframe>
              </parameter></effect></filter>"""
        opacity = ""
        if fade_in:
            opacity = """
            <filter><effect><name>Opacity</name><effectid>opacity</effectid>
              <effectcategory>motion</effectcategory><effecttype>motion</effecttype><mediatype>video</mediatype>
              <parameter><parameterid>opacity</parameterid><name>Opacity</name><valuemin>0</valuemin><valuemax>100</valuemax>
                <value>100</value>
                <keyframe><when>0</when><value>0</value></keyframe>
                <keyframe><when>8</when><value>100</value></keyframe>
              </parameter></effect></filter>"""
        return f"""
          <clipitem id="{cid}">
            <name>{name}</name><enabled>TRUE</enabled><duration>{end-start}</duration>
            <rate><timebase>{FPS}</timebase><ntsc>FALSE</ntsc></rate>
            <start>{start}</start><end>{end}</end><in>0</in><out>{end-start}</out>
            <file id="{fid}"><name>{name}</name><pathurl>media/{name}</pathurl>
              <rate><timebase>{FPS}</timebase><ntsc>FALSE</ntsc></rate>
              <media><video><samplecharacteristics><width>{W}</width><height>{H}</height></samplecharacteristics></video></media>
            </file>{motion}{opacity}
          </clipitem>"""

    def dissolve(at):
        return f"""
          <transitionitem>
            <start>{at - XF//2}</start><end>{at + XF//2}</end><alignment>center</alignment>
            <rate><timebase>{FPS}</timebase><ntsc>FALSE</ntsc></rate>
            <effect><name>Cross Dissolve</name><effectid>Cross Dissolve</effectid>
              <effectcategory>Dissolve</effectcategory><effecttype>transition</effecttype><mediatype>video</mediatype></effect>
          </transitionitem>"""

    v1, v2 = [], []
    for i, s in enumerate(SHOTS, 1):
        st, en = s["start"], s["start"] + s["dur"]
        if i > 1:
            v1.append(dissolve(st))
        v1.append(clip(f"plate-{i}", f"plate_{i:02d}_{s['name']}.png", "", st, en,
                       f"fp{i}", scale=s["z"]))
        tin = st + (12 if s["kind"] == "end" else 4)
        v2.append(clip(f"telop-{i}", f"telop_{i:02d}.png", "", tin, en, f"ft{i}", fade_in=True))

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE xmeml>
<xmeml version="4">
  <sequence id="seq-1">
    <name>Sクラス_レーダー探知機取付_15s</name>
    <duration>{TOTAL}</duration>
    <rate><timebase>{FPS}</timebase><ntsc>FALSE</ntsc></rate>
    <media>
      <video>
        <format><samplecharacteristics>
          <rate><timebase>{FPS}</timebase><ntsc>FALSE</ntsc></rate>
          <width>{W}</width><height>{H}</height>
          <pixelaspectratio>square</pixelaspectratio><fielddominance>none</fielddominance>
        </samplecharacteristics></format>
        <track>{''.join(v1)}
        </track>
        <track>{''.join(v2)}
        </track>
      </video>
      <audio>
        <numOutputChannels>2</numOutputChannels>
        <format><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics></format>
        <track>
          <clipitem id="bgm-1">
            <name>bgm.wav</name><enabled>TRUE</enabled><duration>{TOTAL}</duration>
            <rate><timebase>{FPS}</timebase><ntsc>FALSE</ntsc></rate>
            <start>0</start><end>{TOTAL}</end><in>0</in><out>{TOTAL}</out>
            <file id="fbgm"><name>bgm.wav</name><pathurl>media/bgm.wav</pathurl>
              <rate><timebase>{FPS}</timebase><ntsc>FALSE</ntsc></rate>
              <duration>{TOTAL}</duration>
              <media><audio><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics>
                <channelcount>2</channelcount></audio></media>
            </file>
            <sourcetrack><mediatype>audio</mediatype><trackindex>1</trackindex></sourcetrack>
          </clipitem>
        </track>
      </audio>
    </media>
  </sequence>
</xmeml>
"""
    with open(os.path.join(HERE, "sclass_radar_15s.xml"), "w", encoding="utf-8") as f:
        f.write(xml)

if __name__ == "__main__":
    main()
