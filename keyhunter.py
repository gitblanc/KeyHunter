import os
import argparse
from colorama import init, Fore, Style
from datetime import datetime
from tqdm import tqdm
import mmap

# Initialize colorama
init(autoreset=True)

def print_logo():
    logo = """
 _  __          _   _             _            
| |/ /___ _   _| | | |_   _ _ __ | |_ ___ _ __    
| ' // _ | | | | |_| | | | | '_ \| __/ _ | '__| __
| . |  __| |_| |  _  | |_| | | | | ||  __| |   /o \_____
|_|\_\___|\__, |_| |_|\__,_|_| |_|\__\___|_|   \__/-="="
          |___/                                
                                         @gitblanc, v1.1
    """
    print(Fore.MAGENTA + logo + Style.RESET_ALL)

def print_with_timestamp(message, color=Fore.RESET):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = f"{color}[{timestamp}] {message}{Style.RESET_ALL}"
    print(formatted_message)

def search_in_file(file_path, search_term, block_size=1024 * 1024, verbose=False):
    search_term_bytes = search_term.encode()  # Convert search term to bytes
    search_term_len = len(search_term_bytes)

    with open(file_path, 'rb') as f:
        size = os.path.getsize(file_path)
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            occurrences = 0
            pbar = tqdm(total=size, unit='B', unit_scale=True, desc='Looking for biscuits')

            buffer = b""
            offset = 0

            while offset < size:
                chunk_size = min(block_size, size - offset)
                chunk = mm[offset:offset + chunk_size]
                buffer += chunk
                lines = buffer.split(b'\n')

                # The last part might not end with a newline, so handle it separately
                buffer = lines.pop()

                for line in lines:
                    if search_term_bytes in line:
                        occurrences += 1
                        # Decode and highlight the line with the search term
                        line_decoded = line.decode(errors='ignore')
                        highlighted_line = line_decoded.replace(search_term, f"{Fore.RED}{search_term}{Style.RESET_ALL}")
                        tqdm.write(highlighted_line)  # Print highlighted line

                # Update progress bar
                pbar.update(chunk_size)
                offset += chunk_size

            # Handle the last buffer
            if search_term_bytes in buffer:
                occurrences += 1
                # Decode and highlight the line with the search term
                last_line = buffer.decode(errors='ignore')
                highlighted_last_line = last_line.replace(search_term, f"{Fore.RED}{search_term}{Style.RESET_ALL}")
                tqdm.write(highlighted_last_line)

            pbar.close()
            print_with_timestamp(f"Passwords found: {occurrences}", Fore.GREEN)

# CLI commands configuration
parser = argparse.ArgumentParser(description="Search for a password inside a [massive] wordlist.")
parser.add_argument("file_path", help="The path to the wordlist.")
parser.add_argument("search_term", help="The password (or part of the password) to search for.")
parser.add_argument("-b", "--block_size", type=int, default=1024*1024, help="Reading block size in bytes (default 1 MB).")
parser.add_argument("-v", "--verbose", action="store_true", help="Verbose.")

args = parser.parse_args()

print_logo()

# Execute the search function
search_in_file(args.file_path, args.search_term, args.block_size, args.verbose)
