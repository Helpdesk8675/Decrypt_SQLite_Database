"""
This will decrypt a encrypted sqlite database, such as signal if you
have the config.json file.  It will add in the WAL file if it is in
the same folder as the encrypted database.  

Grumpy Old Men
https[://]github.com/reineckejd
https[://]github.com/Helpdesk8675

Version: 1.00 12 Jan 25 
"""


import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os
import subprocess
from PIL import Image, ImageTk
from pathlib import Path

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("SQLite Decrypter by the Grumpy Old Men (reineckejd and Helpdesk8675")
        
        # Center the window on screen
        window_width = 600
        window_height = 400
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        self.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

        # Configure grid weights for proper alignment
        self.grid_columnconfigure(1, weight=1)
        
        # Create a frame for the logo
        self.logo_frame = tk.Frame(self)
        self.logo_frame.grid(row=0, column=0, columnspan=3, sticky="e", padx=10, pady=5)

        # Load and display logo
        try:
            logo_path = Path(__file__).parent / "logo.png"
            self.logo = ImageTk.PhotoImage(Image.open(logo_path))
            self.logo_label = tk.Label(self.logo_frame, image=self.logo)
            self.logo_label.pack(side="right")
        except Exception as e:
            print(f"Logo loading error: {e}")

        # Variables to store user selections
        self.db_path = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.config_path = tk.StringVar()
        self.sqlite3_path = tk.StringVar()

        # GUI elements
        self.create_widgets()

    def create_widgets(self):
        # Main content frame
        content_frame = tk.Frame(self)
        content_frame.grid(row=1, column=0, columnspan=3, padx=20, pady=10, sticky="nsew")
        
        # Database Selection
        tk.Label(content_frame, text="Select Encrypted Database:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        tk.Entry(content_frame, textvariable=self.db_path, width=40).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        tk.Button(content_frame, text="Browse", command=self.browse_db).grid(row=0, column=2, padx=5, pady=5)

        # Output Folder Selection
        tk.Label(content_frame, text="Select Output Folder:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        tk.Entry(content_frame, textvariable=self.output_folder, width=40).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        tk.Button(content_frame, text="Browse", command=self.browse_output).grid(row=1, column=2, padx=5, pady=5)

        # Config File Selection
        tk.Label(content_frame, text="Select config.json:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        tk.Entry(content_frame, textvariable=self.config_path, width=40).grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        tk.Button(content_frame, text="Browse", command=self.browse_config).grid(row=2, column=2, padx=5, pady=5)

        # sqlite3.exe Selection
        tk.Label(content_frame, text="Select sqlite3.exe:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        tk.Entry(content_frame, textvariable=self.sqlite3_path, width=40).grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        tk.Button(content_frame, text="Browse", command=self.browse_sqlite3).grid(row=3, column=2, padx=5, pady=5)

        # Decrypt Button
        decrypt_button = tk.Button(content_frame, text="Decrypt Database", command=self.decrypt_database, 
                                 bg="#4CAF50", fg="white", pady=10, padx=20)
        decrypt_button.grid(row=4, column=0, columnspan=3, pady=20)

        # Configure grid weights for content frame
        content_frame.grid_columnconfigure(1, weight=1)

    def browse_db(self):
        file_path = filedialog.askopenfilename(
            title="Select Encrypted Database",
            filetypes=(("SQLite Database", "*.sqlite"), ("All files", "*.*"))
        )
        if file_path:
            self.db_path.set(file_path)

    def browse_output(self):
        folder_path = filedialog.askdirectory(title="Select Output Folder")
        if folder_path:
            self.output_folder.set(folder_path)

    def browse_config(self):
        file_path = filedialog.askopenfilename(
            title="Select config.json",
            filetypes=(("JSON files", "*.json"), ("All files", "*.*"))
        )
        if file_path:
            self.config_path.set(file_path)

    def browse_sqlite3(self):
        file_path = filedialog.askopenfilename(
            title="Select sqlite3.exe",
            filetypes=(("Executable files", "*.exe"), ("All files", "*.*"))
        )
        if file_path:
            self.sqlite3_path.set(file_path)

    def decrypt_database(self):
        # Validate inputs
        if not self._validate_inputs():
            return

        try:
            # Read config file
            with open(self.config_path.get(), 'r') as f:
                config = json.load(f)
                hex_key = config.get('key')  

            if not hex_key:
                raise KeyError("Encryption key not found in config.json")

            # Create temp file path in output directory
            temp_file = Path(self.output_folder.get()) / "temp_decrypt.sql"
            output_db = Path(self.output_folder.get()) / "decrypted.sqlite"

            # Write SQL commands
            with open(temp_file, "w") as f:
                f.write(f"""PRAGMA key = "x'{hex_key}'";
PRAGMA cipher_page_size = 4096;
PRAGMA kdf_iter = 256000;
PRAGMA cipher_hmac_algorithm = HMAC_SHA512;
PRAGMA cipher_kdf_algorithm = PBKDF2_HMAC_SHA512;
PRAGMA cipher_default_plaintext_header_size = 0;
ATTACH DATABASE '{output_db}' as DB1 KEY '';
SELECT sqlcipher_export('DB1');
detach database db1;""")

            # Run sqlite3 command
            command = f'"{self.sqlite3_path.get()}" "{self.db_path.get()}" ".read {temp_file}"'
            process = subprocess.run(command, shell=True, cwd=self.output_folder.get(),
                                  capture_output=True, text=True)
            
            if process.returncode != 0:
                raise Exception(f"SQLite Error: {process.stderr}")

            messagebox.showinfo("Success", "Database decrypted successfully!")
            
        except FileNotFoundError as e:
            messagebox.showerror("Error", f"File not found: {e}")
        except KeyError as e:
            messagebox.showerror("Error", f"Configuration error: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
        finally:
            if temp_file.exists():
                temp_file.unlink()

    def _validate_inputs(self):
        """Validate all input fields."""
        missing = []
        if not self.db_path.get():
            missing.append("Encrypted Database")
        if not self.output_folder.get():
            missing.append("Output Folder")
        if not self.config_path.get():
            missing.append("Config File")
        if not self.sqlite3_path.get():
            missing.append("SQLite3 Executable")

        if missing:
            messagebox.showerror("Error", f"Please select the following:\n- " + "\n- ".join(missing))
            return False
        return True

if __name__ == "__main__":
    app = App()
    app.mainloop()
