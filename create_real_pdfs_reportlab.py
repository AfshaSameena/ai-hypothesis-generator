# create_real_pdfs_reportlab.py
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def make_pdf(path, title, authors, paragraphs, table_data=None):
    doc = SimpleDocTemplate(str(path), pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=72)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"<b>{title}</b>", styles["Title"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"<i>{authors}</i>", styles["Normal"]))
    story.append(Spacer(1, 12))

    for p in paragraphs:
        story.append(Paragraph(p, styles["BodyText"]))
        story.append(Spacer(1, 8))

    if table_data:
        # table_data should be a list of lists (rows)
        t = Table(table_data, hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f2f2f2")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ]))
        story.append(Spacer(1, 12))
        story.append(t)

    doc.build(story)
    print(f"Created PDF: {path}")


if __name__ == "__main__":
    # Sample PDF A: shows increase
    title_a = "Study A — Effect of Treatment Y on Biomarker X"
    authors_a = "A. Researcher et al."
    paras_a = [
        "Abstract: In a cohort of n=40 intermediate-stage patients, we observed that Biomarker X increases after treatment Y (mean change +2.3, p=0.02). Measurements used ELISA.",
        "Introduction: This is a sample paper to demonstrate PDF parsing in the AI Hypothesis Generator prototype.",
        "Results: Biomarker X increased significantly in the treated cohort compared with baseline."
    ]
    table_a = [
        ["Group", "n", "Mean change", "p-value"],
        ["Treated (intermediate)", "40", "+2.3", "0.02"],
        ["Control", "40", "+0.1", "0.80"]
    ]
    make_pdf("sample_real_studyA.pdf", title_a, authors_a, paras_a, table_a)

    # Sample PDF B: no significant change
    title_b = "Study B — Observational Study of Biomarker X"
    authors_b = "B. Investigator et al."
    paras_b = [
        "Abstract: In a larger cohort of n=120 (mixed disease stages), measurements using a multiplex assay demonstrated no significant change in Biomarker X after treatment Y (p=0.40).",
        "Methods: Cohort included patients across early, intermediate and advanced stages; assays and sampling times varied.",
        "Results: No statistically significant change observed in pooled analyses."
    ]
    table_b = [
        ["Group", "n", "Mean change", "p-value"],
        ["Mixed (pooled)", "120", "+0.05", "0.40"]
    ]
    make_pdf("sample_real_studyB.pdf", title_b, authors_b, paras_b, table_b)
