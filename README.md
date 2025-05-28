# MediScan - Medical Report Analyzer

![stethoscope_3147004 (1)](https://github.com/user-attachments/assets/edb4f9d2-954c-4dbb-b3c7-da5ea2e58f07)


A Flask-based web application that analyzes medical test reports using OCR (Optical Character Recognition) and provides intelligent insights about your health metrics.

## ✨ Features

- 📄 Upload scanned medical reports (PNG/JPG)
- 🔍 Automatic text extraction using Tesseract OCR
- 📊 Visual analysis of test results
- 💡 Intelligent explanations for abnormal values
- 🩺 Doctor-like recommendations
- 📱 Mobile-friendly interface

## 🖥️ Screenshots

### Dashboard Interfaces
#### Dashboard
![Screenshot 2025-05-28 182525](https://github.com/user-attachments/assets/57b8f4c5-99c3-4b4e-b291-20d763f65d95)
#### Dashboard After Upload
![Screenshot 2025-05-28 182552](https://github.com/user-attachments/assets/18933807-453a-4d88-86fd-b911612ef3c2)

### Analysis Results
#### Rendered Chart
![Screenshot 2025-05-28 182605](https://github.com/user-attachments/assets/93ad12a5-6bf4-44bd-9ca6-b5ac47da0dea)
#### Results with Recommendation 
![Screenshot 2025-05-28 182618](https://github.com/user-attachments/assets/818c7fab-2549-4c8a-af17-4440fd44dea8)


## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- Tesseract OCR ([Installation guide](#tesseract-installation))
- pip

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/MediScan.git
   cd MediScan
2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate  # Windows

4. Install dependencies:
   ```bash
   pip install -r requirements.txt

5. Run the application:
   ```bash
   python app.py

6. Open in browser:
   http://localhost:10000

## 🛠️ Technologies Used

-Python Flask (Backend)

-Tesseract OCR (Text extraction)

-Matplotlib (Visualizations)

-FuzzyWuzzy/RapidFuzz (Text matching)

-HTML/CSS/JavaScript (Frontend)

-Chart.js (Interactive charts)
