import pandas as pd
import random

# Define parameters
course_name = "Machine_Learning"
num_students = 200

# Feedback options for rating questions
options = ["Very Poor", "Poor", "Average", "Good", "Excellent"]

# Example text feedback templates
text_feedback_samples = [
    "Needs more real-world projects.",
    "Too much theory, please add more practical sessions.",
    "Excellent course! Loved the lectures.",
    "Good material but assessments are tough.",
    "More examples would make concepts clearer.",
    "Very interactive sessions, great learning experience!",
    "Include case studies from the industry.",
    "Slides are good but explanations can be improved.",
    "Add more coding assignments.",
    "Content is repetitive, can be made concise."
]

# Rating criteria
criteria = [
    "course_content",
    "lecture_delivery",
    "teaching_materials",
    "practicals",
    "assessment"
]

data = []

for i in range(1, num_students + 1):
    feedback = {
        "student_id": f"S{i:03d}",
        "course": course_name,
    }
    # Add ratings
    for c in criteria:
        feedback[c] = random.choice(options)
    # Add random text feedback
    feedback["text_feedback"] = random.choice(text_feedback_samples)
    data.append(feedback)

# Convert to DataFrame
df = pd.DataFrame(data)

# Save CSV
output_path = r"E:\Apps\DS hackathon\data\{course_name}_feedback.csv".format(course_name=course_name)
df.to_csv(output_path, index=False)

print(f"✅ Generated {num_students} feedback entries for course: {course_name}")
print(f"📁 Saved to: {output_path}")
print(df.head())
