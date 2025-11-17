# HandRecognition
Hand recognition (soon to connect with an audioplayer) using mediapipe, opencv, and tensorflow  

## Setup
- Open terminal and create virtual environment
    - `python -m venv desired_name_of_virtual_env`
- activate venv with
    - `source venv/bin/activate` for linux/mac
    - `venv\Scripts\activate` 
- Download modules for mediapipe, opencv, and tensorflow
  - `pip install mediapipe==0.10.21 opencv-python==4.10.0.84 tensorflow==2.16.1 "numpy<2.0"`

## How to use
- collect data with **collect_data.py**
- train by running **train_model.py**

- (Optional) reset dataset with **reset_gestures.py**

## Disclaimer
- Made with ChatGPT
- On first use, run collect_data.py and train_model.py before running main.py
