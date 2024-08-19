import requests
from bs4 import BeautifulSoup
import time
import os
import json
import zipfile
import random

def download_audio(url, book, chapter, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            audio_tag = soup.find('audio', id='dataman-audio')

            if audio_tag and 'src' in audio_tag.attrs:
                audio_url = audio_tag['src']
                audio_response = requests.get(audio_url, timeout=30)
                audio_response.raise_for_status()

                filename = f'{book}_{chapter:03d}.mp3'

                with open(filename, 'wb') as file:
                    file.write(audio_response.content)

                print(f"Downloaded file of {book} chapter {chapter} successfully!")
                return True
            else:
                print(f"Attempt {attempt + 1}: Không tìm thấy thẻ audio hoặc thuộc tính src trong trang web cho {book} chương {chapter}.")
                if attempt == max_retries - 1:
                    print(f"HTML content: {soup.prettify()[:500]}...")  # Print first 500 characters of HTML
                time.sleep(random.uniform(5, 10))  # Wait randomly between 5 to 10 seconds before retrying
        except requests.RequestException as e:
            print(f"Attempt {attempt + 1}: Lỗi khi tải {book} chương {chapter}: {str(e)}")
            if attempt == max_retries - 1:
                return False
            time.sleep(1)
    return False

def download_book(book, num_chapters, start_chapter=1):
    base_url = "https://www.bible.com/audio-bible/193/{}.{}.VIET1925"
    success_count = 0

    for chapter in range(start_chapter, num_chapters + 1):
        url = base_url.format(book, chapter)
        if download_audio(url, book, chapter):
            success_count += 1
        else:
            print(f"Failed to download {book} chapter {chapter} after multiple attempts. Moving to next chapter.")
        save_progress(book, chapter)
        time.sleep(random.uniform(5, 10))  # Wait randomly between 2 to 5 seconds between each download

    return success_count

def save_progress(current_book, current_chapter):
    progress = {
        "current_book": current_book,
        "current_chapter": current_chapter
    }
    with open('../progress.json', 'w') as f:
        json.dump(progress, f)

def load_progress():
    if os.path.exists('progress.json'):
        with open('progress.json', 'r') as f:
            return json.load(f)
    return None

def create_zip(source_dir):
    zip_filename = 'bible_audio_full.zip'
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_dir)
                zipf.write(file_path, arcname)
    return zip_filename

def get_size(file_path):
    size_bytes = os.path.getsize(file_path)
    size_mb = size_bytes / (1024 * 1024)
    return f"{size_mb:.2f} MB"

# List of books in the Bible
books = [
    ("GEN", 50), ("EXO", 40), ("LEV", 27), ("NUM", 36), ("DEU", 34), 
    ("JOS", 24), ("JDG", 21), ("RUT", 4), ("1SA", 31), ("2SA", 24),
    ("1KI", 22), ("2KI", 25), ("1CH", 29), ("2CH", 36), ("EZR", 10),
    ("NEH", 13), ("EST", 10), ("JOB", 42), ("PSA", 150), ("PRO", 31),
    ("ECC", 12), ("SNG", 8), ("ISA", 66), ("JER", 52), ("LAM", 5),
    ("EZK", 48), ("DAN", 12), ("HOS", 14), ("JOL", 3), ("AMO", 9),
    ("OBA", 1), ("JON", 4), ("MIC", 7), ("NAM", 3), ("HAB", 3),
    ("ZEP", 3), ("HAG", 2), ("ZEC", 14), ("MAL", 4), ("MAT", 28),
    ("MRK", 16), ("LUK", 24), ("JHN", 21), ("ACT", 28), ("ROM", 16),
    ("1CO", 16), ("2CO", 13), ("GAL", 6), ("EPH", 6), ("PHP", 4),
    ("COL", 4), ("1TH", 5), ("2TH", 3), ("1TI", 6), ("2TI", 4),
    ("TIT", 3), ("PHM", 1), ("HEB", 13), ("JAS", 5), ("1PE", 5),
    ("2PE", 3), ("1JN", 5), ("2JN", 1), ("3JN", 1), ("JUD", 1),
    ("REV", 22)
]

# Create main directory to save audio files
main_dir = 'bible_audio_full'
if not os.path.exists(main_dir):
    os.makedirs(main_dir)

os.chdir(main_dir)

total_chapters = sum(num_chapters for _, num_chapters in books)
downloaded_chapters = 0
book_results = {}

# Check saved progress
progress = load_progress()
start_index = 0
start_chapter = 1

if progress:
    for i, (book, _) in enumerate(books):
        if book == progress["current_book"]:
            start_index = i
            start_chapter = progress["current_chapter"] + 1  # Start from next chapter
            if start_chapter > books[i][1]:  # If this book is completed
                start_index += 1
                start_chapter = 1
            break

for i, (book, num_chapters) in enumerate(books[start_index:], start=start_index):
    print(f"\nDownloading book {book}...")

    # Create directory for the book if it doesn't exist
    if not os.path.exists(f"{i+1:02d}_{book}"):
        os.makedirs(f"{i+1:02d}_{book}")

    os.chdir(f"{i+1:02d}_{book}")

    success_count = download_book(book, num_chapters, start_chapter)
    book_results[book] = f"{success_count}/{num_chapters}"
    downloaded_chapters += success_count
    print(f"Downloaded {success_count}/{num_chapters} chapters of book {book}.")
    print(f"Total progress: {downloaded_chapters}/{total_chapters} chapters")

    os.chdir('..')
    start_chapter = 1  # Reset start_chapter for next books

print("\nCompleted downloading all audio files.")
print(f"Total: {downloaded_chapters}/{total_chapters} chapters downloaded.")

# Save results to JSON file
with open('download_results.json', 'w') as f:
    json.dump(book_results, f, indent=4)

print("Detailed results have been saved to 'download_results.json'")

# Create zip file
os.chdir('..')  # Return to parent directory
print("\nCreating zip file...")
zip_file = create_zip(main_dir)
zip_size = get_size(zip_file)

print(f"Zip file created: {zip_file}")
print(f"Zip file size: {zip_size}")

# Information on how to download the zip file to local machine
print("\nTo download the zip file to your local machine:")
print("1. In Replit, open the 'Files' tab on the left.")
print("2. Find the 'bible_audio_full.zip' file.")
print("3. Right-click on the file and select 'Download'.")