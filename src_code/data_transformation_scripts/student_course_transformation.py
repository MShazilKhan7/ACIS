import pandas as pd

def transform_feedback_data(input_csv, output_csv):
    """
    Transforms qualitative feedback (Very Poor → Excellent)
    into numeric format, retains text feedback,
    and saves as a clean new CSV.
    """
    df = pd.read_csv(input_csv)

    # Define mapping for feedback ratings
    rating_to_score = {
        "Very Poor": 1,
        "Poor": 2,
        "Average": 3,
        "Good": 4,
        "Excellent": 5
    }

    # Columns to transform (ignore ID, course, and text feedback)
    feedback_columns = [col for col in df.columns if col not in ["student_id", "course", "text_feedback"]]

    # Map ratings to numeric values directly (replace the text columns)
    for col in feedback_columns:
        df[col] = df[col].map(rating_to_score)

    # Keep numeric columns + identifying + text feedback column
    transformed_df = df[["student_id", "course"] + feedback_columns + ["text_feedback"]]

    # Save the numeric + text feedback file
    transformed_df.to_csv(output_csv, index=False)

    print(f"✅ Transformed feedback (numeric + text) saved to:\n{output_csv}")
    return output_csv


if __name__ == "__main__":
    # Input and output file paths
    input_csv = r"E:\Apps\DS hackathon\data\Machine_Learning_feedback.csv"
    output_csv = r"E:\Apps\DS hackathon\data\Machine_Learning_feedback_numeric.csv"

    transform_feedback_data(input_csv, output_csv)
