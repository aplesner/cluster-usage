import pandas as pd
import re
import os
from datetime import datetime


def run_parser():
    # Open and read the file
    # with open("/usr/nostro/netvar/nfsdiostats/itetnas04/nfsdiostats_tik.log", "r", encoding="utf-8") as file:
    with open("io_usage.log", "r", encoding="utf-8") as file:
        content = file.read()

    # Split the content by "Log: "
    sections = content.split("Log: ")

    # Print the number of sections
    print(f"Total sections: {len(sections)}\n")

    for text_data in sections:
        lines = text_data.strip().split("\n")
        if len(lines) < 2:
            continue

        # Extract start time from the first line
        start_time_match = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \((\d+)\)", lines[0])
        if start_time_match:
            start_time = datetime.strptime(start_time_match.group(1), '%Y-%m-%d %H:%M:%S')
            timestamp = start_time.strftime("%Y-%m-%dT%H-%M-%S")
        else:
            start_time = None
            timestamp = "unknown_time"

        # Initialize lists to store parsed data
        locations = []
        users = []
        types_of_access = []
        total_files = []
        total_size = []

        # Regular expression to capture relevant parts of the text
        client_re = re.compile(r'@(rd|wr)_client\((\w+),(\w+)\)\[(\w+)\(([^)]+)\)\]:')
        data_re = re.compile(r'\[(.*?)\)\s*(\d+)\s\|')

        current_location, current_user, current_type = None, None, None

        for line in lines[1:]:
            client_match = client_re.match(line)
            if client_match:
                current_type = client_match.group(1)  # 'rd' or 'wr'
                current_location = client_match.group(2)
                current_user = client_match.group(4)

            data_match = data_re.match(line)
            if data_match and current_location and current_user:
                file_size_range = data_match.group(1)
                num_files = int(data_match.group(2))

                upper_bound = file_size_range.split(',')[1].strip().replace(')', '')
                size_in_bytes = 0
                if 'K' in upper_bound:
                    size_in_bytes = int(upper_bound.replace('K', '')) * 1024
                elif 'M' in upper_bound:
                    size_in_bytes = int(upper_bound.replace('M', '')) * 1024 ** 2
                elif 'G' in upper_bound:
                    size_in_bytes = int(upper_bound.replace('G', '')) * 1024 ** 3
                elif upper_bound.isdigit():
                    size_in_bytes = int(upper_bound)

                locations.append(current_location)
                users.append(current_user)
                types_of_access.append(current_type)
                total_files.append(num_files)
                total_size.append(size_in_bytes * num_files)

        df = pd.DataFrame({
            'location': locations,
            'user': users,
            'type_of_access': types_of_access,
            'total_files': total_files,
            'total_size': total_size
        })

        columns_to_sum = ['user', 'total_files', 'total_size']
        df_relevant = df[columns_to_sum]
        aggregated_df = df_relevant.groupby('user', as_index=False).sum()
        aggregated_df['total_size_GB'] = aggregated_df['total_size'] / (1024 ** 3)
        aggregated_df = aggregated_df.drop(columns='total_size')

        total_hours = 1
        average_files_per_hour = aggregated_df['total_files'].sum() / total_hours
        average_size_per_hour = aggregated_df['total_size_GB'].sum() / total_hours
        sorted_df = aggregated_df.sort_values(by='total_files', ascending=False)

        print(f'Time: {start_time.isoformat() if start_time else "N/A"}')
        print(f'Average total files per hour: {int(average_files_per_hour):,}')
        print(f'Average total size per hour (GB): {int(average_size_per_hour):,}')
        print(sorted_df)
        print("\n" + "="*50 + "\n")

        # Save DataFrame to CSV file
        filename = f"static/data/{timestamp}.csv"
        df.to_csv(filename, index=False)
        print(f"Saved data to {filename}\n")

if __name__ == "__main__":
    run_parser()
