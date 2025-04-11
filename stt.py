import os
import queue
import pyaudio
from google.cloud import speech
from profanity_check import predict_prob

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "key.json"


def check_profanity(phrase):
    probability = predict_prob(phrase)
    if probability > 0.7:
        print("watch your mouth")


def stt():
    # Initialize Google Speech client
    client = speech.SpeechClient()

    # Define the recognition configuration
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code="en-US",
    )
    streaming_config = speech.StreamingRecognitionConfig(config=config, interim_results=True)

    # Create a queue to store audio data
    audio_queue = queue.Queue()

    # Define a function to capture audio data
    def audio_callback(in_data, frame_count, time_info, status):
        audio_queue.put(in_data)
        return None, pyaudio.paContinue

    # Initialize PyAudio and open a stream
    audio_interface = pyaudio.PyAudio()
    stream = audio_interface.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK,
        stream_callback=audio_callback,
    )

    print("Listening... Press Ctrl+C to stop.")

    try:
        # Generate requests for the Speech-to-Text API
        requests = (
            speech.StreamingRecognizeRequest(audio_content=audio_queue.get())
            for _ in iter(int, 1)
        )

        # Send the requests and process responses
        responses = client.streaming_recognize(streaming_config, requests)

        # for response in responses:
        #     for result in response.results:
        #         if result.is_final:
        #             print(f"Transcript: {result.alternatives[0].transcript}")
        #             check_profanity([result.alternatives[0].transcript])

        for response in responses:
            for result in response.results:
                print(f"Transcript: {result.alternatives[0].transcript}")
                check_profanity([result.alternatives[0].transcript])
    except KeyboardInterrupt:
        print("Stopped listening.")
    finally:
        # Stop and close the stream properly
        stream.stop_stream()
        stream.close()
        audio_interface.terminate()
