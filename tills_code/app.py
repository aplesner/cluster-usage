from flask import Flask, render_template, send_file
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import io

from parser import run_parser


data_folder = "static/data"
app = Flask(__name__)


def load_and_process_data(data_folder):
    # Load all CSV files into a list of DataFrames
    all_files = [f for f in os.listdir(data_folder) if f.endswith(".csv")]
    df_list = []

    for file in all_files:
        file_path = os.path.join(data_folder, file)
        df = pd.read_csv(file_path)

        # Set the timestamp from the filename
        df["timestamp"] = file.replace(".csv", "")

        # Convert the 'timestamp' column to datetime format
        df["timestamp"] = pd.to_datetime(df["timestamp"], format='%Y-%m-%dT%H-%M-%S')

        df_list.append(df)

    # Concatenate all DataFrames into one
    full_df = pd.concat(df_list, ignore_index=True)

    # Use pivot_table to aggregate the data
    aggregated_df = full_df.pivot_table(
        index="timestamp",
        columns="user",
        values="total_files", # total_files, total_size
        aggfunc="sum",
        fill_value=0
    )

    # Sort the timestamps and keep the most recent 48
    aggregated_df = aggregated_df.tail(24*1)

    # Drop users that are 0 everywhere
    aggregated_df = aggregated_df.loc[:, (aggregated_df != 0).any(axis=0)]

    # Keep only the top 5 users based on the sum of their values
    # top_5_users = aggregated_df.sum().sort_values(ascending=False).head(3).index
    # aggregated_df = aggregated_df[top_5_users]

    # Print the aggregated DataFrame for inspection (optional)
    print(aggregated_df)
    print(aggregated_df.sum())

    return aggregated_df


def plot_data(aggregated_df):
    plt.figure(figsize=(12, 6))

    # Sort columns based on the sum of total files (descending)
    aggregated_df = aggregated_df[aggregated_df.sum().sort_values(ascending=False).index]

    # Plot line plot instead of bar plot
    aggregated_df.plot(kind='line', figsize=(12, 12))

    plt.xlabel("Timestamp")
    plt.ylabel("Total Files")

    # Set the x-axis to show year, month, day, hour
    plt.xticks(rotation=45, ha="right")
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))

    # Adjust the legend to be outside the plot, sorted by total files, with multiple columns
    plt.legend(title="User", bbox_to_anchor=(1.05, 1), loc='upper left', ncol=2)

    plt.tight_layout()

    # Save the plot to a BytesIO object to return as image
    img = io.BytesIO()
    plt.savefig(img, format="png", dpi=200)
    img.seek(0)
    return img


@app.route("/")
def index():
    run_parser()
    aggregated_df = load_and_process_data(data_folder)
    img = plot_data(aggregated_df)
    return send_file(img, mimetype="image/png")


if __name__ == "__main__":
    app.run(debug=True)
