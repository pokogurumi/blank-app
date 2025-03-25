import streamlit as st
import pdfplumber
import pandas as pd
import anthropic
import tempfile
import os
from datetime import datetime
import plotly.express as px
import networkx as nx
import matplotlib.pyplot as plt
import io
import re
from PIL import Image

# APIキーの設定 - Streamlitのシークレットから読み込む
# デプロイ時はst.secrets["CLAUDE_API_KEY"]の形式で使用
# ローカル開発時は環境変数を使用
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY") or st.secrets.get("CLAUDE_API_KEY", "YOUR_CLAUDE_API_KEY")

# アプリの設定
st.set_page_config(
    page_title="論文アーギュメント可視化ツール", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# サイドバーの設定
with st.sidebar:
    st.title("⚙️ 設定")
    model_option = st.selectbox(
        "使用するモデル",
        ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"]
    )
    temperature = st.slider("温度（創造性）", 0.0, 1.0, 0.3, 0.1)
    max_tokens = st.slider("最大トークン数", 500, 4000, 1024, 100)
    st.divider()
    st.markdown("### 📊 分析オプション")
    extract_claims = st.checkbox("主張・根拠を抽出", value=True)
    analyze_conversation = st.checkbox("会話構造を分析", value=True)
    visualize_network = st.checkbox("ネットワーク図を生成", value=True)
    st.divider()
    st.markdown("### 🛠️ 開発者情報")
    st.info("バージョン: 1.0.0 (2025-03-25)")

# メイン画面
st.title("📚 論文会話構造マッピング・ツール")
st.markdown("""
このツールでは、PDF論文をアップロードすると、各段落の主張・根拠を抽出し、
さらに複数の論文間の共通前提や会話構造をClaudeによって解析・表示します。

**使い方:**
1. 複数のPDFファイルをアップロード
2. 「分析開始」ボタンをクリック
3. 結果を確認し、必要に応じてCSVやグラフをダウンロード
""")

# タブの設定
tab1, tab2, tab3 = st.tabs(["📄 PDFアップロード", "📝 分析結果", "🔍 会話構造"])

with tab1:
    uploaded_files = st.file_uploader("PDFファイルを複数アップロード", type=["pdf"], accept_multiple_files=True)
    
    if uploaded_files:
        file_info = []
        for file in uploaded_files:
            file_info.append({
                "ファイル名": file.name,
                "サイズ": f"{file.size / 1024:.1f} KB"
            })
        st.table(pd.DataFrame(file_info))
        
        if st.button("🔍 分析開始", use_container_width=True):
            all_paragraphs = []
            
            # プログレスバーの表示
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # PDFからテキスト抽出
            for i, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"PDF処理中: {uploaded_file.name}")
                
                try:
                    with pdfplumber.open(uploaded_file) as pdf:
                        full_text = "\n".join([page.extract_text() or "" for page in pdf.pages])
                        
                    # パラグラフに分割（改良版）
                    paragraphs = []
                    for p in re.split(r'\n{2,}', full_text):
                        # 短すぎる行や参考文献のような行は除外
                        p = p.strip()
                        if len(p) > 50 and not p.startswith("References") and not re.match(r'^[\d\s\.]+$', p):
                            paragraphs.append(p)
                    
                    for j, para in enumerate(paragraphs):
                        all_paragraphs.append({
                            "source": uploaded_file.name,
                            "paragraph_id": f"{uploaded_file.name}-p{j+1}",
                            "text": para,
                            "char_count": len(para)
                        })
                except Exception as e:
                    st.error(f"エラー ({uploaded_file.name}): {str(e)}")
                
                # 進捗更新
                progress_bar.progress((i + 1) / len(uploaded_files) / 2)  # 全体の50%をPDF処理に
            
            # セッションに保存
            st.session_state.all_paragraphs = all_paragraphs
            
            # Claudeでの分析
            if extract_claims and len(all_paragraphs) > 0:
                try:
                    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
                    
                    for i, p in enumerate(all_paragraphs):
                        status_text.text(f"段落分析中 ({i+1}/{len(all_paragraphs)}): {p['paragraph_id']}")
                        
                        prompt = f"""
あなたはアカデミック・ライティングの専門家です。
以下の段落から、主張（Claim）と根拠（Evidence）を抽出してください。
文章に主張や根拠が明確に含まれていない場合は「特定できません」と記入してください。

段落:
"""
{p['text']}
"""

出力形式（必ずこの形式で出力してください）:
- 主張: （主張の内容または「特定できません」）
- 根拠: （根拠の内容または「特定できません」）
"""
                        try:
                            response = client.messages.create(
                                model=model_option,
                                max_tokens=max_tokens,
                                temperature=temperature,
                                messages=[{"role": "user", "content": prompt}]
                            )
                            p["analysis"] = response.content[0].text.strip()
                        except Exception as e:
                            p["analysis"] = f"Error: {e}"
                        
                        # 進捗更新（残りの50%を分析に）
                        progress_value = 0.5 + ((i + 1) / len(all_paragraphs) / 2)
                        progress_bar.progress(min(progress_value, 1.0))
                    
                    # 会話構造の分析
                    if analyze_conversation:
                        status_text.text("会話構造を分析中...")
                        
                        grouped_by_source = {}
                        for p in all_paragraphs:
                            grouped_by_source.setdefault(p["source"], []).append(p)
                            
                        combined_summaries = ""
                        for src, paras in grouped_by_source.items():
                            combined_summaries += f"\n--- 論文: {src} ---\n"
                            # 各論文から最大5段落を使用
                            for p in paras[:5]:
                                combined_summaries += f"- {p.get('analysis', '分析なし')}\n"
                        
                        conversation_prompt = f"""
以下は複数の論文における主張と根拠の抜粋です。
これらの文献が共通して前提としている理論・発想・問題設定について詳しく分析してください。
また、それらに対して新しい主張が介入する余地があるか、どのように「会話の構造を更新」できるかを具体的に提案してください。

分析項目:
1. 共通の前提・理論基盤
2. 対立する主張点
3. 未探索の領域・研究の隙間
4. 会話構造の更新可能性

{combined_summaries}

出力は箇条書きではなく、各セクションごとに段落形式で詳細に記述してください。
"""
                        try:
                            convo_response = client.messages.create(
                                model=model_option,
                                max_tokens=max_tokens * 2,
                                temperature=temperature,
                                messages=[{"role": "user", "content": conversation_prompt}]
                            )
                            st.session_state.conversation_analysis = convo_response.content[0].text.strip()
                        except Exception as e:
                            st.session_state.conversation_analysis = f"分析中にエラーが発生しました: {str(e)}"
                
                except Exception as e:
                    st.error(f"Claude APIエラー: {str(e)}")
                    if "invalid_api_key" in str(e).lower():
                        st.warning("APIキーが無効または未設定です。Streamlitのシークレットまたは環境変数で正しいAPIキーを設定してください。")
            
            # 処理完了
            progress_bar.progress(1.0)
            status_text.text("✅ 分析完了")
            
            # 結果表示タブに切り替え
            st.session_state.active_tab = "分析結果"
            st.experimental_rerun()

with tab2:
    if hasattr(st.session_state, "all_paragraphs") and len(st.session_state.all_paragraphs) > 0:
        result_df = pd.DataFrame(st.session_state.all_paragraphs)
        
        # フィルタオプション
        col1, col2 = st.columns(2)
        with col1:
            source_filter = st.multiselect(
                "論文で絞り込み",
                options=sorted(result_df["source"].unique()),
                default=sorted(result_df["source"].unique())
            )
        with col2:
            min_length = st.slider("最小文字数", 0, 1000, 50, 10)
            
        # フィルタを適用
        filtered_df = result_df[
            (result_df["source"].isin(source_filter)) &
            (result_df["char_count"] >= min_length)
        ]
        
        # 結果表示
        if "analysis" in filtered_df.columns:
            st.dataframe(
                filtered_df[["paragraph_id", "source", "char_count", "analysis"]],
                use_container_width=True,
                height=400,
                column_config={
                    "paragraph_id": "段落ID",
                    "source": "論文",
                    "char_count": "文字数",
                    "analysis": "主張・根拠分析"
                }
            )
            
            # エクスポートオプション
            col1, col2 = st.columns(2)
            with col1:
                csv = filtered_df.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    "📥 CSVをダウンロード", 
                    csv, 
                    f"analysis_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", 
                    "text/csv",
                    use_container_width=True
                )
            
            with col2:
                # データを可視化
                if "analysis" in filtered_df.columns:
                    # 主張と根拠の数を計算（簡易版）
                    claims_count = filtered_df["analysis"].str.contains("主張:").sum()
                    evidence_count = filtered_df["analysis"].str.contains("根拠:").sum()
                    has_both = filtered_df["analysis"].str.contains("主張:") & filtered_df["analysis"].str.contains("根拠:")
                    both_count = has_both.sum()
                    
                    chart_data = pd.DataFrame({
                        "要素": ["主張のみ", "根拠のみ", "主張と根拠"],
                        "数": [claims_count - both_count, evidence_count - both_count, both_count]
                    })
                    
                    fig = px.bar(chart_data, x="要素", y="数", title="段落の分析結果")
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("主張・根拠の分析がまだ行われていません。")
    else:
        st.info("PDFファイルをアップロードして分析を開始してください。")

with tab3:
    if hasattr(st.session_state, "conversation_analysis"):
        st.markdown("### 🗣 論文間の会話構造分析")
        st.markdown(st.session_state.conversation_analysis)
        
        if hasattr(st.session_state, "all_paragraphs") and len(st.session_state.all_paragraphs) > 0 and visualize_network:
            st.markdown("### 🕸 論文関係ネットワーク図")
            
            try:
                # ネットワークグラフの作成
                G = nx.Graph()
                
                # 論文をノードとして追加
                sources = [p["source"] for p in st.session_state.all_paragraphs]
                unique_sources = list(set(sources))
                
                for source in unique_sources:
                    G.add_node(source, type="paper")
                
                # もし論文が2つ以上あれば、関連性を簡易的に作成
                if len(unique_sources) >= 2:
                    for i in range(len(unique_sources)):
                        for j in range(i+1, len(unique_sources)):
                            G.add_edge(unique_sources[i], unique_sources[j], weight=1)
                
                # グラフの描画
                plt.figure(figsize=(10, 8))
                pos = nx.spring_layout(G, seed=42)
                
                nx.draw_networkx_nodes(G, pos, 
                                    node_size=2000, 
                                    node_color='skyblue')
                
                nx.draw_networkx_edges(G, pos, width=2, alpha=0.7)
                nx.draw_networkx_labels(G, pos, font_size=12, font_family='sans-serif')
                
                plt.axis('off')
                
                # 画像をバッファに保存
                buf = io.BytesIO()
                plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
                buf.seek(0)
                
                # 画像を表示
                st.image(buf, caption='論文関係ネットワーク図', use_column_width=True)
                
                # ダウンロードボタン
                btn = st.download_button(
                    label="📥 ネットワーク図をダウンロード",
                    data=buf,
                    file_name=f"network_graph_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                    mime="image/png",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"ネットワーク図の生成中にエラーが発生しました: {str(e)}")
    else:
        st.info("会話構造の分析がまだ行われていません。")

# もしアクティブタブの指定があれば、そのタブに移動
if hasattr(st.session_state, "active_tab"):
    if st.session_state.active_tab == "分析結果":
        # 注: 実際のタブの遷移はStreamlitの制約上、ここでは直接制御できません
        pass
