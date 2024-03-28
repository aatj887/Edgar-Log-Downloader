import tkinter as tk
from tkinter import filedialog, messagebox
import requests
import os
import pandas as pd
import zipfile

# Function to download a ZIP file from a given URL
def download_zip(url, download_folder, filename):
    file_path = os.path.join(download_folder, filename)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-GB,en;q=0.9,en-US;q=0.8',
    }
    with requests.get(url, headers=headers, stream=True) as response:
        if response.status_code == 200:
            os.makedirs(download_folder, exist_ok=True)
            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            return True
        else:
            return False

# Function to process each ZIP file
def process_zip(file_path, cik_list, master_df):
    with zipfile.ZipFile(file_path, 'r') as z:
        csv_filename = os.path.splitext(os.path.basename(file_path))[0] + ".csv"
        with z.open(csv_filename) as csv_file:
            df = pd.read_csv(csv_file, usecols=['date', 'cik'])
            df['cik'] = df['cik'].apply(lambda x: str(x).zfill(10))  # Format CIK with leading zeros
            df_filtered = df[df['cik'].isin(cik_list)]
            cik_counts = df_filtered.groupby(['date', 'cik']).size().reset_index(name='cik_count')
            master_df = pd.concat([master_df, cik_counts], ignore_index=True)
    os.remove(file_path)
    return master_df

# Function to download files from EDGAR and process them
def edgar_file_downloader(date_list, download_folder, cik_list, master_df):
    for date in date_list:
        date_formatted = date.replace("-", "")
        quarter = "Qtr" + str((int(date_formatted[4:6]) - 1) // 3 + 1)
        filename = "log" + date_formatted + ".zip"
        url = f"http://www.sec.gov/dera/data/Public-EDGAR-log-file-data/{date_formatted[:4]}/{quarter}/{filename}"
        if download_zip(url, download_folder, filename):
            file_path = os.path.join(download_folder, filename)
            master_df = process_zip(file_path, cik_list, master_df)
    return master_df

# Main processing function to be called by the GUI
def main_process(download_folder, cik_list, date_list):
    master_df = pd.DataFrame()

    # Assuming dates and CIKs are provided as comma-separated strings
    date_list_formatted = date_list.split(',')
    cik_list = cik_list.split(',')

    master_df = edgar_file_downloader(date_list_formatted, download_folder, cik_list, master_df)

    output_csv_file_path = os.path.join(download_folder, "edgar_cik_searches.csv")
    master_df.to_csv(output_csv_file_path, index=False)
    messagebox.showinfo("Success", f"Data saved to {output_csv_file_path}")

def upload_cik_file(cik_entry):
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("Text files", "*.txt")])
    if file_path:
        with open(file_path, "r") as file:
            cik_list = file.read().replace('\n', ',').strip(',')
            cik_entry.delete(0, tk.END)
            cik_entry.insert(0, cik_list)

def upload_date_file(date_entry):
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("Text files", "*.txt")])
    if file_path:
        with open(file_path, "r") as file:
            date_list = file.read().replace('\n', ',').strip(',')
            date_entry.delete(0, tk.END)
            date_entry.insert(0, date_list)

def gui():
    app = tk.Tk()
    app.title("EDGAR Downloader")

    # Download Folder
    tk.Label(app, text="Download Folder Location:").grid(row=0, sticky=tk.W)
    folder_entry = tk.Entry(app, width=50)
    folder_entry.grid(row=0, column=1)
    tk.Button(app, text="Browse", command=lambda: browse_folder(folder_entry)).grid(row=0, column=2)

    # CIK List
    tk.Label(app, text="CIK Number List (comma-separated or upload):").grid(row=1, sticky=tk.W)
    cik_entry = tk.Entry(app, width=50)
    cik_entry.grid(row=1, column=1)
    tk.Button(app, text="Upload", command=lambda: upload_cik_file(cik_entry)).grid(row=1, column=2)

    # Date List
    tk.Label(app, text="Date List (comma-separated, YYYY-MM-DD or upload):").grid(row=2, sticky=tk.W)
    date_entry = tk.Entry(app, width=50)
    date_entry.grid(row=2, column=1)
    tk.Button(app, text="Upload", command=lambda: upload_date_file(date_entry)).grid(row=2, column=2)

    # Process Button
    tk.Button(app, text="Process", command=lambda: main_process(folder_entry.get(), cik_entry.get(), date_entry.get())).grid(row=3, column=0, columnspan=3)

    app.mainloop()

def browse_folder(entry):
    folder_path = filedialog.askdirectory()
    if folder_path:
        entry.delete(0, tk.END)
        entry.insert(0, folder_path)

if __name__ == "__main__":
    gui()
