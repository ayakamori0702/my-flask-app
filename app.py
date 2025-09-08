import requests
import json
import time
import os
from flask import Flask, render_template, request
import openai
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# OpenAI APIキーの設定
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
openai.api_key = OPENAI_API_KEY

def query_openai(prompt: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
        temperature=0.7
    )
    return response.choices[0].message.content

def analyze_diary(diary_text: str):
    """
    日記のテキストを分析し、感情、アドバイス、四字熟語を抽出します。

    Args:
        diary_text (str): ユーザーが入力した日記のテキスト。

    Returns:
        dict: 感情、アドバイス、四字熟語を含む辞書。
    """
    # OpenAIモデルに送信するプロンプトを構築
    prompt = f"""以下の日記を読んで、筆者の感情を判断し、その感情に合わせたアドバイスと最後に四字熟語を提案してください。

感情の種類は以下の通りです。
1. 悲しい気持ち: しっとりと共感する。
2. 怒りの気持ち: 私以上に怒って私をかばう。
3. やる気に満ちている時: 全力で励まし応援する。
4. 過信している時: 弱点を見抜いて叱咤する。

---
日記：
{diary_text}
---

この日記の感情を上記の種類から判断し、まず「感情: [判断した感情]」と明確に記載してください。
次に、その感情に合わせたアドバイスを生成し、最後に「四字熟語: [提案する四字熟語]」と明確に記載してください。"""

    try:
        generated_text = query_openai(prompt)
        # 生成されたテキストからアドバイス、四字熟語のみをパース
        advice = "アドバイスを抽出できませんでした。"
        idiom = "四字熟語を抽出できませんでした。"

        import re
        # アドバイス抽出
        advice_match = re.search(r"アドバイス:\s*((?:.|\n)*?)(?=\n?四字熟語:|$)", generated_text)
        if advice_match:
            advice = advice_match.group(1).strip()

        # 四字熟語抽出
        idiom_match = re.search(r"四字熟語:\s*(.+?)(?:\n|$)", generated_text)
        if idiom_match:
            idiom = idiom_match.group(1).strip()
        
        # モデルがプロンプトを繰り返す場合の簡単なクリーニング
        if advice.startswith("この日記の感情を上記の種類から判断し、まず「感情:"):
            advice = "モデルからの応答を適切に処理できませんでした。別の表現で日記を試してみてください。"
            idiom = "四字熟語を抽出できませんでした。"

        return {
            "advice": advice,
            "idiom": idiom
        }

    except Exception as e:
        print(f"日記の分析中にエラーが発生しました: {e}")
        return {
            "advice": f"分析中にエラーが発生しました: {e}",
            "idiom": "エラー"
        }

app = Flask(__name__)

# 日記履歴を保存するリスト（本番ではDB推奨）
diary_history = []

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    diary_text = ''
    if request.method == 'POST':
        diary_text = request.form.get('diary_text', '')
        if diary_text:
            result = analyze_diary(diary_text)
            # 履歴に保存
            diary_history.append({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'text': diary_text,
                'result': result
            })
    return render_template('index.html', result=result, diary_text=diary_text, diary_history=reversed(diary_history))

if __name__ == "__main__":
    app.run(debug=True)
