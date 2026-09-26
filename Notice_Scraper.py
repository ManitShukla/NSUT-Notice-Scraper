# IMS NSUT - Notice Checker Pro | Made by Manit Shukla. For more info or contact details, visit https://manitshukla.vercel.app/ . Github Repo: https://github.com/ManitShukla/NSUT-Notice-Scraper
import sys
import os

missing_deps = []
try:
    import requests
except ImportError:
    missing_deps.append("requests")
try:
    from bs4 import BeautifulSoup
except ImportError:
    missing_deps.append("beautifulsoup4")
try:
    from tkcalendar import DateEntry
except ImportError:
    missing_deps.append("tkcalendar")

if missing_deps:
    error_msg = (
        "CRITICAL WARNING: Missing required dependencies!\n\n"
        "Please install the following packages to run this program:\n"
        + "\n".join(f"- {dep}" for dep in missing_deps) + "\n\n"
        "Run this command in your terminal:\n"
        f"pip install {' '.join(missing_deps)}"
    )
    print(error_msg)
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Missing Dependencies", error_msg)
    except ImportError:
        pass
    sys.exit(1)

import json
import re
from urllib.parse import urljoin, urlparse
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import subprocess
import tempfile
import mimetypes
import threading
import math
from datetime import datetime, date

URL = "https://www.imsnsit.org/imsnsit/notifications.php"
STATE_FILE = "seen_notices.json"
ITEMS_PER_PAGE = 50 

BG_COLOR = "#121212"
PANEL_BG = "#1e1e1e"
FG_COLOR = "#e0e0e0"
MUTED_FG = "#a0a0a0"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.imsnsit.org/imsnsit/notifications.php" 
})

def parse_notice_date(date_str):
    if not date_str or date_str == "Unknown Date":
        return datetime.min
    date_str = date_str.strip()
    formats = ["%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y", "%d-%m-%y", "%d/%m/%y", "%d.%m.%y", "%d %b %Y", "%d %B %Y", "%d %B,%Y", "%d %b,%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return datetime.min

def load_seen_notices():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            try:
                data = json.load(f)
                if isinstance(data, list): return {item: {} for item in data}
                return data
            except json.JSONDecodeError:
                return {}
    return {}

def save_seen_notices(seen_dict):
    with open(STATE_FILE, 'w') as f:
        json.dump(seen_dict, f, indent=4)

def handle_url(url, title):
    parsed_url = urlparse(url)
    if "imsnsit.org" in parsed_url.netloc.lower() and ".php" in parsed_url.path.lower():
        threading.Thread(target=download_and_open_locally, args=(url, title), daemon=True).start()
    else:
        webbrowser.open(url)

def download_and_open_locally(url, title):
    try:
        response = session.get(url, stream=True, timeout=15, allow_redirects=True)
        if "invalid operation232" in response.text.lower()[:500]:
            webbrowser.open(url)
            return
        content_type = response.headers.get('Content-Type', '')
        ext = mimetypes.guess_extension(content_type.split(';')[0])
        if not ext: ext = '.pdf'
        safe_title = re.sub(r'[\\/*?:"<>|]', "", title)[:50].strip()
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, f"{safe_title}{ext}")
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192): f.write(chunk)
        if os.name == 'nt': os.startfile(file_path)
        elif sys.platform == 'darwin': subprocess.call(['open', file_path])
        else: subprocess.call(['xdg-open', file_path])
    except Exception as e:
        webbrowser.open(url)

def download_to_downloads(url, title, date_str, ui_widget):
    if "drive.google.com" in url.lower():
        webbrowser.open(url)
        return
    try:
        response = session.get(url, stream=True, timeout=15, allow_redirects=True)
        if "invalid operation232" in response.text.lower()[:500]:
            webbrowser.open(url)
            return
        content_type = response.headers.get('Content-Type', '')
        ext = mimetypes.guess_extension(content_type.split(';')[0])
        if not ext: ext = '.pdf'
        safe_title = re.sub(r'[\\/*?:"<>|]', "", title)[:80].strip()
        safe_date = re.sub(r'[\\/*?:"<>|]', "-", date_str).strip()
        filename = f"Notice - {safe_date} - {safe_title}{ext}"
        downloads_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
        os.makedirs(downloads_dir, exist_ok=True)
        file_path = os.path.join(downloads_dir, filename)
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192): f.write(chunk)
        ui_widget.after(0, lambda: messagebox.showinfo("Download Complete", f"Successfully saved to:\n\n{filename}"))
    except Exception as e:
        ui_widget.after(0, lambda: messagebox.showerror("Download Failed", f"Could not save the file.\n\nError: {e}"))
        webbrowser.open(url)

def download_thread(url, title, date_str, ui_widget):
    threading.Thread(target=download_to_downloads, args=(url, title, date_str, ui_widget), daemon=True).start()

def get_new_notices():
    try:
        response = session.get(URL, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    seen_notices = load_seen_notices()
    new_notices = []
    
    for link_tag in soup.find_all('a', href=True):
        title = link_tag.get_text(strip=True)
        href = link_tag['href']
        
        if not title or href.startswith('javascript:') or title.lower() in ['home', 'login', 'about us', 'contact us', 'syllabus', 'admin']:
            continue
            
        parent_row = link_tag.find_parent('tr')
        row_text = parent_row.get_text(separator=' ', strip=True) if parent_row else title

        date_match = re.search(r'\b\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}\b', row_text) or re.search(r'\b\d{1,2}\s+[a-zA-Z]{3,9}\s+\d{4}\b', row_text)
        date_str = date_match.group(0) if date_match else "Unknown Date"
        unique_id = f"{title} | {date_str}"
        full_url = urljoin(URL, href)
        
        domain_source = urlparse(full_url).netloc[4:] if urlparse(full_url).netloc.startswith("www.") else urlparse(full_url).netloc
        
        if unique_id not in seen_notices:
            new_notice = {'title': title, 'date': date_str, 'url': full_url, 'source': domain_source, 'id': unique_id}
            new_notices.append(new_notice)
            seen_notices[unique_id] = new_notice 
            
    save_seen_notices(seen_notices)
    return new_notices

def build_browser_ui(parent_frame, initial_data, is_main_view=False):
    state = {'current_page': 1, 'search_timer': None}
    catalog_memory = initial_data
    current_filtered_list = catalog_memory.copy()

    filter_frame = tk.Frame(parent_frame, bg=BG_COLOR)
    filter_frame.pack(fill="x", padx=15, pady=5)
    
    row1 = tk.Frame(filter_frame, bg=BG_COLOR)
    row1.pack(fill="x", pady=5)
    tk.Label(row1, text="Search Keywords:", font=("Arial", 11, "bold"), bg=BG_COLOR, fg=FG_COLOR).pack(side="left")
    search_var = tk.StringVar(master=parent_frame)
    tk.Entry(row1, textvariable=search_var, font=("Arial", 11), width=25, bg=PANEL_BG, fg=FG_COLOR, insertbackground=FG_COLOR, relief="flat").pack(side="left", padx=10)
    tk.Label(row1, text="(Use | to separate keywords)", font=("Arial", 9, "italic"), bg=BG_COLOR, fg=MUTED_FG).pack(side="left")
    
    if is_main_view:
        def open_all_filtered():
            for n in current_filtered_list:
                handle_url(n['url'], n['title'])
        tk.Button(row1, text="🚀 Open All Listed", font=("Arial", 10, "bold"), bg="#198754", fg="white", relief="flat", cursor="hand2", padx=5, command=open_all_filtered).pack(side="right")

    row2 = tk.Frame(filter_frame, bg=BG_COLOR)
    row2.pack(fill="x", pady=5)
    tk.Label(row2, text="Sort By:", font=("Arial", 11, "bold"), bg=BG_COLOR, fg=FG_COLOR).pack(side="left")
    sort_var = tk.StringVar(master=parent_frame, value="Date (Newest First)")
    sort_combo = ttk.Combobox(row2, textvariable=sort_var, state="readonly", width=18, values=["Date (Newest First)", "Date (Oldest First)", "Title (A-Z)", "Title (Z-A)"])
    sort_combo.pack(side="left", padx=(5, 10))
    
    tk.Label(row2, text="Category:", font=("Arial", 11, "bold"), bg=BG_COLOR, fg=FG_COLOR).pack(side="left")
    category_var = tk.StringVar(master=parent_frame, value="All Categories")
    category_combo = ttk.Combobox(row2, textvariable=category_var, state="readonly", width=15, values=["All Categories", "Exams", "Results", "Placements", "Fees/Admin", "Other"])
    category_combo.pack(side="left", padx=5)

    row3 = tk.Frame(filter_frame, bg=BG_COLOR)
    row3.pack(fill="x", pady=5)
    tk.Label(row3, text="Date Filter:", font=("Arial", 11, "bold"), bg=BG_COLOR, fg=FG_COLOR).pack(side="left")
    date_mode_var = tk.StringVar(master=parent_frame, value="All Time")
    date_mode_combo = ttk.Combobox(row3, textvariable=date_mode_var, state="readonly", width=12, values=["All Time", "Exact Date"])
    date_mode_combo.pack(side="left", padx=(5, 15))
    
    today_date = datetime.now().date()
    min_allowable_date = date(2015, 1, 1)

    lbl_date = tk.Label(row3, text="Date:", font=("Arial", 10), bg=BG_COLOR, fg=FG_COLOR)
    lbl_date.pack(side="left")
    date_picker = DateEntry(row3, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd', mindate=min_allowable_date, maxdate=today_date)
    date_picker.pack(side="left", padx=(5, 15))

    text_frame = tk.Frame(parent_frame, bg=BG_COLOR)
    text_frame.pack(expand=True, fill="both", padx=10, pady=5)
    scrollbar = tk.Scrollbar(text_frame)
    scrollbar.pack(side="right", fill="y")
    text_area = tk.Text(text_frame, wrap="word", padx=15, pady=15, bg=PANEL_BG, fg=FG_COLOR, relief="flat", font=("Arial", 11), yscrollcommand=scrollbar.set, insertbackground=FG_COLOR)
    text_area.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=text_area.yview)
    text_area.tag_config("date_style", foreground="#85e085")
    text_area.tag_config("title_style", font=("Arial", 12, "bold"), foreground="#ffffff")
    text_area.tag_config("source_style", font=("Arial", 9, "italic"), foreground=MUTED_FG)

    page_frame = tk.Frame(parent_frame, bg=BG_COLOR)
    page_frame.pack(fill="x", pady=5)
    btn_prev = tk.Button(page_frame, text="◀ Previous Page", font=("Arial", 10, "bold"), bg="#333333", fg="white", relief="flat")
    btn_prev.pack(side="left", padx=15)
    lbl_page_info = tk.Label(page_frame, text="Page 1 of 1", font=("Arial", 11, "bold"), bg=BG_COLOR, fg=FG_COLOR)
    lbl_page_info.pack(side="left", expand=True)
    btn_next = tk.Button(page_frame, text="Next Page ▶", font=("Arial", 10, "bold"), bg="#333333", fg="white", relief="flat")
    btn_next.pack(side="right", padx=15)

    def apply_filters(*args):
        query = search_var.get().lower()
        selected_cat = category_var.get()
        selected_sort = sort_var.get()
        date_mode = date_mode_var.get()
        
        nonlocal current_filtered_list
        current_filtered_list = catalog_memory.copy()
        
        if date_mode == "Exact Date":
            target_date = date_picker.get_date()
            current_filtered_list = [n for n in current_filtered_list if parse_notice_date(n['date']) != datetime.min and parse_notice_date(n['date']).date() == target_date]

        if selected_cat != "All Categories":
            cat_map = {
                "Exams": ["exam", "mid sem", "end sem", "datesheet", "date sheet", "schedule"],
                "Results": ["result", "marks", "score"],
                "Placements": ["placement", "internship", "hiring", "tnp", "recruitment"],
                "Fees/Admin": ["fee", "registration", "admission", "hostel", "circular", "notice"]
            }
            if selected_cat in cat_map:
                cat_keywords = cat_map[selected_cat]
                current_filtered_list = [n for n in current_filtered_list if any(k in n['title'].lower() for k in cat_keywords)]
            elif selected_cat == "Other":
                all_keywords = [k for sublist in cat_map.values() for k in sublist]
                current_filtered_list = [n for n in current_filtered_list if not any(k in n['title'].lower() for k in all_keywords)]

        if query:
            search_terms = [term.strip() for term in query.split('|') if term.strip()]
            if search_terms:
                current_filtered_list = [
                    n for n in current_filtered_list 
                    if all(term in n['title'].lower() or term in n['date'].lower() for term in search_terms)
                ]
            
        if selected_sort == "Date (Newest First)":
            current_filtered_list.sort(key=lambda x: parse_notice_date(x['date']), reverse=True)
        elif selected_sort == "Date (Oldest First)":
            current_filtered_list.sort(key=lambda x: parse_notice_date(x['date']), reverse=False)
        elif selected_sort == "Title (A-Z)":
            current_filtered_list.sort(key=lambda x: x['title'].lower(), reverse=False)
        elif selected_sort == "Title (Z-A)":
            current_filtered_list.sort(key=lambda x: x['title'].lower(), reverse=True)
            
        state['current_page'] = 1 
        render_page()

    def render_page():
        text_area.config(state="normal")
        text_area.delete("1.0", tk.END)
        
        total_items = len(current_filtered_list)
        total_pages = math.ceil(total_items / ITEMS_PER_PAGE) if total_items > 0 else 1
        state['current_page'] = max(1, min(state['current_page'], total_pages))
        
        lbl_page_info.config(text=f"Page {state['current_page']} of {total_pages}  (Total: {total_items} records)")
        btn_prev.config(state="normal" if state['current_page'] > 1 else "disabled")
        btn_next.config(state="normal" if state['current_page'] < total_pages else "disabled")
        
        start_idx = (state['current_page'] - 1) * ITEMS_PER_PAGE
        page_items = current_filtered_list[start_idx:start_idx + ITEMS_PER_PAGE]
        
        for idx, notice in enumerate(page_items, start_idx + 1):
            text_area.insert("end", f"[{idx}] 📅 {notice['date']}\n", "date_style")
            text_area.insert("end", f"📌 {notice['title']}\n", "title_style")
            text_area.insert("end", f"🔗 Source: {notice.get('source', 'Unknown')}\n\n", "source_style")
            
            if notice.get('url'):
                btn_frame = tk.Frame(text_area, bg=PANEL_BG)
                tk.Button(btn_frame, text="Open Notice", bg="#0d6efd", fg="white", font=("Arial", 10, "bold"), cursor="hand2", width=15, relief="flat",
                          command=lambda u=notice['url'], t=notice['title']: handle_url(u, t)).pack(side="left", padx=(0, 10))
                tk.Button(btn_frame, text="Save to Downloads", bg="#fd7e14", fg="white", font=("Arial", 10, "bold"), cursor="hand2", width=18, relief="flat",
                          command=lambda u=notice['url'], t=notice['title'], d=notice['date'], w=btn_frame: download_thread(u, t, d, w)).pack(side="left")
                text_area.window_create("end", window=btn_frame)
            else:
                text_area.insert("end", "⚠️ Legacy notice: URL not saved previously", "source_style")
            text_area.insert("end", "\n\n" + "-"*75 + "\n\n")
            
        text_area.config(state="disabled")
        text_area.yview_moveto(0) 

    def update_calendar_ui(*args):
        mode = date_mode_var.get()
        if mode == "All Time":
            date_picker.config(state="disabled")
        elif mode == "Exact Date":
            date_picker.config(state="normal")
        apply_filters()

    def debounce_search(*args):
        if state['search_timer'] is not None: parent_frame.after_cancel(state['search_timer'])
        state['search_timer'] = parent_frame.after(300, apply_filters)

    def change_page(delta):
        state['current_page'] += delta
        render_page()

    btn_prev.config(command=lambda: change_page(-1))
    btn_next.config(command=lambda: change_page(1))
    search_var.trace_add("write", debounce_search)
    sort_combo.bind("<<ComboboxSelected>>", apply_filters)
    category_combo.bind("<<ComboboxSelected>>", apply_filters)
    date_mode_combo.bind("<<ComboboxSelected>>", update_calendar_ui)
    date_picker.bind("<<DateEntrySelected>>", apply_filters)

    update_calendar_ui()

def build_gui():
    root = tk.Tk()
    root.title("IMS NSUT - Notice Checker Pro | By Manit Shukla")
    root.geometry("650x750")
    root.configure(bg=BG_COLOR)
    
    style = ttk.Style()
    if "clam" in style.theme_names():
        style.theme_use("clam")
    style.configure("TCombobox", fieldbackground=PANEL_BG, background="#333333", foreground=FG_COLOR, borderwidth=0)
    style.map('TCombobox', fieldbackground=[('readonly', PANEL_BG)], selectbackground=[('readonly', "#333333")])

    status_lbl = tk.Label(root, text="Fetching new notices...\nThis may take a moment.", font=("Arial", 12), bg=BG_COLOR, fg=FG_COLOR)
    status_lbl.pack(pady=40)

    def open_seen_notices():
        seen_win = tk.Toplevel(root)
        seen_win.title("Seen Notices Archive")
        seen_win.geometry("650x750")
        seen_win.configure(bg=BG_COLOR)
        
        tk.Label(seen_win, text="Local Notice Archive", font=("Arial", 16, "bold"), bg=BG_COLOR, fg=FG_COLOR).pack(pady=10)
        
        seen_dict = load_seen_notices()
        archive_list = []
        for uid, data in seen_dict.items():
            if data: archive_list.append(data)
            else:
                parts = uid.split(" | ")
                archive_list.append({'title': parts[0] if len(parts) > 0 else uid, 'date': parts[1] if len(parts) > 1 else "Unknown Date", 'url': None, 'source': 'Unknown'})
        
        build_browser_ui(seen_win, archive_list, is_main_view=False)

    def fetch_and_display():
        def scrape_worker():
            all_new_notices = get_new_notices()
            root.after(0, lambda: setup_main_view(all_new_notices))
        
        threading.Thread(target=scrape_worker, daemon=True).start()

    def setup_main_view(all_notices):
        status_lbl.destroy()
        
        nav_frame = tk.Frame(root, bg=BG_COLOR)
        nav_frame.pack(fill="x", padx=15, pady=5)
        
        tk.Label(nav_frame, text=f"🎉 Found {len(all_notices)} NEW notice(s)!", font=("Arial", 14, "bold"), bg=BG_COLOR, fg="#85e085").pack(side="left")
        tk.Button(nav_frame, text="📂 Open Archive Database", command=open_seen_notices, font=("Arial", 10, "bold"), bg="#444444", fg="white", relief="flat", padx=10).pack(side="right")

        if not all_notices:
            tk.Label(root, text="No new notices found on the server.\nYou're all caught up!", font=("Arial", 14), bg=BG_COLOR, fg=MUTED_FG).pack(pady=50)
            return
            
        build_browser_ui(root, all_notices, is_main_view=True)

    root.after(100, fetch_and_display)
    root.mainloop()

if __name__ == "__main__":
    build_gui()