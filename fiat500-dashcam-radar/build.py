#!/usr/bin/env python3
"""フィアット500 ドラレコ前後 & レーダー探知機取付 — 施工紹介リール

python3 build.py  →  fiat500_dashcam_radar.mp4 / .xml / media/
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "macky_reel"))
import reel as R

SRC = os.path.join(HERE, "src")
P = lambda n: os.path.join(SRC, n)
k = 1512 / 1500  # 表示座標→実寸

scenes = [
    # 1. タイトル
    dict(label="title", dur=3.0, zoom=(1.0, 1.06), anim="static",
         plate=R.photo_plate(P("IMG_6199.jpg"), fx=0.45, fy=0.5),
         overlay=R.title_overlay("FIAT 500", ["ドラレコ前後＆", "レーダー探知機を", "付けてみた"],
                                 "ユピテル SUPER CAT")),
    # 2. 使用製品
    dict(label="products", dur=2.5, zoom=(1.06, 1.0),
         plate=R.photo_plate(P("IMG_6200.jpg"), fx=0.5, fy=0.5),
         overlay=R.caption_overlay("使用したのはユピテル製", "Z850DR ＋ リアカメラ OP-CM207", y=300)),
    # 3. 製品説明カード
    dict(label="card", dur=3.0, zoom=(1.0, 1.0),
         plate=R.card_plate(P("IMG_6200.jpg"), [int(v * k) for v in (180, 915, 1420, 1665)]),
         overlay=R.card_overlay("Z850DR は 1台2役", "レーダー探知機 × ドライブレコーダー",
                                points=["前方：本体カメラで録画", "後方：リアカメラ OP-CM207"])),
    # 4. 取付完了
    dict(label="done", dur=3.0, zoom=(1.0, 1.06),
         plate=R.photo_plate(P("IMG_6201.jpg"), mode="fit", fy=0.47),
         overlay=R.caption_overlay(["取付完了！"], "ミラー横にスッキリ設置", y=1260)),
    # 5. モニター寄り
    dict(label="monitor", dur=2.5, zoom=(1.0, 1.08),
         plate=R.photo_plate(P("IMG_6201.jpg"), mode="fit", fy=0.47,
                             crop=[int(v * k) for v in (860, 250, 1740, 745)]),
         overlay=R.caption_overlay("映像もその場でチェック", "Z850DR の画面で確認", y=1260)),
    # 6. エンドカード
    dict(label="end", dur=3.0, zoom=(1.0, 1.0), anim="static",
         plate=R.navy_plate(),
         overlay=R.end_overlay("ドラレコ・電装品の取付")),
]

t = sum(s["dur"] for s in scenes[:3])
out = R.render(scenes, HERE, name="fiat500_dashcam_radar",
               bgm_cfg=dict(hits=[t], outro=sum(s["dur"] for s in scenes[:5]), seed=11))
print("wrote", out)
