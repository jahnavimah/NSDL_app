from flask import Flask, render_template, request
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import os

# Determine the root directory of the application
root_dir = os.getcwd()
app = Flask(__name__, static_folder=os.path.join(root_dir, 'public', 'static'), template_folder=os.path.join(root_dir, 'public', 'templates'))

# Load data from CSV
csv_path = os.path.join(root_dir, 'public', 'formatted_file.csv')
df = pd.read_csv(csv_path)
df['combined_date1'] = pd.to_datetime(df['combined_date1'])  # Ensure combined_date is in datetime format

# Assuming sectors start from column D to AA
sectors = df.columns[3:29].tolist()  # Adjust the indices if necessary
categories = df['Type_main'].unique().tolist()

@app.route('/')
def index():
    return render_template('index.html', sectors=sectors, categories=categories)

@app.route('/plot', methods=['POST'])
def plot():
    if request.method == 'POST':
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
                ax.plot(filtered_data['formatted_date'], filtered_data[sector], marker='o', label=sector)
            
            ax.set_title(f'Line Plot of {selected_type_main} - {", ".join(selected_sectors)}', fontsize=14)  # Adjust title fontsize
            ax.set_xlabel('', fontsize=12)  # Adjust fontsize for x-axis label
            ax.set_ylabel('', fontsize=12)  # Adjust fontsize for y-axis label
            ax.tick_params(axis='both', which='major', labelsize=10)  # Adjust tick label size

            # Adjust tick label size dynamically based on date range
            if (end_date - start_date).days > 30:
                ax.tick_params(axis='both', which='major', labelsize=8)  # Smaller tick labels for longer date ranges

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

    else:
        return render_template('index.html', sectors=sectors, categories=categories)

if __name__ == '__main__':
    app.run(debug=False)
