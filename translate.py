import cv2
from google.cloud import translate_v2 as translate
from google.cloud import vision
import os
import tkinter as tk
from tkinter import ttk
import re

# Set the environment variable to the path of your JSON key file
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'path_to_your_json_key_file'

# Create the Google Cloud Vision API client
vision_client = vision.ImageAnnotatorClient()

# Create the Google Translate API client
translate_client = translate.Client()

# Define the font properties for the translated text overlay
font = cv2.FONT_HERSHEY_SIMPLEX
scale = 0.5
color = (0, 0, 255)
thickness = 1

# Define the source and target languages
source_language = ""
target_language = ""
video_source = ""
frame_interval = ""

# Function to convert language codes to names and vice versa
def get_language_name_to_code_map(supported_languages):
    return {lang['name']: lang['language'] for lang in supported_languages}

def get_language_code_to_name_map(supported_languages):
    return {lang['language']: lang['name'] for lang in supported_languages}

# Function to select the source and target languages using a GUI
def select_languages():
    # Get the supported languages for the Google Translate API
    supported_languages = translate_client.get_languages()
    language_name_to_code = get_language_name_to_code_map(supported_languages)
    language_code_to_name = get_language_code_to_name_map(supported_languages)

    # Create the main window and set its properties
    root = tk.Tk()
    root.title("Select Languages and Video Source")
    root.geometry("400x400")

    # Create the label and combobox for selecting the source language
    source_label = ttk.Label(root, text="Source Language:")
    source_label.pack(pady=5)
    source_combobox = ttk.Combobox(root, state="readonly", values=list(language_code_to_name.values()))
    source_combobox.pack(pady=5)

    # Create the label and combobox for selecting the target language
    target_label = ttk.Label(root, text="Target Language:")
    target_label.pack(pady=5)
    target_combobox = ttk.Combobox(root, state="readonly", values=list(language_code_to_name.values()))
    target_combobox.pack(pady=5)

    # Create the label and combobox for selecting the video source
    video_source_label = ttk.Label(root, text="Video Source:")
    video_source_label.pack(pady=5)
    video_source_combobox = ttk.Combobox(root, state="readonly", values=list(range(3)))
    video_source_combobox.pack(pady=5)

    # Create the label and entry for setting the frame interval
    frame_interval_label = ttk.Label(root, text="Frame Interval:")
    frame_interval_label.pack(pady=5)
    frame_interval_entry = ttk.Entry(root)
    frame_interval_entry.pack(pady=5)

    # Function to handle the "OK" button click event
    def ok_button_click():
        global source_language
        global target_language
        global video_source
        global frame_interval
        source_language = language_name_to_code[source_combobox.get()]
        target_language = language_name_to_code[target_combobox.get()]
        video_source = int(video_source_combobox.get())
        frame_interval = int(frame_interval_entry.get())
        root.destroy()

    # Create the "OK" button
    ok_button = ttk.Button(root, text="OK", command=ok_button_click)
    ok_button.pack(pady=10)

    # Start the main event loop
    root.mainloop()

# Function to extract and translate text
def extract_and_translate_text(response):
    if not response:
        return {}

    translated_sentences = {}

    # Extract all the text blocks from the response
    for annotation in response.text_annotations[1:]:
        text_block = annotation.description

        # Filter the extracted text
        if text_block:

            # Translate the filtered text using the Google Translate API
            result = translate_client.translate(text_block, target_language=target_language, source_language=source_language)
            print(f"Translation result: {result}")

            # Split the translated text into individual sentences
            translated_sentences_list = result['translatedText'].split('\n')
            print(f"Translated sentences list: {translated_sentences_list}")


            # Save the translated sentences and their bounding box coordinates
            start_index = 0
            for sentence in translated_sentences_list:
                end_index = start_index + len(text_block)
                vertices_tuple = (annotation.bounding_poly.vertices[0], result['translatedText'], annotation.bounding_poly.vertices[2].y - annotation.bounding_poly.vertices[0].y)
                translated_sentences[sentence] = vertices_tuple
                start_index = end_index

    return translated_sentences

# Function to convert OpenCV image to Vision API compatible format
def cv2_to_vision(cv2_image):
    is_success, im_buf_arr = cv2.imencode(".jpg", cv2_image)
    byte_im = im_buf_arr.tobytes()
    image = vision.Image(content=byte_im)
    return image

# Function to get video capture
def get_video_capture(source):
    cap = cv2.VideoCapture(source)
    if cap is None or not cap.isOpened():
        raise Exception("No valid video source found")
    return cap

# Function to put text with background
def put_text_with_background(img, text, x, y, font, scale, color, thickness, bg_color=(255, 255, 255), bg_padding=5):
    (text_w, text_h), _ = cv2.getTextSize(text, font, scale, thickness)

    # Draw the background rectangle
    cv2.rectangle(img, (x - bg_padding, y - text_h - bg_padding),
                  (x + text_w + bg_padding, y + bg_padding), bg_color, -1)

    # Draw the text
    cv2.putText(img, text, (x, y), font, scale, color, thickness)

# Call the select_languages() function before using the video_source variable
select_languages()

# Capture video from webcam
cap = get_video_capture(video_source)
print(f"Video source: {video_source}")

frame_counter = 0
previous_translations = {}
translation_lifespan = 10

while True:
    # Read a frame from the video feed
    ret, frame = cap.read()
    frame_counter += 1

    if ret:
        print("Frame captured")
        try:
            if frame_counter % frame_interval == 0:
                # Convert the frame to grayscale
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                # Threshold the grayscale image to remove noise
                _, thresholded = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

                # Invert the thresholded image to make text black
                inverted = cv2.bitwise_not(thresholded)

                # Convert the OpenCV image to Vision API compatible format
                vision_image = cv2_to_vision(inverted)

                # Use Google Cloud Vision API to extract text from the frame
                response = vision_client.document_text_detection(image=vision_image)
                print("Detected text: ", response.full_text_annotation.text)


                # Extract and translate individual text blocks from the response
                new_translated_sentences = extract_and_translate_text(response)
                print(f"New translated sentences: {new_translated_sentences}")


                # Update previous_translations with new translations
                for sentence, (vertex, translated_text, _) in new_translated_sentences.items():
                    x = vertex.x
                    y = vertex.y
                    previous_translations[sentence] = (frame_counter, (x, y))

                # Decrement lifespan of existing translations and remove if lifespan reaches 0
                sentences_to_remove = []
                for sentence, (start_frame, (x, y)) in previous_translations.items():
                    lifespan = frame_counter - start_frame
                    if lifespan <= translation_lifespan:
                        put_text_with_background(frame, sentence, x, y, font, scale, color, thickness)  # Fixed: Call put_text_with_background() instead of cv2.putText()
                    else:
                        sentences_to_remove.append(sentence)

                for sentence in sentences_to_remove:
                    print(f"Removed sentences: {sentences_to_remove}")
                    del previous_translations[sentence]


            # Overlay the remaining translations on the frame
            for text, (frame_counter, (x, y)) in previous_translations.items():
                cv2.putText(frame, text, (x, y), font, scale, color, thickness)


            # Display the frame with the translated text
            cv2.imshow("Translated Video", frame)


            # Break the loop if the 'q' key is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        except Exception as e:
            print(e)
            break

    else:
        break

# Release the video capture and close the display window
cap.release()
cv2.destroyAllWindows()
