# 論文アーギュメント可視化ツール

## 概要

このツールは、学術論文のPDFファイルをアップロードすると、各段落の主張（Claim）と根拠（Evidence）を自動的に抽出し、複数の論文間の共通前提や会話構造を分析・可視化するWebアプリケーションです。Claude AIを活用して、論文間の関係性を探索し、研究の隙間を発見するのに役立ちます。

## 主な機能

- 複数のPDFファイルからテキスト抽出
- 段落ごとの主張・根拠の自動識別
- 論文間の共通前提・理論基盤の分析
- 論文間の会話構造の可視化
- 分析結果のCSVエクスポート
- ネットワークグラフによる論文関係の表示

## インストールと実行方法

### 必要条件

- Python 3.8以上
- Anthropic API キー (Claude)

### 環境のセットアップ

1. リポジトリをクローンまたはダウンロードします。

```bash
git clone https://github.com/yourusername/paper-argument-visualizer.git
cd paper-argument-visualizer
```

2. 必要なパッケージをインストールします。

```bash
pip install -r requirements.txt
```

3. 環境変数に Claude API キーを設定します。

```bash
# Linuxまたは macOS
export CLAUDE_API_KEY="your_api_key_here"

# Windows (コマンドプロンプト)
set CLAUDE_API_KEY=your_api_key_here

# Windows (PowerShell)
$env:CLAUDE_API_KEY="your_api_key_here"
```

### アプリケーションの実行

```bash
streamlit run app.py
```

ブラウザで `http://localhost:8501` にアクセスすると、アプリケーションが表示されます。

## 使い方

1. 「PDFアップロード」タブで、分析したいPDFファイルを複数アップロードします。
2. サイドバーで使用するClaudeモデルやその他の設定を調整します。
3. 「分析開始」ボタンをクリックして処理を開始します。
4. 「分析結果」タブで、段落ごとの主張・根拠の抽出結果を確認します。
5. 「会話構造」タブで、論文間の関係性分析と視覚化されたネットワークグラフを表示します。
6. 必要に応じて結果をCSVファイルやグラフ画像としてダウンロードできます。

## Intel MKLエラーの対処法

アプリケーション実行時に以下のようなエラーが発生した場合:
```
Intel MKL FATAL ERROR: Cannot load libmkl_intel_thread.dylib.
```

以下の対処法を試してください:

### Conda環境を使用している場合:
```bash
conda install nomkl
```

### pip環境を使用している場合:
```bash
pip uninstall numpy
pip install numpy --no-binary numpy
```

### macOS固有の対応:
Intel Macの場合:
```bash
conda install -c conda-forge numpy scipy pandas matplotlib
```

Apple Silicon (M1/M2) Macの場合:
```bash
CONDA_SUBDIR=osx-arm64 conda install -c conda-forge numpy scipy pandas matplotlib
```

### 環境変数の設定:
```bash
export MKL_SERVICE_FORCE_INTEL=1
```
または
```bash
export MKL_THREADING_LAYER=GNU
```

## Streamlit Cloudへのデプロイ

1. GitHubにリポジトリをプッシュします。
2. [Streamlit Cloud](https://streamlit.io/cloud) にアクセスしてログインします。
3. 「New app」をクリックし、GitHubリポジトリを選択します。
4. 「Advanced settings」で以下のシークレットを追加します:
   - `CLAUDE_API_KEY`: your_api_key_here
5. 「Deploy!」ボタンをクリックしてデプロイします。

## ファイル構成

- `app.py` - メインアプリケーションコード
- `README.md` - このドキュメント
- `requirements.txt` - 依存パッケージのリスト
- `.streamlit/config.toml` - Streamlit設定ファイル (オプション)

## 依存パッケージ

- streamlit - Webアプリケーションフレームワーク
- pdfplumber - PDFテキスト抽出
- pandas - データ操作
- anthropic - Claude API連携
- plotly - データ可視化
- networkx - ネットワークグラフ生成
- matplotlib - グラフ描画
- pillow - 画像処理

## 注意事項

- このアプリケーションはClaude APIを使用するため、APIの使用量に応じた課金が発生する可能性があります。
- 処理するPDFファイルの数や大きさによって、実行時間やメモリ使用量が大きく変わります。
- 非常に長い論文や複雑な構造のPDFファイルでは、テキスト抽出の精度が低下する場合があります。

## ライセンス

MIT

## 開発者情報

このアプリケーションは研究者や学術コミュニティのためのツールとして開発されました。改善提案やバグ報告は歓迎します。

バージョン: 1.0.0 (2025-03-25)
