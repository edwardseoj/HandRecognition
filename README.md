# HandRecognition
Hand recognition (soon to connect with an audioplayer) using mediapipe, opencv, and tensorflow  

## Setup
- Open terminal and create virtual environment
    - `python -m venv desired_name_of_virtual_env`
- activate myenv with
    - `source myenv/bin/activate` for linux/mac
    - `myenv\Scripts\activate` for windows (may need to make one yourself)
- import mediapipe, opencv, and tensorflow
  - `pip install mediapipe==0.10.21 opencv-python==4.10.0.84 tensorflow==2.16.1 numpy<2.0`

## How to use
- collect data with **collect_data.py**
- train by running **train_model.py**
- see real-time gesture recognition with **main.py**
- (Optional) reset dataset with **reset_gestures.py**

