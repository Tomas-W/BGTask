# Task Manager App

A simple Kivy-based Android app to manage daily tasks. 

## Features

- Create tasks with date, time, and message
- View tasks organized by day
- Native Android date and time pickers
- Simple and intuitive interface

## Requirements

- Python 3.7+
- Kivy 2.1.0+
- For Android deployment:
  - Buildozer
  - Android SDK/NDK

## Dependencies

```
kivy==2.1.0
python-dateutil==2.8.2
```

## Running the App

### Desktop Testing

1. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the app:
   ```
   python main.py
   ```

### Android Deployment

1. Install Buildozer:
   ```
   pip install buildozer
   ```

2. Initialize buildozer:
   ```
   buildozer init
   ```

3. Edit buildozer.spec to configure the app build

4. Build and deploy to a connected Android device:
   ```
   buildozer android debug deploy run
   ```

## App Structure

- `main.py`: Main entry point for the app
- `task.py`: Task data model
- `taskmanager.py`: Manages task storage and retrieval
- `homescreen.py`: Home screen UI with task list
- `taskscreen.py`: Screen for creating new tasks
- `settings.py`: Color definitions and app settings

## Usage

1. Open the app
2. Tap the "+" button in the top bar to create a new task
3. Select date and time
4. Enter your task message
5. Tap "Save" to create the task
6. View your tasks organized by day on the home screen 