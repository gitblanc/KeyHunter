#!/usr/bin/env python3

import os
import argparse
from colorama import init, Fore, Style
from datetime import datetime
from tqdm import tqdm
import mmap
import multiprocessing

# Initialize colorama
init(autoreset=True)

# Global multiprocessing lock for safe writing
lock = multiprocessing.Lock()

def print_logo():
    logo = r"""
 _  __          _   _             _            
| |/ /___ _   _| | | |_   _ _ __ | |_ ___ _ __    
| ' // _ | | | | |_| | | | | '_ \| __/ _ | '__| __
| . |  __| |_| |  _  | |_| | | | | ||  __| |   /o \_____
|_|\_\___|\__, |_| |_|\__,_|_| |_|\__\___|_|   \__/-="="
          |___/                                
                                         @gitblanc, v1.3
    """
    print(Fore.MAGENTA + logo + Style.RESET_ALL)

def print_with_timestamp(message, color=Fore.RESET):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = f"{color}[{timestamp}] {message}{Style.RESET_ALL}"
    print(formatted_message)

def search_in_file(file_path, search_term, output_file, block_size=1024 * 1024, verbose=False):
    search_term_bytes = search_term.encode()
    line_number = 0
    occurrences_count = 0  

    with open(file_path, 'rb') as f:
        size = os.path.getsize(file_path)
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            pbar = tqdm(total=size, unit='B', unit_scale=True, desc=f'Searching in {os.path.basename(file_path)}', leave=False)

            buffer = b""
            offset = 0

            while offset < size:
                chunk_size = min(block_size, size - offset)
                chunk = mm[offset:offset + chunk_size]
                buffer += chunk
                lines = buffer.split(b'\n')
                buffer = lines.pop()  

                for line in lines:
                    line_number += 1
                    if search_term_bytes in line:
                        occurrences_count += 1
                        line_decoded = line.decode(errors='ignore')
                        highlighted_line = line_decoded.replace(
                                search_term, f"{Fore.RED}{search_term}{Style.RESET_ALL}"
                            )
                        occurrence_message = f"{highlighted_line}"
                        occurrence_message_verbose = f"[{Fore.YELLOW}Line {line_number}{Style.RESET_ALL}] {highlighted_line} [{Fore.YELLOW}Found at {file_path}{Style.RESET_ALL}]"

                        # Write immediately with a lock
                        with lock:
                            with open(output_file, 'a', encoding='utf-8') as out_f:
                                if verbose:
                                    out_f.write(f"{occurrence_message_verbose}\n")
                                else:
                                    out_f.write(f"{occurrence_message}\n")

                        if verbose:
                            tqdm.write(f"{occurrence_message_verbose}")
                        else:
                            tqdm.write(f"{occurrence_message}")

                pbar.update(chunk_size)
                offset += chunk_size

            if buffer and search_term_bytes in buffer:
                line_number += 1
                occurrences_count += 1
                last_line = buffer.decode(errors='ignore')
                highlighted_last_line = last_line.replace(
                        search_term, f"{Fore.RED}{search_term}{Style.RESET_ALL}"
                    )
                occurrence_message = f"{highlighted_last_line}"
                occurrence_message_verbose = f"[{Fore.YELLOW}Line {line_number}{Style.RESET_ALL}] {highlighted_last_line} [{Fore.YELLOW}Found at {file_path}{Style.RESET_ALL}]"

                with lock:
                    with open(output_file, 'a', encoding='utf-8') as out_f:
                        if verbose:
                            out_f.write(f"{occurrence_message_verbose}\n")
                        else:
                            out_f.write(f"{occurrence_message}\n")

                if verbose:
                    tqdm.write(f"{occurrence_message_verbose}")
                else:
                    tqdm.write(f"{occurrence_message}")

            pbar.close()

            if verbose:
                print(f"{Fore.GREEN}Matches found in {file_path}: {occurrences_count}{Style.RESET_ALL}")

def process_file(args):
    file_path, search_term, output_file, block_size, verbose = args
    search_in_file(file_path, search_term, output_file, block_size, verbose)
    

def split_wordlist(file_path, max_size_mb=100):
    """
    Splits a large file into smaller chunks stored in a new folder with a structured naming convention.

    Args:
        file_path (str): Path to the input file.
        max_size_mb (int): Maximum size of each split file in MB. Default is 100MB.

    Returns:
        list: List of created file parts with their paths.
    """
    max_size_bytes = max_size_mb * 1024 * 1024  # Convert MB to bytes
    file_size = os.path.getsize(file_path)  # Get the total file size
    num_parts = (file_size + max_size_bytes - 1) // max_size_bytes  # Compute minimum number of parts
    num_digits = len(str(num_parts))  # Determine padding for filenames

    # Create output directory: filename_part/
    base_name = os.path.basename(file_path)
    output_folder = f"{base_name}_part"
    os.makedirs(output_folder, exist_ok=True)  # Ensure the directory exists

    part_files = []

    with open(file_path, 'rb') as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
        print(f"Splitting '{file_path}' ({file_size} bytes) into {num_parts} parts of ~{max_size_bytes} bytes each.")
        pbar = tqdm(total=file_size, unit='B', unit_scale=True, desc="Splitting")

        for i in range(num_parts):
            part_name = os.path.join(output_folder, f"{base_name}_{str(i+1).zfill(num_digits)}")
            with open(part_name, 'wb') as part:
                start = i * max_size_bytes
                end = min(start + max_size_bytes, file_size)
                part.write(mm[start:end])  # Efficient writing using mmap
                pbar.update(end - start)
            
            part_files.append(part_name)

        pbar.close()

    print(f"Files saved in: {output_folder}")


# CLI commands configuration
parser = argparse.ArgumentParser(description="Search for a password inside a [massive] wordlist.")
parser.add_argument("file_path", help="The path to the wordlist.")
parser.add_argument("search_term", nargs="?", help="The password (or part of the password) to search for.")
parser.add_argument("-b", "--block_size", type=int, default=1024*1024, help="Reading block size in bytes (default 1 MB).")
parser.add_argument("--output", type=str, help="Specify output file name. Default: keyhunter_results/result_<date>.txt")
parser.add_argument("-v", "--verbose", action="store_true", help="Verbose.")
parser.add_argument("--workers", type=int, default=max(1, os.cpu_count() - 4), help="Number of parallel workers (default: CPU count - 4).")

parser.add_argument("-s", "--split", action="store_true", help="Split a wordlist in multiple small parts.")
parser.add_argument("--max_size", type=int, default=100, help="Max size per split file in MB (default: 100MB).") # Max size Github allows

args = parser.parse_args()

print_logo()

# Ensure output directory exists
output_dir = "keyhunter_results"
os.makedirs(output_dir, exist_ok=True)
# Default output
output_file = args.output if args.output else os.path.join(output_dir, f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")


if args.split:
    split_wordlist(args.file_path, args.max_size)
    exit(0)  # Exit after splitting
else: # Direct search without splitting
    # Determine if input is a single file or a directory
    if os.path.isdir(args.file_path):
        files = []
        for root, _, filenames in os.walk(args.file_path):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                files.append(file_path)
    else:
        files = [args.file_path]
    
    # Process files in parallel
    with multiprocessing.Pool(args.workers) as pool:
        pool.map(process_file, [(file, args.search_term, output_file, args.block_size, args.verbose) for file in files])
    print(f"{Fore.BLUE}Results saved at: {output_file}{Style.RESET_ALL}")
