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
from typing import List, Tuple, Dict, Optional
import subprocess
import json
import tempfile
import chardet
import pysubs2
import platform
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from dataclasses import dataclass


@dataclass
class SubtitleLine:
    """Cached subtitle line data"""
    start_ms: int
    text: str
    
@dataclass
class CachedSubtitle:
    """Cached subtitle file data"""
    file_path: str
    lines: List[SubtitleLine]
    last_modified: float


class SubtitleSearchTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Subtitle Search Tool")
        self.root.geometry("900x700")
        
        self.folder_path = ""
        self.subtitle_files = []
        self.search_results = []
        # Map subtitle file to original video file and track info
        self.subtitle_to_video_map: Dict[str, Dict] = {}
        # Map tree item IDs to start times in milliseconds
        self.item_start_times: Dict[str, int] = {}
        # Cache for parsed subtitle files
        self.subtitle_cache: Dict[str, CachedSubtitle] = {}
        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        self.setup_ui()
        
        # Bind cleanup to window close event
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
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
        
        # Bind double-click event for jumping to video
        self.tree.bind("<Double-1>", self.on_result_double_click)
        
        # Right-click context menu
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Jump to Video", command=self.jump_to_video)
        self.tree.bind("<Button-2>", self.show_context_menu)  # macOS right-click
        self.tree.bind("<Button-3>", self.show_context_menu)  # Windows/Linux right-click
        
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
        
        # Instructions
        instructions = ttk.Label(main_frame, 
                               text="Double-click or right-click search results to jump to video position",
                               font=("TkDefaultFont", 9))
        instructions.grid(row=6, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))
        
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
            
        # Clear cache when scanning new folder
        self._clear_cache()
        
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
            self.subtitle_to_video_map = {}
            subtitle_extensions = {'.srt', '.vtt', '.ass', '.ssa', '.sub', '.sbv', '.ttml'}
            
            # Scan for subtitle files
            for root, dirs, files in os.walk(self.folder_path):
                for file in files:
                    file_path = Path(root) / file
                    
                    # Check for subtitle files
                    if file_path.suffix.lower() in subtitle_extensions:
                        subtitle_file = str(file_path)
                        self.subtitle_files.append(subtitle_file)
                        # Map standalone subtitle to itself
                        self.subtitle_to_video_map[subtitle_file] = {
                            'original_file': subtitle_file,
                            'is_extracted': False,
                            'track_index': -1
                        }
                    
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
                
                # Get language info if available
                tags = stream.get('tags', {})
                language = tags.get('language', f'track{i}')
                title = tags.get('title', '')
                
                # Create descriptive filename
                track_info = f"_{language}"
                if title:
                    track_info += f"_{title}"
                
                output_path = os.path.join(temp_dir, f"{base_name}{track_info}{ext}")
                
                # Extract subtitle
                extract_cmd = [
                    'ffmpeg', '-y', '-i', mkv_path, '-map', f'0:s:{i}',
                    '-c', 'copy', output_path
                ]
                
                extract_result = subprocess.run(extract_cmd, capture_output=True)
                if extract_result.returncode == 0 and os.path.exists(output_path):
                    extracted_files.append(output_path)
                    
                    # Map extracted subtitle to original video
                    self.subtitle_to_video_map[output_path] = {
                        'original_file': mkv_path,
                        'is_extracted': True,
                        'track_index': i,
                        'language': language,
                        'title': title
                    }
                    
            return extracted_files
            
        except Exception:
            return []
    
    def _scan_complete(self):
        """Called when scan is complete"""
        count = len(self.subtitle_files)
        self.status_var.set(f"Found {count} subtitle files")
        
        # Pre-load subtitle files in background for faster searching
        if count > 0:
            self.status_var.set(f"Found {count} subtitle files - Pre-loading...")
            threading.Thread(target=self._preload_subtitles, daemon=True).start()
        
    def _preload_subtitles(self):
        """Pre-load subtitle files for faster searching"""
        try:
            loaded = 0
            for subtitle_file in self.subtitle_files:
                self._get_cached_subtitle(subtitle_file)
                loaded += 1
                # Update status periodically
                if loaded % 5 == 0:
                    self.root.after(0, lambda: self.status_var.set(
                        f"Pre-loaded {loaded}/{len(self.subtitle_files)} files"))
            
            self.root.after(0, lambda: self.status_var.set(
                f"Found {len(self.subtitle_files)} subtitle files - Ready for fast search"))
        except Exception as e:
            print(f"Error pre-loading subtitles: {e}")
            self.root.after(0, lambda: self.status_var.set(
                f"Found {len(self.subtitle_files)} subtitle files"))
    
    def _get_cached_subtitle(self, file_path: str) -> Optional[CachedSubtitle]:
        """Get cached subtitle or parse and cache it"""
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return None
                
            file_mtime = os.path.getmtime(file_path)
            
            # Check cache
            if file_path in self.subtitle_cache:
                cached = self.subtitle_cache[file_path]
                if cached.last_modified >= file_mtime:
                    return cached
            
            # Parse and cache the file
            lines = []
            
            # Detect encoding once
            with open(file_path, 'rb') as f:
                raw_data = f.read(8192)  # Read first 8KB for encoding detection
                encoding_result = chardet.detect(raw_data)
                encoding = encoding_result.get('encoding', 'utf-8')
            
            # Parse subtitle file
            subs = pysubs2.load(file_path, encoding=encoding)
            
            for line in subs:
                lines.append(SubtitleLine(
                    start_ms=line.start,
                    text=line.text.strip()
                ))
            
            # Cache the result
            cached_subtitle = CachedSubtitle(
                file_path=file_path,
                lines=lines,
                last_modified=file_mtime
            )
            self.subtitle_cache[file_path] = cached_subtitle
            
            return cached_subtitle
            
        except Exception as e:
            print(f"Error parsing subtitle file {file_path}: {e}")
            return None
    
    def _clear_cache(self):
        """Clear subtitle cache"""
        self.subtitle_cache.clear()
    
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
            
        self.status_var.set(f"Searching '{search_term}' in {len(self.subtitle_files)} files...")
        self.root.update()
        
        # Clear previous results
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Clear previous timing data
        self.item_start_times.clear()
            
        # Run search in a separate thread
        thread = threading.Thread(target=self._search_worker, args=(search_term,))
        thread.daemon = True
        thread.start()
        
    def _search_worker(self, search_term: str):
        """Worker thread for searching with parallel processing"""
        try:
            start_time = time.time()
            results = []
            flags = 0 if self.case_sensitive.get() else re.IGNORECASE
            pattern = re.compile(re.escape(search_term), flags)
            
            # Use parallel processing for faster search
            search_tasks = []
            
            # Submit search tasks to thread pool
            with ThreadPoolExecutor(max_workers=4) as executor:
                for subtitle_file in self.subtitle_files:
                    future = executor.submit(self._search_in_file_cached, subtitle_file, pattern)
                    search_tasks.append(future)
                
                # Collect results as they complete
                for future in as_completed(search_tasks):
                    try:
                        file_results = future.result()
                        results.extend(file_results)
                    except Exception as e:
                        print(f"Error searching file: {e}")
            
            search_time = time.time() - start_time
            print(f"Search completed in {search_time:.2f} seconds")
            
            # Update UI in main thread
            self.root.after(0, lambda: self._search_complete(results))
            
        except Exception as e:
            self.root.after(0, lambda: self._search_error(str(e)))
    
    def _search_in_file_cached(self, file_path: str, pattern) -> List[Tuple[str, str, str, int]]:
        """Search for pattern in a cached subtitle file"""
        results = []
        
        # Try to get cached subtitle first
        cached_subtitle = self._get_cached_subtitle(file_path)
        
        if cached_subtitle:
            # Search in cached data (much faster)
            for line in cached_subtitle.lines:
                if pattern.search(line.text):
                    # Format time
                    start_time = self._format_time(line.start_ms)
                    
                    # Get display file name
                    display_name = self._get_display_filename(file_path)
                    
                    results.append((display_name, start_time, line.text, line.start_ms))
        else:
            # Fallback to original method if caching failed
            try:
                # Detect encoding
                with open(file_path, 'rb') as f:
                    raw_data = f.read(8192)
                    encoding_result = chardet.detect(raw_data)
                    encoding = encoding_result.get('encoding', 'utf-8')
                
                # Parse subtitle file
                subs = pysubs2.load(file_path, encoding=encoding)
                
                for line in subs:
                    if pattern.search(line.text):
                        # Format time
                        start_time = self._format_time(line.start)
                        
                        # Get display file name
                        display_name = self._get_display_filename(file_path)
                        
                        results.append((display_name, start_time, line.text.strip(), line.start))
                        
            except Exception:
                # If pysubs2 fails, try simple text search
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                    if pattern.search(content):
                        display_name = self._get_display_filename(file_path)
                        results.append((display_name, "--:--:--", "Text found (format not parsed)", 0))
                        
                except Exception:
                    pass
                
        return results
    
    def _get_display_filename(self, file_path: str) -> str:
        """Get the display filename for search results"""
        video_info = self.subtitle_to_video_map.get(file_path, {})
        
        if video_info.get('is_extracted', False):
            # For extracted subtitles, show original video filename with track info
            original_file = video_info['original_file']
            rel_path = os.path.relpath(original_file, self.folder_path)
            
            # Add track information
            language = video_info.get('language', 'unknown')
            title = video_info.get('title', '')
            track_index = video_info.get('track_index', 0)
            
            track_info = f" [Track {track_index}: {language}"
            if title:
                track_info += f" - {title}"
            track_info += "]"
            
            return rel_path + track_info
        else:
            # For standalone subtitle files, show relative path
            return os.path.relpath(file_path, self.folder_path)
    
    def _format_time(self, milliseconds: int) -> str:
        """Format time in milliseconds to HH:MM:SS"""
        seconds = milliseconds // 1000
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def _search_complete(self, results: List[Tuple[str, str, str, int]]):
        """Called when search is complete"""
        # Add results to tree
        for file_path, time, text, start_ms in results:
            # Store the start time in milliseconds as hidden data
            item = self.tree.insert("", "end", values=(file_path, time, text))
            self.item_start_times[item] = start_ms
            
        count = len(results)
        files_count = len(self.subtitle_files)
        self.status_var.set(f"Found {count} matches in {files_count} files")
        
    def _search_error(self, error_msg):
        """Called when search encounters an error"""
        self.status_var.set("Search failed")
        messagebox.showerror("Error", f"Search failed: {error_msg}")
    
    def show_context_menu(self, event):
        """Show context menu on right-click"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def on_result_double_click(self, event):
        """Handle double-click on search result"""
        self.jump_to_video()
    
    def jump_to_video(self):
        """Jump to video at the selected time"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a search result first")
            return
            
        item = selection[0]
        file_display_name = self.tree.item(item, "values")[0]
        start_time_ms = self.item_start_times.get(item, 0)
        
        # Find the original video file
        video_file = self._find_video_file_from_display_name(file_display_name)
        
        if not video_file:
            messagebox.showerror("Error", "Could not find video file")
            return
            
        if not os.path.exists(video_file):
            messagebox.showerror("Error", f"Video file not found: {video_file}")
            return
            
        # Try to open with video player
        success = self._open_video_at_time(video_file, start_time_ms)
        
        if not success:
            system = platform.system().lower()
            if system == 'darwin':
                messagebox.showerror("Error", "Could not open video file. Please install IINA or VLC Media Player.")
            else:
                messagebox.showerror("Error", "Could not open video file. Please install VLC or another compatible video player.")
    
    def _find_video_file_from_display_name(self, display_name: str) -> Optional[str]:
        """Find the original video file from display name"""
        # Remove track information if present
        if " [Track " in display_name:
            display_name = display_name.split(" [Track ")[0]
        
        # Search in subtitle_to_video_map
        for subtitle_file, video_info in self.subtitle_to_video_map.items():
            original_file = video_info['original_file']
            rel_path = os.path.relpath(original_file, self.folder_path)
            
            if rel_path == display_name:
                return original_file
                
        return None
    
    def _open_video_at_time(self, video_file: str, start_time_ms: int) -> bool:
        """Open video file at specified time"""
        try:
            start_seconds = start_time_ms // 1000
            
            # Try IINA first on macOS (excellent player with mpv backend)
            if platform.system().lower() == 'darwin' and self._try_iina(video_file, start_seconds):
                return True
            
            # Try VLC (best cross-platform support for seeking)
            if self._try_vlc(video_file, start_seconds):
                return True
                
            # Try mpv
            if self._try_mpv(video_file, start_seconds):
                return True
                
            # Try system default player (without seeking)
            if self._try_system_default(video_file):
                messagebox.showinfo("Info", f"Video opened with default player. Please seek to {self._format_time(start_time_ms)}")
                return True
                
            return False
            
        except Exception as e:
            print(f"Error opening video: {e}")
            return False
    
    def _try_iina(self, video_file: str, start_seconds: int) -> bool:
        """Try to open with IINA (macOS)"""
        iina_commands = [
            'iina',
            '/Applications/IINA.app/Contents/MacOS/iina'
        ]
        
        for iina_cmd in iina_commands:
            try:
                # IINA uses mpv arguments
                cmd = [iina_cmd, f'--mpv-start={start_seconds}', video_file]
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
            except (FileNotFoundError, OSError):
                continue
                
        # Try using open command with IINA
        try:
            cmd = ['open', '-a', 'IINA', '--args', f'--mpv-start={start_seconds}', video_file]
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except (FileNotFoundError, OSError):
            return False
    
    def _try_vlc(self, video_file: str, start_seconds: int) -> bool:
        """Try to open with VLC"""
        vlc_commands = ['vlc', '/Applications/VLC.app/Contents/MacOS/VLC']
        
        for vlc_cmd in vlc_commands:
            try:
                cmd = [vlc_cmd, '--start-time', str(start_seconds), video_file]
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
            except (FileNotFoundError, OSError):
                continue
        return False
    
    def _try_mpv(self, video_file: str, start_seconds: int) -> bool:
        """Try to open with mpv"""
        try:
            cmd = ['mpv', f'--start={start_seconds}', video_file]
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except (FileNotFoundError, OSError):
            return False
    
    def _try_system_default(self, video_file: str) -> bool:
        """Try to open with system default player"""
        try:
            system = platform.system().lower()
            
            if system == 'darwin':  # macOS
                subprocess.Popen(['open', video_file])
            elif system == 'windows':
                subprocess.Popen(['start', video_file], shell=True)
            else:  # Linux
                subprocess.Popen(['xdg-open', video_file])
            
            return True
        except Exception:
            return False
    
    def _on_closing(self):
        """Clean up resources when closing the application"""
        try:
            # Shutdown thread pool
            self.executor.shutdown(wait=False)
            # Clear cache
            self._clear_cache()
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            self.root.destroy()


def main():
    """Main function"""
    root = tk.Tk()
    app = SubtitleSearchTool(root)
    root.mainloop()


if __name__ == "__main__":
    main() 