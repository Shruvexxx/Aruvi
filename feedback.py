def save_feedback(feedback_text):
    with open("feedback.txt", "a") as f:
        f.write(feedback_text + "\n")
