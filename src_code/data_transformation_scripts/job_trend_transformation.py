import pandas as pd
import re

def transform_job_trend_data(input_csv, output_csv):
    """
    Transforms a raw job market trends dataset into a clean, analysis-ready form.
    Keeps only relevant columns and standardizes text fields.
    """

    # Load dataset
    df = pd.read_csv(input_csv)

    # ----------------------------
    # 1️⃣ Keep only useful columns
    # ----------------------------
    keep_cols = [
        "job_title",
        "required_skills",
        "salary_usd",
        "experience_level",
        "industry"
    ]
    df = df[keep_cols]

    # ----------------------------
    # 2️⃣ Clean salary column
    # ----------------------------
    # Remove invalid or non-numeric salaries
    df["salary_usd"] = (
        df["salary_usd"]
        .astype(str)
        .str.replace(r"[^0-9.]", "", regex=True)
        .replace("", None)
        .astype(float)
    )

    # Drop rows with missing salary or job title
    df = df.dropna(subset=["job_title", "required_skills"])

    # ----------------------------
    # 3️⃣ Normalize text fields
    # ----------------------------
    df["job_title"] = df["job_title"].str.strip().str.lower()
    df["required_skills"] = (
        df["required_skills"]
        .str.lower()
        .apply(lambda x: re.sub(r"[^a-z0-9, +#\-/]", "", x))
    )
    df["experience_level"] = df["experience_level"].str.strip().str.title()
    df["industry"] = df["industry"].fillna("Unknown").str.title()

    # ----------------------------
    # 4️⃣ Expand multiple skills into list-like structure
    # ----------------------------
    # Standardize delimiters
    df["required_skills"] = df["required_skills"].str.replace(";", ",")
    df["required_skills"] = df["required_skills"].str.replace("|", ",", regex=False)
    df["required_skills"] = df["required_skills"].str.replace(" / ", ",", regex=False)

    # Deduplicate comma-separated skills
    def clean_skill_list(skill_str):
        skills = [s.strip() for s in skill_str.split(",") if s.strip()]
        unique = list(dict.fromkeys(skills))  # preserve order, remove duplicates
        return ", ".join(unique)

    df["required_skills"] = df["required_skills"].apply(clean_skill_list)

    # ----------------------------
    # 5️⃣ Normalize salary scale (optional)
    # ----------------------------
    # Remove outliers for unrealistic salaries
    df = df[df["salary_usd"].between(1000, 500000)]

    # ----------------------------
    # 6️⃣ Compute derived stats (for better filtering later)
    # ----------------------------
    # Example: salary buckets
    bins = [0, 50000, 100000, 150000, 200000, 500000]
    labels = ["<50K", "50–100K", "100–150K", "150–200K", "200K+"]
    df["salary_bucket"] = pd.cut(df["salary_usd"], bins=bins, labels=labels)

    # ----------------------------
    # 7️⃣ Save transformed dataset
    # ----------------------------
    df.to_csv(output_csv, index=False)

    print(f"✅ Job trends data transformed and saved to: {output_csv}")
    print(f"📊 Shape: {df.shape[0]} rows, {df.shape[1]} columns")

    return output_csv


# Example usage
if __name__ == "__main__":
    transform_job_trend_data(
        input_csv=r"E:\Apps\DS hackathon\data\ai_job_market_2024_2025.csv",
        output_csv=r"E:\Apps\DS hackathon\data\ai_job_market_2024_2025_transformed.csv"
        
)
