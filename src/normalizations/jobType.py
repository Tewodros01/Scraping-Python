import joblib
import os

class JobType:
    
    assuption = ["rem", "remo", "remot", "remote", "mote", "rmote", "rmte", "remt", "rmt", "remte"]
    model_path = os.path.join(os.path.dirname(__file__), 'saved_sgd_wt_model.joblib')  # Model path
    
    @classmethod
    def predictJobType(cls, job_type):
        """
        Predict the job type for a given input using the trained model.
        """
        if not os.path.exists(cls.model_path):
            raise FileNotFoundError(f"Model file {cls.model_path} does not exist. Please ensure the model is trained and saved.")
        
        # Load the model from the specified path
        pipeline_loaded = joblib.load(cls.model_path)
        
        # Predict and return the job type
        prediction = pipeline_loaded.predict([job_type])

        if cls.isRemote(text=job_type):
            return prediction[0] + " (Remote)"
        
        return prediction[0]
    
    
    @classmethod
    def isRemote(cls, text):
        if any(word.lower() in text.lower() for word in cls.assuption):
            return True
        else:
            return False

# Example usage:
# prediction = JobType.predictJobType("full remo")
# print(prediction)
