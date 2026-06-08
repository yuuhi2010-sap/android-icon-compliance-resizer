# Android Icon Compliance Resizer

[English README](README.md)

1枚のアイコン画像から、Android ランチャー用リソース、Google Play Store 用画像、Adaptive Icon XML、見切れプレビュー、検証レポートを作るツールです。

アプリアイコンの最後の面倒な作業を助けます。素材としては良く見えるのに、Android のホーム画面で丸く切り抜かれると見切れる、Google Play 用アイコンだけ別に必要になる、そういう地味だけど品質に効く部分をまとめて確認できます。

<p>
  <img src="docs/images/mieru-play-store-icon.png" alt="Generated Play Store icon" width="150">
  <img src="docs/images/mieru-preview-circle.png" alt="Circle preview" width="150">
  <img src="docs/images/mieru-preview-rounded-square.png" alt="Rounded square preview" width="150">
  <img src="docs/images/mieru-preview-squircle.png" alt="Squircle preview" width="150">
  <img src="docs/images/mieru-preview-safe-zone.png" alt="Safe zone preview" width="150">
</p>

## なぜ使うのか

- 正方形では良く見えるのに、実機のホーム画面で見切れる問題を避けやすくなります。
- 同じ素材から Google Play 用アイコンと Android ランチャー用アイコンを作れます。
- circle、rounded-square、squircle、square、安全領域のプレビューをリリース前に確認できます。
- `--dry-run` と `--backup` により、置き換え前に確認しやすく、戻しやすいです。
- Codex Skill としても、単体の Python ツールとしても使えます。

## どんな素材を用意すればよいか

いちばん簡単なのは、大きめの正方形 PNG を1枚用意することです。できれば `1024x1024` 以上、最低でも `512x512` をおすすめします。ロゴ、文字、キャラクター、記号などの主役は中央に置き、周囲にしっかり余白を残してください。Android のホーム画面では丸や角丸に切り抜かれることがあるため、端の近くに大事な部分を置くと見切れやすくなります。

Android Adaptive Icon としてきれいに作るなら、次の素材を分けて用意するのが理想です。

- `foreground.png`: 透明背景のロゴ、記号、文字、キャラクターなど主役部分
- `background.png`: 背景の単色、グラデーション、模様、画像
- `monochrome.png`: 任意。Android のテーマアイコン用の単色版

アプリ制作やアイコン制作に慣れていない場合は、次の流れが簡単です。

1. Figma、Canva、Adobe Express、Illustrator、Photoshop、Affinity Designer、Inkscape などで正方形のアイコン画像を作ります。
2. デザインはシンプルにします。主役は1つ、コントラストは強め、小さな文字は避け、余白を多めにします。
3. `1024x1024` または `512x512` の PNG として書き出します。
4. レイヤーを分けられる場合は、主役だけを透明背景の `foreground.png`、背景だけを `background.png` として書き出します。
5. このツールでまず `--dry-run` を実行し、その後プレビュー画像で丸く切り抜かれても見切れないか確認します。

PNG が1枚しかなくても大丈夫です。その場合は `--source` を使います。Google Play 用アイコンと Android ランチャー用の保守的な候補を作れます。ただし、1枚の平坦な画像から foreground と background を正確に分離することはできません。

### 画像生成AIで素材を作る場合のヒント

画像生成AIを使う場合は、「完成したアプリアイコンの見本」ではなく、このツールで加工しやすい「アイコン素材」を作るつもりで指示すると失敗しにくくなります。

プロンプトのコツ:

- 正方形キャンバスの中央に主役を置くように指示します。
- 主役の周囲に十分な余白を残すように指示します。
- 小さいサイズでも読める、シンプルでコントラストの強い形にします。
- 小さな文字、複雑な背景、細すぎる線、端に近い影、アプリアイコン風の角丸フレームは避けます。
- `foreground.png` を作りたい場合は、透明背景にするよう指示します。
- レイヤー分けできる場合は、背景だけの画像も別に作ります。

1枚 PNG 用のプロンプト例:

```text
Create a square 1024x1024 app icon source image for a magnifying glass camera app. Center one clear magnifying glass symbol, leave generous padding on all sides, use high contrast, simple shapes, no text, no rounded-corner frame, no drop shadow outside the artwork.
```

foreground レイヤー用のプロンプト例:

```text
Create only the foreground symbol for an Android adaptive icon: a centered magnifying glass with a small camera detail, transparent background, simple high-contrast vector-like style, generous padding, no text, no shadow, no background.
```

background レイヤー用のプロンプト例:

```text
Create only the background layer for an Android adaptive icon: square 1024x1024, calm blue-green gradient, subtle soft texture, no logo, no text, no border, no rounded corners.
```

生成後は、このツールを実行する前に画像を目視確認してください。主役が端に近すぎる、小さな文字が読めない、すでに角丸が入っている、といった場合は、プロンプトを直して再生成するか、画像編集ツールで調整してから使います。

## クイックスタート

GitHub からインストール:

```bash
python -m pip install git+https://github.com/yuuhi2010-sap/android-icon-compliance-resizer.git
```

または、リポジトリを clone して依存関係をインストールします:

```bash
git clone https://github.com/yuuhi2010-sap/android-icon-compliance-resizer.git
cd android-icon-compliance-resizer
python -m pip install -r requirements.txt
```

まず dry-run で変更予定を確認します:

```bash
android-icon-pack \
  --project-root /path/to/android-project \
  --source /path/to/icon.png \
  --name ic_launcher \
  --legacy \
  --adaptive \
  --round \
  --preview \
  --dry-run
```

バックアップ付きで生成します:

```bash
android-icon-pack \
  --project-root /path/to/android-project \
  --source /path/to/icon.png \
  --name ic_launcher \
  --legacy \
  --adaptive \
  --round \
  --preview \
  --backup
```

生成済みリソースを検証します:

```bash
android-icon-validate \
  --project-root /path/to/android-project \
  --name ic_launcher \
  --strict
```

## 作られるもの

- `512x512` の Google Play Store 用 PNG を生成します。
- Android Adaptive Icon の foreground / background レイヤーを生成します。
- `mipmap-anydpi-v26` 用の Adaptive Icon XML を生成します。
- 必要に応じて従来の density 別 PNG を生成します。
- round icon XML とプレビューを生成できます。
- 透明ピクセルを除いた前景 bounds を検出し、重要なピクセルを Android Adaptive Icon の安全領域内に収めます。
- circle、rounded-square、squircle、square、安全領域オーバーレイのプレビューを生成します。
- Play アイコン形式、Adaptive Icon XML、参照 drawable、legacy サイズ、manifest 参照、見切れリスクを検証します。

## 必要なもの

- Python 3.9 以上
- Pillow

パッケージとしてインストールせず、リポジトリを直接使う場合は、`android-icon-pack` を `python scripts/pack_android_icons.py` に、`android-icon-validate` を `python scripts/validate_android_icons.py` に置き換えてください。

## 初心者向け: 実際の画像を見ながら試す

この例では、このリポジトリに入っている Mieru アプリのアイコン素材を使います。入力画像、生成される Google Play 用アイコン、Android ランチャーでの見え方を順番に確認できます。

### 1. まずは1枚のアイコン画像から始める

元になるアイコン素材です:

<img src="docs/images/mieru-source.png" alt="Mieru source icon" width="220">

手元に PNG が1枚だけある場合は `--source` を使います。Google Play 用アイコンと、Android ランチャー用の保守的な候補を作れます。

```bash
python scripts/pack_android_icons.py \
  --project-root /path/to/android-project \
  --source docs/images/mieru-source.png \
  --name ic_launcher \
  --legacy \
  --adaptive \
  --round \
  --preview \
  --dry-run
```

`--dry-run` は「実際には書き込まず、何が作られるかだけ確認する」という意味です。初心者はまずこれを実行してください。

### 2. 可能なら foreground と background を分ける

Android Adaptive Icon は、前景と背景が分かれているほうがきれいに作れます。

| Foreground | Background |
| --- | --- |
| <img src="docs/images/mieru-foreground.png" alt="Mieru foreground" width="180"> | <img src="docs/images/mieru-background.png" alt="Mieru background" width="180"> |

実際にアイコンリソースを生成するコマンドです:

```bash
python scripts/pack_android_icons.py \
  --project-root /path/to/android-project \
  --foreground docs/images/mieru-foreground.png \
  --background docs/images/mieru-background.png \
  --name ic_launcher \
  --legacy \
  --adaptive \
  --round \
  --preview \
  --backup
```

`--backup` は、既存のアイコンファイルを置き換える前にバックアップを残す指定です。

### 3. 作られたアイコンを見る

Google Play Store 用アイコンは `512x512` の正方形 PNG です:

<img src="docs/images/mieru-play-store-icon.png" alt="Generated Play Store icon" width="220">

Android のホーム画面では、端末やランチャーによってアイコンが丸、角丸、squircle などに切り抜かれます。下のプレビューで見切れないか確認します。

| Circle | Rounded square | Squircle | Safe zone |
| --- | --- | --- | --- |
| <img src="docs/images/mieru-preview-circle.png" alt="Circle preview" width="140"> | <img src="docs/images/mieru-preview-rounded-square.png" alt="Rounded square preview" width="140"> | <img src="docs/images/mieru-preview-squircle.png" alt="Squircle preview" width="140"> | <img src="docs/images/mieru-preview-safe-zone.png" alt="Safe zone preview" width="140"> |

重要なロゴや文字が赤い安全領域ガイドに近すぎる、または circle preview で消えている場合は、元画像の余白を増やすか、foreground 画像を調整してください。

### 4. リリース前に検証する

アイコン生成後は、次のコマンドで検証します:

```bash
python scripts/validate_android_icons.py \
  --project-root /path/to/android-project \
  --name ic_launcher \
  --strict
```

警告が出た場合は、Google Play にアップロードしたりアプリを公開したりする前に内容を確認してください。

## より良い Adaptive Icon を作るには

可能なら foreground / background / monochrome を分けて渡します:

```bash
python scripts/pack_android_icons.py \
  --project-root /path/to/android-project \
  --foreground /path/to/foreground.png \
  --background "#0F172A" \
  --monochrome /path/to/monochrome.png \
  --name ic_launcher \
  --adaptive \
  --round \
  --preview \
  --backup
```

単一の平坦な PNG からも生成できますが、ロゴと背景を完全には分離できません。その場合、Adaptive Icon の出力は保守的な候補として扱い、リリース前に生成プレビューを必ず目視確認してください。

## 注意

- Google Play Store 用アイコンと Android ランチャーアイコンは別物です。
- Google Play 用アイコンに角丸、外枠、ドロップシャドウを焼き込まないでください。
- Android Adaptive Icon の foreground の重要部分は中央の安全領域内に収める必要があります。
- 実際のリリース前に、生成されたプレビューを必ず目視確認してください。
- アプリプロジェクトへ書き込む前に、まず `--dry-run` を使ってください。

## プロジェクト構成

```text
android-icon-compliance-resizer/
├── SKILL.md
├── requirements.txt
├── scripts/
│   ├── pack_android_icons.py
│   ├── validate_android_icons.py
│   └── generate_icon_previews.py
├── references/
│   └── android_icon_requirements.md
└── examples/
    └── README.md
```

## コントリビュート

Issue や pull request を歓迎します。ローカル開発、テストコマンド、取り組みやすい改善案は [CONTRIBUTING.md](CONTRIBUTING.md) を参照してください。
