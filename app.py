from flask import Flask, request, jsonify, send_from_directory, send_file
from groq import Groq
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os
import io

app = Flask(__name__, static_folder='.')

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
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
    data         = request.json
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

STRICT RULES:
- Write ONLY the numbered paragraphs (1., 2., 2.1 etc.)
- Do NOT include file number, date, subject line, reference line at the top
- Do NOT include signature block at the end
- Do NOT include Copy to section at the end
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


@app.route('/download', methods=['POST'])
def download():
    data       = request.json
    file_no    = data.get('file_no', '')
    date       = data.get('date', '')
    addressees = data.get('addressees', '')
    subject    = data.get('subject', '')
    reference  = data.get('reference', '')
    body       = data.get('body', '')
    signed_by  = data.get('signed_by', 'ADME (C&W)/BCT')
    for_off    = data.get('for_officer', 'Sr. DME (Co)/BCT')
    copy_to    = data.get('copy_to', '')

    doc = Document()

    # Page margins
    for section in doc.sections:
        section.top_margin    = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin   = Inches(1.0)
        section.right_margin  = Inches(1.0)

    # Header table with logos and title
    header_table = doc.add_table(rows=1, cols=3)
    header_table.autofit = False
    header_table.columns[0].width = Inches(1.2)
    header_table.columns[1].width = Inches(4.1)
    header_table.columns[2].width = Inches(1.2)

    # Left logo
    left_cell = header_table.cell(0, 0)
    left_para = left_cell.paragraphs[0]
    left_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    try:
        run = left_para.add_run()
        run.add_picture('logo1.gif', width=Inches(0.9))
    except:
        left_para.add_run('WR')

    # Center text
    center_cell = header_table.cell(0, 1)
    center_cell.paragraphs[0].clear()

    p_hindi = center_cell.add_paragraph('पश्चिम रेलवे')
    p_hindi.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p_hindi.runs[0]; r.font.size = Pt(16); r.font.bold = True

    p_eng = center_cell.add_paragraph('WESTERN RAILWAY')
    p_eng.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p_eng.runs[0]; r.font.size = Pt(15); r.font.bold = True

    p_div = center_cell.add_paragraph('मंडल कार्यालय  |  Divisional Office')
    p_div.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_div.runs[0].font.size = Pt(11)

    p_addr = center_cell.add_paragraph('मुंबई सेंट्रल, मुंबई–400008  |  Mumbai Central, Mumbai-400008')
    p_addr.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_addr.runs[0].font.size = Pt(9)

    # Right logo
    right_cell = header_table.cell(0, 2)
    right_para = right_cell.paragraphs[0]
    right_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    try:
        run = right_para.add_run()
        run.add_picture('logo2.jpeg', width=Inches(0.9))
    except:
        right_para.add_run('IR')

    doc.add_paragraph('')

    # File No and Date
    p_file = doc.add_paragraph()
    run_no = p_file.add_run(f'No. M/{file_no}')
    run_no.font.size = Pt(11)
    p_file.add_run('\t\t\t\t\t')
    run_date = p_file.add_run(f'Date: {date}')
    run_date.font.size = Pt(11)

    doc.add_paragraph('')

  # Addressed To — each on separate line
    if addressees:
        addr_lines = [a.strip() for a in addressees.split('||') if a.strip()]
        for addr_line in addr_lines:
            p_to = doc.add_paragraph()
            p_to.add_run(addr_line).font.size = Pt(11)

    doc.add_paragraph('')

    # Subject
    p_sub = doc.add_paragraph()
    run_sub = p_sub.add_run(f'Subject: {subject}')
    run_sub.font.size = Pt(11)
    run_sub.font.bold = True

    # Reference
    if reference:
        p_ref = doc.add_paragraph()
        run_ref = p_ref.add_run(f'Reference: {reference}')
        run_ref.font.size = Pt(11)

    doc.add_paragraph('')

    # Body paragraphs
    for line in body.split('\n'):
        if line.strip():
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            run = p.add_run(line)
            run.font.size = Pt(11)
        else:
            doc.add_paragraph('')

    doc.add_paragraph('')
    doc.add_paragraph('')

    # Signature
    p_sig1 = doc.add_paragraph()
    p_sig1.add_run(signed_by).font.size = Pt(11)

    p_sig2 = doc.add_paragraph()
    p_sig2.add_run(f'For {for_off}').font.size = Pt(11)

    doc.add_paragraph('')

    # Copy To
    if copy_to:
        p_ct = doc.add_paragraph()
        r = p_ct.add_run('Copy to:')
        r.font.size = Pt(11)
        r.font.bold = True
        for line in copy_to.split('\n'):
            if line.strip():
                p_copy = doc.add_paragraph()
                p_copy.add_run(line.strip()).font.size = Pt(11)

    # Save to buffer
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    filename = f"BCT_CW_{subject[:30].replace(' ','_')}.docx"
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )


if __name__ == '__main__':
    print("BCT Division C&W Circular Drafter is running!")
    print("Open your browser and go to: http://localhost:5000")
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
