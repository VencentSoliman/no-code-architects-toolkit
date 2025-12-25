# Image to Video Conversion

## 1. Overview

The `/v1/image/convert/video` endpoint is part of the Flask API application and is responsible for converting an image into a video file with customizable aspect ratios and resolutions. This endpoint is registered in the `app.py` file under the `v1_image_convert_video_bp` blueprint, which is imported from the `routes.v1.image.convert.image_to_video` module.

## Key Features

- **Flexible Aspect Ratios**: Support for various aspect ratios including original, square (1:1), standard (4:3), widescreen (16:9), vertical (9:16), ultrawide (21:9), and cinema (2.35:1)
- **Multiple Resolutions**: Options from 720p to 4K, plus original resolution preservation
- **Smart Fit Modes**: Three fitting strategies (cover, contain, fill) to handle different image-to-video transformations
- **High-Quality Processing**: 4x upscaling during processing for better quality output
- **Backward Compatible**: Defaults maintain existing behavior for existing integrations

## 2. Endpoint

**URL Path:** `/v1/image/convert/video`
**HTTP Method:** `POST`

## 3. Request

### Headers

- `x-api-key` (required): The API key for authentication.

### Body Parameters

The request body must be in JSON format and should include the following parameters:

| Parameter   | Type   | Required | Description                                                  |
|-------------|--------|----------|--------------------------------------------------------------|
| `image_url` | string | Yes      | The URL of the image to be converted into a video.          |
| `length`    | number | No       | The desired length of the video in seconds (default: 5).    |
| `frame_rate`| integer| No       | The frame rate of the output video (default: 30).           |
| `zoom_speed`| number | No       | The speed of the zoom effect (0-100, default: 3).           |
| `webhook_url`| string| No       | The URL to receive a webhook notification upon completion.  |
| `id`        | string | No       | An optional identifier for the request.                      |
| `aspect_ratio` | string | No | Target aspect ratio (default: "original"). Options: "original", "1:1", "4:3", "3:2", "16:9", "9:16", "21:9", "2.35:1" |
| `resolution` | string | No | Target resolution (default: "1080p"). Options: "original", "720p", "1080p", "1440p", "4k", "square" |
| `fit_mode` | string | No | How to fit the image (default: "cover"). Options: "cover" (fill frame, may crop), "contain" (fit within frame, may have padding), "fill" (stretch to fill frame) |

The `validate_payload` decorator in the `routes.v1.image.convert.image_to_video` module enforces the following JSON schema for the request body:

```json
{
    "type": "object",
    "properties": {
        "image_url": {"type": "string", "format": "uri"},
        "length": {"type": "number", "minimum": 0.1, "maximum": 400},
        "frame_rate": {"type": "integer", "minimum": 15, "maximum": 60},
        "zoom_speed": {"type": "number", "minimum": 0, "maximum": 100},
        "webhook_url": {"type": "string", "format": "uri"},
        "id": {"type": "string"},
        "aspect_ratio": {
            "type": "string",
            "enum": ["original", "1:1", "4:3", "3:2", "16:9", "9:16", "21:9", "2.35:1"],
            "default": "original"
        },
        "resolution": {
            "type": "string",
            "enum": ["original", "720p", "1080p", "1440p", "4k", "square"],
            "default": "1080p"
        },
        "fit_mode": {
            "type": "string",
            "enum": ["cover", "contain", "fill"],
            "default": "cover"
        }
    },
    "required": ["image_url"],
    "additionalProperties": false
}
```

### Example Request

```json
{
    "image_url": "https://example.com/image.jpg",
    "length": 10,
    "frame_rate": 24,
    "zoom_speed": 5,
    "webhook_url": "https://example.com/webhook",
    "id": "request-123",
    "aspect_ratio": "16:9",
    "resolution": "1080p",
    "fit_mode": "cover"
}
```

```bash
curl -X POST \
     -H "x-api-key: YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"image_url": "https://example.com/image.jpg", "length": 10, "frame_rate": 24, "zoom_speed": 5, "webhook_url": "https://example.com/webhook", "id": "request-123"}' \
     http://your-api-endpoint/v1/image/convert/video
```

## 4. Response

### Success Response

Upon successful processing, the endpoint returns a JSON response with the following structure:

```json
{
    "code": 200,
    "id": "request-123",
    "job_id": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6",
    "response": "https://cloud-storage.example.com/converted-video.mp4",
    "message": "success",
    "run_time": 2.345,
    "queue_time": 0.123,
    "total_time": 2.468,
    "pid": 12345,
    "queue_id": 1234567890,
    "queue_length": 0,
    "build_number": "1.0.0"
}
```

The `response` field contains the URL of the converted video file uploaded to cloud storage.

### Error Responses

#### 429 Too Many Requests

If the maximum queue length is reached, the endpoint returns a 429 Too Many Requests response:

```json
{
    "code": 429,
    "id": "request-123",
    "job_id": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6",
    "message": "MAX_QUEUE_LENGTH (10) reached",
    "pid": 12345,
    "queue_id": 1234567890,
    "queue_length": 10,
    "build_number": "1.0.0"
}
```

#### 500 Internal Server Error

If an exception occurs during the image-to-video conversion process, the endpoint returns a 500 Internal Server Error response:

```json
{
    "code": 500,
    "id": "request-123",
    "job_id": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6",
    "message": "Error message describing the exception",
    "pid": 12345,
    "queue_id": 1234567890,
    "queue_length": 0,
    "build_number": "1.0.0"
}
```

## 5. Error Handling

The endpoint handles the following types of errors:

- **Missing or invalid parameters**: If the request body is missing required parameters or contains invalid parameter values, the `validate_payload` decorator will return a 400 Bad Request response with a descriptive error message.
- **Queue length exceeded**: If the maximum queue length is reached and the `bypass_queue` parameter is set to `False`, the endpoint returns a 429 Too Many Requests response.
- **Exceptions during processing**: If an exception occurs during the image-to-video conversion process, the endpoint returns a 500 Internal Server Error response with the error message.

## 6. Usage Notes

- The `image_url` parameter must be a valid URL pointing to an image file.
- The `length` parameter specifies the duration of the output video in seconds and must be between 1 and 60.
- The `frame_rate` parameter specifies the frame rate of the output video and must be between 15 and 60.
- The `zoom_speed` parameter controls the speed of the zoom effect and must be between 0 and 100.
- The `webhook_url` parameter is optional and can be used to receive a notification when the conversion is complete.
- The `id` parameter is optional and can be used to identify the request.

## 7. Migration from Previous Version

If you were using the previous version of this endpoint, the following changes were made:

### Automatic Backward Compatibility
- The endpoint now defaults to `aspect_ratio: "original"` which preserves the previous behavior
- Default resolution is `"1080p"` (was previously forced based on orientation)
- Default fit mode is `"cover"` (best matches previous behavior)

### Breaking Changes
- None - all existing requests will continue to work with the same behavior
- New parameters are optional and have sensible defaults

### New Capabilities
- Support for multiple aspect ratios instead of automatic orientation detection
- Choice of output resolutions
- Flexible image fitting strategies
- High-quality 4x upscaling during processing

## 8. Common Issues

- Providing an invalid or inaccessible `image_url` will result in an error during processing.
- Specifying invalid parameter values outside the allowed ranges will result in a 400 Bad Request response.
- If the maximum queue length is reached and the `bypass_queue` parameter is set to `False`, the request will be rejected with a 429 Too Many Requests response.

## 8. Aspect Ratio Guide

### Available Aspect Ratios

| Ratio | Description | Use Case |
|-------|-------------|----------|
| `original` | Preserves the original image aspect ratio | When you want to maintain the image's natural proportions |
| `1:1` | Square format | Social media posts, profile pictures |
| `4:3` | Standard television format | Traditional presentations, older video content |
| `3:2` | Classic photography format | DSLR photos, film photography |
| `16:9` | Widescreen HD format | Modern displays, YouTube videos |
| `9:16` | Vertical/Portrait format | Mobile videos, TikTok, Instagram Stories |
| `21:9` | Ultrawide format | Cinema displays, immersive content |
| `2.35:1` | CinemaScope format | Movie theaters, cinematic content |

### Available Resolutions

| Resolution | Dimensions | Use Case |
|------------|------------|----------|
| `original` | Uses original image dimensions | When you want to maintain original quality |
| `720p` | 1280×720 | Web videos, smaller file sizes |
| `1080p` | 1920×1080 | Standard HD quality (default) |
| `1440p` | 2560×1440 | Quad HD, high-quality displays |
| `4k` | 3840×2160 | Ultra HD, premium quality |
| `square` | 1080×1080 | Social media square format |

### Fit Mode Explanations

| Mode | Behavior | When to Use |
|------|----------|-------------|
| `cover` | Scales image to fill the entire frame, may crop edges | When you want to fill the frame completely (default) |
| `contain` | Scales image to fit within frame, may add padding | When you want to preserve the entire image |
| `fill` | Stretches image to exactly match frame dimensions | When aspect ratio matching is not critical |

## 9. Common Use Cases

### Instagram Story (9:16 vertical)
```json
{
    "image_url": "https://example.com/photo.jpg",
    "aspect_ratio": "9:16",
    "resolution": "1080p",
    "fit_mode": "cover"
}
```

### YouTube Video (16:9 widescreen)
```json
{
    "image_url": "https://example.com/photo.jpg",
    "aspect_ratio": "16:9",
    "resolution": "1080p",
    "fit_mode": "contain"
}
```

### Social Media Square Post
```json
{
    "image_url": "https://example.com/photo.jpg",
    "aspect_ratio": "1:1",
    "resolution": "square",
    "fit_mode": "cover"
}
```

### Preserve Original Quality
```json
{
    "image_url": "https://example.com/photo.jpg",
    "aspect_ratio": "original",
    "resolution": "original",
    "fit_mode": "contain"
}
```

## 10. Best Practices

- Validate the `image_url` parameter before sending the request to ensure it points to a valid and accessible image file.
- Use the `webhook_url` parameter to receive notifications about the completion of the conversion process, rather than polling the API repeatedly.
- Provide the `id` parameter to easily identify and track the request in logs or notifications.
- Consider setting the `bypass_queue` parameter to `True` for time-sensitive requests to bypass the queue and process the request immediately.
- Choose `aspect_ratio` based on your target platform (e.g., "9:16" for mobile, "16:9" for YouTube)
- Use `contain` fit mode when you want to preserve the entire image without cropping
- Use `cover` fit mode when you want to maximize screen coverage
- For high-quality output, use "4k" resolution, but be aware of larger file sizes
- Test different combinations of aspect_ratio, resolution, and fit_mode to find the best results for your specific use case
