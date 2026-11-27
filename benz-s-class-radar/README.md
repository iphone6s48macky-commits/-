# Mercedes-Benz 新型Sクラス レーダー探知機取付 — 15秒紹介動画

縦型 1080×1920 / 30fps / 15秒（Reels・TikTok・Shorts 向け）

## 構成
| 秒 | 写真 | テロップ |
|---|---|---|
| 0.0–2.5 | IMG_8532 ボンネット | Mercedes-Benz / 新型 Sクラス / レーダー探知機 取付 |
| 2.5–4.5 | IMG_8537 製品箱 | Yupiteru / SUPER CAT ZK3200 |
| 4.5–6.5 | IMG_8535 運転席・内装脱着 | 内装パネルを外して / 見えない配線処理 |
| 6.5–8.5 | IMG_8533 リア分解 | リア周りも / 丁寧に脱着 |
| 8.5–10.5 | IMG_8534 リア復元 | アンビエントライトも / 純正どおり復元 |
| 10.5–12.0 | IMG_8536 フロントガラス | 取付位置を / ミリ単位でチェック |
| 12.0–15.0 | IMG_8538 取付後 | 取付完了！ / macky's car shop |

※ IMG_8535 右下の車台番号ラベルはぼかし済み。

## ファイル
- `preview.mp4` … 完成版（BGM入り・そのまま投稿可）
- `media/bgm.wav` … オリジナルBGM（120BPM、カット点に効果音、12秒で決めのヒット）
- `sclass_radar_15s.xml` … Premiere Pro 用シーケンス
- `media/plate_*.png` … V1 写真（9:16 切り抜き済み）
- `media/telop_*.png` … V2 テロップ（透過PNG）
- `build.py` … 映像の再生成スクリプト
- `bgm.py` … BGM の再生成スクリプト（`python3 bgm.py`）

## Premiere Pro での開き方
1. `benz-s-class-radar` フォルダごと PC に保存
2. Premiere Pro →「ファイル > 読み込み」で `sclass_radar_15s.xml` を選択
3. メディアのリンク確認が出たら `media` フォルダ内の同名ファイルを指定
4. シーケンス「Sクラス_レーダー探知機取付_15s」を開く
   - V1：写真（スケール 100→110% のキーフレームでズーム、カット間はクロスディゾルブ 8f）
   - V2：テロップ（不透明度 0→100% で 8f フェードイン）
   - A1：BGM（`media/bgm.wav`）
5. 書き出し（H.264 / 1080×1920 / 30fps、ラウドネスは -14 LUFS 目安）

テロップ文言を変えたいときは `build.py` の `lines` を書き換えて
`python3 build.py <写真フォルダ> <Noto Sans JP フォントフォルダ>` で再生成。
