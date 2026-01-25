# HandRecognition
Hand recognition (soon to connect with an audioplayer) using mediapipe, opencv, and tensorflow  

## Setup
- Download zip file from FinalTouchUp
- Download python 3.10.x (best if 3.10.11)
    - Anything more or less will break the code
    - verify with `python --version`
- Open terminal and create virtual environment
    - `python -m venv desired_name_of_virtual_env`
- activate venv with
    - `source venvName/bin/activate` for linux/mac
    - `venvName\Scripts\activate` for Windows
- Download modules for mediapipe, opencv, and tensorflow
  - `pip install mediapipe opencv-python numpy tensorflow pyqt5 keyboard pycawpip install "mediapipe==0.10.21" "numpy<2.0.0" "opencv-python>=4.5.0,<4.8.0" "tensorflow>=2.10.0,<2.13.0" "PyQt5>=5.15.0" keyboard pycaw`


## How to use
- run app.py
- Edit Commands will allow you to edit commands to your liking, as long as it is a valid command
- Reset will reset all commands to its default dataset labels (like, palm, fist, etc)
- Start recognition will open the camera and start hand recognition
    - Open Spotify first before pressing this button

## Limitations
- Made without Spotify API, thus commands are severely limited
- Mapping of gesture to commands are through *global key commands* and therefore, if other media players are opened, it may not directly communicate with Spotify
- Allows cross-compatibility but may experience performance overhead in Start Recognition (slow startup ~20 seconds), especially in Windows
