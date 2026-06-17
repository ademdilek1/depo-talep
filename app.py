import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# Font Ayarı
FONT_NAME = 'Arial'
if os.path.exists("arial.ttf"):
    pdfmetrics.registerFont(TTFont(FONT_NAME, "arial.ttf"))
else:
    FONT_NAME = 'Helvetica'

def create_pdf(df, firma_adi, sip_no, sip_tar):
    file_name = "talep_formu.pdf"
    doc = SimpleDocTemplate(file_name, pagesize=A4, leftMargin=40, rightMargin=40)
    elements = []
    styles = getSampleStyleSheet()
    
    # Başlık
    title_style = ParagraphStyle('TitleStyle', parent=styles['Title'], fontName=FONT_NAME, fontSize=26, alignment=1)
    elements.append(Paragraph("DEPO TALEP FORMU", title_style))
    elements.append(Spacer(1, 15))
    
    # 2 Sütunlu Bilgi Alanı (Tabloyla hizalı)
    bilgi_data = [
        ["Dgs Dış Ticaret Anonim Şirketi", "Sevk Tarihi:"],
        [f" {firma_adi}", f"Sipariş No: {sip_no}"],
        ["", f"Sipariş Tarihi: {sip_tar}"]
    ]
    
    bilgi_table = Table(bilgi_data, colWidths=[280 , 280])
    bilgi_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(bilgi_table)
    elements.append(Spacer(1, 15))
    
    # Ana Tablo
    headers = ["Stok Kod", "Stok Ad", "Miktar", "Depo Stok", "KG", "Üretici", "Paket", "Palet", "Raf"]
    data = [headers]
    for _, row in df.iterrows():
        data.append([
            str(row.get('Stok Kod', '')), 
            str(row.get('Stok Ad', '')), 
            str(row.get('Miktar', '')), # Miktar verisi burada
            str(row.get('Depo', '')),
            str(row.get('KG', '')), 
            str(row.get('Menşei', '')), 
            "", "", 
            str(row.get('Raf', ''))
        ])
    
    table = Table(data, colWidths=[60, 110, 60, 60, 50, 60, 50, 50, 60])
    table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
    ]))
    elements.append(table)
    doc.build(elements)
    return file_name

# --- ANA UYGULAMA ---
st.title("Depo Talep Oluşturucu")

# EXCEL YÜKLEME KISMI
stok_file = st.file_uploader("Ana Stok Listesini (Excel) Yükle", type=["xlsx"])
talep_kodlari = st.text_area("Talep Edilecek Stok Kodlarını Gir (Örn: A31 5)")

# df_sonuc değişkenini burada boş olarak başlatıyoruz
df_sonuc = pd.DataFrame()

# Eğer dosya yüklendiyse ve kodlar girildiyse işlem yap
if stok_file and talep_kodlari:
    df_stok = pd.read_excel(stok_file)
    df_stok['Stok Kod'] = df_stok['Stok Kod'].astype(str).str.strip()
    
    # Burada talep_kodlari değişkenini kullanıyoruz
    stok_listesi = []
    for satir in talep_kodlari.split("\n"):
        if satir.strip():
            parcalar = satir.split() 
            kod = parcalar[0]
            miktar = parcalar[1] if len(parcalar) > 1 else "1"
            stok_listesi.append({'kod': kod, 'miktar': miktar})
            
    sonuc_listesi = []
    for item in stok_listesi:
        kayit = df_stok[df_stok['Stok Kod'] == item['kod']]
        row = kayit.iloc[0] if not kayit.empty else {}
        sonuc_listesi.append({
            'Stok Kod': item['kod'],
            'Stok Ad': row.get('Stok Adı', ''), 
            'Miktar': item['miktar'], 
            'Depo': row.get('Depo Stok Miktarı', ''), 
            'KG': row.get('Ağırlık', ''), 
            'Menşei': row.get('Menşei', ''), 
            'Raf': row.get('Raf', '')
        })
    df_sonuc = pd.DataFrame(sonuc_listesi)
    st.dataframe(df_sonuc)

    # 3 Adet Textbox
    st.subheader("Form Bilgileri")
    col1, col2, col3 = st.columns(3)
    firma = col1.text_input("Firma Adı", value="FİRMA ADI")
    sip_no = col2.text_input("Sipariş No")
    sip_tar = col3.text_input("Sipariş Tarihi")

    if not df_sonuc.empty and st.button("PDF Oluştur ve İndir"):
        pdf_path = create_pdf(df_sonuc, firma, sip_no, sip_tar)
        with open(pdf_path, "rb") as f:
            st.download_button("PDF Dosyasını İndir", f, file_name="Talep_Formu.pdf")