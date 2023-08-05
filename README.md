# Real-Time Video Translation Using Google Cloud Vision and Translate APIs

This project allows you to perform real-time translations of text detected in a video feed using Google Cloud Vision API for text detection and Google Translate API for translation. The video source can be from a webcam or a video file.

## Prerequisites

1. Python 3.6 or higher
2. OpenCV, Google Cloud, and tkinter libraries installed in Python
3. A Google Cloud account with Vision API and Translate API enabled
4. A valid JSON key file for authenticating with Google Cloud

## Usage

1. Set the path to your Google Cloud JSON key file in the `os.environ['GOOGLE_APPLICATION_CREDENTIALS']` variable in the script.

2. Run the script. A graphical user interface (GUI) will appear.

3. In the GUI, select the source language (the language of the text in the video), the target language (the language to which the text should be translated), the video source (0 for the default webcam, 1 for a secondary webcam, or the path to a video file), and the frame interval (how often frames should be processed).

4. Press the "OK" button in the GUI. The video feed will appear, and any text detected in the frames will be translated and overlayed on the frames.

5. Press 'q' to quit the video feed.

## Notes

The translated text is displayed for a set number of frames (defined by the `translation_lifespan` variable in the script) before being removed.
