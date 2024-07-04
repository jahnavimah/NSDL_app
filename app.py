from flask import Flask, render_template, request
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import os
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Flask app
app = Flask(__name__, static_folder='public/static', template_folder='public/templates')

# Load Firebase credentials from a secure file path
firebase_cred_path = os.path.join(os.getcwd(), 'credentials', 'firebase_credentials.json')
cred = credentials.Certificate(firebase_cred_path)

# Initialize Firebase Admin SDK
firebase_admin.initialize_app(cred)

# Load data from CSV
csv_path = os.path.join('public', 'formatted_file.csv')
df = pd.read_csv(csv_path)
df['combined_date1'] = pd.to_datetime(df['combined_date1'])

# Assuming sectors start from column D to AA
sectors = df.columns[3:29].tolist()
categories = df['Type_main'].unique().tolist()

@app.route('/')
def index():
    return render_template('index.html', sectors=sectors, categories=categories)

@app.route('/plot', methods=['POST'])
def plot():
    selected_sectors = request.form.getlist('sectors')
    selected_type_mains = request.form.getlist('type_mains')
    start_date = pd.to_datetime(request.form['start_date'])
    end_date = pd.to_datetime(request.form['end_date'])

    plots = []

    for selected_type_main in selected_type_mains:
        filtered_data = df[(df['combined_date1'] >= start_date) &
                           (df['combined_date1'] <= end_date) &
                           (df['Type_main'] == selected_type_main)]

        if filtered_data.empty:
            plots.append({
                'plot_base64': None,
                'selected_type_main': selected_type_main,
                'selected_sectors': selected_sectors,
                'message': f'No data available for {selected_type_main} and date range.'
            })
            continue

        fig, ax = plt.subplots(figsize=(10, 6))
        for sector in selected_sectors:
            ax.plot(filtered_data['combined_date1'], filtered_data[sector], marker='o', label=sector)

        ax.set_title(f'Line Plot of {selected_type_main} - {", ".join(selected_sectors)}', fontsize=14)
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Value', fontsize=12)
        ax.tick_params(axis='both', which='major', labelsize=10)

        if (end_date - start_date).days > 30:
            ax.tick_params(axis='both', which='major', labelsize=8)

        ax.legend()

        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        plot_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close(fig)

        plots.append({
            'plot_base64': plot_data,
            'selected_type_main': selected_type_main,
            'selected_sectors': selected_sectors,
            'message': None
        })

    return render_template('plot.html', plots=plots)

if __name__ == '__main__':
    app.run(debug=True)
