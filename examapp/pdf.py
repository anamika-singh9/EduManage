"""Report card PDF generation (ReportLab)."""
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

SCHOOL_NAME = "Seth Anandram Jaipuria School, Ved Campus – Barabanki"


def build_report_card(student, exam, results):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, title=f"Report Card - {student.name}")
    styles = getSampleStyleSheet()
    story = [
        Paragraph(SCHOOL_NAME, styles['Title']),
        Paragraph("Report Card", styles['Heading2']),
        Paragraph(f"<b>Student:</b> {student.name} &nbsp;&nbsp; <b>Roll No:</b> {student.rollno} &nbsp;&nbsp; <b>Class:</b> {student.sclass}", styles['Normal']),
        Paragraph(f"<b>Exam:</b> {exam.name} &nbsp;&nbsp; <b>Date:</b> {exam.exam_date}", styles['Normal']),
        Spacer(1, 16),
    ]
    data = [["Subject", "Marks Obtained", "Max Marks", "Percentage", "Grade"]]
    total = max_total = 0
    for r in results:
        data.append([r.subject_name, f"{r.marks_obtained}", f"{r.max_marks}", f"{r.percentage}%", r.grade])
        total += float(r.marks_obtained)
        max_total += float(r.max_marks)
    overall = round(total / max_total * 100, 2) if max_total else 0
    data.append(["Total", f"{total:g}", f"{max_total:g}", f"{overall}%", ""])
    table = Table(data, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f4f6f7')]),
    ]))
    story += [table, Spacer(1, 24), Paragraph(f"<b>Overall Percentage:</b> {overall}%", styles['Normal'])]
    doc.build(story)
    return buf.getvalue()


def build_fee_receipt(payment):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, title=f"Receipt {payment.receipt_no}")
    styles = getSampleStyleSheet()
    stu = payment.student
    story = [
        Paragraph(SCHOOL_NAME, styles['Title']),
        Paragraph("Fee Receipt", styles['Heading2']),
        Paragraph(f"<b>Receipt No:</b> {payment.receipt_no} &nbsp;&nbsp; <b>Date:</b> {payment.paid_on}", styles['Normal']),
        Spacer(1, 10),
        Paragraph(f"<b>Student:</b> {stu.name} &nbsp;&nbsp; <b>Roll No:</b> {stu.rollno} &nbsp;&nbsp; <b>Class:</b> {stu.sclass}", styles['Normal']),
        Spacer(1, 16),
    ]
    data = [["Description", "Amount"],
            [f"Fee payment ({payment.mode}{' - ' + payment.reference if payment.reference else ''})", f"Rs. {payment.amount}"]]
    if payment.note:
        data.append([payment.note, ""])
    data.append(["Total Paid", f"Rs. {payment.amount}"])
    table = Table(data, hAlign='LEFT', colWidths=[350, 120])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    story += [table, Spacer(1, 20), Paragraph(f"<b>Balance Due:</b> Rs. {stu.duefee}", styles['Normal']),
             Spacer(1, 30), Paragraph("This is a computer-generated receipt.", styles['Normal'])]
    doc.build(story)
    return buf.getvalue()
