#!/usr/bin/env python3
"""
Subtitle Search Tool
A GUI application to search text in subtitle files including embedded MKV subtitles
"""

import os
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading
from typing import List, Tuple
import subprocess
import json
import tempfile
import chardet
import pysubs2


class SubtitleSearchTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Subtitle Search Tool")
        self.root.geometry("900x700")
        
        self.folder_path = ""
        self.subtitle_files = []
        self.search_results = []
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Folder selection
        ttk.Label(main_frame, text="Select Folder:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        folder_frame = ttk.Frame(main_frame)
        folder_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        folder_frame.columnconfigure(0, weight=1)
        
        self.folder_var = tk.StringVar()
        self.folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_var, state="readonly")
        self.folder_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(folder_frame, text="Browse", command=self.browse_folder).grid(row=0, column=1)
        
        # Scan button
        ttk.Button(main_frame, text="Scan Subtitles", command=self.scan_subtitles).grid(row=2, column=0, sticky=tk.W, pady=(0, 10))
        
        # Search section
        search_frame = ttk.Frame(main_frame)
        search_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        search_frame.columnconfigure(1, weight=1)
        
        ttk.Label(search_frame, text="Search:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        self.search_entry.bind('<Return>', lambda e: self.search_text())
        
        ttk.Button(search_frame, text="Search", command=self.search_text).grid(row=0, column=2)
        
        # Case sensitive checkbox
        self.case_sensitive = tk.BooleanVar()
        ttk.Checkbutton(search_frame, text="Case Sensitive", variable=self.case_sensitive).grid(row=0, column=3, padx=(10, 0))
        
        # Results area
        results_frame = ttk.Frame(main_frame)
        results_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # Treeview for results
        self.tree = ttk.Treeview(results_frame, columns=("file", "time", "text"), show="headings")
        self.tree.heading("file", text="File")
        self.tree.heading("time", text="Time")
        self.tree.heading("text", text="Text")
        
        self.tree.column("file", width=200)
        self.tree.column("time", width=100)
        self.tree.column("text", width=500)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(results_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
    def browse_folder(self):
        """Browse and select a folder"""
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path = folder
            self.folder_var.set(folder)
            
    def scan_subtitles(self):
        """Scan the selected folder for subtitle files"""
        if not self.folder_path:
            messagebox.showwarning("Warning", "Please select a folder first")
            return
            
        self.status_var.set("Scanning subtitles...")
        self.root.update()
        
        # Run scan in a separate thread
        thread = threading.Thread(target=self._scan_worker)
        thread.daemon = True
        thread.start()
        
    def _scan_worker(self):
        """Worker thread for scanning subtitles"""
        try:
            self.subtitle_files = []
            subtitle_extensions = {'.srt', '.vtt', '.ass', '.ssa', '.sub', '.sbv', '.ttml'}
            
            # Scan for subtitle files
            for root, dirs, files in os.walk(self.folder_path):
                for file in files:
                    file_path = Path(root) / file
                    
                    # Check for subtitle files
                    if file_path.suffix.lower() in subtitle_extensions:
                        self.subtitle_files.append(str(file_path))
                    
                    # Check for MKV files with embedded subtitles
                    elif file_path.suffix.lower() == '.mkv':
                        embedded_subs = self._extract_mkv_subtitles(str(file_path))
                        self.subtitle_files.extend(embedded_subs)
            
            # Update UI in main thread
            self.root.after(0, self._scan_complete)
            
        except Exception as e:
            self.root.after(0, lambda: self._scan_error(str(e)))
            
    def _extract_mkv_subtitles(self, mkv_path: str) -> List[str]:
        """Extract subtitle tracks from MKV file"""
        try:
            # Use ffprobe to get subtitle stream info
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_streams', '-select_streams', 's', mkv_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return []
                
            data = json.loads(result.stdout)
            streams = data.get('streams', [])
            
            extracted_files = []
            
            for i, stream in enumerate(streams):
                # Create temporary file for extracted subtitle
                temp_dir = tempfile.gettempdir()
                base_name = Path(mkv_path).stem
                codec = stream.get('codec_name', 'unknown')
                
                if codec == 'subrip':
                    ext = '.srt'
                elif codec == 'ass':
                    ext = '.ass'
                elif codec == 'webvtt':
                    ext = '.vtt'
                else:
                    ext = '.srt'  # Default
                
                output_path = os.path.join(temp_dir, f"{base_name}_track{i}{ext}")
                
                # Extract subtitle
                extract_cmd = [
                    'ffmpeg', '-y', '-i', mkv_path, '-map', f'0:s:{i}',
                    '-c', 'copy', output_path
                ]
                
                extract_result = subprocess.run(extract_cmd, capture_output=True)
                if extract_result.returncode == 0 and os.path.exists(output_path):
                    extracted_files.append(output_path)
                    
            return extracted_files
            
        except Exception:
            return []
    
    def _scan_complete(self):
        """Called when scan is complete"""
        count = len(self.subtitle_files)
        self.status_var.set(f"Found {count} subtitle files")
        
    def _scan_error(self, error_msg):
        """Called when scan encounters an error"""
        self.status_var.set("Scan failed")
        messagebox.showerror("Error", f"Failed to scan subtitles: {error_msg}")
        
    def search_text(self):
        """Search for text in subtitle files"""
        search_term = self.search_var.get().strip()
        if not search_term:
            messagebox.showwarning("Warning", "Please enter search text")
            return
            
        if not self.subtitle_files:
            messagebox.showwarning("Warning", "Please scan for subtitles first")
            return
            
        self.status_var.set("Searching...")
        self.root.update()
        
        # Clear previous results
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Run search in a separate thread
        thread = threading.Thread(target=self._search_worker, args=(search_term,))
        thread.daemon = True
        thread.start()
        
    def _search_worker(self, search_term: str):
        """Worker thread for searching"""
        try:
            results = []
            flags = 0 if self.case_sensitive.get() else re.IGNORECASE
            pattern = re.compile(re.escape(search_term), flags)
            
            for subtitle_file in self.subtitle_files:
                file_results = self._search_in_file(subtitle_file, pattern)
                results.extend(file_results)
                
            # Update UI in main thread
            self.root.after(0, lambda: self._search_complete(results))
            
        except Exception as e:
            self.root.after(0, lambda: self._search_error(str(e)))
            
    def _search_in_file(self, file_path: str, pattern) -> List[Tuple[str, str, str]]:
        """Search for pattern in a subtitle file"""
        results = []
        
        try:
            # Detect encoding
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                encoding_result = chardet.detect(raw_data)
                encoding = encoding_result.get('encoding', 'utf-8')
            
            # Parse subtitle file
            subs = pysubs2.load(file_path, encoding=encoding)
            
            for line in subs:
                if pattern.search(line.text):
                    # Format time
                    start_time = self._format_time(line.start)
                    
                    # Get relative file path
                    rel_path = os.path.relpath(file_path, self.folder_path)
                    
                    results.append((rel_path, start_time, line.text.strip()))
                    
        except Exception:
            # If pysubs2 fails, try simple text search
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                if pattern.search(content):
                    rel_path = os.path.relpath(file_path, self.folder_path)
                    results.append((rel_path, "--:--:--", "Text found (format not parsed)"))
                    
            except Exception:
                pass
                
        return results
    
    def _format_time(self, milliseconds: int) -> str:
        """Format time in milliseconds to HH:MM:SS"""
        seconds = milliseconds // 1000
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def _search_complete(self, results: List[Tuple[str, str, str]]):
        """Called when search is complete"""
        # Add results to tree
        for file_path, time, text in results:
            self.tree.insert("", "end", values=(file_path, time, text))
            
        count = len(results)
        self.status_var.set(f"Found {count} matches")
        
    def _search_error(self, error_msg):
        """Called when search encounters an error"""
        self.status_var.set("Search failed")
        messagebox.showerror("Error", f"Search failed: {error_msg}")


def main():
    """Main function"""
    root = tk.Tk()
    app = SubtitleSearchTool(root)
    root.mainloop()


if __name__ == "__main__":
    main() 