import pandas as pd
import random
import os

# List of courses (from transcript)
courses = [
    "Machine Learning",
]

# Letter grade boundaries
def get_grade(marks):
    if marks >= 85:
        return "A+", 4.0
    elif marks >= 80:
        return "A", 3.7
    elif marks >= 75:
        return "A-", 3.5
    elif marks >= 70:
        return "B+", 3.3
    elif marks >= 65:
        return "B", 3.0
    elif marks >= 60:
        return "C+", 2.7
    elif marks >= 55:
        return "C", 2.5
    elif marks >= 50:
        return "D", 2.0
    else:
        return "F", 0.0

# Semester options (for diversity)
semesters = ["Fall 2023", "Spring 2024", "Fall 2024"]

# Generate data per course
num_students = 200  # adjust as needed

for course in courses:
    data = []
    for i in range(1, num_students + 1):
        student_id = f"S{i:03d}"
        student_name = f"Student_{i}"
        marks = random.gauss(72, 10)  # normal distribution centered around 72%
        marks = min(max(int(marks), 35), 100)  # clip to 35–100
        grade, gp = get_grade(marks)
        attendance = round(random.uniform(70, 100), 1)
        semester = random.choice(semesters)

        data.append({
            "student_id": student_id,
            "student_name": student_name,
            "course": course,
            "marks_obtained": marks,
            "total_marks": 100,
            "grade": grade,
            "grade_points": gp,
            "attendance_percentage": attendance,
            "semester": semester,
        })

    df = pd.DataFrame(data)
    safe_name = course.lower().replace(" ", "_").replace("&", "and")
    file_path = r"E:\Apps\DS hackathon\data\{safe_name}_performance.csv".format(safe_name=safe_name)
    df.to_csv(file_path, index=False)
    print(f"✅ Generated performance data for: {course} → {file_path}")

print("\nAll course performance files generated successfully!")
