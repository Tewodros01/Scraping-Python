import os
import inflect
import joblib
import re


class Experience:

    # Initialize the inflect engine
    init = inflect.engine()

    @classmethod
    def convert_numbers_to_words(cls, text):
        if text is None:
            return ""  # Return an empty string if text is None

        numbers = re.findall(r"\d+", text)
        for number in numbers:
            word = cls.init.number_to_words(number)
            text = text.replace(number, word)

        return text

    @classmethod
    def getExperience(cls, text):
        if text is None:
            text = ""  # Replace None with an empty string to avoid issues

        model_path = os.path.join(
            os.path.dirname(__file__), "saved_sgd_EL_model.joblib"
        )  # Model path
        pipeline_loaded = joblib.load(model_path)
        processed_text = cls.convert_numbers_to_words(text)
        prediction = pipeline_loaded.predict([processed_text])

        return cls.getCareerLevel(prediction[0]), prediction[0]

    @classmethod
    def getCareerLevel(cls, text):
        if text == "Fresh":
            return "Student"

        match = re.search(r"\d+", text)
        if match:
            match = int(match.group())
            if match < 2:
                return "Entry"
            elif 2 <= match < 4:
                return "Junior Level"
            elif 4 <= match < 7:
                return "Mid-Level"
            elif 7 <= match < 10:
                return "Senior-Level"
            elif match >= 10:
                return "Executive"
            else:
                return "unknown"
        else:
            return "NA"
