import tkinter as tk
from tkinter import filedialog
from tkinter import END
from tkinter import *
from tkinter import ttk
from datetime import datetime
import PyPDF2
import cv2
import pytesseract
import re
import mysql.connector
import os

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="tashu@123",
  database="invoices"
)

similar_words = {
    "Invoice Number": ["invoice no.", "invoice num", "number" ,"Invoice Number","Invoice","INVOICE TO","LIC Order Number"],
    "Date": ["dated", "invoice date","DATE","date","Date","Dated"],
    "Total Amount": ["total", "amount", "invoice total","Total Amount","Taal","Total","TOTAL","SUBTOTAL","Payment Amount(Rs.)"],
    
}
def extract_data():
    file_n = entry_file_name.get()
    file_path = entry_file_path.get()
    file_extension = os.path.splitext(file_path)[1]


    if file_extension.lower() == ".pdf":
    
        with open(file_path, 'rb') as file:
            pdf = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf.pages:
                text += page.extract_text()
                print(text)
    else:
        pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'
        image = cv2.imread(file_path)
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(gray_image)
        print(text)
    
    field_names = {
    "Invoice Number": r'Invoice Number\s*(\w+)',
    "Date": r'Dated\s*(\d{2}/\d{2}/\d{4})',
    "Total Amount": r'Total\s*\$([\d.,]+)',
    
}
    extracted_data = {}

    for field_name, regex in field_names.items():
        match = re.search(regex, text, re.IGNORECASE)
        value = match.group(1) if match else None
        if value is None:
            
            similar_words_list = similar_words.get(field_name)
            if similar_words_list:
                for word in similar_words_list:
                    match = re.search(rf'{word}\s*([\d.,:$/]+)', text, re.IGNORECASE)
                    value = match.group(1) if match else None
                    if value:
                        break
        extracted_data[field_name] = value
        
        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

    entry_field_value.delete(0, END)
    for field_name, value in extracted_data.items():
        entry_field_value.insert(0, field_name + ": " + str(value) + "\n")
    for field_name, value in extracted_data.items():
        if value is None:
            label_message.config(text=f"Information not found for field: {field_name}")
            
    mycursor = mydb.cursor()
    sql = "INSERT INTO invoice (file_name,invoice_number, date, total_amount,added_datetime) VALUES (%s,%s, %s, %s,%s)"
    val = (file_n,extracted_data.get("Invoice Number"), extracted_data.get("Date"), extracted_data.get("Total Amount"),formatted_datetime)
    mycursor.execute(sql, val)
    mydb.commit()

    for field_name, value in extracted_data.items():
        print(field_name + ":", value)

def select_invoice_file():
    file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg"),("PDF Files", "*.pdf")])
    entry_file_path.delete(0, tk.END)
    entry_file_path.insert(0, file_path)

    file_name = os.path.basename(file_path)
    entry_file_name.delete(0, tk.END)
    entry_file_name.insert(0, file_name)

def fetch_data():
    mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="tashu@123",
    database="invoices"
    )
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM invoice")
    rows = mycursor.fetchall()
    for row in tree.get_children():
        tree.delete(row)
    
    for row in rows:
        tree.insert('', 'end', values=row)

    mycursor.close()
    mydb.close()


window = tk.Tk()
window.title("Invoice Data Extraction")
window.geometry("1100x700")

label_file_path = tk.Label(window, text="Invoice File:")
label_file_path.pack()
entry_file_path = tk.Entry(window, width=50)
entry_file_path.pack()
button_browse = tk.Button(window, text="Browse", command=select_invoice_file)
button_browse.pack()

label_file_name = tk.Label(window, text="File Name:")
label_file_name.pack()
entry_file_name = tk.Entry(window, width=50)
entry_file_name.pack()

label_field_value = tk.Label(window, text="Field value:")
label_field_value.pack()
entry_field_value = tk.Entry(window, width=50)
entry_field_value.pack()

button_extract = tk.Button(window, text="Extract", command=extract_data)
button_extract.pack()

label_message = tk.Label(window)
label_message.pack()

label_table = tk.Label(window, text="Database Table:")
label_table.pack()

tree = ttk.Treeview(window, columns=("#1", "#2", "#3","#4","#5"))
tree.heading("#1", text="invoice_number")  
tree.heading("#2", text="date")  
tree.heading("#3", text="total_amount")
tree.heading("#4", text="file_name")
tree.heading("#5", text="Date_Time")
tree.column("#0", width=0)
tree.pack()
fetch_button =tk.Button(window, text="Fetch Data", command=fetch_data)
fetch_button.pack()

window.mainloop()
    
