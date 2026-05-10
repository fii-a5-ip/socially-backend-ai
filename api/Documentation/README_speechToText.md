# Speech-to-Text API Documentation

This module manages the speech-to-text API routing. It receives audio files via HTTP and utilizes the Groq Whisper API for high-fidelity transcription.

## ⚙️ Features

* **File Upload:** Accepts audio files (MP3, WAV, etc.) sent via `multipart/form-data`.
* **AI Transcription:** Leverages the Groq `whisper-large-v3` model for fast and accurate text conversion.
* **Automatic Cleanup:** To save disk space, the server automatically deletes the temporary file immediately after the transcription is generated.

---

## 🔌 Endpoints

### `POST /speechToText/`

Endpoint to receive an audio file and return its transcription.

* **Request Headers:** `Content-Type: multipart/form-data`
* **Request Body:** 
  * `file`: The audio file binary (MP3/WAV).

#### Responses:

| Status Code | Description | JSON Response Example |
| :--- | :--- | :--- |
| **200 OK** | Success | `{"status": "success", "transcription": "Hello world"}` |
| **400 Bad Request** | Missing file | `{"status": "error", "transcription": ""}` |
| **500 Internal Error** | API/Server Fail | `{"status": "error", "transcription": ""}` |

---

## ☕ Java Client Example (With Error Handling)

This client includes logic to handle file errors, connection timeouts, and server-side failures.

```java
import java.io.IOException;
import java.net.ConnectException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.http.HttpTimeoutException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.Duration;
import java.util.ArrayList;
import java.util.UUID;

public class SpeechToTextClient {
    public static void main(String[] args) {
        String endpointUrl = "[http://127.0.0.1:5000/speechToText/](http://127.0.0.1:5000/speechToText/)";
        Path filePath = Paths.get("audio_sample.mp3"); // Ensure this file exists

        // 1. Check if local file exists before sending
        if (!Files.exists(filePath)) {
            System.err.println("Error: The file " + filePath.toAbsolutePath() + " was not found.");
            return;
        }

        try {
            String boundary = "Boundary-" + UUID.randomUUID().toString();
            HttpClient client = HttpClient.newBuilder()
                    .connectTimeout(Duration.ofSeconds(10))
                    .build();

            byte[] multipartBody = createMultipartBody(filePath, boundary);

            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(endpointUrl))
                    .header("Content-Type", "multipart/form-data; boundary=" + boundary)
                    .POST(HttpRequest.BodyPublishers.ofByteArray(multipartBody))
                    .timeout(Duration.ofSeconds(60))
                    .build();

            System.out.println("Uploading and transcribing...");
            HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

            // 2. Handle HTTP-level errors
            if (response.statusCode() == 200) {
                System.out.println("Success! Response: " + response.body());
            } else {
                System.err.println("Server Error (Status " + response.statusCode() + "): " + response.body());
            }

        } catch (HttpTimeoutException e) {
            System.err.println("Error: The request timed out. The server might be busy.");
        } catch (ConnectException e) {
            System.err.println("Error: Could not connect to the server. Is the Flask app running?");
        } catch (IOException | InterruptedException e) {
            System.err.println("An unexpected error occurred: " + e.getMessage());
        }
    }

    private static byte[] createMultipartBody(Path filePath, String boundary) throws IOException {
        var byteList = new ArrayList<byte[]>();
        String separator = "--" + boundary + "\r\n";
        String fileHeader = separator + 
                            "Content-Disposition: form-data; name=\"file\"; filename=\"" + 
                            filePath.getFileName() + "\"\r\n" +
                            "Content-Type: audio/mpeg\r\n\r\n";
        
        byteList.add(fileHeader.getBytes());
        byteList.add(Files.readAllBytes(filePath));
        byteList.add(("\r\n--" + boundary + "--\r\n").getBytes());

        int totalLength = byteList.stream().mapToInt(b -> b.length).sum();
        byte[] result = new byte[totalLength];
        int offset = 0;
        for (byte[] b : byteList) {
            System.arraycopy(b, 0, result, offset, b.length);
            offset += b.length;
        }
        return result;
    }
}