import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
import pickle
import os

class WellnessModel:
    def __init__(self):
        self.model = LinearRegression()
        self.model_path = "wellness_model.pkl"
        
        # If model exists, load it; otherwise train a new one with synthetic data
        if os.path.exists(self.model_path):
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
        else:
            self.train_on_synthetic_data()

    def train_on_synthetic_data(self):
        """
        Generates synthetic data to train the model.
        Features: [Screen Time (hrs), App Switches, Time Of Day (0-23)]
        Target: Focus Score (0-100)
        """
        np.random.seed(42)
        num_samples = 1000
        
        # Screen Time: 0 to 12 hours
        screen_time = np.random.uniform(0, 12, num_samples)
        
        # App Switches: 10 to 500
        app_switches = np.random.randint(10, 501, num_samples)
        
        # Time of Day: 0 to 23
        time_of_day = np.random.randint(0, 24, num_samples)
        
        X = np.column_stack((screen_time, app_switches, time_of_day))
        
        # Arbitrary logic for focus score:
        # Lower screen time = higher focus
        # Lower app switches = higher focus
        # Morning (8-11) = peak focus
        y = (
            100 
            - (screen_time * 5) 
            - (app_switches / 10) 
            + np.where((time_of_day >= 8) & (time_of_day <= 11), 15, 0)
            + np.random.normal(0, 5, num_samples) # Add some noise
        )
        
        # Clip y to [0, 100]
        y = np.clip(y, 0, 100)
        
        self.model.fit(X, y)
        
        # Save model
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)

    def predict_focus_score(self, screen_time, app_switches, hour):
        """
        Predicts the focus score for a given set of parameters.
        """
        X_input = np.array([[screen_time, app_switches, hour]])
        prediction = self.model.predict(X_input)[0]
        return round(float(np.clip(prediction, 0, 100)), 1)

# Singleton instance
model_instance = WellnessModel()
