# 🎓 IMS NSUT - Notice Checker Pro

> **Developed by [Manit Shukla](https://manitshukla.vercel.app/)**  
> 🌐 Portfolio: [manitshukla.vercel.app](https://manitshukla.vercel.app/) | 🐙 GitHub: [ManitShukla](https://github.com/ManitShukla)

A high-performance, Python-based desktop application designed to seamlessly scrape, track, filter, and view college notifications from the [IMS NSUT portal](https://www.imsnsit.org/imsnsit/notifications.php). 

Built to solve the frustrations of the official portal, this app not only tracks new notices so you never miss an update, but it also features a **custom bypass for the infamous "Invalid operation232" database error**, allowing you to view and download college PDFs instantly.

---

## ✨ Key Features

* 🚀 **Smart Bypass & Auto-Downloader:** Tired of the "Invalid operation232" error when clicking IMS links? This app spoofs the `Referer` headers and downloads the documents securely in the background, opening them natively on your OS instantly.
* 🔔 **New Notice Tracking:** Remembers what you've already seen (saved locally in `seen_notices.json`). You'll only be alerted to brand new circulars when you launch the app.
* 🗄️ **High-Performance Archive Browser:** Browse a historical catalog of 10,000+ notices without UI lag. Features strict pagination (50 items/page) to keep memory usage exceptionally low.
* 🔍 **Advanced Filtering Engine:**
  * **Pipe-Delimited Search:** Use `|` to chain strict queries (e.g., `exam | datesheet | 2024`).
  * **Smart Categories:** Automatically filters notices into categories like *Exams*, *Results*, *Placements*, and *Fees/Admin*.
  * **Bounded Date Picker:** Filter exact dates securely using an interactive calendar UI.
* 💾 **Direct Downloads:** A dedicated "Save to Downloads" button bypasses the temporary folder and saves perfectly formatted, date-prefixed files directly to your OS Downloads folder.

---

## 🛠️ Prerequisites

To run this application, you will need **Python 3.x** installed on your system. 

The application features a built-in dependency checker, but you can manually install the required third-party libraries using `pip`:

```bash
pip install requests beautifulsoup4 tkcalendar
```
*(Note: `tkinter` is used for the GUI, which comes pre-installed with standard Python distributions on Windows and macOS. Linux users may need to run `sudo apt-get install python3-tk`)*

---

## 🚀 Installation & Usage

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ManitShukla/NSUT-Notice-Scraper.git
   cd NSUT-Notice-Scraper
   ```

2. **Run the application:**
   ```bash
   python Notice_Scraper.py
   ```

3. **Using the App:**
   * **Dashboard:** Upon launch, the app scrapes the portal and displays *only* the new notices since your last visit. 
   * **Viewing:** Click **"Open Notice"** to instantly open the document, or **"Save to Downloads"** to store it permanently.
   * **Archive:** Click **"📂 Open Archive Database"** in the top right to view every notice you've ever tracked. 
   * **Searching:** In the archive, type in the search bar. The UI uses *debouncing* (waits 300ms after you stop typing) so it won't freeze while you type.

---

## 🧠 How it Works (Under the Hood)

* **State Management:** The app tracks notices by combining the *Notice Title* and *Date* into a unique ID, storing them in a local `seen_notices.json` file as an O(1) lookup dictionary.
* **Smart Routing:** The `handle_url()` function checks if a link is an internal `.php` IMS link or an external link (like Google Drive). Internal links are routed through the Referer-spoofing background downloader, while external links open safely in your standard web browser.
* **Concurrency:** Web scraping and file downloading are handed off to daemon `threading` workers, ensuring the Tkinter GUI remains buttery smooth and never reads as "Not Responding".
