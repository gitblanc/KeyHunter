import sys
import os
import argparse
from colorama import init, Fore, Style
from datetime import datetime
from tqdm import tqdm

# Initialize colorama
init(autoreset=True)

# Prints the logo
def print_logo():
    logo = """
 _  __          _   _             _            
| |/ /___ _   _| | | |_   _ _ __ | |_ ___ _ __    
| ' // _ | | | | |_| | | | | '_ \| __/ _ | '__| __
| . |  __| |_| |  _  | |_| | | | | ||  __| |   /o \_____
|_|\_\___|\__, |_| |_|\__,_|_| |_|\__\___|_|   \__/-="="
          |___/                                
                                         @gitblanc, v1.0
    """
    print(Fore.MAGENTA + logo + Style.RESET_ALL)

def print_with_timestamp(message, color=Fore.RESET):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = f"{color}[{timestamp}] {message}{Style.RESET_ALL}"
    print(formatted_message)

def search_in_file(file_path, search_term, block_size=1024 * 1024, verbose=False):
    # Get the size of the wordlist
    total_size = os.path.getsize(file_path)
    
    if verbose:
        print_with_timestamp(f"Wordlist size: {total_size} bytes", Fore.YELLOW)
        print_with_timestamp("Let's dive in...")

    occurrences = 0
    with open(file_path, 'rb') as file, tqdm(total=total_size, unit='B', unit_scale=True, desc='Looking for biscuits') as pbar:
        buffer = b""
        
        while True:
            block = file.read(block_size)
            if not block:
                break

            buffer += block
            lines = buffer.split(b'\n')
            buffer = lines.pop()

            for line in lines:
                if search_term.encode() in line:
                    occurrences += 1
                    # Highlight in red the match 
                    highlighted_line = line.decode(errors='ignore').replace(search_term, f"{Fore.RED}{search_term}{Style.RESET_ALL}")
                    tqdm.write(highlighted_line)  # Avoid progress bar conflicts

            # Update progress bar
            pbar.update(len(block))

        # Verify final buffer
        if search_term.encode() in buffer:
            occurrences += 1
            highlighted_buffer = buffer.decode(errors='ignore').replace(search_term, f"{Fore.RED}{search_term}{Style.RESET_ALL}")
            tqdm.write(highlighted_buffer)

        print_with_timestamp(f"Passwords found: {occurrences}", Fore.GREEN)

# CLI commands configuration
parser = argparse.ArgumentParser(description="Search for a password inside a [massive] wordlist.")
parser.add_argument("file_path", help="The path to the wordlist.")
parser.add_argument("search_term", help="The password (or part of the password) to search for.")
parser.add_argument("-b", "--block_size", type=int, default=1024*1024, help="Reading block size in bytes (default 1 MB).")
parser.add_argument("-v", "--verbose", action="store_true", help="Verbose.")

args = parser.parse_args()

print_logo()

# Verbose mode execution if specified
search_in_file(args.file_path, args.search_term, args.block_size, args.verbose)

