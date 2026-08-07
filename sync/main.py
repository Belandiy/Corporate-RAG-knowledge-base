import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from parser import parse_file
from chunker import get_chunks
from qdrant_store import store

DOCS_DIR = os.environ.get("DOCS_DIR", "/app/docs")

class DocumentSyncHandler(FileSystemEventHandler):
    def process_file(self, event):
        if event.is_directory:
            return

        filepath = event.src_path
        filename = os.path.basename(filepath)

        # We only care about specific extensions
        if not filepath.lower().endswith(('.md', '.pdf', '.doc', '.docx', '.txt')):
            return

        print(f"Processing updated/created file: {filepath}")

        # 1. Parse
        text = parse_file(filepath)

        # 2. Chunk
        # Using 512 tokens approx for chunk size as per docs
        chunks = get_chunks(text, chunk_size=512, chunk_overlap=50)

        # 3. Upsert to DB
        store.upsert_document(filepath, filename, chunks)

    def on_created(self, event):
        self.process_file(event)

    def on_modified(self, event):
        self.process_file(event)

    def on_deleted(self, event):
        if event.is_directory:
            return
        filepath = event.src_path
        print(f"Processing deleted file: {filepath}")
        store.delete_document(filepath)

def sync_existing_files():
    print("Syncing existing files...")
    for root, dirs, files in os.walk(DOCS_DIR):
        for file in files:
            filepath = os.path.join(root, file)
            # Create a mock event
            class MockEvent:
                is_directory = False
                src_path = filepath
            handler = DocumentSyncHandler()
            handler.process_file(MockEvent())

if __name__ == "__main__":
    if not os.path.exists(DOCS_DIR):
        os.makedirs(DOCS_DIR)

    # Initial sync
    sync_existing_files()

    # Start observer
    event_handler = DocumentSyncHandler()
    observer = Observer()
    observer.schedule(event_handler, DOCS_DIR, recursive=True)
    observer.start()
    print(f"Started monitoring {DOCS_DIR} for changes...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
