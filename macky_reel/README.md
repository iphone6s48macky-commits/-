# macky_reel — 施工紹介リールの共通テンプレート

RAV4「センチュリーの純正ホーンを付けてみた」動画のフォーマットを再現する共通部品です。

- 縦型 1080×1920 / 30fps / ハードカット + ゆっくりズーム
- タイトル：赤ピル（車種）＋極太白文字＋黄色サブ
- 本編：左上「● macky's car shop」バッジ、紺の半透明ボックス＋赤縦ラインのテロップ
- 紺背景の説明カード（写真入り白カード＋ポイント）
- エンドカード（ご予約・ご相談は／プロフィールのリンクから／対応エリア：大阪府全域）
- オリジナルBGM（カット点にウーシュ、決めのヒット、エンドで締め）、-14 LUFS

## 新しい案件の作り方
1. `<案件名>/src/` に写真を入れる
2. `fiat500-dashcam-radar/build.py` をコピーしてシーンを書き換える
3. `python3 build.py` → `<名前>.mp4`（完成版）、`<名前>.xml`（Premiere 用）、`media/`

## 部品
| 関数 | 用途 |
|---|---|
| `photo_plate(path, fx, fy, mode="fill"/"fit", crop, blur_boxes)` | 写真背景。縦写真は fill、横写真は fit（ぼかし背景）。blur_boxes でナンバー等をモザイク |
| `card_plate(path, crop)` / `card_overlay(見出し, サブ, points)` | 紺背景の説明カード |
| `title_overlay(車種, [3行], 黄サブ)` | タイトル |
| `caption_overlay(main, sub, y, tag="AFTER")` | 本編テロップ（tag で BEFORE/AFTER ピル） |
| `end_overlay(キャッチ)` | エンドカード |

## Premiere Pro
XML を「ファイル > 読み込み」。V1=背景プレート（ズームはスケールのキーフレーム）、V2=テロップ PNG、A1=BGM。
リンク確認が出たら `media/` を指定。

フォント：Noto Sans JP（SIL Open Font License, `fonts/LICENSE_FONT`）
