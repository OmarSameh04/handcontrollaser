import cv2
import mediapipe as mp
import serial
import time
import threading

# Initialize MediaPipe Hands and Video Capture
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
video = cv2.VideoCapture(0)

frame_width = 1600
frame_height = 900
sensitivity = 45
isArduinoAvailable = True

# Arduino Initialization
try:
    arduino = serial.Serial(port='/dev/ttyACM0', baudrate=2000000, timeout=10)
    time.sleep(0.001)
    print("Arduino connected successfully.")
    arduino.write("9998 9999".encode())  # Turn on Arduino initially
except serial.SerialException:
    print("Failed to communicate with Arduino.")
    isArduinoAvailable = False

# Define Arduino Commands
def reset():
    if isArduinoAvailable:
        arduino.write("960 1000".encode())
        time.sleep(0.1)
        arduino.write("960 540".encode())

def toggle():
    if isArduinoAvailable:
        arduino.write("9999 9999".encode())

def turn_off():
    if isArduinoAvailable:
        arduino.write("9998 9998".encode())

def turn_on():
    if isArduinoAvailable:
        arduino.write("9998 9999".encode())

# Reset Position Thread
def reset_position():
    global reset_flag
    reset_flag = threading.Event()
    while not reset_flag.is_set():
        reset()
        time.sleep(20)

# Start Reset Position Thread if Arduino is Available
if isArduinoAvailable:
    reset_thread = threading.Thread(target=reset_position)
    reset_thread.start()

# Main Loop for Hand Tracking and Arduino Control
try:
    while True:
        check, frame = video.read()
        if not check:
            print("Failed to read frame.")
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)
        frame = cv2.resize(frame, (frame_width, frame_height))

        if results.multi_hand_landmarks:
            landmark_count = 0
            sumX, sumY = 0, 0

            for hand_landmarks in results.multi_hand_landmarks:
                for landmark in hand_landmarks.landmark:
                    h, w, _ = frame.shape
                    cx, cy = int(landmark.x * w), int(landmark.y * h)
                    cv2.circle(frame, (cx, cy), 5, (0, 0, 0), cv2.FILLED)
                    sumX += cx
                    sumY += cy
                    landmark_count += 1

            # Calculate Average Coordinates and Send to Arduino
            if landmark_count > 0:
                average_x = sumX // landmark_count
                average_y = sumY // landmark_count
                cv2.circle(frame, (average_x, average_y), 10, (0, 255, 0), cv2.FILLED)

                if isArduinoAvailable:
                    arduino.write(f"{average_x} {average_y}".encode())
        
        cv2.imshow("Hand Tracking", frame)

        # Key Controls for Arduino
        key = cv2.waitKey(1)
        if key == ord('e'):
            break
        elif key == ord('l'):
            toggle()
        elif key == ord('r'):
            reset()
        elif key == ord('1'):
            turn_on()
        elif key == ord('2'):
            turn_off()

except Exception as e:
    print(f"An error occurred: {e}")
finally:
    # Clean up
    video.release()
    cv2.destroyAllWindows()
    if isArduinoAvailable:
        turn_off()
        reset_flag.set()
        reset_thread.join()
        arduino.close()
