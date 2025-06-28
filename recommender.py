def get_recommendations(text):
    # Mock recommendation based on keywords
    if "AI" in text or "machine" in text:
        return ["AI Ethics – Blog", "Machine Learning Basics – Medium", "Deep Learning with Python"]
    elif "history" in text:
        return ["World History Overview", "Ancient Civilizations – Book Summary", "History of Science"]
    else:
        return ["Popular Articles", "Book Summary of the Week", "Trending Science Reads"]
