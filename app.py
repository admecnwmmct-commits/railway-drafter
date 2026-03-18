from flask import Flask, request, jsonify, send_from_directory
from groq import Groq
import os

app = Flask(__name__, static_folder='.')

GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)

@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

@app.route('/logo1.gif')
def logo1():
    return send_from_directory('.', 'logo1.gif')

@app.route('/logo2.jpeg')
def logo2():
    return send_from_directory('.', 'logo2.jpeg')

@app.route('/draft', methods=['POST'])
def draft():
    data = request.json
    doc_type     = data.get('doc_type', 'Office Order')
    subject      = data.get('subject', '')
    reference    = data.get('reference', '')
    instructions = data.get('instructions', '')
    addressees   = data.get('addressees', 'All Concerned')
    authority    = data.get('for_officer', 'Sr. DME (Co)/BCT')
    tone         = data.get('tone', 'directive')

    tone_guide = {
        'directive':     'Use firm directive language. Use phrases like "it is hereby ordered", "all concerned are directed to".',
        'advisory':      'Use advisory language. Use phrases like "it is advised", "staff may note".',
        'clarificatory': 'This is a clarification. Use phrases like "it is clarified that", "doubts have been raised regarding".',
        'reminder':      'This is a reminder. Reference earlier instructions and state compliance is still awaited.'
    }

    prompt = f"""You are a senior Indian Railways officer in the C&W section of BCT Division, Western Railway.

Your task is to write ONLY the numbered body paragraphs of a {doc_type}. 

STRICT RULES — you must follow these exactly:
- Write ONLY the numbered paragraphs (1., 2., 2.1 etc.)
- Do NOT include file number, date, subject line, reference line at the top
- Do NOT include signature block at the end
- Do NOT include "Copy to" section at the end
- Do NOT write any heading or title
- Start directly with paragraph 1.
- End with the approval paragraph only (e.g. "3. This issues with the approval of {authority}.")

Document details:
- Type: {doc_type}
- Subject: {subject}
- Reference: {reference}
- Instructions to cover: {instructions}
- Addressed to: {addressees}
- Tone: {tone_guide.get(tone, tone_guide['directive'])}

Write only the numbered body paragraphs now:"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800
        )
        return jsonify({"text": response.choices[0].message.content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("BCT Division C&W Circular Drafter is running!")
    print("Open your browser and go to: http://localhost:5000")
    app.run(debug=False, port=5000)
