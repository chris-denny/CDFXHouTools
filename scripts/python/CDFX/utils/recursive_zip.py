"""
This module provides functionality to recursively search a directory for specifically named folders,
and create a .zip backup of their contents. The zip file name is timestamped. Entries are recorded
in a .csv file within each backup folder.
"""
import argparse
import csv
import datetime
import os
import sys
import re
import zipfile
import stat
import time
import concurrent.futures
from operator import itemgetter
import threading


class RecursiveZipper:
    def __init__(self):
        self.args = self.parse_arguments()
        self.folders_dict = {}
        self.folder_pattern = re.compile(f"^{re.escape(self.args.folder)}$", re.IGNORECASE)
        self.progress_lock = threading.Lock()
        self.progress_lines = {}

    def parse_arguments(self):
        parser = argparse.ArgumentParser(
            description="Recursively search a directory for specifically named folders, and create .zip backup of their contents. "
            "System folders and hidden folders and files will be ignored. Existing generated zip files will be skipped. "
            "The zip file name is timestamped. Entries are recorded in a .csv file within each backup folder."
        )
        parser.add_argument("directory", type=str, help="The directory to search.")
        parser.add_argument("folder", type=str, help="The name of the folder to search for.")
        parser.add_argument("-z", "--zip", action="store_true", help="Force files to be zipped.")
        parser.add_argument("-d", "--delete", action="store_true", help="Force files to be deleted.")
        parser.add_argument(
            "-u",
            "--unattended",
            action="store_true",
            help="Run in unattended mode without prompting for user input.",
        )
        parser.add_argument(
            "-p",
            "--parallel",
            type=int,
            default=4,
            choices=range(1, 17),
            metavar="1-16",
            help="Number of parallel zip processes to run. Defaults to 4.",
        )
        parser.add_argument(
            "-c",
            "--compression",
            type=int,
            default=2,
            choices=range(0, 10),
            metavar="0-9",
            help="Compression level for ZIP_DEFLATED. 0 for no compression, 9 for highest (default: 2).",
        )
        return parser.parse_args()
    
    def is_hidden(self, path):
        if os.name == "nt": # For Windows
            attributes = os.stat(path).st_file_attributes
            return bool(attributes & stat.FILE_ATTRIBUTE_HIDDEN or 
                    attributes & stat.FILE_ATTRIBUTE_SYSTEM)
        else: # For Linux and Mac
            return os.path.basename(path).startswith(".")

    def get_size_mb(self, size_bytes):
        return round(size_bytes / 1_000_000, 2)
    
    def find_folders(self):
        list_file_name = f"{self.args.folder}_zip_log.csv"
        current_datetime = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_pattern = re.compile(rf"{re.escape(self.args.folder)}_\d{{8}}_\d{{6}}\.zip", re.IGNORECASE)

        for root, dirs, _ in os.walk(self.args.directory):
            dirs[:] = [d for d in dirs if not self.is_hidden(os.path.join(root, d))]
            matching_dirs = [d for d in dirs if self.folder_pattern.match(d)]
            for matched_dir in matching_dirs:
                backups_dir = os.path.join(root, matched_dir)

                zip_file_name = f"{matched_dir}_{current_datetime}.zip"
                existing_zips = [f for f in os.listdir(backups_dir) if zip_pattern.match(f)]
                exclude_files = set(existing_zips + [list_file_name])
                
                backup_files = self.create_backup_files(backups_dir, exclude_files)
                if backup_files:
                    if self.args.unattended:
                        should_zip = self.args.zip
                        should_delete = self.args.delete
                        if not should_zip and not should_delete:
                            print(f"No action specified for '{matched_dir}' within {root}")
                    else:
                        should_zip = self.print_and_confirm_files("zip", backups_dir, backup_files)
                        if should_zip:
                            should_delete = self.print_and_confirm_files("delete", backups_dir, backup_files)
                        else:
                            should_delete = False
                    if should_zip:
                        self.folders_dict[backups_dir] = {
                            "zip_name": zip_file_name,
                            "zip_path": os.path.join(backups_dir, zip_file_name),
                            "list_path": os.path.join(backups_dir, list_file_name),
                            "file_list": backup_files,
                            "delete": should_delete,
                        }
                else:
                    print(f"No files to compress in '{matched_dir}' within {root}")

    def create_backup_files(self, backups_dir, exclude_files):
        backup_files = []
        for root, _, files in os.walk(backups_dir):
            for file in files:
                if (file not in exclude_files and not self.is_hidden(os.path.join(root, file))):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, backups_dir)
                    file_size = round(os.path.getsize(file_path) / 1000)
                    backup_files.append((relative_path, file_size))
        return backup_files

    def print_and_confirm_files(self, action, backups_dir, files):
        total_size_mb = self.get_size_mb(sum(size for _, size in files) * 1_000)

        message = f"Files to {action} in {backups_dir}:\n"
        if (action == "zip"):
            if len(files) > 10:
                for file, size in files[:5]:
                    message += f"{file} ({size} kB)\n"
                message += f"... {len(files) - 10} more files ...\n"
                for file, size in files[-5:]:
                    message += f"{file} ({size} kB)\n"
            else:
                for file, size in files:
                    message += f"{file} ({size} kB)\n"
            
            message += f"Folder: {backups_dir}\n    Num Files: {len(files)}\n    Total size: {total_size_mb} MB\n"
            print(message)
        
        if (action == "zip" and self.args.zip) or (action == "delete" and self.args.delete):
            return True
        
        return input(f"Do you want to {action} these files? (y/n): ").strip().lower() == "y"

    def update_progress(self, folder_path, index, total_files, file, size):
        progress = index / total_files
        bar_length = 20
        filled_length = int(bar_length * progress)
        bar = "=" * filled_length + "-" * (bar_length - filled_length)
        progress_line = f"[{bar}] {index}/{total_files} {folder_path}/{file}, {size}kB"
        
        with self.progress_lock:
            if folder_path not in self.progress_lines:
                self.progress_lines[folder_path] = len(self.progress_lines)
            line_number = self.progress_lines[folder_path]
            self.print_progress(line_number, progress_line)

    def print_progress(self, line_number, progress_line):
        print(f"\033[{line_number + 1};0H\033[K{progress_line}", end="", flush=True)

    def multithreaded_zip(self, folder_path, folder_info):
        zip_file_name = folder_info["zip_path"]

        if os.path.exists(zip_file_name):
            return f"Skipped '{folder_path}', a zip file with the same timestamp already exists."
        total_files = len(folder_info["file_list"])
        total_size_mb = sum(size / 1_000 for _, size in folder_info["file_list"])  # Convert kB to MB

        try:
            with zipfile.ZipFile(zip_file_name, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=self.args.compression) as zip_file, \
                 open(folder_info["list_path"], "a", newline="") as list_file:
                writer = csv.DictWriter(
                    list_file, fieldnames=["Time", "Filename", "Size in kB", "Zip File"]
                )
                if list_file.tell() == 0:
                    writer.writeheader()

                successfully_zipped = []
                if not __name__ == "__main__":
                    print(f"Processing {folder_path}...")
                for index, (file, size) in enumerate(sorted(folder_info["file_list"], key=itemgetter(1)), 1):
                    full_path = os.path.join(folder_path, file)
                    try:
                        zip_file.write(full_path, file)
                        if __name__ == "__main__":
                            self.update_progress(folder_path, index, total_files, file, size)

                        time_current = datetime.datetime.now().replace(microsecond=0)
                        writer.writerow({
                            "Time": time_current,
                            "Filename": file,
                            "Size in kB": size,
                            "Zip File": folder_info["zip_name"],
                        })
                        successfully_zipped.append(file)
                    except FileNotFoundError:
                        print(f"Warning: File not found and skipped: {full_path}")
                    except PermissionError:
                        print(f"Warning: Permission denied for file: {full_path}")
                    except Exception as e:
                        print(f"Error processing file {full_path}: {str(e)}")
                    
            folder_info["successfully_zipped"] = successfully_zipped

            zip_size_mb = self.get_size_mb(os.path.getsize(zip_file_name))
            saved_mb = round(total_size_mb - zip_size_mb, 2)
            
            if __name__ == "__main__":
                newline = "\n"
            else:
                newline = ""
            return f"{newline}All files in '{folder_path}' added to '{zip_file_name}' Saved: {saved_mb:.2f} MB"
            
        except zipfile.BadZipFile:
            folder_info["delete"] = False
            print(f"Error: Failed to create zip file {zip_file_name}. The zip file may be corrupted.")
            if os.path.exists(zip_file_name):
                os.remove(zip_file_name)
            return f"Failed to create zip file for '{folder_path}'. The operation was aborted."
        except PermissionError:
            folder_info["delete"] = False
            return f"Error: Permission denied when creating zip file {zip_file_name}"
        except Exception as e:
            folder_info["delete"] = False
            return f"An unexpected error occurred while processing '{folder_path}': {str(e)}"
            
    def export_zip(self):
        if __name__ == "__main__":
            print("\033[2J\033[H")  # Clear screen and move cursor to top-left
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.args.parallel) as executor:
            futures = [executor.submit(self.multithreaded_zip, k, v) for k, v in self.folders_dict.items()]
            for future in concurrent.futures.as_completed(futures):
                print(future.result())

    def delete_files(self):
        for folder_path, folder_info in self.folders_dict.items():
            if folder_info["delete"]:
                deleted_files = 0
                deleted_folders = 0
                for root, dirs, files in os.walk(folder_path, topdown=False):
                    for file in files:
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(file_path, folder_path)
                        if relative_path in folder_info.get("successfully_zipped", []):
                            if os.path.exists(file_path):
                                try:
                                    os.remove(file_path)
                                    deleted_files += 1
                                except OSError as e:
                                    print(f"Error deleting file {file_path}: {e}")
                            else:
                                print(f"File not found: {file_path}")
                    for dir in dirs:
                        dir_path = os.path.join(root, dir)
                        if os.path.exists(dir_path) and not os.listdir(dir_path):
                            try:
                                os.rmdir(dir_path)
                                deleted_folders += 1
                            except OSError as e:
                                print(f"Error deleting folder {dir_path}: {e}")
                print(f"Deleted {deleted_files} files and {deleted_folders} empty folders from {folder_path}")


    def run(self):
        if os.path.exists(self.args.directory):
            self.find_folders()
        else:
            print("Directory not found")
            return
        if self.folders_dict:
            start_time = time.time()
            self.export_zip()
            self.delete_files()
            end_time = time.time()
            execution_time = end_time - start_time
            print(f"Total execution time: {execution_time:.2f} seconds")


def run_recursive_zipper(directory, folder, zip=False, delete=False, unattended=False, parallel=4, compression=2, print_and_confirm_callback=None):
    """
    Run the RecursiveZipper with the given parameters.
    
    :param directory: The directory to search.
    :param folder: The name of the folder to search for.
    :param zip: Force files to be zipped.
    :param delete: Force files to be deleted.
    :param unattended: Run in unattended mode without prompting for user input.
    :param parallel: Number of parallel zip processes to run.
    :param compression: Compression level for ZIP_DEFLATED.
    :param print_and_confirm_callback: Callback function for user confirmation.
    :return: Total execution time in seconds.
    """
    sys.argv = [sys.argv[0], directory, folder]  # Set positional arguments
    if zip:
        sys.argv.append("--zip")
    if delete:
        sys.argv.append("--delete")
    if unattended:
        sys.argv.append("--unattended")
    sys.argv.extend(["--parallel", str(parallel)])
    sys.argv.extend(["--compression", str(compression)])\
    
    zipper = RecursiveZipper()
    if print_and_confirm_callback:
        zipper.print_and_confirm_files = print_and_confirm_callback
    zipper.run()
    


if __name__ == "__main__":
    zipper = RecursiveZipper()
    start_time = time.time()
    zipper.run()
    end_time = time.time()
    print(f"Total execution time: {end_time - start_time:.2f} seconds")
